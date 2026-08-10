"""Load rule policies and time-bounded exemptions."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from spec_eval.config import EvaluationConfig
from spec_eval.errors import ConfigurationError
from spec_eval.models.finding import Severity


@dataclass(frozen=True)
class RulePolicy:
    pattern: str
    severity: Severity | None = None
    gate: str | None = None


@dataclass(frozen=True)
class Exemption:
    rule_id: str
    func_id: str
    reason: str
    owner: str
    expires: date

    def active(self, today: date | None = None) -> bool:
        return self.expires >= (today or date.today())


@dataclass
class RuleConfiguration:
    version: str
    defaults: dict[str, str]
    policies: tuple[RulePolicy, ...]
    exemptions: tuple[Exemption, ...]

    def policy_for(self, rule_id: str) -> RulePolicy | None:
        matches = [policy for policy in self.policies if fnmatch.fnmatch(rule_id, policy.pattern)]
        return matches[-1] if matches else None

    def exemption_for(self, func_id: str, rule_id: str) -> Exemption | None:
        for exemption in self.exemptions:
            if exemption.func_id == func_id and fnmatch.fnmatch(rule_id, exemption.rule_id) and exemption.active():
                return exemption
        return None


class RuleLoader:
    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def load(self) -> RuleConfiguration:
        gate_path = self.config.rules_root / "gate_rules.yaml"
        exemption_path = self.config.rules_root / "exemptions.yaml"
        if not gate_path.is_file():
            raise ConfigurationError(f"gate rules do not exist: {gate_path}")
        try:
            gate_doc = yaml.safe_load(gate_path.read_text(encoding="utf-8")) or {}
            exemption_doc = yaml.safe_load(exemption_path.read_text(encoding="utf-8")) if exemption_path.is_file() else {}
        except yaml.YAMLError as error:
            raise ConfigurationError(f"invalid evaluator rule YAML: {error}") from error
        policies = tuple(
            RulePolicy(
                pattern=str(entry.get("pattern", "")),
                severity=Severity.from_text(str(entry["severity"])) if entry.get("severity") else None,
                gate=str(entry["gate"]) if entry.get("gate") else None,
            )
            for entry in gate_doc.get("rules", [])
            if entry.get("pattern")
        )
        exemptions: list[Exemption] = []
        for entry in (exemption_doc or {}).get("exemptions", []):
            try:
                exemptions.append(
                    Exemption(
                        rule_id=str(entry["rule_id"]),
                        func_id=str(entry["func_id"]),
                        reason=str(entry["reason"]),
                        owner=str(entry["owner"]),
                        expires=date.fromisoformat(str(entry["expires"])),
                    )
                )
            except (KeyError, ValueError) as error:
                raise ConfigurationError(f"invalid exemption entry: {entry}") from error
        return RuleConfiguration(
            version=str(gate_doc.get("version", self.config.rule_version)),
            defaults={str(key): str(value) for key, value in gate_doc.get("defaults", {}).items()},
            policies=policies,
            exemptions=tuple(exemptions),
        )

