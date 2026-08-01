"""Repository path and runtime configuration discovery."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from spec_eval import __version__


@dataclass(frozen=True)
class EvaluationConfig:
    repo_root: Path
    specs_root: Path
    oh_root: Path
    functions_registry: Path
    features_registry: Path
    rules_root: Path
    schemas_root: Path
    output_root: Path
    tool_version: str = __version__
    rule_version: str = "0.2.15"

    @classmethod
    def discover(cls, output_root: Path | None = None) -> "EvaluationConfig":
        repo_root = Path(__file__).resolve().parents[3]
        specs_root = repo_root / "specs"
        oh_root = repo_root.parents[2]
        evaluation_root = specs_root / "evaluation"
        return cls(
            repo_root=repo_root,
            specs_root=specs_root,
            oh_root=oh_root,
            functions_registry=specs_root / "registry" / "functions.yaml",
            features_registry=specs_root / "registry" / "features.yaml",
            rules_root=evaluation_root,
            schemas_root=evaluation_root / "schemas",
            output_root=output_root or repo_root / "out" / "spec-evaluation",
        )

    def git_revision(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return "unknown"
        return result.stdout.strip() or "unknown"

    def repo_relative(self, path: Path) -> str:
        resolved = path.resolve()
        try:
            return resolved.relative_to(self.repo_root.resolve()).as_posix()
        except ValueError:
            return resolved.as_posix()
