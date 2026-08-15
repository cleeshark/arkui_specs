"""Host unit tests for the NEXT-011 semantic service Phase 1 foundation.

Covers the Job state machine, the SQLite Job Store idempotency, monotonic event
seq under concurrency, cancel/retry history preservation, checkpoint idempotency,
the crash-recovery anti-fake-completion rule, and the job JSON Schema.

Pure Python stdlib (unittest), no device and no Codex. Run from specs/tools:

    python3 -m unittest spec_eval.tests.test_next_011_semantic_service -v
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from spec_eval.protocol_validator import JsonSchemaSubsetValidator
from spec_eval.service.domain import states as S
from spec_eval.service.domain.errors import (
    CheckpointExistsError,
    DuplicateJobError,
    IllegalTransitionError,
    JobNotFoundError,
)
from spec_eval.service.domain.models import (
    Attempt,
    CreateJobCommand,
    DependencySnapshot,
    default_progress,
    make_job_id,
)
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EventRepository,
    JobStatisticsRepository,
    JobRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore, utc_now

EVALUATOR_VERSION = "0.1.11"
JOB_ID = "a" * 24 + "b" * 24  # 48 chars, satisfies minLength 16


def _attempt(job_id: str, *, stage: str = S.STAGE_EVIDENCE, status: str = S.ATTEMPT_COMPLETED) -> Attempt:
    return Attempt(
        attempt_id=make_job_id(),
        job_id=job_id,
        run_id=None,
        feat_id=None,
        stage=stage,
        status=status,
        started_at=utc_now(),
        finished_at=utc_now(),
        exit_code=0,
        artifact_dir=None,
    )


class _StoreTestBase(unittest.TestCase):
    """Common fixture: a fresh store + repositories in a temp data-root."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.events = EventRepository(self.store)
        self.attempts = AttemptRepository(self.store)
        self.artifacts = ArtifactRepository(self.store)
        self.snapshots = DependencySnapshotRepository(self.store)
        self.statistics = JobStatisticsRepository(self.store)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _create(self, **overrides) -> CreateJobCommand:
        kwargs = {
            "func_id": "04-01-01",
            "source_revision": "rev-1234567890abcdef",
            "run_count": 3,
            "job_id": JOB_ID,
        }
        kwargs.update(overrides)
        return CreateJobCommand(**kwargs)


class IdempotentCreateTest(_StoreTestBase):
    def test_repeat_create_returns_same_job_and_no_duplicate_row(self) -> None:
        cmd = self._create()
        first = self.jobs.create_job(cmd, evaluator_version=EVALUATOR_VERSION)
        second = self.jobs.create_job(cmd, evaluator_version=EVALUATOR_VERSION)
        self.assertEqual(first.job_id, second.job_id)
        self.assertEqual(len(self.jobs.list_jobs()), 1)

    def test_create_without_job_id_always_mints_new(self) -> None:
        a = self.jobs.create_job(self._create(job_id=None), evaluator_version=EVALUATOR_VERSION)
        b = self.jobs.create_job(self._create(job_id=None), evaluator_version=EVALUATOR_VERSION)
        self.assertNotEqual(a.job_id, b.job_id)
        self.assertEqual(len(self.jobs.list_jobs()), 2)

    def test_conflicting_immutable_fields_raise_duplicate(self) -> None:
        self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        conflict = self._create(source_revision="different-revision")
        with self.assertRaises(DuplicateJobError):
            self.jobs.create_job(conflict, evaluator_version=EVALUATOR_VERSION)
        # The conflicting request must not have created a second row.
        self.assertEqual(len(self.jobs.list_jobs()), 1)

    def test_get_unknown_job_raises(self) -> None:
        with self.assertRaises(JobNotFoundError):
            self.jobs.get_job("no-such-job")


