"""Job and Attempt state constants and the allowed transition matrix.

The status tokens and transitions mirror the service plan §4.1 state table.
``TRANSITIONS`` is the worker-facing matrix: the only backward edges are
``failed -> queued`` and ``cancelled -> queued`` (explicit retry). The crash
recovery path in the store is a *privileged* startup operation that does NOT go
through this matrix (see ``sqlite_store.recover_active_jobs``); workers can
never move a job backward by accident.
"""

from __future__ import annotations

# --- Job status tokens (service plan §4.1) ---------------------------------

QUEUED = "queued"
PREPARING = "preparing"
EVIDENCE = "evidence"
SEMANTIC = "semantic"
AWAITING_EXECUTOR = "awaiting_executor"
AGGREGATION = "aggregation"
ARCHIVE = "archive"
SITE_HISTORY = "site_history"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"

JOB_STATES = frozenset({
    QUEUED,
    PREPARING,
    EVIDENCE,
    SEMANTIC,
    AWAITING_EXECUTOR,
    AGGREGATION,
    ARCHIVE,
    SITE_HISTORY,
    COMPLETED,
    FAILED,
    CANCELLED,
})
"""All 11 Job status tokens, used by the DB CHECK constraint and the schema enum."""

TERMINAL_STATES = frozenset({COMPLETED, FAILED, CANCELLED})
ACTIVE_STATES = frozenset({
    PREPARING,
    EVIDENCE,
    SEMANTIC,
    AGGREGATION,
    ARCHIVE,
    SITE_HISTORY,
})
"""Non-terminal worker-owned states. On crash recovery each is reset to queued."""

CANCELLABLE_WORKER_STATES = frozenset({PREPARING, EVIDENCE, SEMANTIC, AGGREGATION})
"""States whose active worker must cooperatively finish a cancellation request."""

IMMEDIATE_CANCEL_STATES = frozenset({QUEUED, AWAITING_EXECUTOR})
"""States with no executing worker; cancellation can be persisted immediately."""

QUIESCENT_STATES = TERMINAL_STATES | frozenset({AWAITING_EXECUTOR})
"""States in which a dispatcher worker may release its in-memory registration."""

RESUMABLE_STATES = frozenset({QUEUED, FAILED, CANCELLED, AWAITING_EXECUTOR})
"""States a recovered job may legitimately land in (never completed)."""

# --- Attempt status tokens -------------------------------------------------

ATTEMPT_RUNNING = "running"
ATTEMPT_COMPLETED = "completed"
ATTEMPT_FAILED = "failed"
ATTEMPT_CANCELLED = "cancelled"

ATTEMPT_STATES = frozenset({ATTEMPT_RUNNING, ATTEMPT_COMPLETED, ATTEMPT_FAILED, ATTEMPT_CANCELLED})

# --- Attempt stage tokens --------------------------------------------------
# These mirror the Job active states that produce durable checkpoints. The
# staged-run validator sub-stages (observations / aggregation / final) live
# inside the SEMANTIC / AGGREGATION stages and are tracked by feat_id, not as
# separate attempt stages.

STAGE_PREPARING = PREPARING
STAGE_EVIDENCE = EVIDENCE
STAGE_SEMANTIC = SEMANTIC
STAGE_AGGREGATION = AGGREGATION
STAGE_ARCHIVE = ARCHIVE
STAGE_SITE_HISTORY = SITE_HISTORY

ATTEMPT_STAGES = frozenset({
    STAGE_PREPARING,
    STAGE_EVIDENCE,
    STAGE_SEMANTIC,
    STAGE_AGGREGATION,
    STAGE_ARCHIVE,
    STAGE_SITE_HISTORY,
})

STAGE_NULLABILITY: dict[str, tuple[bool, bool]] = {
    # stage -> (run_id required, feat_id required)
    # Job-level stages carry no run/feat; only SEMANTIC (per Feat in a run) has both.
    STAGE_PREPARING: (False, False),
    STAGE_EVIDENCE: (False, False),
    STAGE_SEMANTIC: (True, True),
    STAGE_AGGREGATION: (False, False),
    STAGE_ARCHIVE: (False, False),
    STAGE_SITE_HISTORY: (False, False),
}

# --- Worker-facing transition matrix (service plan §4.1 "可转移到") ----------

TRANSITIONS: dict[str, frozenset[str]] = {
    QUEUED: frozenset({PREPARING, CANCELLED}),
    PREPARING: frozenset({EVIDENCE, FAILED, CANCELLED}),
    EVIDENCE: frozenset({SEMANTIC, FAILED, CANCELLED}),
    SEMANTIC: frozenset({AGGREGATION, FAILED, CANCELLED, AWAITING_EXECUTOR}),
    AWAITING_EXECUTOR: frozenset({SEMANTIC, CANCELLED}),
    AGGREGATION: frozenset({ARCHIVE, FAILED, CANCELLED}),
    ARCHIVE: frozenset({SITE_HISTORY, FAILED}),
    SITE_HISTORY: frozenset({COMPLETED, FAILED}),
    COMPLETED: frozenset(),  # terminal, read-only
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
