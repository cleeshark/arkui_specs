"""Safe resolution of model-declared evidence paths.

Evidence declarations use canonical OpenHarmony repository-relative POSIX
paths.  The model is never allowed to select an arbitrary host path: absolute
paths, parent traversal and symlink escapes are rejected before any file is
opened.  The resolver also understands the four repositories frozen for an
evaluation Job.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping


@dataclass(frozen=True)
class EvidencePathResolution:
    """One canonical evidence path resolved inside a frozen repository."""

    canonical_path: str
    absolute_path: Path
    repository: str


class EvidencePathError(ValueError):
    """A model-declared path is not a legal frozen evidence path."""

    def __init__(self, code: str, path: str, expected: str) -> None:
        super().__init__(f"{code}: {path}")
        self.code = code
        self.path = path
        self.expected = expected


class FrozenEvidencePathResolver:
    """Resolve canonical evidence paths against an immutable four-repo view."""

    _SDK_PREFIXES = (
        ("interface/sdk-js", "sdk-js"),
        ("interface/sdk_c", "sdk_c"),
    )
    _SERVICE_PREFIXES = (
        "evidence",
        "runs",
        "specs/.evaluator/service-data",
    )

    def __init__(
        self,
        repository_roots: Mapping[str, Path],
        *,
        forbidden_roots: tuple[Path, ...] = (),
        required_paths: tuple[str, ...] = (),
    ) -> None:
        if "ace_engine" not in repository_roots:
            raise ValueError("ace_engine evidence root is required")
        self._roots = {
            name: root.resolve() for name, root in repository_roots.items()
        }
        self._forbidden_roots = tuple(root.resolve() for root in forbidden_roots)
        self._required_paths = frozenset(required_paths)

    @classmethod
    def ace_engine_only(cls, repo_root: Path) -> "FrozenEvidencePathResolver":
        """Compatibility constructor for kernel callers and isolated tests."""
        return cls({"ace_engine": repo_root})

    def resolve(self, path_text: str) -> EvidencePathResolution:
        canonical = self._validate_canonical(path_text)
        repository, relative = self._select_repository(canonical)
        root = self._roots.get(repository)
        if root is None:
            code = (
                "FROZEN_EVIDENCE_UNREADABLE"
                if canonical in self._required_paths
                else "EVIDENCE_PATH_NOT_ALLOWED"
            )
            raise EvidencePathError(
                code,
                path_text,
                f"path in a frozen repository; {repository} is not available",
            )
        try:
            resolved = (root / relative).resolve(strict=True)
        except (OSError, RuntimeError):
            code = (
                "FROZEN_EVIDENCE_UNREADABLE"
                if canonical in self._required_paths
                else "EVIDENCE_PATH_NOT_FOUND"
            )
            raise EvidencePathError(
                code,
                path_text,
                "existing file in the frozen workspace",
            ) from None
        if not self._is_relative_to(resolved, root):
            raise EvidencePathError(
                "EVIDENCE_PATH_NOT_ALLOWED",
                path_text,
                "path contained by its frozen repository root",
            )
        if any(self._is_relative_to(resolved, root) for root in self._forbidden_roots):
            raise EvidencePathError(
                "EVIDENCE_PATH_NOT_ALLOWED",
                path_text,
                "frozen source/spec/SDK path, not service job data",
            )
        if not resolved.is_file():
            code = (
                "FROZEN_EVIDENCE_UNREADABLE"
                if canonical in self._required_paths
                else "EVIDENCE_PATH_NOT_FOUND"
            )
            raise EvidencePathError(
                code,
                path_text,
                "existing regular file in the frozen workspace",
            )
        return EvidencePathResolution(canonical, resolved, repository)

    @staticmethod
    def _validate_canonical(path_text: str) -> str:
        if not path_text or "\\" in path_text:
            raise EvidencePathError(
                "EVIDENCE_DECLARATION_INVALID",
                path_text,
                "non-empty canonical repository-relative POSIX path",
            )
        path = PurePosixPath(path_text)
        parts = path_text.split("/")
        if path.is_absolute() or any(part in ("", ".", "..") for part in parts):
            raise EvidencePathError(
                "EVIDENCE_PATH_NOT_ALLOWED",
                path_text,
                "canonical repository-relative path without '.', '..' or empty segments",
            )
        canonical = path.as_posix()
        if canonical != path_text:
            raise EvidencePathError(
                "EVIDENCE_PATH_NOT_ALLOWED",
                path_text,
                "canonical repository-relative POSIX path",
            )
        if any(
            canonical == prefix or canonical.startswith(prefix + "/")
            for prefix in FrozenEvidencePathResolver._SERVICE_PREFIXES
        ):
            raise EvidencePathError(
                "EVIDENCE_PATH_NOT_ALLOWED",
                path_text,
                "frozen source/spec/SDK path, not service evidence or run data",
            )
        return canonical

    def _select_repository(self, canonical: str) -> tuple[str, Path]:
        for prefix, repository in self._SDK_PREFIXES:
            if canonical == prefix:
                return repository, Path(".")
            marker = prefix + "/"
            if canonical.startswith(marker):
                return repository, Path(canonical[len(marker):])
        return "ace_engine", Path(canonical)

    @staticmethod
    def _is_relative_to(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True
