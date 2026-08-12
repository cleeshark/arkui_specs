"""Frozen domain DTOs for the semantic evaluation service.

Field names align with service plan §4.2. The store maps these to/from the
SQLite rows; no DTO imports the store or any I/O module.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any


def make_job_id() -> str:
    """Mint a fresh, opaque job id (24 hex chars)."""
    return secrets.token_hex(12)


def default_progress(stage: str | None = None) -> dict[str, Any]:
    """Build the initial ``progress`` blob stored on ``jobs.progress_json``."""
    return {
        "stage": stage,
        "run_id": None,
        "feat_id": None,
        "completed_checkpoints": [],
        "total_checkpoints": None,
        "note": None,
    }


@dataclass(frozen=True)
class Event:
    """An append-only, monotonic event in a job's lifecycle."""

    job_id: str
    seq: int
    event_type: str
    payload: dict[str, Any]
    created_at: str


@dataclass(frozen=True)
class Artifact:
    """An immutable file produced by a job (path, sha256, size)."""

    artifact_id: str
    job_id: str
    kind: str
    path: str
    sha256: str
    size: int
    created_at: str


@dataclass(frozen=True)
class DependencySnapshot:
    """A task-level frozen dependency revision (specs/sdk repos)."""

    job_id: str
    repo_name: str
    branch: str
    sha: str
    status: str  # "frozen" | "stale"
    created_at: str


@dataclass(frozen=True)
class Attempt:
    """A durable checkpoint for one (run, feat, stage) of a job.

    ``run_id``/``feat_id`` are ``None`` for job-level stages; the store maps
    ``None <-> ""`` at the DB boundary so the UNIQUE(job_id, run_id, feat_id,
    stage) constraint actually enforces checkpoint idempotency.
    """

    attempt_id: str
    job_id: str
    run_id: str | None
    feat_id: str | None
    stage: str
    status: str
    started_at: str
    finished_at: str | None = None
    exit_code: int | None = None
    artifact_dir: str | None = None


@dataclass(frozen=True)
class Job:
    """A semantic evaluation job.

    ``func_id``, ``source_revision``, ``protocol_version`` and
    ``evaluator_version`` are immutable after creation (service plan §4.2).
    """

    job_id: str
    func_id: str
    source_revision: str
    run_count: int
    selected_run_ids: tuple[str, ...]
    status: str
    progress: dict[str, Any]
    executor_config: dict[str, Any]
    protocol_version: str
    evaluator_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CreateJobCommand:
    """Request to create a job.

    If ``job_id`` is supplied and already exists with matching immutable
    fields, creation is idempotent and returns the existing job. If it exists
    with conflicting immutable fields, ``DuplicateJobError`` is raised. If
    ``job_id`` is ``None`` a fresh id is minted (no idempotency).
    """

    func_id: str
    source_revision: str
    run_count: int = 3
    selected_run_ids: tuple[str, ...] = ()
    max_parallel: int = 2
    executor_config: dict[str, Any] | None = None
    job_id: str | None = None
