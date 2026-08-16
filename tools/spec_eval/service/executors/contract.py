"""Executor contract DTOs (TASK-011-04).

These types are the stable boundary between the pipeline and any semantic
executor backend. The Codex CLI adapter is the only implementation in this
phase; Claude/API/remote adapters will implement the same contract later
without changing the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# --- Executor result status tokens ----------------------------------------

STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_TIMEOUT = "timeout"
STATUS_CANCELLED = "cancelled"
STATUS_AWAITING = "awaiting_executor"

EXECUTOR_VERSION = "codex-cli-0.4"
PROTOCOL_VERSION = "0.2.0"


@dataclass(frozen=True)
class WorkItemInput:
    """Everything an executor needs to process exactly one staged work item."""

    job_id: str
    func_id: str
    run_id: str
    work_item_id: str
    work_item: dict[str, Any]  # full work item from show_next_work_item (for the prompt)
    run_dir: str  # staged run dir; exposed as an extra read root for initialized inputs
    input_paths: tuple[str, ...]  # absolute paths the executor may read
    executor_result_path: str  # absolute path the executor must write
    repo_root: str  # working directory granted read-only
    skill_version: str
    protocol_version: str
    forbidden_paths: tuple[str, ...] = ()  # must NOT be read (confirmed reviews, other runs)
    prompt_extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionEvent:
    """A progress/observability event emitted by the executor (JSONL line, etc.)."""

    kind: str  # "jsonl" | "stage" | "command" | "error" | "info"
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    """The outcome of executing one work item.

    On ``completed`` the adapter must have written a valid structured result to
    ``executor_result_path``. The pipeline reads + schema-validates that file,
    extracts the executor-owned payload, merges it into the service-owned staged
    template, then runs the staged validator before publishing. Anything else
    (failed/timeout/cancelled) means the current work item must NOT be complete.
    """

    status: str
    exit_code: int | None = None
    executor_result_path: str | None = None
    observation: dict[str, Any] | None = None
    error: str | None = None
    elapsed_seconds: float = 0.0
    event_count: int = 0
    token_usage: dict[str, int] = field(default_factory=dict)
    usage_reported: bool = False
    telemetry: dict[str, int] = field(default_factory=dict)
    telemetry_reported: bool = False

    @property
    def succeeded(self) -> bool:
        return self.status == STATUS_COMPLETED


# Type alias for the progress callback the pipeline passes into execute().
EventSink = Callable[[ExecutionEvent], None]
