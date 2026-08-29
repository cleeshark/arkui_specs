"""Error classification for the semantic evaluation service.

Phase 1 instantiates the store/protocol errors. The worker-facing trio
(:class:`RetryableError`, :class:`AwaitingExecutorError`,
:class:`UnrecoverableJobError`) is frozen here per TASK-011-01 and consumed by
the Phase 2+ pipeline; it is not raised by Phase 1 code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Job


class SemanticServiceError(Exception):
    """Base class for all semantic service errors."""


class IllegalTransitionError(SemanticServiceError):
    """A Job status transition is not allowed by the transition matrix."""

    def __init__(self, src: str, dst: str) -> None:
        super().__init__(f"illegal job state transition: {src!r} -> {dst!r}")
        self.src = src
        self.dst = dst


class JobNotFoundError(SemanticServiceError):
    """No job exists for the given job_id."""

    def __init__(self, job_id: str) -> None:
        super().__init__(f"job not found: {job_id!r}")
        self.job_id = job_id


class DuplicateJobError(SemanticServiceError):
    """A job with the same id exists but with conflicting immutable fields."""

    def __init__(self, job_id: str, existing: "Job") -> None:
        super().__init__(f"job {job_id!r} already exists with different immutable fields")
        self.job_id = job_id
        self.existing = existing


class CheckpointExistsError(SemanticServiceError):
    """An attempt checkpoint for (job_id, run_id, feat_id, stage) already exists."""

    def __init__(self, job_id: str, stage: str, run_id: str | None, feat_id: str | None) -> None:
        super().__init__(
            f"checkpoint already exists for job={job_id!r} stage={stage!r} "
            f"run={run_id!r} feat={feat_id!r}"
        )
        self.job_id = job_id
        self.stage = stage
        self.run_id = run_id
        self.feat_id = feat_id


class SnapshotConflictError(SemanticServiceError):
    """A Job dependency snapshot was frozen previously with different data."""

    def __init__(self, job_id: str, repo_name: str) -> None:
        super().__init__(
            f"dependency snapshot conflict for job={job_id!r} repo={repo_name!r}"
        )
        self.job_id = job_id
        self.repo_name = repo_name


class ReportConflictError(SemanticServiceError):
    """An immutable report id or job id already maps to different content."""


class ReportPromotionError(SemanticServiceError):
    """A report cannot become current for the Function's desired generation."""


class FreshnessPolicyError(SemanticServiceError):
    """A freshness policy is invalid or attempts to reuse a version."""


class SchedulerConfigError(SemanticServiceError):
    """An auto-scheduler configuration is invalid or reuses a version."""


class ValidationError(SemanticServiceError):
    """A document failed JSON Schema or protocol validation."""


# --- Worker-facing errors (TASK-011-01 freeze; used by Phase 2+ pipeline) ---

class RetryableError(SemanticServiceError):
    """A transient failure; the current work item should be retried."""


class AwaitingExecutorError(SemanticServiceError):
    """No executor is available; the job should enter ``awaiting_executor``."""


class UnrecoverableJobError(SemanticServiceError):
    """An unrecoverable failure; the job should enter ``failed`` and keep history."""
