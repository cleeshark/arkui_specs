"""Command objects interpreted by the store.

Commands carry no behavior. Phase 1 implements cancel and retry; ``ResumeJobCommand``
is a stub that the Phase 3 scheduler fills in.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CancelJobCommand:
    """Cancel a job from any non-terminal state."""

    job_id: str
    reason: str | None = None


@dataclass(frozen=True)
class RetryJobCommand:
    """Reset a ``failed``/``cancelled`` job back to ``queued`` (keeps history)."""

    job_id: str
    reason: str | None = None


@dataclass(frozen=True)
class ResumeJobCommand:
    """Resume a recovered job (Phase 3 scheduler fills the execution).

    Phase 1 only persists this as intent; no worker consumes it yet.
    """

    job_id: str
