"""Function evaluation context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FunctionContext:
    func_id: str
    function_path: Path
    design_path: Path | None
    feature_specs: tuple[Path, ...]
    function_registry_entry: dict[str, Any]
    feature_registry_entries: tuple[dict[str, Any], ...]
    source_revision: str
    tool_version: str
    rule_version: str
    discovery_notes: tuple[str, ...] = field(default_factory=tuple)

    def all_documents(self) -> tuple[Path, ...]:
        documents: list[Path] = list(self.feature_specs)
        if self.design_path is not None:
            documents.append(self.design_path)
        return tuple(documents)

    def feature_ids(self) -> tuple[str, ...]:
        return tuple(str(entry.get("id", "")) for entry in self.feature_registry_entries if entry.get("id"))

    def to_dict(self, repo_root: Path | None = None) -> dict[str, Any]:
        def display(path: Path | None) -> str | None:
            if path is None:
                return None
            if repo_root is not None:
                try:
                    return path.resolve().relative_to(repo_root.resolve()).as_posix()
                except ValueError:
                    pass
            return path.as_posix()

        return {
            "func_id": self.func_id,
            "function_path": display(self.function_path),
            "design_path": display(self.design_path),
            "feature_specs": [display(path) for path in self.feature_specs],
            "function_registry_entry": self.function_registry_entry,
            "feature_registry_entries": list(self.feature_registry_entries),
            "source_revision": self.source_revision,
            "tool_version": self.tool_version,
            "rule_version": self.rule_version,
            "discovery_notes": list(self.discovery_notes),
        }

