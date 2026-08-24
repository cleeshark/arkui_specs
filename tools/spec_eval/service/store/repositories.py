"""Repository layer: the only DB read/write API for the semantic service.

No other module imports ``sqlite3`` or touches the store connection. The
repositories own the row<->DTO mapping, including the ``None <-> ""`` mapping
for the nullable attempt key columns (service plan decision 3).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ..domain import states as S
from ..domain.errors import (
    CheckpointExistsError,
    DuplicateJobError,
    FreshnessPolicyError,
    JobNotFoundError,
    ReportConflictError,
    ReportPromotionError,
    SnapshotConflictError,
)
from ..domain.models import (
    Artifact,
    Attempt,
    CreateJobCommand,
    DependencySnapshot,
    EvaluationReportRecord,
    Event,
    FreshnessPolicy,
    FunctionReportHead,
    Job,
    JobStatistics,
    RefreshTarget,
    ReportDelta,
    default_progress,
    make_job_id,
)
from .sqlite_store import SqliteStore, utc_now


# --- row <-> DTO converters -------------------------------------------------

def _job_from_row(row: sqlite3.Row) -> Job:
    return Job(
        job_id=row["job_id"],
        func_id=row["func_id"],
        source_revision=row["source_revision"],
        run_count=int(row["run_count"]),
        selected_run_ids=tuple(json.loads(row["selected_run_ids"])),
        status=row["status"],
        stage=row["stage"] if "stage" in row.keys() else "preparing",
        progress=json.loads(row["progress_json"]),
        executor_config=json.loads(row["executor_config"]),
        protocol_version=row["protocol_version"],
        evaluator_version=row["evaluator_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _attempt_from_row(row: sqlite3.Row) -> Attempt:
    return Attempt(
        attempt_id=row["attempt_id"],
        job_id=row["job_id"],
        run_id=row["run_id"] or None,  # "" -> None
        feat_id=row["feat_id"] or None,
        stage=row["stage"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        exit_code=row["exit_code"],
        artifact_dir=row["artifact_dir"],
    )


def _event_from_row(row: sqlite3.Row) -> Event:
    return Event(
        job_id=row["job_id"],
        seq=int(row["seq"]),
        event_type=row["event_type"],
        payload=json.loads(row["payload_json"]),
        created_at=row["created_at"],
    )


def _artifact_from_row(row: sqlite3.Row) -> Artifact:
    return Artifact(
        artifact_id=row["artifact_id"],
        job_id=row["job_id"],
        kind=row["kind"],
        path=row["path"],
        sha256=row["sha256"],
        size=int(row["size"]),
        created_at=row["created_at"],
    )


def _snapshot_from_row(row: sqlite3.Row) -> DependencySnapshot:
    return DependencySnapshot(
        job_id=row["job_id"],
        repo_name=row["repo_name"],
        branch=row["branch"],
        sha=row["sha"],
        status=row["status"],
        created_at=row["created_at"],
    )


def _report_from_row(row: sqlite3.Row) -> EvaluationReportRecord:
    return EvaluationReportRecord(
        report_id=row["report_id"],
        job_id=row["job_id"],
        func_id=row["func_id"],
        source_revision=row["source_revision"],
        revision_set=json.loads(row["revision_set_json"]),
        input_fingerprint=row["input_fingerprint"],
        evidence_fingerprint=row["evidence_fingerprint"],
        evaluator_version=row["evaluator_version"],
        protocol_version=row["protocol_version"],
        rubric_version=row["rubric_version"],
        selected_run_id=row["selected_run_id"],
        run_count=int(row["run_count"]),
        target_generation=int(row["target_generation"]),
        completed_at=row["completed_at"],
        archive_path=row["archive_path"],
        manifest_sha256=row["manifest_sha256"],
        summary=json.loads(row["summary_json"]),
    )


def _head_from_row(row: sqlite3.Row) -> FunctionReportHead:
    return FunctionReportHead(
        func_id=row["func_id"],
        current_report_id=row["current_report_id"],
        desired_generation=int(row["desired_generation"]),
        desired_revision=row["desired_revision"],
        desired_input_fingerprint=row["desired_input_fingerprint"],
        freshness=row["freshness"],
        stale_reasons=tuple(json.loads(row["stale_reasons_json"])),
        warn_at=row["warn_at"],
        expires_at=row["expires_at"],
        refresh_status=row["refresh_status"],
        active_job_id=row["active_job_id"],
        last_refresh_error=row["last_refresh_error"],
        updated_at=row["updated_at"],
    )


def _policy_from_row(row: sqlite3.Row) -> FreshnessPolicy:
    return FreshnessPolicy(
        scope_type=row["scope_type"],
        scope_key=row["scope_key"],
        max_age_days=int(row["max_age_days"]),
        warning_days=int(row["warning_days"]),
        version=int(row["version"]),
        updated_at=row["updated_at"],
    )


def _refresh_target_from_row(row: sqlite3.Row) -> RefreshTarget:
    return RefreshTarget(
        job_id=row["job_id"],
        func_id=row["func_id"],
        generation=int(row["generation"]),
        desired_revision=row["desired_revision"],
        revision_set=json.loads(row["revision_set_json"]),
        provisional_fingerprint=row["provisional_fingerprint"],
        input_fingerprint=row["input_fingerprint"],
        evidence_fingerprint=row["evidence_fingerprint"],
        dedupe_key=row["dedupe_key"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _report_delta_from_row(row: sqlite3.Row) -> ReportDelta:
    return ReportDelta(
        report_id=row["report_id"],
        previous_report_id=row["previous_report_id"],
        summary=json.loads(row["summary_json"]),
        details_path=row["details_path"],
    )


def _job_statistics_from_row(row: sqlite3.Row) -> JobStatistics:
    return JobStatistics(
        job_id=row["job_id"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        executor_invocations=int(row["executor_invocations"]),
        usage_reported_invocations=int(row["usage_reported_invocations"]),
        telemetry_reported_invocations=int(row["telemetry_reported_invocations"]),
        executor_elapsed_ms=int(row["executor_elapsed_ms"]),
        executor_tool_calls=int(row["executor_tool_calls"]),
        executor_command_calls=int(row["executor_command_calls"]),
        input_paths_accessed=int(row["input_paths_accessed"]),
        evidence_paths_accessed=int(row["evidence_paths_accessed"]),
        input_tokens=int(row["input_tokens"]),
        cached_input_tokens=int(row["cached_input_tokens"]),
        cache_write_input_tokens=int(row["cache_write_input_tokens"]),
        output_tokens=int(row["output_tokens"]),
        reasoning_output_tokens=int(row["reasoning_output_tokens"]),
        total_tokens=int(row["total_tokens"]),
        updated_at=row["updated_at"],
    )


# --- repositories -----------------------------------------------------------

class JobRepository:
    """jobs table access (create is idempotent by job_id)."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def create_job(
        self,
        cmd: CreateJobCommand,
        *,
        evaluator_version: str,
        executor_config: dict[str, Any] | None = None,
    ) -> Job:
        """Create a job, idempotently by ``cmd.job_id``.

        * If ``cmd.job_id`` is ``None`` a fresh id is minted (always a new job).
        * If a job with that id exists and the immutable fields match, the
          existing job is returned (idempotent success).
        * If a job with that id exists but immutable fields differ,
          :class:`DuplicateJobError` is raised.
        """
        executor_config = cmd.executor_config or executor_config or {}
        protocol_version = self._store.settings.protocol_version
        job_id = cmd.job_id or make_job_id()
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if existing is not None:
                job = _job_from_row(existing)
                if self._immutables_match(existing, cmd, executor_config, protocol_version):
                    return job
                raise DuplicateJobError(job_id, job)

            now = utc_now()
            progress = default_progress(S.QUEUED)
            self._conn.execute(
                "INSERT INTO jobs (job_id, func_id, source_revision, run_count, "
                "selected_run_ids, status, stage, progress_json, executor_config, "
                "protocol_version, evaluator_version, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    cmd.func_id,
                    cmd.source_revision,
                    cmd.run_count,
                    json.dumps(list(cmd.selected_run_ids)),
                    S.QUEUED,
                    S.STAGE_PREPARING,
                    json.dumps(progress, ensure_ascii=False),
                    json.dumps(executor_config, ensure_ascii=False),
                    protocol_version,
                    evaluator_version,
                    now,
                    now,
                ),
            )
            self._conn.execute(
                "INSERT INTO job_statistics (job_id, updated_at) VALUES (?, ?)",
                (job_id, now),
            )
            self._store._append_event(
                job_id,
                "job_created",
                {
                    "func_id": cmd.func_id,
                    "source_revision": cmd.source_revision,
                    "run_count": cmd.run_count,
                },
                now=now,
            )
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _job_from_row(row)

    @staticmethod
    def _immutables_match(
        row: sqlite3.Row,
        cmd: CreateJobCommand,
        executor_config: dict[str, Any],
        protocol_version: str,
    ) -> bool:
        same_run_ids = tuple(json.loads(row["selected_run_ids"])) == tuple(cmd.selected_run_ids)
        same_exec = json.loads(row["executor_config"]) == executor_config
        return (
            row["func_id"] == cmd.func_id
            and row["source_revision"] == cmd.source_revision
            and int(row["run_count"]) == cmd.run_count
            and row["protocol_version"] == protocol_version
            and same_run_ids
            and same_exec
        )

    def get_job(self, job_id: str) -> Job:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            return _job_from_row(row)

    def list_jobs(self, *, status: str | None = None, limit: int = 100) -> list[Job]:
        with self._store._tx():
            if status is None:
                rows = self._conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            return [_job_from_row(r) for r in rows]

    def transition_status(
        self,
        job_id: str,
        dst: str,
        *,
        event_type: str,
        payload: dict[str, Any] | None = None,
        stage: str | None = None,
    ) -> Job:
        """Validate the transition via the state matrix, update status/stage.

        ``stage`` advances the pipeline stage independently of the lifecycle
        status (running -> running transitions advance the stage); when
        omitted the persisted stage is left untouched (failures keep the
        stage that failed).
        """
        with self._store._tx(immediate=True):
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            src = row["status"]
            new = S.transition(src, dst)  # raises IllegalTransitionError if illegal
            now = utc_now()
            if stage is not None and stage in S.JOB_STAGES:
                self._conn.execute(
                    "UPDATE jobs SET status = ?, stage = ?, updated_at = ? "
                    "WHERE job_id = ?",
                    (new, stage, now, job_id),
                )
            else:
                self._conn.execute(
                    "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                    (new, now, job_id),
                )
            effective_stage = stage if stage is not None else row["stage"]
            if new == S.RUNNING and effective_stage == S.STAGE_PREPARING:
                self._conn.execute(
                    "UPDATE job_statistics SET started_at = COALESCE(started_at, ?), "
                    "finished_at = NULL, updated_at = ? WHERE job_id = ?",
                    (now, now, job_id),
                )
            elif new in S.TERMINAL_STATES:
                self._conn.execute(
                    "UPDATE job_statistics SET finished_at = ?, updated_at = ? WHERE job_id = ?",
                    (now, now, job_id),
                )
            elif new == S.QUEUED:
                self._conn.execute(
                    "UPDATE job_statistics SET finished_at = NULL, updated_at = ? WHERE job_id = ?",
                    (now, job_id),
                )
            event_payload = {"from": src, "to": new}
            if payload:
                event_payload.update(payload)
            self._store._append_event(job_id, event_type, event_payload, now=now)
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _job_from_row(row)

    def cancel(self, job_id: str, reason: str | None = None) -> Job:
        return self.transition_status(
            job_id, S.CANCELLED, event_type="cancelled", payload={"reason": reason}
        )

    def retry(self, job_id: str, reason: str | None = None) -> Job:
        # Only failed/cancelled may retry; the matrix enforces it.
        return self.transition_status(
            job_id, S.QUEUED, event_type="retry", payload={"reason": reason}
        )

    def update_progress(self, job_id: str, progress: dict[str, Any]) -> Job:
        with self._store._tx(immediate=True):
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            self._conn.execute(
                "UPDATE jobs SET progress_json = ?, updated_at = ? WHERE job_id = ?",
                (json.dumps(progress, ensure_ascii=False), utc_now(), job_id),
            )
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _job_from_row(row)


