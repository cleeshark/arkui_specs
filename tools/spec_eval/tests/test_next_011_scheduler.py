"""Host unit tests for the Phase 3 scheduler (TASK-011-05).

The dispatcher is driven with an injectable counting fake runner (no real
pipeline/Codex), covering bounded concurrency, same-FuncID serialization,
cooperative cancellation, fail-then-retry, and start-up recovery of queued jobs.

    python3 -m unittest spec_eval.tests.test_next_011_scheduler -v
"""

from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline.semantic_stage import SemanticStageResult
from spec_eval.service.scheduler.dispatcher import Dispatcher
from spec_eval.service.scheduler.job_worker import build_runner
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore


class _CountingRunner:
    """Fake job_runner: records concurrency, honours cancel, can fail once."""

    def __init__(self, store: SqliteStore, *, fail_once: set[str] | None = None, hold: float = 0.25) -> None:
        self.store = store
        self.fail_once = set(fail_once or ())
        self.hold = hold
        self._guard = threading.Lock()
        self.active = 0
        self.max_active = 0
        self.started: list[str] = []
        self.finished: list[str] = []
        self.cancelled: list[str] = []
        self._failed_already: set[str] = set()

    def __call__(self, job_id: str, cancel: threading.Event) -> None:
        with self._guard:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.started.append(job_id)
        try:
            # mimic the real pipeline's legal state prefix before work begins
            self._advance_to_semantic(job_id)
            end = time.monotonic() + self.hold
            while time.monotonic() < end:
                if cancel.is_set():
                    with self._guard:
                        self.cancelled.append(job_id)
                    return
                time.sleep(0.01)
            if job_id in self.fail_once and job_id not in self._failed_already:
                self._failed_already.add(job_id)
                JobRepository(self.store).transition_status(
                    job_id, S.FAILED, event_type="fake_fail", payload={"reason": "injected"}
                )
            elif JobRepository(self.store).get_job(job_id).status == S.RUNNING:
                jobs = JobRepository(self.store)
                for stage in (S.STAGE_AGGREGATION, S.STAGE_REPORT, S.STAGE_ARCHIVE):
                    jobs.transition_status(
                        job_id, S.RUNNING, stage=stage, event_type=f"enter_{stage}"
                    )
                jobs.transition_status(job_id, S.COMPLETED, event_type="job_completed")
        finally:
            with self._guard:
                self.active -= 1
                self.finished.append(job_id)

    def _advance_to_semantic(self, job_id: str) -> None:
        jobs = JobRepository(self.store)
        job = jobs.get_job(job_id)
        if job.status == S.QUEUED:
            jobs.transition_status(job_id, S.RUNNING, event_type="enter_running")
        for stage in (S.STAGE_PREPARING, S.STAGE_EVIDENCE, S.STAGE_OBSERVATION):
            jobs.transition_status(
                job_id, S.RUNNING, stage=stage, event_type=f"enter_{stage}"
            )


class _SchedulerTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _create(self, func_id: str, *, job_id: str | None = None) -> str:
        cmd = CreateJobCommand(
            func_id=func_id, source_revision="rev-" + func_id, run_count=1, job_id=job_id
        )
        return self.jobs.create_job(cmd, evaluator_version="x").job_id

    def _wait_idle(self, dispatcher: Dispatcher, timeout: float = 5.0) -> None:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if dispatcher.is_idle:
                return
            time.sleep(0.02)


