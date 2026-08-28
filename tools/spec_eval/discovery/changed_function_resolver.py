"""Resolve changed files to unique affected Functions."""

from __future__ import annotations

from pathlib import Path

from .function_locator import FunctionLocator
from .registry_diff_analyzer import RegistryDiffAnalyzer
from ..errors import FunctionNotFoundError
from ..models.function import FunctionContext


class ChangedFunctionResolver:
    def __init__(self, locator: FunctionLocator, base_ref: str = "HEAD") -> None:
        self.locator = locator
        self.base_ref = base_ref
        self.registry_analyzer = RegistryDiffAnalyzer(locator.config.repo_root)

    def resolve(self, paths: list[str | Path]) -> tuple[FunctionContext, ...]:
        contexts: dict[str, FunctionContext] = {}

        # Registry files that support incremental analysis
        registry_files = {
            self.locator.config.functions_registry.resolve(),
            self.locator.config.features_registry.resolve(),
        }

        # Truly global paths that always trigger full scan
        global_paths = set()
        global_paths.update(
            (self.locator.config.rules_root / name).resolve()
            for name in (
                "gate_rules.yaml",
                "structure_rules.yaml",
                "citation_rules.yaml",
                "sdk_rules.yaml",
                "exemptions.yaml",
                "rule_applicability.yaml",
            )
        )
        tool_root = self.locator.config.specs_root / "tools" / "spec_eval"
        global_roots = tuple(
            (tool_root / name).resolve()
            for name in ("checks", "discovery", "evidence", "models", "parser", "rules")
        )
        global_paths.update((tool_root / name).resolve() for name in ("config.py", "orchestrator.py"))

        for value in paths:
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = self.locator.config.repo_root / candidate
            candidate = candidate.resolve()

            # Check if it's a registry file that supports incremental analysis
            if candidate in registry_files:
                affected_func_ids = self.registry_analyzer.get_affected_func_ids_from_diff(
                    candidate, self.base_ref
                )
                if affected_func_ids is None:
                    # Cannot analyze or too many changes - trigger full scan
                    return tuple(self.locator.locate(func_id) for func_id in self.locator.all_func_ids())
                elif not affected_func_ids:
                    # Empty set = only metadata changed, no functions affected
                    continue
                else:
                    # Add affected functions to contexts
                    for func_id in affected_func_ids:
                        try:
                            contexts[func_id] = self.locator.locate(func_id)
                        except FunctionNotFoundError:
                            continue
                continue

            # Check truly global paths/roots
            if candidate in global_paths or any(candidate.is_relative_to(root) for root in global_roots):
                return tuple(self.locator.locate(func_id) for func_id in self.locator.all_func_ids())

            # Regular spec file - resolve to its function
            try:
                context = self.locator.locate_by_path(candidate)
            except FunctionNotFoundError:
                continue
            contexts[context.func_id] = context

        return tuple(contexts[key] for key in sorted(contexts))