class JobStatisticsRepository:
    """Durable job timing and aggregate Codex usage counters."""

    _TOKEN_FIELDS = (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    )

    def __init__(self, store: SqliteStore) -> None:
        self.store = store
        self._conn = store._conn

    def get(self, job_id: str) -> JobStatistics:
        with self.store._tx(immediate=True):
            row = self._conn.execute(
                "SELECT * FROM job_statistics WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                job = self._conn.execute(
                    "SELECT updated_at FROM jobs WHERE job_id = ?", (job_id,)
                ).fetchone()
                if job is None:
                    raise JobNotFoundError(job_id)
                self._conn.execute(
                    "INSERT INTO job_statistics (job_id, updated_at) VALUES (?, ?)",
                    (job_id, job["updated_at"]),
                )
                row = self._conn.execute(
                    "SELECT * FROM job_statistics WHERE job_id = ?", (job_id,)
                ).fetchone()
            return _job_statistics_from_row(row)

    def list_all(self) -> list[JobStatistics]:
        with self.store._tx():
            rows = self._conn.execute(
                "SELECT * FROM job_statistics ORDER BY job_id"
            ).fetchall()
            return [_job_statistics_from_row(row) for row in rows]

    def record_executor_result(
        self,
        job_id: str,
        *,
        elapsed_seconds: float,
        token_usage: dict[str, int] | None,
        usage_reported: bool,
        telemetry: dict[str, int] | None = None,
        telemetry_reported: bool = False,
    ) -> JobStatistics:
        usage = token_usage or {}
        values = []
        for name in self._TOKEN_FIELDS:
            raw = usage.get(name, 0)
            values.append(
                raw
                if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0
                else 0
            )
        elapsed_ms = max(0, int(round(float(elapsed_seconds) * 1000.0)))
        telemetry_values = []
        telemetry = telemetry or {}
        for name in (
            "tool_calls",
            "command_calls",
            "input_paths_accessed",
            "evidence_paths_accessed",
        ):
            raw = telemetry.get(name, 0)
            telemetry_values.append(
                raw
                if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0
                else 0
            )
        with self.store._tx(immediate=True):
            self.get(job_id)
            now = utc_now()
            self._conn.execute(
                "UPDATE job_statistics SET executor_invocations = executor_invocations + 1, "
                "usage_reported_invocations = usage_reported_invocations + ?, "
                "telemetry_reported_invocations = telemetry_reported_invocations + ?, "
                "executor_elapsed_ms = executor_elapsed_ms + ?, "
                "executor_tool_calls = executor_tool_calls + ?, "
                "executor_command_calls = executor_command_calls + ?, "
                "input_paths_accessed = input_paths_accessed + ?, "
                "evidence_paths_accessed = evidence_paths_accessed + ?, "
                "input_tokens = input_tokens + ?, cached_input_tokens = cached_input_tokens + ?, "
                "cache_write_input_tokens = cache_write_input_tokens + ?, "
                "output_tokens = output_tokens + ?, "
                "reasoning_output_tokens = reasoning_output_tokens + ?, "
                "total_tokens = total_tokens + ?, updated_at = ? WHERE job_id = ?",
                (
                    1 if usage_reported else 0,
                    1 if telemetry_reported else 0,
                    elapsed_ms,
                    *telemetry_values,
                    *values,
                    now,
                    job_id,
                ),
            )
            row = self._conn.execute(
                "SELECT * FROM job_statistics WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _job_statistics_from_row(row)


class AttemptRepository:
    """attempts table access; checkpoint record is idempotent on the UNIQUE key."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def record_checkpoint(self, attempt: Attempt) -> Attempt:
        run_id = attempt.run_id or ""
        feat_id = attempt.feat_id or ""
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM attempts WHERE job_id = ? AND run_id = ? "
                "AND feat_id = ? AND stage = ?",
                (attempt.job_id, run_id, feat_id, attempt.stage),
            ).fetchone()
            if existing is not None:
                # Idempotent only when re-asserting the same completed checkpoint
                # (same status, and artifact_dir absent or matching). A different
                # status or artifact_dir for the same key is a genuine conflict.
                same_status = existing["status"] == attempt.status
                same_dir = attempt.artifact_dir is None or existing["artifact_dir"] == attempt.artifact_dir
                if (
                    existing["status"] == S.ATTEMPT_COMPLETED
                    and same_status
                    and same_dir
                ):
                    return _attempt_from_row(existing)
                raise CheckpointExistsError(
                    attempt.job_id, attempt.stage, attempt.run_id, attempt.feat_id
                )
            self._conn.execute(
                "INSERT INTO attempts (attempt_id, job_id, run_id, feat_id, stage, "
                "status, started_at, finished_at, exit_code, artifact_dir) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt.attempt_id,
                    attempt.job_id,
                    run_id,
                    feat_id,
                    attempt.stage,
                    attempt.status,
                    attempt.started_at,
                    attempt.finished_at,
                    attempt.exit_code,
                    attempt.artifact_dir,
                ),
            )
            return attempt

    def get_checkpoint(
        self, job_id: str, run_id: str | None, feat_id: str | None, stage: str
    ) -> Attempt | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM attempts WHERE job_id = ? AND run_id = ? "
                "AND feat_id = ? AND stage = ?",
                (job_id, run_id or "", feat_id or "", stage),
            ).fetchone()
            return _attempt_from_row(row) if row is not None else None

    def list_for_job(self, job_id: str, *, stage: str | None = None) -> list[Attempt]:
        with self._store._tx():
            if stage is None:
                rows = self._conn.execute(
                    "SELECT * FROM attempts WHERE job_id = ? ORDER BY started_at",
                    (job_id,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM attempts WHERE job_id = ? AND stage = ? ORDER BY started_at",
                    (job_id, stage),
                ).fetchall()
            return [_attempt_from_row(r) for r in rows]


class ProjectionRepository:
    """Asynchronous projection outbox (protocol 0.2.0 S3, design R6/D2).

    One row per completed job; ``report_id`` is the idempotency key. A
    projection failure is recorded here and never changes the completed
    job's terminal state.
    """

    def __init__(self, store: "SqliteStore") -> None:
        self._store = store

    def enqueue(
        self,
        *,
        job_id: str,
        report_id: str,
        archive_dir: str,
        aggregate_dir: str,
        selected_run_id: str,
    ) -> None:
        now = utc_now()
        with self._store._tx() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO projection_requests (
                    job_id, report_id, status, attempts, requested_at,
                    archive_dir, aggregate_dir, selected_run_id
                ) VALUES (?, ?, 'pending', 0, ?, ?, ?, ?)
                """,
                (job_id, report_id, now, archive_dir, aggregate_dir, selected_run_id),
            )

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._store._tx() as conn:
            row = conn.execute(
                "SELECT * FROM projection_requests WHERE job_id = ?", (job_id,)
            ).fetchone()
        return dict(row) if row is not None else None

    def mark_running(self, job_id: str) -> None:
        with self._store._tx() as conn:
            conn.execute(
                "UPDATE projection_requests SET status = 'running', "
                "attempts = attempts + 1, last_error = NULL WHERE job_id = ?",
                (job_id,),
            )

    def mark_completed(self, job_id: str) -> None:
        with self._store._tx() as conn:
            conn.execute(
                "UPDATE projection_requests SET status = 'completed', "
                "finished_at = ? WHERE job_id = ?",
                (utc_now(), job_id),
            )

    def mark_failed(self, job_id: str, error: str) -> None:
        with self._store._tx() as conn:
            conn.execute(
                "UPDATE projection_requests SET status = 'failed', "
                "last_error = ?, finished_at = ? WHERE job_id = ?",
                (error, utc_now(), job_id),
            )

    def requeue_failed(self, job_id: str) -> None:
        with self._store._tx() as conn:
            conn.execute(
                "UPDATE projection_requests SET status = 'pending', "
                "last_error = NULL, finished_at = NULL WHERE job_id = ?",
                (job_id,),
            )

    def list_by_status(self, status: str) -> list[dict[str, Any]]:
        with self._store._tx() as conn:
            rows = conn.execute(
                "SELECT * FROM projection_requests WHERE status = ? "
                "ORDER BY requested_at",
                (status,),
            ).fetchall()
        return [dict(row) for row in rows]