class ConcurrencyTest(_SchedulerTestBase):
    def test_different_funcids_run_in_parallel(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        b = self._create("04-02-02", job_id="b" * 40)
        runner = _CountingRunner(self.store, hold=0.3)
        d = Dispatcher(self.store, job_runner=runner, max_workers=2)
        d.start()
        try:
            d.submit(a, "04-01-01")
            d.submit(b, "04-02-02")
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertEqual(runner.max_active, 2)
            self.assertEqual(sorted(runner.started), [a, b])
        finally:
            d.shutdown()

    def test_same_funcid_is_serialized(self) -> None:
        a = self._create("04-03-03", job_id="a" * 40)
        b = self._create("04-03-03", job_id="b" * 40)
        runner = _CountingRunner(self.store, hold=0.3)
        d = Dispatcher(self.store, job_runner=runner, max_workers=2)
        d.start()
        try:
            d.submit(a, "04-03-03")
            d.submit(b, "04-03-03")
            self._wait_idle(d)
            time.sleep(0.05)
            # same FuncID never overlaps
            self.assertEqual(runner.max_active, 1)
            self.assertEqual(sorted(runner.started), [a, b])
        finally:
            d.shutdown()

    def test_single_failure_does_not_block_others(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        b = self._create("04-02-02", job_id="b" * 40)
        runner = _CountingRunner(self.store, fail_once={a}, hold=0.2)
        d = Dispatcher(self.store, job_runner=runner, max_workers=2)
        d.start()
        try:
            d.submit(a, "04-01-01")
            d.submit(b, "04-02-02")
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertEqual(self.jobs.get_job(a).status, S.FAILED)
            # b still ran to completion (not failed)
            self.assertIn(b, runner.finished)
            self.assertNotEqual(self.jobs.get_job(b).status, S.FAILED)
        finally:
            d.shutdown()


class CancellationTest(_SchedulerTestBase):
    def test_cancel_is_observed_and_persisted_by_runner(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        runner = _CountingRunner(self.store, hold=1.0)
        d = Dispatcher(self.store, job_runner=runner, max_workers=1)
        d.start()
        try:
            d.submit(a, "04-01-01")
            time.sleep(0.1)  # let the worker start
            result = d.cancel(a)
            self.assertTrue(result.accepted)
            self.assertEqual(result.outcome, "cancellation_requested")
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertIn(a, runner.cancelled)
            self.assertEqual(self.jobs.get_job(a).status, S.CANCELLED)
            self.assertIn(
                "cancelled",
                [event.event_type for event in EventRepository(self.store).list_for_job(a)],
            )
            self.assertIsNotNone(JobStatisticsRepository(self.store).get(a).finished_at)
            self.assertNotIn(a, d._cancels.active())
        finally:
            d.shutdown()

    def test_queued_job_is_cancelled_before_worker_start(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        runner = _CountingRunner(self.store, hold=0.1)
        d = Dispatcher(self.store, job_runner=runner, max_workers=1)
        d.submit(a, "04-01-01")

        result = d.cancel(a)

        self.assertTrue(result.accepted)
        self.assertEqual(result.outcome, "cancelled")
        self.assertEqual(self.jobs.get_job(a).status, S.CANCELLED)
        d.start()
        try:
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertNotIn(a, runner.started)
        finally:
            d.shutdown()

    def test_awaiting_executor_job_is_cancelled_without_registry_entry(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        self.jobs.transition_status(a, S.RUNNING, event_type="enter_running")
        self.jobs.transition_status(a, S.WAITING, event_type="awaiting_executor")
        d = Dispatcher(self.store, job_runner=lambda job_id, cancel: None, max_workers=1)

        result = d.cancel(a)

        self.assertTrue(result.accepted)
        self.assertEqual(result.outcome, "cancelled")
        self.assertEqual(self.jobs.get_job(a).status, S.CANCELLED)

    def test_runner_returning_nonterminal_job_is_failed(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)

        def incomplete_runner(job_id: str, cancel: threading.Event) -> None:
            jobs = JobRepository(self.store)
            jobs.transition_status(job_id, S.RUNNING, event_type="enter_running")
            jobs.transition_status(
                job_id, S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="enter_observation"
            )

        d = Dispatcher(self.store, job_runner=incomplete_runner, max_workers=1)
        d.start()
        try:
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertEqual(self.jobs.get_job(a).status, S.FAILED)
            self.assertIn(
                "worker_returned_nonterminal",
                [event.event_type for event in EventRepository(self.store).list_for_job(a)],
            )
        finally:
            d.shutdown()

    def test_job_cancelled_while_waiting_for_func_lock_never_enters_runner(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        b = self._create("04-01-01", job_id="b" * 40)
        runner = _CountingRunner(self.store, hold=0.5)
        d = Dispatcher(self.store, job_runner=runner, max_workers=2)
        d.start()
        try:
            deadline = time.monotonic() + 3.0
            while not runner.started and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(runner.started)
            running = runner.started[0]
            waiting = b if running == a else a

            result = d.cancel(waiting)

            self.assertTrue(result.accepted)
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertNotIn(waiting, runner.started)
            self.assertEqual(self.jobs.get_job(waiting).status, S.CANCELLED)
        finally:
            d.shutdown()


class JobWorkerCancellationTest(_SchedulerTestBase):
    def test_aggregation_cancelled_outcome_is_persisted_before_cleanup(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        self.jobs.transition_status(a, S.RUNNING, event_type="enter_running")
        self.jobs.transition_status(
            a, S.RUNNING, stage=S.STAGE_PREPARING, event_type="enter_preparing"
        )
        self.jobs.transition_status(
            a, S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="enter_evidence"
        )
        self.jobs.transition_status(
            a, S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="enter_observation"
        )
        self.jobs.transition_status(
            a, S.RUNNING, stage=S.STAGE_AGGREGATION, event_type="enter_aggregation"
        )
        runner = build_runner(self.settings, self.store, object())

        with (
            patch(
                "spec_eval.service.scheduler.job_worker.run_job_pipeline",
                return_value=SemanticStageResult(C.STATUS_CANCELLED, 0, "cancelled by user"),
            ),
            patch(
                "spec_eval.service.scheduler.job_worker._mark_refresh_failed"
            ) as mark_refresh_failed,
            patch(
                "spec_eval.service.scheduler.job_worker.RevisionWorkspaceManager.release"
            ) as release_workspace,
        ):
            runner(a, threading.Event())

        self.assertEqual(self.jobs.get_job(a).status, S.CANCELLED)
        self.assertIn(
            "cancelled",
            [event.event_type for event in EventRepository(self.store).list_for_job(a)],
        )
        mark_refresh_failed.assert_called_once_with(self.store, ANY, a, S.CANCELLED)
        release_workspace.assert_called_once_with(a)


class RetryTest(_SchedulerTestBase):
    def test_failed_job_can_be_retried_and_reruns(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        runner = _CountingRunner(self.store, fail_once={a}, hold=0.15)
        d = Dispatcher(self.store, job_runner=runner, max_workers=1)
        d.start()
        try:
            d.submit(a, "04-01-01")
            # wait for first (failing) run
            end = time.monotonic() + 5.0
            while time.monotonic() < end and self.jobs.get_job(a).status != S.FAILED:
                time.sleep(0.02)
            self.assertEqual(self.jobs.get_job(a).status, S.FAILED)
            self.assertEqual(runner.started.count(a), 1)
            # retry resets to queued and re-enqueues; second run succeeds
            self.assertEqual(d.retry(a), S.QUEUED)
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertEqual(runner.started.count(a), 2)
            self.assertNotEqual(self.jobs.get_job(a).status, S.FAILED)
        finally:
            d.shutdown()


class StartupRecoveryTest(_SchedulerTestBase):
    def test_queued_jobs_are_picked_up_on_start(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)  # created queued
        runner = _CountingRunner(self.store, hold=0.1)
        d = Dispatcher(self.store, job_runner=runner, max_workers=1)
        d.start()  # no explicit submit
        try:
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertIn(a, runner.started)
        finally:
            d.shutdown()


if __name__ == "__main__":
    unittest.main()
