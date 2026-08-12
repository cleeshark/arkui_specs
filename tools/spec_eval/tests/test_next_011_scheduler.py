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

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand
from spec_eval.service.scheduler.dispatcher import Dispatcher
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import JobRepository
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
        finally:
            with self._guard:
                self.active -= 1
                self.finished.append(job_id)

    def _advance_to_semantic(self, job_id: str) -> None:
        jobs = JobRepository(self.store)
        status = jobs.get_job(job_id).status
        if status == S.QUEUED:
            jobs.transition_status(job_id, S.PREPARING, event_type="enter_preparing")
            jobs.transition_status(job_id, S.EVIDENCE, event_type="enter_evidence")
            jobs.transition_status(job_id, S.SEMANTIC, event_type="enter_semantic")


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
    def test_cancel_is_observed_by_runner(self) -> None:
        a = self._create("04-01-01", job_id="a" * 40)
        runner = _CountingRunner(self.store, hold=1.0)
        d = Dispatcher(self.store, job_runner=runner, max_workers=1)
        d.start()
        try:
            d.submit(a, "04-01-01")
            time.sleep(0.1)  # let the worker start
            self.assertTrue(d.cancel(a))
            self._wait_idle(d)
            time.sleep(0.05)
            self.assertIn(a, runner.cancelled)
        finally:
            d.shutdown()


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