class ExecutorCallRepository:
    """Per-executor-call invocations (protocol 0.2.0, design R6).

    One row per executor call (observe/correct) with executor identity,
    duration and normalized usage/telemetry payloads. The legacy ``attempts``
    table remains the stage-level checkpoint record.
    """

    def __init__(self, store: "SqliteStore") -> None:
        self._store = store

    def record_call(
        self,
        *,
        job_id: str,
        run_id: str | None,
        work_item_id: str,
        attempt_type: str,
        executor: str,
        status: str,
        duration_ms: int,
        usage: dict[str, Any],
        telemetry: dict[str, Any],
    ) -> int:
        now = utc_now()
        with self._store._tx() as conn:
            cursor = conn.execute(
                """
                INSERT INTO executor_calls (
                    job_id, run_id, work_item_id, attempt_type, executor,
                    status, started_at, duration_ms, usage_json, telemetry_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id, run_id or "", work_item_id, attempt_type, executor,
                    status, now, max(0, int(duration_ms)),
                    json.dumps(usage, ensure_ascii=False, sort_keys=True),
                    json.dumps(telemetry, ensure_ascii=False, sort_keys=True),
                ),
            )
            return int(cursor.lastrowid or 0)

    def list_for_job(self, job_id: str) -> list[dict[str, Any]]:
        with self._store._tx() as conn:
            rows = conn.execute(
                """
                SELECT call_id, run_id, work_item_id, attempt_type, executor,
                       status, started_at, duration_ms, usage_json, telemetry_json
                FROM executor_calls WHERE job_id = ? ORDER BY call_id
                """,
                (job_id,),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            for key in ("usage_json", "telemetry_json"):
                try:
                    item[key[:-5]] = json.loads(item.pop(key) or "{}")
                except json.JSONDecodeError:
                    item[key[:-5]] = {}
            result.append(item)
        return result


class EventRepository:
    """events table access; append produces a monotonic seq."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def append(self, job_id: str, event_type: str, payload: dict[str, Any]) -> Event:
        with self._store._tx(immediate=True):
            now = utc_now()
            seq = self._store._append_event(job_id, event_type, payload, now=now)
            return Event(
                job_id=job_id,
                seq=seq,
                event_type=event_type,
                payload=payload,
                created_at=now,
            )

    def list_for_job(
        self,
        job_id: str,
        *,
        since_seq: int = 0,
        limit: int | None = None,
        tail: bool = False,
    ) -> list[Event]:
        if since_seq < 0:
            raise ValueError("since_seq must be non-negative")
        if limit is not None and limit < 0:
            raise ValueError("limit must be non-negative or None")
        with self._store._tx():
            query = (
                "SELECT * FROM events WHERE job_id = ? AND seq > ? "
                f"ORDER BY seq {'DESC' if tail and limit is not None else 'ASC'}"
            )
            params: tuple[Any, ...] = (job_id, since_seq)
            if limit is not None:
                query += " LIMIT ?"
                params += (limit,)
            rows = self._conn.execute(query, params).fetchall()
            events = [_event_from_row(r) for r in rows]
            if tail and limit is not None:
                events.reverse()
            return events


class ArtifactRepository:
    """artifacts table access; same (job_id, kind) always points at the latest."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def record(self, artifact: Artifact) -> Artifact:
        with self._store._tx(immediate=True):
            self._conn.execute(
                "INSERT INTO artifacts (artifact_id, job_id, kind, path, sha256, size, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(job_id, kind) DO UPDATE SET "
                "artifact_id = excluded.artifact_id, path = excluded.path, "
                "sha256 = excluded.sha256, size = excluded.size, "
                "created_at = excluded.created_at",
                (
                    artifact.artifact_id,
                    artifact.job_id,
                    artifact.kind,
                    artifact.path,
                    artifact.sha256,
                    artifact.size,
                    artifact.created_at,
                ),
            )
            return artifact

    def get(self, job_id: str, kind: str) -> Artifact | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM artifacts WHERE job_id = ? AND kind = ?", (job_id, kind)
            ).fetchone()
            return _artifact_from_row(row) if row is not None else None

    def list_for_job(self, job_id: str) -> list[Artifact]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM artifacts WHERE job_id = ? ORDER BY kind", (job_id,)
            ).fetchall()
            return [_artifact_from_row(r) for r in rows]


class DependencySnapshotRepository:
    """dependency_snapshots access; PK (job_id, repo_name) = task-level freeze."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def freeze(self, snapshot: DependencySnapshot) -> DependencySnapshot:
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM dependency_snapshots WHERE job_id = ? AND repo_name = ?",
                (snapshot.job_id, snapshot.repo_name),
            ).fetchone()
            if existing is not None:
                frozen = _snapshot_from_row(existing)
                if (
                    frozen.branch == snapshot.branch
                    and frozen.sha == snapshot.sha
                    and frozen.status == snapshot.status
                ):
                    return frozen
                raise SnapshotConflictError(snapshot.job_id, snapshot.repo_name)
            self._conn.execute(
                "INSERT INTO dependency_snapshots (job_id, repo_name, branch, sha, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    snapshot.job_id,
                    snapshot.repo_name,
                    snapshot.branch,
                    snapshot.sha,
                    snapshot.status,
                    snapshot.created_at,
                ),
            )
            return snapshot

    def get(self, job_id: str, repo_name: str) -> DependencySnapshot | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM dependency_snapshots WHERE job_id = ? AND repo_name = ?",
                (job_id, repo_name),
            ).fetchone()
            return _snapshot_from_row(row) if row is not None else None

    def list_for_job(self, job_id: str) -> list[DependencySnapshot]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM dependency_snapshots WHERE job_id = ? ORDER BY repo_name",
                (job_id,),
            ).fetchall()
            return [_snapshot_from_row(r) for r in rows]