class StateTransitionTest(_StoreTestBase):
    def test_job_statistics_track_lifecycle_and_executor_usage(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        initial = self.statistics.get(job.job_id)
        self.assertIsNone(initial.started_at)
        self.assertIsNone(initial.finished_at)

        self.jobs.transition_status(job.job_id, S.PREPARING, event_type="enter_preparing")
        running = self.statistics.get(job.job_id)
        self.assertIsNotNone(running.started_at)
        self.statistics.record_executor_result(
            job.job_id,
            elapsed_seconds=1.25,
            token_usage={
                "input_tokens": 100,
                "cached_input_tokens": 20,
                "cache_write_input_tokens": 0,
                "output_tokens": 30,
                "reasoning_output_tokens": 5,
                "total_tokens": 130,
            },
            usage_reported=True,
        )
        for dst in (
            S.EVIDENCE, S.SEMANTIC, S.AGGREGATION, S.ARCHIVE,
            S.SITE_HISTORY, S.COMPLETED,
        ):
            self.jobs.transition_status(job.job_id, dst, event_type=f"enter_{dst}")

        completed = self.statistics.get(job.job_id)
        self.assertIsNotNone(completed.finished_at)
        self.assertEqual(completed.executor_invocations, 1)
        self.assertEqual(completed.usage_reported_invocations, 1)
        self.assertEqual(completed.executor_elapsed_ms, 1250)
        self.assertEqual(completed.total_tokens, 130)

    def test_legal_worker_path(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        job = self.jobs.transition_status(job.job_id, S.PREPARING, event_type="enter_preparing")
        self.assertEqual(job.status, S.PREPARING)
        job = self.jobs.transition_status(job.job_id, S.EVIDENCE, event_type="enter_evidence")
        self.assertEqual(job.status, S.EVIDENCE)

    def test_matrix_rejects_illegal_move(self) -> None:
        # completed is terminal: no outbound edges
        for dst in S.JOB_STATES:
            if dst == S.COMPLETED:
                continue
            self.assertFalse(S.can_transition(S.COMPLETED, dst), dst)
        with self.assertRaises(IllegalTransitionError):
            S.transition(S.COMPLETED, S.QUEUED)

    def test_backward_edge_only_via_retry(self) -> None:
        # aggregation has no direct backward edge to queued (only -> archive/failed)
        self.assertFalse(S.can_transition(S.AGGREGATION, S.QUEUED))
        # only failed/cancelled may go back to queued
        self.assertTrue(S.can_transition(S.FAILED, S.QUEUED))
        self.assertTrue(S.can_transition(S.CANCELLED, S.QUEUED))
        self.assertTrue(S.can_transition(S.AGGREGATION, S.CANCELLED))

    def test_transition_unknown_job_raises(self) -> None:
        with self.assertRaises(JobNotFoundError):
            self.jobs.transition_status("nope", S.PREPARING, event_type="x")

    def test_repo_transition_rejects_illegal(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        with self.assertRaises(IllegalTransitionError):
            # queued -> completed is not in the matrix
            self.jobs.transition_status(job.job_id, S.COMPLETED, event_type="x")


class EventSeqConcurrencyTest(_StoreTestBase):
    def test_monotonic_seq_under_threads(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        collected: list[int] = []
        lock = threading.Lock()
        n_threads, per_thread = 8, 50

        def worker() -> None:
            local: list[int] = []
            for _ in range(per_thread):
                ev = self.events.append(job.job_id, "progress", {"i": 1})
                local.append(ev.seq)
            with lock:
                collected.extend(local)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected_count = n_threads * per_thread
        self.assertEqual(len(collected), expected_count)
        self.assertEqual(len(set(collected)), len(collected))  # no dups
        # contiguous: no gaps (the job_created event occupies seq 1, so the
        # thread events start at seq 2; assert contiguity rather than a hardcoded range).
        lo, hi = min(collected), max(collected)
        self.assertEqual(hi - lo + 1, expected_count)


class CancelPreservesAttemptsTest(_StoreTestBase):
    def test_cancel_keeps_history(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        self.jobs.transition_status(job.job_id, S.PREPARING, event_type="enter_preparing")
        att = self.attempts.record_checkpoint(_attempt(job.job_id))
        self.events.append(job.job_id, "note", {"k": "v"})

        cancelled = self.jobs.cancel(job.job_id, reason="user")
        self.assertEqual(cancelled.status, S.CANCELLED)

        # history attempts and events survive cancel
        self.assertEqual(len(self.attempts.list_for_job(job.job_id)), 1)
        ev_types = [e.event_type for e in self.events.list_for_job(job.job_id)]
        self.assertIn("job_created", ev_types)
        self.assertIn("note", ev_types)
        self.assertIn("cancelled", ev_types)
        cancelled_ev = next(e for e in self.events.list_for_job(job.job_id) if e.event_type == "cancelled")
        self.assertEqual(cancelled_ev.payload["from"], S.PREPARING)
        self.assertEqual(cancelled_ev.payload["to"], S.CANCELLED)
        self.assertEqual(cancelled_ev.payload["reason"], "user")
        self.assertEqual(att.attempt_id, self.attempts.list_for_job(job.job_id)[0].attempt_id)


class RetryResetsToQueuedTest(_StoreTestBase):
    def test_retry_from_cancelled_resets_and_keeps_history(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        self.jobs.cancel(job.job_id)
        self.attempts.record_checkpoint(_attempt(job.job_id))

        retried = self.jobs.retry(job.job_id, reason="manual")
        self.assertEqual(retried.status, S.QUEUED)
        # prior attempt + events still present
        self.assertEqual(len(self.attempts.list_for_job(job.job_id)), 1)
        retry_ev = next(e for e in self.events.list_for_job(job.job_id) if e.event_type == "retry")
        self.assertEqual(retry_ev.payload["from"], S.CANCELLED)
        self.assertEqual(retry_ev.payload["to"], S.QUEUED)

    def test_retry_only_from_failed_or_cancelled(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        with self.assertRaises(IllegalTransitionError):
            self.jobs.retry(job.job_id)  # queued -> queued is not a retry edge


class CheckpointIdempotencyTest(_StoreTestBase):
    def test_repeat_completed_checkpoint_is_idempotent(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        first = _attempt(job.job_id)
        second = self.attempts.record_checkpoint(first)
        self.assertEqual(second.attempt_id, first.attempt_id)
        # second record of the same key returns the existing row, no new row
        again = self.attempts.record_checkpoint(_attempt(job.job_id))
        self.assertEqual(again.attempt_id, first.attempt_id)
        self.assertEqual(len(self.attempts.list_for_job(job.job_id)), 1)

    def test_conflicting_checkpoint_status_raises(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        # a completed checkpoint exists
        self.attempts.record_checkpoint(_attempt(job.job_id, status=S.ATTEMPT_COMPLETED, stage=S.STAGE_EVIDENCE))
        # re-recording the same key as FAILED (different status) is a real conflict
        with self.assertRaises(CheckpointExistsError):
            self.attempts.record_checkpoint(
                _attempt(job.job_id, status=S.ATTEMPT_FAILED, stage=S.STAGE_EVIDENCE)
            )

    def test_run_level_uses_run_and_feat(self) -> None:
        job = self.jobs.create_job(self._create(), evaluator_version=EVALUATOR_VERSION)
        a = Attempt(
            attempt_id=make_job_id(), job_id=job.job_id, run_id="run-1", feat_id="Feat-01",
            stage=S.STAGE_SEMANTIC, status=S.ATTEMPT_COMPLETED, started_at=utc_now(),
            finished_at=utc_now(), exit_code=0, artifact_dir=None,
        )
        self.attempts.record_checkpoint(a)
        # None <-> "" round-trips: stored None comes back as None
        got = self.attempts.get_checkpoint(job.job_id, "run-1", "Feat-01", S.STAGE_SEMANTIC)
        assert got is not None
        self.assertEqual(got.run_id, "run-1")
        self.assertEqual(got.feat_id, "Feat-01")


class CrashRecoveryTest(unittest.TestCase):
    """The anti-fake-completion probe (service plan §9)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _raw(self, sql: str, params: tuple = ()) -> None:
        conn = sqlite3.connect(str(self.settings.db_path))
        conn.execute(sql, params)
        conn.commit()
        conn.close()

    def test_active_job_resumes_to_queued_not_completed(self) -> None:
        # 1) create a job through the store
        store = SqliteStore(self.settings)
        jobs = JobRepository(store)
        attempts = AttemptRepository(store)
        cmd = CreateJobCommand(
            func_id="04-01-01", source_revision="rev", run_count=3, job_id=JOB_ID
        )
        job = jobs.create_job(cmd, evaluator_version=EVALUATOR_VERSION)
        attempts.record_checkpoint(_attempt(job.job_id))
        store.close()

        # 2) simulate a worker that died mid-stage: force status to 'evidence'
        self._raw("UPDATE jobs SET status = 'evidence' WHERE job_id = ?", (job.job_id,))

        # 3) reopen the store; __init__ runs recover_active_jobs()
        store2 = SqliteStore(self.settings)
        jobs2 = JobRepository(store2)
        events2 = EventRepository(store2)
        attempts2 = AttemptRepository(store2)
        recovered = jobs2.get_job(job.job_id)

        # 4) recovered to a resumable non-terminal state, NEVER completed/failed
        self.assertEqual(recovered.status, S.QUEUED)
        self.assertNotIn(recovered.status, S.TERMINAL_STATES)

        # 5) a recovery_reset event records the prior status, and it is auditable
        reset_events = [
            e for e in events2.list_for_job(job.job_id) if e.event_type == "recovery_reset"
        ]
        self.assertEqual(len(reset_events), 1)
        self.assertEqual(reset_events[0].payload["prior_status"], "evidence")

        # 6) the durable checkpoint survived the crash
        self.assertEqual(len(attempts2.list_for_job(job.job_id)), 1)
        store2.close()

    def test_awaiting_executor_is_not_reset(self) -> None:
        store = SqliteStore(self.settings)
        jobs = JobRepository(store)
        job = jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=3, job_id=JOB_ID),
            evaluator_version=EVALUATOR_VERSION,
        )
        store.close()
        # force into scheduler-owned waiting state
        self._raw("UPDATE jobs SET status = 'awaiting_executor' WHERE job_id = ?", (job.job_id,))
        store2 = SqliteStore(self.settings)
        jobs2 = JobRepository(store2)
        self.assertEqual(jobs2.get_job(job.job_id).status, S.AWAITING_EXECUTOR)
        store2.close()

    def test_terminal_jobs_are_not_reset(self) -> None:
        store = SqliteStore(self.settings)
        jobs = JobRepository(store)
        job = jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=3, job_id=JOB_ID),
            evaluator_version=EVALUATOR_VERSION,
        )
        store.close()
        self._raw("UPDATE jobs SET status = 'completed' WHERE job_id = ?", (job.job_id,))
        store2 = SqliteStore(self.settings)
        jobs2 = JobRepository(store2)
        self.assertEqual(jobs2.get_job(job.job_id).status, S.COMPLETED)
        store2.close()


class JobSchemaValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = JsonSchemaSubsetValidator(
            ServiceSettings.discover().schemas_root
        )
        self.schema_path = ServiceSettings.discover().schemas_root / "semantic-service-job.schema.json"

    def _valid_job(self) -> dict:
        return {
            "schema_version": 1,
            "func_id": "04-01-01",
            "source_revision": "rev-1234",
            "run_count": 3,
            "selected_run_ids": ["run-1", "run-2"],
            "max_parallel": 2,
            "status": "queued",
            "progress": default_progress("queued"),
            "executor_config": {
                "type": "codex-cli",
                "command": "codex",
                "model": None,
                "sandbox": "read-only",
                "timeout_seconds": 3600,
                "max_parallel": 2,
                "output_schema": "executor-result.schema.json",
            },
            "protocol_version": "0.1.0",
            "evaluator_version": EVALUATOR_VERSION,
            "created_at": "2026-08-12T00:00:00+00:00",
            "updated_at": "2026-08-12T00:00:00+00:00",
        }

    def test_accepts_valid_job(self) -> None:
        errors = self.validator.validate_file(self._valid_job(), self.schema_path)
        self.assertEqual(errors, [], errors)

    def test_rejects_bad_func_id(self) -> None:
        job = self._valid_job()
        job["func_id"] = "not-a-funcid"
        errors = self.validator.validate_file(job, self.schema_path)
        self.assertTrue(errors, "expected validation errors for bad func_id")

    def test_rejects_unknown_status(self) -> None:
        job = self._valid_job()
        job["status"] = "frobnicated"
        errors = self.validator.validate_file(job, self.schema_path)
        self.assertTrue(errors)

    def test_rejects_additional_property(self) -> None:
        job = self._valid_job()
        job["secret_token"] = "leak"
        errors = self.validator.validate_file(job, self.schema_path)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
