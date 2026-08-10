"""Aggregate deterministic findings into a Function-level gate."""

from __future__ import annotations

from dataclasses import dataclass, replace

from spec_eval.models.finding import Finding, Severity
from spec_eval.rules.rule_loader import RuleConfiguration
from spec_eval.rules.severity import default_gate, max_gate


@dataclass
class GateResult:
    gate: str
    findings: list[Finding]
    counts: dict[str, int]
    exempted_count: int = 0


class GateEngine:
    def __init__(self, configuration: RuleConfiguration) -> None:
        self.configuration = configuration

    def evaluate(self, func_id: str, findings: list[Finding]) -> GateResult:
        gate = "pass"
        normalized: list[Finding] = []
        counts = {severity.label(): 0 for severity in Severity}
        exempted = 0
        for finding in findings:
            policy = self.configuration.policy_for(finding.rule_id)
            severity = policy.severity if policy and policy.severity is not None else finding.severity
            normalized_finding = replace(finding, severity=severity)
            normalized.append(normalized_finding)
            counts[severity.label()] += 1
            if self.configuration.exemption_for(func_id, finding.rule_id):
                exempted += 1
                continue
            finding_gate = policy.gate if policy and policy.gate else self.configuration.defaults.get(severity.label(), default_gate(severity))
            gate = max_gate(gate, finding_gate)
        return GateResult(gate, normalized, counts, exempted)