class EvaluationReportRepository:
    """Immutable evaluation report index."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def insert(self, report: EvaluationReportRecord) -> EvaluationReportRecord:
        values = (
            report.report_id, report.job_id, report.func_id, report.source_revision,
            json.dumps(report.revision_set, ensure_ascii=False, sort_keys=True),
            report.input_fingerprint, report.evidence_fingerprint,
            report.evaluator_version, report.protocol_version, report.rubric_version,
            report.selected_run_id, report.run_count, report.target_generation,
            report.completed_at, report.archive_path, report.manifest_sha256,
            json.dumps(report.summary, ensure_ascii=False, sort_keys=True),
        )
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM evaluation_reports WHERE report_id = ? OR job_id = ?",
                (report.report_id, report.job_id),
            ).fetchone()
            if existing is not None:
                frozen = _report_from_row(existing)
                if frozen == report:
                    return frozen
                raise ReportConflictError(
                    f"immutable report conflict: report_id={report.report_id!r} job_id={report.job_id!r}"
                )
            self._conn.execute(
                "INSERT INTO evaluation_reports (report_id, job_id, func_id, source_revision, "
                "revision_set_json, input_fingerprint, evidence_fingerprint, evaluator_version, "
                "protocol_version, rubric_version, selected_run_id, run_count, target_generation, "
                "completed_at, archive_path, manifest_sha256, summary_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                values,
            )
            return report

    def get(self, report_id: str) -> EvaluationReportRecord | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM evaluation_reports WHERE report_id = ?", (report_id,)
            ).fetchone()
            return _report_from_row(row) if row is not None else None

    def get_for_job(self, job_id: str) -> EvaluationReportRecord | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM evaluation_reports WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _report_from_row(row) if row is not None else None

    def list_for_func(self, func_id: str, *, limit: int = 100) -> list[EvaluationReportRecord]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM evaluation_reports WHERE func_id = ? "
                "ORDER BY completed_at DESC, report_id DESC LIMIT ?",
                (func_id, limit),
            ).fetchall()
            return [_report_from_row(row) for row in rows]


class FunctionReportHeadRepository:
    """Function current pointer, desired target, and freshness projection."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def ensure(self, func_id: str) -> FunctionReportHead:
        with self._store._tx(immediate=True):
            now = utc_now()
            self._conn.execute(
                "INSERT OR IGNORE INTO function_report_heads (func_id, updated_at) VALUES (?, ?)",
                (func_id, now),
            )
            return _head_from_row(self._get_row(func_id))

    def get(self, func_id: str) -> FunctionReportHead | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM function_report_heads WHERE func_id = ?", (func_id,)
            ).fetchone()
            return _head_from_row(row) if row is not None else None

    def list_all(self) -> list[FunctionReportHead]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM function_report_heads ORDER BY func_id"
            ).fetchall()
            return [_head_from_row(row) for row in rows]

    def set_desired_target(
        self,
        func_id: str,
        *,
        revision: str,
        input_fingerprint: str,
        active_job_id: str | None,
        stale_reasons: tuple[str, ...] = (),
    ) -> FunctionReportHead:
        with self._store._tx(immediate=True):
            self.ensure(func_id)
            row = self._get_row(func_id)
            generation = int(row["desired_generation"]) + 1
            freshness = "MISSING" if row["current_report_id"] is None else "STALE_INPUT"
            self._conn.execute(
                "UPDATE function_report_heads SET desired_generation = ?, desired_revision = ?, "
                "desired_input_fingerprint = ?, freshness = ?, stale_reasons_json = ?, "
                "refresh_status = ?, active_job_id = ?, last_refresh_error = NULL, updated_at = ? "
                "WHERE func_id = ?",
                (
                    generation, revision, input_fingerprint, freshness,
                    json.dumps(list(stale_reasons), ensure_ascii=False),
                    "REFRESHING" if active_job_id else "IDLE", active_job_id, utc_now(), func_id,
                ),
            )
            return _head_from_row(self._get_row(func_id))

    def promote(
        self,
        report: EvaluationReportRecord,
        *,
        freshness: str,
        warn_at: str,
        expires_at: str,
    ) -> FunctionReportHead:
        with self._store._tx(immediate=True):
            row = self._get_row(report.func_id)
            if int(row["desired_generation"]) != report.target_generation:
                raise ReportPromotionError("SUPERSEDED_ON_ARRIVAL: desired generation changed")
            if row["desired_input_fingerprint"] != report.input_fingerprint:
                raise ReportPromotionError("SUPERSEDED_ON_ARRIVAL: desired input fingerprint changed")
            if row["active_job_id"] != report.job_id:
                raise ReportPromotionError("SUPERSEDED_ON_ARRIVAL: active Job changed")
            self._conn.execute(
                "UPDATE function_report_heads SET current_report_id = ?, freshness = ?, "
                "stale_reasons_json = '[]', warn_at = ?, expires_at = ?, refresh_status = 'IDLE', "
                "active_job_id = NULL, last_refresh_error = NULL, updated_at = ? WHERE func_id = ?",
                (report.report_id, freshness, warn_at, expires_at, utc_now(), report.func_id),
            )
            return _head_from_row(self._get_row(report.func_id))

    def update_freshness(
        self,
        func_id: str,
        *,
        freshness: str,
        stale_reasons: tuple[str, ...],
        warn_at: str | None,
        expires_at: str | None,
    ) -> FunctionReportHead:
        with self._store._tx(immediate=True):
            self._conn.execute(
                "UPDATE function_report_heads SET freshness = ?, stale_reasons_json = ?, "
                "warn_at = ?, expires_at = ?, updated_at = ? WHERE func_id = ?",
                (
                    freshness, json.dumps(list(stale_reasons), ensure_ascii=False),
                    warn_at, expires_at, utc_now(), func_id,
                ),
            )
            return _head_from_row(self._get_row(func_id))

    def mark_refresh_failed(self, func_id: str, job_id: str, error: str) -> FunctionReportHead:
        with self._store._tx(immediate=True):
            self._conn.execute(
                "UPDATE function_report_heads SET refresh_status = 'REFRESH_FAILED', "
                "active_job_id = NULL, last_refresh_error = ?, updated_at = ? "
                "WHERE func_id = ? AND active_job_id = ?",
                (error[:1000], utc_now(), func_id, job_id),
            )
            return _head_from_row(self._get_row(func_id))

    def bind_fingerprint(
        self,
        func_id: str,
        *,
        generation: int,
        job_id: str,
        input_fingerprint: str,
        stale_reasons: tuple[str, ...],
    ) -> FunctionReportHead:
        """Replace a provisional target only when this Job still owns the head."""
        with self._store._tx(immediate=True):
            row = self._get_row(func_id)
            if int(row["desired_generation"]) == generation and row["active_job_id"] == job_id:
                freshness = "MISSING" if row["current_report_id"] is None else "STALE_INPUT"
                self._conn.execute(
                    "UPDATE function_report_heads SET desired_input_fingerprint = ?, freshness = ?, "
                    "stale_reasons_json = ?, updated_at = ? WHERE func_id = ?",
                    (
                        input_fingerprint, freshness,
                        json.dumps(list(stale_reasons), ensure_ascii=False), utc_now(), func_id,
                    ),
                )
            return _head_from_row(self._get_row(func_id))

    def _get_row(self, func_id: str) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT * FROM function_report_heads WHERE func_id = ?", (func_id,)
        ).fetchone()
        if row is None:
            raise ReportPromotionError(f"Function head not found: {func_id}")
        return row


