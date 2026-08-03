"""Resolve changed files to unique affected Functions."""

from __future__ import annotations

from pathlib import Path

from spec_eval.discovery.function_locator import FunctionLocator
from spec_eval.errors import FunctionNotFoundError
from spec_eval.models.function import FunctionContext


class ChangedFunctionResolver:
    def __init__(self, locator: FunctionLocator) -> None:
        self.locator = locator

    def resolve(self, paths: list[str | Path]) -> tuple[FunctionContext, ...]:
        contexts: dict[str, FunctionContext] = {}
        global_paths = {
            self.locator.config.functions_registry.resolve(),
            self.locator.config.features_registry.resolve(),
        }
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
            if candidate in global_paths or any(candidate.is_relative_to(root) for root in global_roots):
                return tuple(self.locator.locate(func_id) for func_id in self.locator.all_func_ids())
            try:
                context = self.locator.locate_by_path(candidate)
            except FunctionNotFoundError:
                continue
            contexts[context.func_id] = context
        return tuple(contexts[key] for key in sorted(contexts))
