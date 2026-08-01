"""Evaluation result aggregation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from spec_eval.models.evidence import EvidenceBundle
from spec_eval.models.finding import Finding
from spec_eval.models.function import FunctionContext
from spec_eval.models.traceability import TraceGraph


@dataclass
class StaticResult:
    func_id: str
    source_revision: str
    tool_version: str
    rule_version: str
    gate: str
    findings: list[Finding]
    metrics: dict[str, Any] = field(default_factory=dict)
    traceability: TraceGraph | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "func_id": self.func_id,
            "source_revision": self.source_revision,
            "tool_version": self.tool_version,
            "rule_version": self.rule_version,
            "gate": self.gate,
            "findings": [finding.to_dict() for finding in self.findings],
            "metrics": self.metrics,
        }
        if self.traceability is not None:
            result["traceability"] = self.traceability.to_dict()
        return result


@dataclass
class EvaluationRun:
    context: FunctionContext
    static_result: StaticResult
    evidence: EvidenceBundle

    def to_dict(self, repo_root=None) -> dict[str, Any]:
        return {
            "context": self.context.to_dict(repo_root),
            "static": self.static_result.to_dict(),
            "evidence": self.evidence.to_dict(),
        }

