"""Executor registry: maps executor names to factory callables.

Design §10 defines the ExecutorRegistry as a pluggable lookup that the service
uses to resolve an executor name (``"codex"``, ``"claude"``, …) into a concrete
:class:`SemanticExecutor`.  The pipeline and kernel are executor-agnostic;
only the registry and the adapters under ``executors/`` know how to build a
backend from a configuration dict.

Current phase: single built-in entry ``codex`` → :class:`CodexCliExecutor`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .base import SemanticExecutor

# ---- type aliases --------------------------------------------------------

ExecutorFactory = Callable[[dict[str, Any], Path], SemanticExecutor]
"""(config, schemas_root) → SemanticExecutor"""


# ---- built-in factory ----------------------------------------------------

def _codex_factory(config: dict[str, Any], schemas_root: Path) -> SemanticExecutor:
    from .codex_cli import CodexCliExecutor

    return CodexCliExecutor(config, schemas_root=schemas_root)


# ---- registry ------------------------------------------------------------

# Name of the default executor when no explicit executor is requested.
DEFAULT_EXECUTOR = "codex"

# Internal mutable registry; populated by register() / unregister().
_REGISTRY: dict[str, ExecutorFactory] = {
    "codex": _codex_factory,
}


def register(name: str, factory: ExecutorFactory) -> None:
    """Register (or replace) an executor factory under *name*."""
    if not name or not name.isidentifier():
        raise ValueError(
            f"executor name must be a non-empty Python identifier, got {name!r}"
        )
    _REGISTRY[name] = factory


def unregister(name: str) -> ExecutorFactory | None:
    """Remove an executor factory; returns the removed factory or ``None``."""
    return _REGISTRY.pop(name, None)


def available() -> tuple[str, ...]:
    """Return the registered executor names in sorted order."""
    return tuple(sorted(_REGISTRY))


def get_factory(name: str) -> ExecutorFactory:
    """Look up a factory by name; raise :class:`KeyError` if unknown."""
    try:
        return _REGISTRY[name]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(
            f"unknown executor {name!r}; registered executors: {known}"
        ) from None


def create(
    name: str,
    config: dict[str, Any],
    schemas_root: Path,
) -> SemanticExecutor:
    """Resolve *name* → factory, then build and return an executor instance."""
    factory = get_factory(name)
    return factory(config, schemas_root)


def create_default(
    config: dict[str, Any],
    schemas_root: Path,
) -> SemanticExecutor:
    """Shorthand: create an executor using :data:`DEFAULT_EXECUTOR`."""
    return create(DEFAULT_EXECUTOR, config, schemas_root)