class FreshnessPolicyRepository:
    """Versioned global and FuncID-specific freshness policies."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def ensure_default(self) -> FreshnessPolicy:
        with self._store._tx(immediate=True):
            now = utc_now()
            self._conn.execute(
                "INSERT OR IGNORE INTO freshness_policies "
                "(scope_type, scope_key, max_age_days, warning_days, version, updated_at) "
                "VALUES ('global', '*', 30, 7, 1, ?)",
                (now,),
            )
            row = self._conn.execute(
                "SELECT * FROM freshness_policies WHERE scope_type = 'global' AND scope_key = '*'"
            ).fetchone()
            return _policy_from_row(row)

    def set(self, policy: FreshnessPolicy) -> FreshnessPolicy:
        if policy.scope_type not in {"global", "func"}:
            raise FreshnessPolicyError(f"invalid policy scope: {policy.scope_type}")
        if policy.max_age_days <= 0 or not 0 <= policy.warning_days < policy.max_age_days:
            raise FreshnessPolicyError("policy requires 0 <= warning_days < max_age_days")
        with self._store._tx(immediate=True):
            row = self._conn.execute(
                "SELECT * FROM freshness_policies WHERE scope_type = ? AND scope_key = ?",
                (policy.scope_type, policy.scope_key),
            ).fetchone()
            if row is not None and policy.version <= int(row["version"]):
                raise FreshnessPolicyError("policy version must increase")
            self._conn.execute(
                "INSERT INTO freshness_policies (scope_type, scope_key, max_age_days, "
                "warning_days, version, updated_at) VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(scope_type, scope_key) DO UPDATE SET "
                "max_age_days = excluded.max_age_days, warning_days = excluded.warning_days, "
                "version = excluded.version, updated_at = excluded.updated_at",
                (
                    policy.scope_type, policy.scope_key, policy.max_age_days,
                    policy.warning_days, policy.version, policy.updated_at,
                ),
            )
            return policy

    def get(self, scope_type: str, scope_key: str) -> FreshnessPolicy | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM freshness_policies WHERE scope_type = ? AND scope_key = ?",
                (scope_type, scope_key),
            ).fetchone()
            return _policy_from_row(row) if row is not None else None

    def effective_for(self, func_id: str) -> FreshnessPolicy | None:
        return self.get("func", func_id) or self.get("global", "*")

    def list_all(self) -> list[FreshnessPolicy]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM freshness_policies ORDER BY scope_type, scope_key"
            ).fetchall()
            return [_policy_from_row(row) for row in rows]


class RefreshTargetRepository:
    """Manual-refresh generation and deduplication state."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    @property
    def store(self) -> SqliteStore:
        return self._store

    def create_active(
        self,
        *,
        job_id: str,
        func_id: str,
        desired_revision: str,
        revision_set: dict[str, str],
        provisional_fingerprint: str,
        dedupe_key: str,
        stale_reasons: tuple[str, ...],
    ) -> tuple[RefreshTarget, bool]:
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM refresh_targets WHERE dedupe_key = ? AND status = 'ACTIVE'",
                (dedupe_key,),
            ).fetchone()
            if existing is not None:
                return _refresh_target_from_row(existing), False
            now = utc_now()
            self._conn.execute(
                "INSERT OR IGNORE INTO function_report_heads (func_id, updated_at) VALUES (?, ?)",
                (func_id, now),
            )
            head = self._conn.execute(
                "SELECT * FROM function_report_heads WHERE func_id = ?", (func_id,)
            ).fetchone()
            generation = int(head["desired_generation"]) + 1
            freshness = "MISSING" if head["current_report_id"] is None else "STALE_INPUT"
            self._conn.execute(
                "UPDATE function_report_heads SET desired_generation = ?, desired_revision = ?, "
                "desired_input_fingerprint = ?, freshness = ?, stale_reasons_json = ?, "
                "refresh_status = 'REFRESHING', active_job_id = ?, last_refresh_error = NULL, "
                "updated_at = ? WHERE func_id = ?",
                (
                    generation, desired_revision, provisional_fingerprint, freshness,
                    json.dumps(list(stale_reasons), ensure_ascii=False), job_id, now, func_id,
                ),
            )
            self._conn.execute(
                "INSERT INTO refresh_targets (job_id, func_id, generation, desired_revision, "
                "revision_set_json, provisional_fingerprint, input_fingerprint, evidence_fingerprint, "
                "dedupe_key, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 'ACTIVE', ?, ?)",
                (
                    job_id, func_id, generation, desired_revision,
                    json.dumps(revision_set, ensure_ascii=False, sort_keys=True),
                    provisional_fingerprint, dedupe_key, now, now,
                ),
            )
            row = self._conn.execute(
                "SELECT * FROM refresh_targets WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _refresh_target_from_row(row), True

    def get(self, job_id: str) -> RefreshTarget | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM refresh_targets WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _refresh_target_from_row(row) if row is not None else None

    def get_active_by_dedupe(self, dedupe_key: str) -> RefreshTarget | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM refresh_targets WHERE dedupe_key = ? AND status = 'ACTIVE'",
                (dedupe_key,),
            ).fetchone()
            return _refresh_target_from_row(row) if row is not None else None

    def bind_fingerprints(
        self, job_id: str, *, input_fingerprint: str, evidence_fingerprint: str
    ) -> RefreshTarget:
        with self._store._tx(immediate=True):
            self._conn.execute(
                "UPDATE refresh_targets SET input_fingerprint = ?, evidence_fingerprint = ?, "
                "updated_at = ? WHERE job_id = ? AND status = 'ACTIVE'",
                (input_fingerprint, evidence_fingerprint, utc_now(), job_id),
            )
            row = self._conn.execute(
                "SELECT * FROM refresh_targets WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            return _refresh_target_from_row(row)

    def finish(self, job_id: str, *, status: str) -> RefreshTarget | None:
        if status not in {"COMPLETED", "FAILED"}:
            raise ValueError(f"invalid refresh target terminal status: {status}")
        with self._store._tx(immediate=True):
            self._conn.execute(
                "UPDATE refresh_targets SET status = ?, updated_at = ? "
                "WHERE job_id = ? AND status = 'ACTIVE'",
                (status, utc_now(), job_id),
            )
            row = self._conn.execute(
                "SELECT * FROM refresh_targets WHERE job_id = ?", (job_id,)
            ).fetchone()
            return _refresh_target_from_row(row) if row is not None else None


class ReportDeltaRepository:
    """Immutable per-report delta index."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def insert(self, delta: ReportDelta) -> ReportDelta:
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM report_deltas WHERE report_id = ?", (delta.report_id,)
            ).fetchone()
            if existing is not None:
                frozen = _report_delta_from_row(existing)
                if frozen == delta:
                    return frozen
                raise ReportConflictError(f"report delta conflict: {delta.report_id}")
            self._conn.execute(
                "INSERT INTO report_deltas (report_id, previous_report_id, summary_json, details_path) "
                "VALUES (?, ?, ?, ?)",
                (
                    delta.report_id, delta.previous_report_id,
                    json.dumps(delta.summary, ensure_ascii=False, sort_keys=True), delta.details_path,
                ),
            )
            return delta

    def get(self, report_id: str) -> ReportDelta | None:
        with self._store._tx():
            row = self._conn.execute(
                "SELECT * FROM report_deltas WHERE report_id = ?", (report_id,)
            ).fetchone()
            return _report_delta_from_row(row) if row is not None else None


class FindingLedgerRepository:
    """Per-FuncID Finding lifecycle tracking (0.2.1 S3)."""

    def __init__(self, store: SqliteStore) -> None:
        self._store = store
        self._conn = store._conn

    def get_active(self, func_id: str) -> list[dict[str, Any]]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM finding_ledger WHERE func_id = ? AND status = 'active' "
                "ORDER BY first_seen_at",
                (func_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_all(self, func_id: str) -> list[dict[str, Any]]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM finding_ledger WHERE func_id = ? ORDER BY first_seen_at",
                (func_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def upsert_finding(
        self,
        *,
        finding_id: str,
        func_id: str,
        criterion_id: str,
        severity: str,
        message: str,
        run_id: str,
        executor: str,
    ) -> None:
        now = utc_now()
        with self._store._tx(immediate=True):
            existing = self._conn.execute(
                "SELECT * FROM finding_ledger WHERE finding_id = ?",
                (finding_id,),
            ).fetchone()
            if existing is None:
                self._conn.execute(
                    "INSERT INTO finding_ledger "
                    "(finding_id, func_id, criterion_id, severity, message, status, "
                    " first_seen_run_id, first_seen_at, last_confirmed_run_id, "
                    " last_confirmed_at, confirmation_count, executor_set) "
                    "VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, 1, ?)",
                    (
                        finding_id, func_id, criterion_id, severity, message,
                        run_id, now, run_id, now,
                        json.dumps([executor]),
                    ),
                )
            else:
                executor_set = json.loads(existing["executor_set"] or "[]")
                if executor not in executor_set:
                    executor_set.append(executor)
                self._conn.execute(
                    "UPDATE finding_ledger SET "
                    "  last_confirmed_run_id = ?, "
                    "  last_confirmed_at = ?, "
                    "  confirmation_count = confirmation_count + 1, "
                    "  executor_set = ?, "
                    "  status = 'active', "
                    "  severity = ?, "
                    "  message = ? "
                    "WHERE finding_id = ?",
                    (
                        run_id, now, json.dumps(executor_set),
                        severity, message, finding_id,
                    ),
                )

    def mark_resolved(self, func_id: str, active_finding_ids: set[str], run_id: str) -> int:
        """Mark active findings NOT in the current run as resolved. Returns count."""
        now = utc_now()
        with self._store._tx(immediate=True):
            rows = self._conn.execute(
                "SELECT finding_id FROM finding_ledger "
                "WHERE func_id = ? AND status = 'active'",
                (func_id,),
            ).fetchall()
            resolved_count = 0
            for row in rows:
                if row["finding_id"] not in active_finding_ids:
                    disposition = json.dumps({
                        "run_id": run_id, "action": "resolved", "at": now,
                    })
                    self._conn.execute(
                        "UPDATE finding_ledger SET status = 'resolved', "
                        "disposition_history = json_insert(disposition_history, '$[#]', ?) "
                        "WHERE finding_id = ?",
                        (disposition, row["finding_id"]),
                    )
                    resolved_count += 1
            return resolved_count
