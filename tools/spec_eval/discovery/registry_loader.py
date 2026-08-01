"""Load Function and Feature registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from spec_eval.config import EvaluationConfig
from spec_eval.errors import ConfigurationError


@dataclass(frozen=True)
class RegistryData:
    functions: tuple[dict[str, Any], ...]
    features: tuple[dict[str, Any], ...]

    def function_map(self) -> dict[str, dict[str, Any]]:
        return {str(entry.get("id")): entry for entry in self.functions if entry.get("id")}

    def features_for(self, func_id: str) -> tuple[dict[str, Any], ...]:
        entries = [entry for entry in self.features if str(entry.get("func_id")) == func_id]
        return tuple(sorted(entries, key=lambda item: str(item.get("id", ""))))


class RegistryLoader:
    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def load(self) -> RegistryData:
        for path in (self.config.functions_registry, self.config.features_registry):
            if not path.is_file():
                raise ConfigurationError(f"registry does not exist: {path}")
        try:
            functions_doc = yaml.safe_load(self.config.functions_registry.read_text(encoding="utf-8")) or {}
            features_doc = yaml.safe_load(self.config.features_registry.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as error:
            raise ConfigurationError(f"invalid registry YAML: {error}") from error
        functions = functions_doc.get("functions", [])
        features = features_doc.get("features", [])
        if not isinstance(functions, list) or not isinstance(features, list):
            raise ConfigurationError("registry roots must contain list fields `functions` and `features`")
        return RegistryData(tuple(functions), tuple(features))

