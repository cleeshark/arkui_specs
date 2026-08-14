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
                "selected_run_ids, status, progress_json, executor_config, "
                "protocol_version, evaluator_version, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id,
                    cmd.func_id,
                    cmd.source_revision,
                    cmd.run_count,
                    json.dumps(list(cmd.selected_run_ids)),
                    S.QUEUED,
                    json.dumps(progress, ensure_ascii=False),
                    json.dumps(executor_config, ensure_ascii=False),
                    protocol_version,
                    evaluator_version,
                    now,
                    now,
                ),
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
    ) -> Job:
        """Validate the transition via the state matrix, update status and log it."""
        with self._store._tx(immediate=True):
            row = self._conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                raise JobNotFoundError(job_id)
            src = row["status"]
            new = S.transition(src, dst)  # raises IllegalTransitionError if illegal
            now = utc_now()
            self._conn.execute(
                "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                (new, now, job_id),
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
        self, job_id: str, *, since_seq: int = 0, limit: int = 200
    ) -> list[Event]:
        with self._store._tx():
            rows = self._conn.execute(
                "SELECT * FROM events WHERE job_id = ? AND seq > ? "
                "ORDER BY seq LIMIT ?",
                (job_id, since_seq, limit),
            ).fetchall()
            return [_event_from_row(r) for r in rows]


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
