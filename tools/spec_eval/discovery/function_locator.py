"""Resolve complete Function evaluation contexts."""

from __future__ import annotations

from pathlib import Path

from spec_eval.config import EvaluationConfig
from spec_eval.discovery.registry_loader import RegistryData, RegistryLoader
from spec_eval.errors import FunctionNotFoundError
from spec_eval.models.function import FunctionContext


class FunctionLocator:
    def __init__(self, config: EvaluationConfig, registry: RegistryData | None = None) -> None:
        self.config = config
        self.registry = registry or RegistryLoader(config).load()

    def all_func_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.registry.function_map()))

    def locate(self, func_id: str) -> FunctionContext:
        function_entry = self.registry.function_map().get(func_id)
        if function_entry is None:
            raise FunctionNotFoundError(f"FuncID is not registered: {func_id}")
        path_value = str(function_entry.get("path") or "")
        function_path = (self.config.specs_root / path_value).resolve()
        feature_entries = self.registry.features_for(func_id)
        notes: list[str] = []

        registered_specs: list[Path] = []
        for entry in feature_entries:
            spec_value = entry.get("spec")
            if spec_value:
                registered_specs.append((self.config.specs_root / str(spec_value)).resolve())
        disk_specs = sorted(function_path.glob("Feat-*-spec.md")) if function_path.is_dir() else []
        feature_specs = tuple(sorted(set(registered_specs) | set(disk_specs)))

        design_value = function_entry.get("design")
        registered_design = (self.config.specs_root / str(design_value)).resolve() if design_value else None
        disk_design = function_path / "design.md"
        if registered_design is not None:
            design_path = registered_design
        elif disk_design.is_file():
            design_path = disk_design.resolve()
            notes.append("design.md exists on disk but is not registered")
        else:
            design_path = None

        return FunctionContext(
            func_id=func_id,
            function_path=function_path,
            design_path=design_path,
            feature_specs=feature_specs,
            function_registry_entry=function_entry,
            feature_registry_entries=feature_entries,
            source_revision=self.config.git_revision(),
            tool_version=self.config.tool_version,
            rule_version=self.config.rule_version,
            discovery_notes=tuple(notes),
        )

    def locate_by_path(self, path: Path | str) -> FunctionContext:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.config.repo_root / candidate
        candidate = candidate.resolve()
        matches: list[tuple[int, str]] = []
        for func_id, entry in self.registry.function_map().items():
            function_path = (self.config.specs_root / str(entry.get("path") or "")).resolve()
            try:
                candidate.relative_to(function_path)
            except ValueError:
                continue
            matches.append((len(function_path.parts), func_id))
        if not matches:
            raise FunctionNotFoundError(f"path is not inside a registered Function: {candidate}")
        return self.locate(max(matches)[1])

