"""Job and Attempt state constants and the allowed transition matrix.

Protocol 0.2.0 (design v3 R6, audit §2.3): the Job lifecycle status and the
execution stage are separate dimensions.

- ``status`` is the six-state lifecycle: queued | running | waiting |
  completed | failed | cancelled. Only the status participates in the worker
  transition matrix; ``waiting`` replaces the old ``awaiting_executor`` and is
  recovered to ``queued`` on restart (no dead-end states, audit §7.1).
- ``stage`` is the progress dimension persisted next to the status:
  preparing → evidence → observation → aggregation → report → archive →
  projection. The synchronous critical path ends at ``archive`` (the job is
  completed); ``projection`` progress lives on the independent Projection
  entity and is surfaced through the stage only for display.

``TRANSITIONS`` is the worker-facing matrix: the only backward edges are
``failed -> queued`` and ``cancelled -> queued`` (explicit retry). The crash
recovery path in the store is a *privileged* startup operation that does NOT go
through this matrix (see ``sqlite_store.recover_active_jobs``); workers can
never move a job backward by accident.
"""

from __future__ import annotations

# --- Job status tokens (design v3 R6) ---------------------------------------

QUEUED = "queued"
RUNNING = "running"
WAITING = "waiting"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"

JOB_STATES = frozenset({
    QUEUED, RUNNING, WAITING, COMPLETED, FAILED, CANCELLED,
})
"""All six Job status tokens, used by the DB CHECK constraint and the API."""

TERMINAL_STATES = frozenset({COMPLETED, FAILED, CANCELLED})
ACTIVE_STATES = frozenset({RUNNING})
"""Worker-owned status. On crash recovery each running job is reset to queued."""

WAITING_STATES = frozenset({WAITING})
"""No executing worker; the executor was unavailable. Recovered to queued."""

CANCELLABLE_WORKER_STATES = frozenset({RUNNING})
"""Statuses whose active worker must cooperatively finish a cancellation."""

IMMEDIATE_CANCEL_STATES = frozenset({QUEUED, WAITING})
"""Statuses with no executing worker; cancellation can persist immediately."""

QUIESCENT_STATES = TERMINAL_STATES | frozenset({WAITING})
"""Statuses in which a dispatcher worker may release its in-memory registration."""

RESUMABLE_STATES = frozenset({QUEUED, FAILED, CANCELLED, WAITING})
"""Statuses a recovered job may legitimately land in (never completed)."""

# --- Stage tokens ------------------------------------------------------------
# The synchronous critical path ends at ARCHIVE; PROJECTION runs after the job
# is completed and its progress lives on the Projection entity.

STAGE_PREPARING = "preparing"
STAGE_EVIDENCE = "evidence"
STAGE_OBSERVATION = "observation"
STAGE_AGGREGATION = "aggregation"
STAGE_REPORT = "report"
STAGE_ARCHIVE = "archive"
STAGE_PROJECTION = "projection"

STAGES = (
    STAGE_PREPARING,
    STAGE_EVIDENCE,
    STAGE_OBSERVATION,
    STAGE_AGGREGATION,
    STAGE_REPORT,
    STAGE_ARCHIVE,
    STAGE_PROJECTION,
)
"""Ordered pipeline stages (UI stepper, design D4)."""

STAGE_SEQUENCE: dict[str, int] = {stage: index for index, stage in enumerate(STAGES)}

JOB_STAGES = frozenset(STAGES)

# Legacy attempt-stage tokens (checkpoint labels in the attempts table; they
# document what produced the checkpoint and are intentionally not renamed).
ATTEMPT_STAGE_PREPARING = "preparing"
ATTEMPT_STAGE_EVIDENCE = "evidence"
ATTEMPT_STAGE_OBSERVATION = "semantic"
ATTEMPT_STAGE_AGGREGATION = "aggregation"
ATTEMPT_STAGE_ARCHIVE = "archive"

# --- Attempt status tokens ---------------------------------------------------

ATTEMPT_RUNNING = "running"
ATTEMPT_COMPLETED = "completed"
ATTEMPT_FAILED = "failed"
ATTEMPT_CANCELLED = "cancelled"

ATTEMPT_STATES = frozenset({ATTEMPT_RUNNING, ATTEMPT_COMPLETED, ATTEMPT_FAILED, ATTEMPT_CANCELLED})

ATTEMPT_STAGES = frozenset({
    ATTEMPT_STAGE_PREPARING,
    ATTEMPT_STAGE_EVIDENCE,
    ATTEMPT_STAGE_OBSERVATION,
    ATTEMPT_STAGE_AGGREGATION,
    ATTEMPT_STAGE_ARCHIVE,
})

STAGE_NULLABILITY: dict[str, tuple[bool, bool]] = {
    # stage -> (run_id required, feat_id required)
    # Job-level stages carry no run/feat; only the observation stage (per Feat
    # in a run) has both.
    ATTEMPT_STAGE_PREPARING: (False, False),
    ATTEMPT_STAGE_EVIDENCE: (False, False),
    ATTEMPT_STAGE_OBSERVATION: (True, True),
    ATTEMPT_STAGE_AGGREGATION: (False, False),
    ATTEMPT_STAGE_ARCHIVE: (False, False),
}

# --- Worker-facing transition matrix ----------------------------------------

TRANSITIONS: dict[str, frozenset[str]] = {
    QUEUED: frozenset({RUNNING, CANCELLED}),
    RUNNING: frozenset({RUNNING, WAITING, COMPLETED, FAILED, CANCELLED}),
    # running -> running advances the stage without a lifecycle change;
    # running -> waiting pauses on executor unavailability
    WAITING: frozenset({RUNNING, CANCELLED}),
    # waiting -> running resumes the paused worker (run_job_pipeline restart)
    COMPLETED: frozenset(),  # terminal, read-only; projection is independent
    FAILED: frozenset({QUEUED}),  # explicit retry only
    CANCELLED: frozenset({QUEUED}),  # explicit retry only
}


def can_transition(src: str, dst: str) -> bool:
    """Return True if ``dst`` is a legal worker transition from ``src``."""
    return dst in TRANSITIONS.get(src, frozenset())


def transition(src: str, dst: str) -> str:
    """Validate and return ``dst`` for a transition from ``src``.

    Raises:
        IllegalTransitionError: if ``src -> dst`` is not in :data:`TRANSITIONS`.
    """
    # Imported here to avoid a circular import at module load time.
    from .errors import IllegalTransitionError

    if not can_transition(src, dst):
        raise IllegalTransitionError(src, dst)
    return dst


# --- Projection entity status ------------------------------------------------

PROJECTION_PENDING = "pending"
PROJECTION_RUNNING = "running"
PROJECTION_COMPLETED = "completed"
PROJECTION_FAILED = "failed"

PROJECTION_STATES = frozenset({
    PROJECTION_PENDING, PROJECTION_RUNNING, PROJECTION_COMPLETED, PROJECTION_FAILED,
})
