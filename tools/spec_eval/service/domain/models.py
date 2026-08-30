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
class EvaluationReportRecord:
    """Immutable query index for one archived automated evaluation report."""

    report_id: str
    job_id: str
    func_id: str
    source_revision: str
    revision_set: dict[str, str]
    input_fingerprint: str
    evidence_fingerprint: str
    evaluator_version: str
    protocol_version: str
    rubric_version: str
    selected_run_id: str
    run_count: int
    target_generation: int
    completed_at: str
    archive_path: str
    manifest_sha256: str
    summary: dict[str, Any]


@dataclass(frozen=True)
class FunctionReportHead:
    """Mutable projection selecting the current report for one Function."""

    func_id: str
    current_report_id: str | None
    desired_generation: int
    desired_revision: str | None
    desired_input_fingerprint: str | None
    freshness: str
    stale_reasons: tuple[str, ...]
    warn_at: str | None
    expires_at: str | None
    refresh_status: str
    active_job_id: str | None
    last_refresh_error: str | None
    updated_at: str


@dataclass(frozen=True)
class FreshnessPolicy:
    """Global or FuncID-specific report validity policy."""

    scope_type: str
    scope_key: str
    max_age_days: int
    warning_days: int
    version: int
    updated_at: str


@dataclass(frozen=True)
class SchedulerConfig:
    """Singleton auto-scheduler policy (schema v9).

    ``start_times`` are ``"HH:MM"`` local-time daily triggers. ``executor_priority``
    is an ordered chain of registered executor ids; dispatch uses the first
    executor whose daily token usage is still under its ``executor_quota`` entry,
    failing over down the chain and stopping the run only when all are exhausted.
    Holds policy only — never tokens, credentials or prompts.
    """

    enabled: bool
    start_times: tuple[str, ...]
    parallel_tasks: int
    executor_priority: tuple[str, ...]
    executor_quota: dict[str, int]
    version: int
    updated_at: str


@dataclass(frozen=True)
class RefreshTarget:
    """Frozen target metadata binding a manual refresh Job to one generation."""

    job_id: str
    func_id: str
    generation: int
    desired_revision: str
    revision_set: dict[str, str]
    provisional_fingerprint: str
    input_fingerprint: str | None
    evidence_fingerprint: str | None
    dedupe_key: str
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ReportDelta:
    """Difference between a promoted report and the prior current report."""

    report_id: str
    previous_report_id: str | None
    summary: dict[str, Any]
    details_path: str | None


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
    stage: str
    progress: dict[str, Any]
    executor_config: dict[str, Any]
    protocol_version: str
    evaluator_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class JobStatistics:
    """Durable execution timing and non-sensitive executor usage counters."""

    job_id: str
    started_at: str | None
    finished_at: str | None
    run_started_at: str | None
    active_elapsed_ms: int
    executor_invocations: int
    usage_reported_invocations: int
    telemetry_reported_invocations: int
    executor_elapsed_ms: int
    executor_tool_calls: int
    executor_command_calls: int
    input_paths_accessed: int
    evidence_paths_accessed: int
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    reasoning_output_tokens: int
    total_tokens: int
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
