"""Immutable paths and revisions for one evaluation workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..settings import ServiceSettings


@dataclass(frozen=True)
class EvaluationWorkspace:
    """An OpenHarmony-shaped checkout frozen for one Job."""

    workspace_root: Path
    repo_root: Path
    specs_root: Path
    schemas_root: Path
    revisions: dict[str, str]

    @classmethod
    def control_checkout(
        cls,
        settings: ServiceSettings,
        source_revision: str,
        *,
        revisions: dict[str, str] | None = None,
    ) -> "EvaluationWorkspace":
        """Build a non-isolated workspace for explicit unit-test injection.

        Production workers always use :class:`RevisionWorkspaceManager`.
        """
        frozen = dict(revisions or {})
        frozen.setdefault("ace_engine", source_revision)
        return cls(
            workspace_root=settings.repo_root,
            repo_root=settings.repo_root,
            specs_root=settings.specs_root,
            schemas_root=settings.schemas_root,
            revisions=frozen,
        )
