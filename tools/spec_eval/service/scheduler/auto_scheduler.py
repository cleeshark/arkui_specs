"""Auto-Scheduler: unattended, quota-bounded evaluation planning.

A thin planning layer *on top of* the :class:`~..scheduler.dispatcher.Dispatcher`
worker pool. The dispatcher only runs jobs it is handed; this decides *when* and
*which* FuncID to evaluate:

* **Start times** — one or more ``"HH:MM"`` local-time daily triggers. When a
  start time is reached a *run* becomes active.
* **Completion-chained dispatch** — while a run is active the scheduler keeps
  ``parallel_tasks`` jobs in flight; as each finishes it dispatches the next,
  draining candidates until the current per-executor token quota is exhausted or
  no eligible FuncID remains.
* **Per-executor daily quota + failover** — before every dispatch it walks the
  ordered ``executor_priority`` chain and picks the first executor whose *today's*
  token usage (all consumption, from ``executor_calls``) is still under its
  quota. When one is exhausted it fails over to the next; the run only stops when
  all executors in the chain are exhausted. Reset is daily (local midnight).
* **Failure skip** — a FuncID whose most recent job is ``failed``/``cancelled`` is
  skipped and never auto-retried; it becomes eligible again once a human retries
  it (its latest job leaves the terminal-failed state).

Selection order per dispatch: freshness tier ``MISSING > EXPIRED > EXPIRING >
FRESH`` (EXPIRED = EXPIRED_TIME or STALE_INPUT), FuncID ascending within a tier,
and FRESH additionally ordered by the current report's ``completed_at`` ascending
(oldest report refreshed first).

Dispatch reuses ``app.refresh_function(...)`` so job creation, fingerprint
dedup, workspace preparation and enqueue are not re-implemented here.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from .. import freshness as F
from ..domain import states as S

LOGGER = logging.getLogger(__name__)

DEFAULT_DAILY_QUOTA = 10_000_000
"""Default per-executor daily token budget when the config omits one."""

_IDLE_POLL_SECONDS = 15.0
_ACTIVE_POLL_SECONDS = 5.0

# Freshness value -> priority tier (lower runs first).
_TIER = {
    F.MISSING: 0,
    F.EXPIRED_TIME: 1,
    F.STALE_INPUT: 1,
    F.EXPIRING: 2,
    F.FRESH: 3,
}
_SKIP_STATUSES = frozenset({S.FAILED, S.CANCELLED})


class AutoScheduler:
    """Timer-triggered, quota-bounded planner layered over the dispatcher."""

    def __init__(self, app, *, config_repo, usage_repo, jobs_repo) -> None:
        self._app = app
        self._config_repo = config_repo
        self._usage_repo = usage_repo
        self._jobs_repo = jobs_repo
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # in-memory run state (see module docstring for the recovery rationale)
        self._run_active = False
        self._inflight: dict[str, str] = {}  # job_id -> func_id dispatched this run
        self._skipped_this_run: set[str] = set()  # dispatch-error funcs, transient
        self._trigger_day: str | None = None  # local date of the current trigger set
        self._triggered: set[str] = set()  # HH:MM already fired today
        self._last_dispatched: str | None = None
        self._last_error: str | None = None
        self._active_executor: str | None = None

    # --- lifecycle --------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="auto-scheduler", daemon=True
        )
        self._thread.start()

    def stop(self, *, timeout: float = 5.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)
        self._thread = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:  # noqa: BLE001 - a planning tick must never kill the loop
                LOGGER.exception("auto-scheduler tick failed")
            interval = _ACTIVE_POLL_SECONDS if self._run_active else _IDLE_POLL_SECONDS
            self._stop.wait(interval)

    # --- core planning tick ----------------------------------------------
    def tick(self, *, now: datetime | None = None) -> None:
        """Reconcile one planning step. Safe to call directly from tests."""
        now = now or datetime.now().astimezone()
        with self._lock:
            config = self._config_repo.get()
            if not config.enabled:
                self._run_active = False
                self._active_executor = None
                return
            self._reap_inflight()
            if self._should_trigger(config, now):
                self._run_active = True
                self._skipped_this_run.clear()
            if self._run_active:
                self._dispatch_due(config, now)

    # --- trigger detection ------------------------------------------------
    def _should_trigger(self, config, now: datetime) -> bool:
        day = now.strftime("%Y-%m-%d")
        if day != self._trigger_day:
            self._trigger_day = day
            self._triggered = set()
        current = now.strftime("%H:%M")
        fired = False
        for start in config.start_times:
            if start in self._triggered:
                continue
            if current >= start:
                self._triggered.add(start)
                fired = True
        return fired

    # --- dispatch loop ----------------------------------------------------
    def _dispatch_due(self, config, now: datetime) -> None:
        usage = self._usage_repo.usage_by_executor_since(self._day_start_iso(now))
        while len(self._inflight) < max(1, config.parallel_tasks):
            executor = self._select_executor(config, usage)
            if executor is None:
                # every executor in the chain is over quota -> run is finished
                self._run_active = False
                self._active_executor = None
                return
            self._active_executor = executor
            func_id = self._select_next_func(config)
            if func_id is None:
                if not self._inflight:
                    self._run_active = False
                return  # wait for in-flight jobs to finish / free a slot
            try:
                result = self._app.refresh_function(func_id=func_id, agent_id=executor)
            except Exception as exc:  # noqa: BLE001 - one func must not stall the run
                self._skipped_this_run.add(func_id)
                self._last_error = f"{func_id}: {exc}"
                LOGGER.warning("auto-scheduler dispatch failed for %s: %s", func_id, exc)
                continue
            self._inflight[result.job.job_id] = func_id
            self._last_dispatched = func_id

    def _select_executor(self, config, usage: dict[str, int]) -> str | None:
        chain = config.executor_priority or (self._app.default_agent,)
        for name in chain:
            quota = config.executor_quota.get(name, DEFAULT_DAILY_QUOTA)
            used = usage.get(self._executor_identity(name), 0)
            if used < quota:
                return name
        return None

    def _select_next_func(self, config) -> str | None:
        skip = self._skip_funcs()
        candidates: list[tuple[int, str, str]] = []
        for func in self._app.list_functions():
            func_id = func["func_id"]
            if func_id in self._inflight.values() or func_id in self._skipped_this_run:
                continue
            if func.get("active_job_id"):
                continue
            if func_id in skip:
                continue
            tier = _TIER.get(func.get("freshness"), 3)
            report = func.get("current_report") or {}
            completed_at = report.get("completed_at") or "" if tier == 3 else ""
            candidates.append((tier, completed_at, func_id))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        return candidates[0][2]

    # --- helpers ----------------------------------------------------------
    def _reap_inflight(self) -> None:
        for job_id in list(self._inflight):
            try:
                job = self._jobs_repo.get_job(job_id)
            except Exception:  # noqa: BLE001 - a vanished job frees its slot
                self._inflight.pop(job_id, None)
                continue
            if job.status in S.TERMINAL_STATES:
                self._inflight.pop(job_id, None)

    def _skip_funcs(self) -> set[str]:
        """FuncIDs whose most recent job is terminal-failed/cancelled."""
        latest: dict[str, Any] = {}
        for job in self._jobs_repo.list_jobs(limit=100_000):
            prev = latest.get(job.func_id)
            if prev is None or job.created_at > prev.created_at:
                latest[job.func_id] = job
        return {
            func_id
            for func_id, job in latest.items()
            if job.status in _SKIP_STATUSES
        }

    def _executor_identity(self, agent_id: str) -> str:
        """Map an agent id (``codex``) to the stored executor identity (``codex-cli``).

        ``executor_calls.executor`` records the executor ``type``, so quota
        accounting must key on that, not the short agent id.
        """
        try:
            return str(self._app.resolve_executor_config(agent_id).get("type", agent_id))
        except Exception:  # noqa: BLE001 - unknown agent -> use the id verbatim
            return agent_id

    @staticmethod
    def _day_start_iso(now: datetime) -> str:
        """UTC ISO timestamp of local midnight for ``now`` (quota window start)."""
        local = now if now.tzinfo is not None else now.astimezone()
        midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
        return midnight.astimezone(timezone.utc).isoformat(timespec="seconds")

    # --- observability ----------------------------------------------------
    def status(self, *, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now().astimezone()
        with self._lock:
            config = self._config_repo.get()
            usage = self._usage_repo.usage_by_executor_since(self._day_start_iso(now))
            chain = config.executor_priority or (self._app.default_agent,)
            executors = [
                {
                    "agent_id": name,
                    "used_tokens": usage.get(self._executor_identity(name), 0),
                    "quota_tokens": config.executor_quota.get(name, DEFAULT_DAILY_QUOTA),
                }
                for name in chain
            ]
            return {
                "enabled": config.enabled,
                "run_active": self._run_active,
                "active_executor": self._active_executor,
                "inflight_jobs": [
                    {"job_id": jid, "func_id": fid}
                    for jid, fid in self._inflight.items()
                ],
                "inflight_count": len(self._inflight),
                "parallel_tasks": config.parallel_tasks,
                "start_times": list(config.start_times),
                "next_start_time": self._next_start_time(config, now),
                "last_dispatched_func": self._last_dispatched,
                "last_error": self._last_error,
                "executors": executors,
                "quota_window_start": self._day_start_iso(now),
            }

    def _next_start_time(self, config, now: datetime) -> str | None:
        if not config.start_times:
            return None
        current = now.strftime("%H:%M")
        upcoming = sorted(t for t in config.start_times if t > current)
        return upcoming[0] if upcoming else sorted(config.start_times)[0]
