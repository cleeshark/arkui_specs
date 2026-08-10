"""Evaluate Function-level baseline deltas without blocking on historical debt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from spec_eval.models.finding import Severity
from spec_eval.rules.rule_loader import RuleConfiguration
from spec_eval.rules.severity import default_gate, max_gate


SEVERITY_LABELS = ("Critical", "Major", "Minor", "Info")


@dataclass(frozen=True)
class DeltaGateResult:
    gate: str
    baseline_status: str
    added_counts: dict[str, int]
    resolved_count: int
    reclassified_count: int
    unchanged_count: int
    exempted_added_count: int
    reason_codes: tuple[str, ...]
    reasons: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "baseline_status": self.baseline_status,
            "added_counts": self.added_counts,
            "resolved_count": self.resolved_count,
            "reclassified_count": self.reclassified_count,
            "unchanged_count": self.unchanged_count,
            "exempted_added_count": self.exempted_added_count,
            "reason_codes": list(self.reason_codes),
            "reasons": list(self.reasons),
        }


class DeltaGateEngine:
    """Apply the no-regression policy to one Function delta."""

    def __init__(self, configuration: RuleConfiguration) -> None:
        self.configuration = configuration

    def evaluate(self, func_id: str, absolute_gate: str, delta: dict[str, Any]) -> DeltaGateResult:
        baseline_status = str(delta.get("baseline_status", "existing"))
        added_counts = {label: 0 for label in SEVERITY_LABELS}
        resolved_count = self._count(delta.get("resolved", []))
        reclassified_count = self._count(delta.get("reclassified", []))
        unchanged_count = int(delta.get("unchanged", 0) or 0)

        if baseline_status == "new":
            exempted_added = 0
            for finding in delta.get("added", []):
                count = int(finding.get("count", 1) or 1)
                rule_id = str(finding.get("rule_id", "UNKNOWN"))
                if self.configuration.exemption_for(func_id, rule_id):
                    exempted_added += count
                    continue
                severity = self._effective_severity(rule_id, str(finding.get("severity", "Info")))
                added_counts[severity.label()] += count
            code = None
            if absolute_gate == "fail":
                code = "NEW_FUNCTION_ABSOLUTE_GATE_FAILED"
            elif absolute_gate == "warn":
                code = "NEW_FUNCTION_ABSOLUTE_GATE_WARN"
            reasons = (
                ({"code": code, "func_id": func_id, "count": 1, "gate": absolute_gate},)
                if code is not None
                else ()
            )
            return DeltaGateResult(
                gate=absolute_gate,
                baseline_status=baseline_status,
                added_counts=added_counts,
                resolved_count=resolved_count,
                reclassified_count=reclassified_count,
                unchanged_count=unchanged_count,
                exempted_added_count=exempted_added,
                reason_codes=(code,) if code is not None else (),
                reasons=reasons,
            )

        gate = "pass"
        reasons: list[dict[str, Any]] = []
        exempted_added = 0
        for finding in delta.get("added", []):
            count = int(finding.get("count", 1) or 1)
            rule_id = str(finding.get("rule_id", "UNKNOWN"))
            if self.configuration.exemption_for(func_id, rule_id):
                exempted_added += count
                continue
            severity = self._effective_severity(rule_id, str(finding.get("severity", "Info")))
            added_counts[severity.label()] += count
            finding_gate = self._finding_gate(rule_id, severity)
            gate = max_gate(gate, finding_gate)
            if finding_gate != "pass":
                reasons.append(
                    self._reason(
                        f"DELTA_{severity.name}_ADDED",
                        func_id,
                        finding,
                        severity.label(),
                        count,
                        finding_gate,
                    )
                )

        for finding in delta.get("reclassified", []):
            count = int(finding.get("count", 1) or 1)
            rule_id = str(finding.get("rule_id", "UNKNOWN"))
            if self.configuration.exemption_for(func_id, rule_id):
                continue
            before = finding.get("before", {})
            after = finding.get("after", {})
            before_severity = self._effective_severity(rule_id, str(before.get("severity", "Info")))
            after_severity = self._effective_severity(rule_id, str(after.get("severity", "Info")))
            if after_severity > before_severity:
                finding_gate = self._finding_gate(rule_id, after_severity)
                gate = max_gate(gate, finding_gate)
                reasons.append(
                    self._reason(
                        "DELTA_SEVERITY_INCREASED",
                        func_id,
                        finding,
                        after_severity.label(),
                        count,
                        finding_gate,
                    )
                )
            elif after_severity == before_severity and after.get("message") != before.get("message"):
                gate = max_gate(gate, "warn")
                reasons.append(
                    self._reason(
                        "DELTA_MESSAGE_RECLASSIFIED",
                        func_id,
                        finding,
                        after_severity.label(),
                        count,
                        "warn",
                    )
                )

        reason_codes = tuple(dict.fromkeys(str(item["code"]) for item in reasons))
        return DeltaGateResult(
            gate=gate,
            baseline_status=baseline_status,
            added_counts=added_counts,
            resolved_count=resolved_count,
            reclassified_count=reclassified_count,
            unchanged_count=unchanged_count,
            exempted_added_count=exempted_added,
            reason_codes=reason_codes,
            reasons=tuple(reasons),
        )

    def _effective_severity(self, rule_id: str, value: str) -> Severity:
        policy = self.configuration.policy_for(rule_id)
        return policy.severity if policy and policy.severity is not None else Severity.from_text(value)

    def _finding_gate(self, rule_id: str, severity: Severity) -> str:
        policy = self.configuration.policy_for(rule_id)
        if policy and policy.gate:
            return policy.gate
        return self.configuration.defaults.get(severity.label(), default_gate(severity))

    @staticmethod
    def _count(values: list[dict[str, Any]]) -> int:
        return sum(int(item.get("count", 1) or 1) for item in values)

    @staticmethod
    def _reason(
        code: str,
        func_id: str,
        finding: dict[str, Any],
        severity: str,
        count: int,
        gate: str,
    ) -> dict[str, Any]:
        result = {
            "code": code,
            "func_id": func_id,
            "finding_id": str(finding.get("finding_id", "")),
            "rule_id": str(finding.get("rule_id", "UNKNOWN")),
            "severity": severity,
            "count": count,
            "gate": gate,
        }
        if finding.get("path"):
            result["path"] = str(finding["path"])
        return result
