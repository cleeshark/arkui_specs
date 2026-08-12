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
    JobNotFoundError,
)
from ..domain.models import (
    Artifact,
    Attempt,
    CreateJobCommand,
    DependencySnapshot,
    Event,
    Job,
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
            self._conn.execute(
                "INSERT INTO dependency_snapshots (job_id, repo_name, branch, sha, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(job_id, repo_name) DO UPDATE SET "
                "branch = excluded.branch, sha = excluded.sha, "
                "status = excluded.status, created_at = excluded.created_at",
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
