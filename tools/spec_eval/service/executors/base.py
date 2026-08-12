"""The SemanticExecutor interface (TASK-011-04).

The pipeline depends on this Protocol, never on a concrete backend. The Codex
CLI adapter (``codex_cli.py``) is the only implementation in this phase.
"""

from __future__ import annotations

import threading
from typing import Any, Protocol, runtime_checkable

from .contract import EventSink, ExecutionResult, WorkItemInput


@runtime_checkable
class SemanticExecutor(Protocol):
    """Process exactly one staged work item and return a structured result.

    Implementations must:
    * be deterministic given the same ``WorkItemInput`` and frozen revision;
    * write their final structured result to ``work.executor_result_path``;
    * report progress via ``emit`` (used for UI/logs only, never as completion
      evidence);
    * honour ``cancel`` by terminating promptly and returning a ``cancelled``
      result;
    * never modify formal Spec/Design/Registry/source or read ``forbidden_paths``.
    """

    def is_available(self) -> bool:
        """Return True iff the backend is installed, authenticated and usable."""
        ...

    def describe(self) -> dict[str, Any]:
        """Return a redacted descriptor (type, command, sandbox, versions)."""
        ...

    def execute(
        self,
        work: WorkItemInput,
        emit: EventSink,
        cancel: threading.Event | None = None,
    ) -> ExecutionResult:
        ...
