"""Host unit tests for the Auto-Scheduler (定时任务调度 / auto planning layer).

The planner is driven directly via ``tick(now=...)`` with a fake app so no real
pipeline, executor or timer thread is needed. Covers freshness-tier selection,
failed-task skip, per-executor daily quota with priority failover, the parallel
in-flight cap with completion-chained dispatch, start-time triggering, and the
config/usage repositories plus HTTP routes.

    python3 -m unittest spec_eval.tests.test_next_013_auto_scheduler -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand, SchedulerConfig
from spec_eval.service.http import routes
from spec_eval.service.scheduler.auto_scheduler import AutoScheduler, DEFAULT_DAILY_QUOTA
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    ExecutorCallRepository,
    JobRepository,
    SchedulerConfigRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore, utc_now


def _func(func_id: str, freshness: str, *, completed_at: str = "", active_job_id=None):
    report = {"completed_at": completed_at} if completed_at else None
    return {
        "func_id": func_id,
        "freshness": freshness,
        "current_report": report,
        "active_job_id": active_job_id,
    }


class _FakeApp:
    """Minimal app surface the AutoScheduler needs; creates real job rows."""

    def __init__(self, store: SqliteStore, functions: list[dict]) -> None:
        self.store = store
        self.jobs = JobRepository(store)
        self._functions = functions
        self.default_agent = "codex"
        self.dispatched: list[tuple[str, str]] = []

    def list_functions(self):
        return list(self._functions)

    def default_source_revision(self) -> str:
        return "rev"

    def resolve_executor_config(self, agent_id=None, agent_params=None) -> dict:
        name = agent_id or self.default_agent
        return {"type": f"{name}-cli", "agent_id": name}

    def refresh_function(self, *, func_id, source_revision=None, run_count=1,
                         agent_id=None, agent_params=None):
        cmd = CreateJobCommand(func_id=func_id, source_revision="rev", run_count=1)
        job = self.jobs.create_job(cmd, evaluator_version="x")
        self.dispatched.append((func_id, agent_id))
        return SimpleNamespace(job=job, target=None, deduplicated=False)


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.config_repo = SchedulerConfigRepository(self.store)
        self.usage_repo = ExecutorCallRepository(self.store)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _scheduler(self, functions: list[dict]) -> tuple[AutoScheduler, _FakeApp]:
        app = _FakeApp(self.store, functions)
        sched = AutoScheduler(
            app,
            config_repo=self.config_repo,
            usage_repo=self.usage_repo,
            jobs_repo=self.jobs,
        )
        return sched, app

    def _set_config(self, **fields) -> SchedulerConfig:
        defaults = dict(
            enabled=True, start_times=("00:00",), parallel_tasks=1,
            executor_priority=("codex",), executor_quota={"codex": DEFAULT_DAILY_QUOTA},
            version=self.config_repo.get().version + 1, updated_at=utc_now(),
        )
        defaults.update(fields)
        return self.config_repo.set(SchedulerConfig(**defaults))

    def _set_status(self, job_id: str, status: str) -> None:
        with self.store._tx(immediate=True) as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (status, utc_now(), job_id),
            )

    def _record_usage(self, executor: str, total_tokens: int, *, when=None) -> None:
        # executor_calls needs a real job (FK); attach the usage to a throwaway one.
        job = self.jobs.create_job(
            CreateJobCommand(func_id="99-99-99", source_revision="rev", run_count=1),
            evaluator_version="x",
        )
        with self.store._tx() as conn:
            conn.execute(
                "INSERT INTO executor_calls (job_id, run_id, work_item_id, attempt_type, "
                "executor, status, started_at, duration_ms, usage_json, telemetry_json) "
                "VALUES (?, '', 'w', 'observe', ?, 'completed', ?, 0, ?, '{}')",
                (
                    job.job_id, executor, when or utc_now(),
                    json.dumps({"total_tokens": total_tokens}),
                ),
            )


class SelectionOrderTest(_Base):
    def test_tier_then_funcid_then_fresh_by_date(self) -> None:
        functions = [
            _func("04-01-02", "FRESH", completed_at="2026-01-10T00:00:00+00:00"),
            _func("04-01-01", "FRESH", completed_at="2026-01-05T00:00:00+00:00"),
            _func("03-02-02", "EXPIRING"),
            _func("02-01-02", "EXPIRED_TIME"),
            _func("02-01-01", "STALE_INPUT"),
            _func("01-01-02", "MISSING"),
            _func("01-01-01", "MISSING"),
        ]
        sched, app = self._scheduler(functions)
        config = self._set_config(executor_quota={"codex": DEFAULT_DAILY_QUOTA})
        order = []
        # Drain by removing each selected func from the catalog.
        while True:
            picked = sched._select_next_func(config)
            if picked is None:
                break
            order.append(picked)
            app._functions = [f for f in app._functions if f["func_id"] != picked]
        self.assertEqual(
            order,
            [
                "01-01-01", "01-01-02",       # MISSING, by func_id
                "02-01-01", "02-01-02",       # EXPIRED (STALE_INPUT + EXPIRED_TIME)
                "03-02-02",                    # EXPIRING
                "04-01-01", "04-01-02",       # FRESH, earliest completed_at first
            ],
        )

    def test_active_job_func_is_excluded(self) -> None:
        functions = [_func("04-01-01", "MISSING", active_job_id="job-x")]
        sched, _ = self._scheduler(functions)
        config = self._set_config()
        self.assertIsNone(sched._select_next_func(config))


class FailedSkipTest(_Base):
    def test_failed_func_is_skipped_until_retried(self) -> None:
        functions = [_func("04-01-01", "MISSING")]
        sched, app = self._scheduler(functions)
        config = self._set_config()
        # A prior failed job for this func -> skipped.
        failed = self.jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=1),
            evaluator_version="x",
        )
        self._set_status(failed.job_id, S.FAILED)
        self.assertIsNone(sched._select_next_func(config))
        # Human retries: the job leaves the failed state -> eligible again.
        self._set_status(failed.job_id, S.QUEUED)
        self.assertEqual(sched._select_next_func(config), "04-01-01")


class QuotaFailoverTest(_Base):
    def test_failover_then_stop_when_all_exhausted(self) -> None:
        functions = [_func(f"04-01-0{i}", "MISSING") for i in range(1, 6)]
        sched, app = self._scheduler(functions)
        self._set_config(
            parallel_tasks=1,
            executor_priority=("codex", "claude"),
            executor_quota={"codex": 1000, "claude": 1000},
        )
        now = datetime.now().astimezone()
        # codex over quota -> failover to claude.
        self._record_usage("codex-cli", 1000)
        sched.tick(now=now)
        self.assertEqual(len(app.dispatched), 1)
        self.assertEqual(app.dispatched[-1][1], "claude")
        # claude also over quota -> run stops, nothing more dispatched.
        self._record_usage("claude-cli", 1000)
        # free the in-flight slot so the quota check (not the cap) is what stops us
        self._set_status(_job_for(self, app.dispatched[-1][0]), S.COMPLETED)
        before = len(app.dispatched)
        sched.tick(now=now)
        self.assertEqual(len(app.dispatched), before)
        self.assertFalse(sched._run_active)


class ParallelChainingTest(_Base):
    def test_cap_and_refill_on_completion(self) -> None:
        functions = [_func(f"04-01-0{i}", "MISSING") for i in range(1, 6)]
        sched, app = self._scheduler(functions)
        self._set_config(parallel_tasks=2)
        now = datetime.now().astimezone()
        sched.tick(now=now)
        self.assertEqual(len(app.dispatched), 2)  # filled the cap
        # remove dispatched funcs from the catalog so they are not reselected
        done_func, done_job = app.dispatched[0][0], _job_for(self, app.dispatched[0][0])
        app._functions = [f for f in app._functions if f["func_id"] != done_func]
        sched.tick(now=now)
        self.assertEqual(len(app.dispatched), 2)  # still capped, both in flight
        # complete one -> a slot frees -> next tick dispatches one more
        self._set_status(done_job, S.COMPLETED)
        sched.tick(now=now)
        self.assertEqual(len(app.dispatched), 3)


class StartTimeTest(_Base):
    def test_run_only_after_start_time(self) -> None:
        functions = [_func("04-01-01", "MISSING")]
        sched, app = self._scheduler(functions)
        self._set_config(start_times=("23:59",))
        early = datetime.now().astimezone().replace(hour=0, minute=5)
        sched.tick(now=early)
        self.assertEqual(app.dispatched, [])
        self.assertFalse(sched._run_active)
        late = datetime.now().astimezone().replace(hour=23, minute=59)
        sched.tick(now=late)
        self.assertEqual(len(app.dispatched), 1)

    def test_disabled_never_dispatches(self) -> None:
        functions = [_func("04-01-01", "MISSING")]
        sched, app = self._scheduler(functions)
        self._set_config(enabled=False, start_times=("00:00",))
        sched.tick(now=datetime.now().astimezone())
        self.assertEqual(app.dispatched, [])


class RepositoryTest(_Base):
    def test_usage_by_executor_since_window(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(timespec="seconds")
        self._record_usage("codex-cli", 500, when=old)      # outside window
        self._record_usage("codex-cli", 1500)
        self._record_usage("claude-cli", 700)
        start = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
        usage = self.usage_repo.usage_by_executor_since(start)
        self.assertEqual(usage.get("codex-cli"), 1500)
        self.assertEqual(usage.get("claude-cli"), 700)

    def test_config_version_must_increase(self) -> None:
        self._set_config(version=self.config_repo.get().version + 1)
        with self.assertRaises(Exception):
            self.config_repo.set(self.config_repo.get())  # same version


class HttpRouteTest(_Base):
    def _app(self):
        return _FakeApp(self.store, [])

    def test_config_get_post_and_status(self) -> None:
        # Use the real SemanticServiceApp for routes (needs set_scheduler_config).
        from spec_eval.service.app import SemanticServiceApp
        app = SemanticServiceApp(self.settings, max_workers=1)
        try:
            def call(method, path, body=None):
                raw = json.dumps(body).encode() if body is not None else b""
                r = routes.route_request(method, path, raw, {}, app)
                return r.status, json.loads(r.body.decode())

            status, cfg = call("GET", "/api/scheduler/config")
            self.assertEqual(status, 200)
            self.assertFalse(cfg["enabled"])

            status, cfg = call("POST", "/api/scheduler/config", {
                "enabled": True, "start_times": ["02:00"], "parallel_tasks": 2,
                "executor_priority": ["codex", "claude"],
                "executor_quota": {"codex": 10_000_000},
            })
            self.assertEqual(status, 200)
            self.assertEqual(cfg["executor_priority"], ["codex", "claude"])

            status, body = call("GET", "/api/scheduler/status")
            self.assertEqual(status, 200)
            self.assertIn("executors", body)

            status, _ = call("POST", "/api/scheduler/config", {"nope": 1})
            self.assertEqual(status, 400)
            status, _ = call("POST", "/api/scheduler/config", {"executor_priority": ["ghost"]})
            self.assertEqual(status, 400)
        finally:
            app.stop()


def _job_for(test: _Base, func_id: str) -> str:
    for job in test.jobs.list_jobs(limit=1000):
        if job.func_id == func_id:
            return job.job_id
    raise AssertionError(f"no job for {func_id}")


if __name__ == "__main__":
    unittest.main()
