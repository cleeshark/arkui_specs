"""Build the static-site snapshot for a full Function evaluation scan."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GATES = ("pass", "warn", "fail", "error")
SEVERITIES = ("Critical", "Major", "Minor", "Info")


class SiteReporter:
    """Convert full scan results into a compact, site-ready JSON document."""

    def build(
        self,
        scan_results: list[dict[str, Any]],
        *,
        source_revision: str,
        tool_version: str,
        rule_version: str,
        generated_at: str | None = None,
        report_only: bool = False,
        performance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        functions = [self._function(item) for item in sorted(scan_results, key=lambda value: value["func_id"])]
        gate_counts = Counter(item["gate"] for item in functions)
        severity_counts: Counter[str] = Counter()
        rule_counts: Counter[str] = Counter()
        for item in functions:
            severity_counts.update(item["severityCounts"])
            rule_counts.update(item["ruleCounts"])

        claim_count = sum(item["evidence"]["claimCount"] for item in functions)
        resolved_claim_count = sum(item["evidence"]["resolvedClaimCount"] for item in functions)
        result = {
            "schemaVersion": 1,
            "available": True,
            "mode": "report-only" if report_only else "enforce",
            "generatedAt": generated_at or datetime.now(timezone.utc).isoformat(),
            "sourceRevision": source_revision,
            "toolVersion": tool_version,
            "ruleVersion": rule_version,
            "summary": {
                "registeredFunctionCount": len(functions),
                "completedFunctionCount": sum(1 for item in functions if item["gate"] != "error"),
                "errorCount": gate_counts["error"],
                "gateCounts": {gate: gate_counts[gate] for gate in GATES},
                "findingCount": sum(item["findingCount"] for item in functions),
                "severityCounts": {severity: severity_counts[severity] for severity in SEVERITIES},
                "ruleCounts": dict(sorted(rule_counts.items())),
                "featureCount": sum(item["featureCount"] for item in functions),
                "documentCount": sum(item["documentCount"] for item in functions),
                "claimCount": claim_count,
                "resolvedClaimCount": resolved_claim_count,
                "evidenceCoverage": resolved_claim_count / claim_count if claim_count else 0.0,
            },
            "functions": functions,
        }
        if performance:
            result["performance"] = {
                key: value for key, value in performance.items() if key != "functions"
            }
        return result

    def write(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_compact(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def write_archive(self, output_root: Path, source_revision: str, value: dict[str, Any]) -> Path:
        report_path = output_root / "site-report.json"
        self.write_compact(report_path, value)
        self.write(
            output_root / "latest.json",
            {
                "schemaVersion": 1,
                "sourceRevision": source_revision,
                "generatedAt": value.get("generatedAt"),
                "siteReport": "site-report.json",
            },
        )
        return report_path

    def _function(self, item: dict[str, Any]) -> dict[str, Any]:
        context = item.get("context", {})
        result = item.get("result")
        function_entry = context.get("function_registry_entry", {})
        feature_entries = context.get("feature_registry_entries", [])
        base = {
            "funcId": item["func_id"],
            "title": str(function_entry.get("l3", {}).get("title", "")),
            "l1": self._level(function_entry.get("l1")),
            "l2": self._level(function_entry.get("l2")),
            "path": str(function_entry.get("path", "")),
            "docs": self._docs(function_entry, feature_entries),
        }
        if result is None:
            return {
                **base,
                "gate": "error",
                "error": str(item.get("error", "evaluation failed")),
                "featureCount": len(feature_entries),
                "documentCount": 0,
                "findingCount": 0,
                "severityCounts": {severity: 0 for severity in SEVERITIES},
                "ruleCounts": {},
                "evidence": {"claimCount": 0, "resolvedClaimCount": 0, "coverage": 0.0},
                "findings": [],
            }

        static = result.get("static", {})
        metrics = static.get("metrics", {})
        evidence_metrics = result.get("evidence", {}).get("metrics", {})
        findings = static.get("findings", [])
        severity_counts = Counter(str(finding.get("severity", "Info")) for finding in findings)
        rule_counts = Counter(str(finding.get("rule_id", "UNKNOWN")) for finding in findings)
        return {
            **base,
            "gate": str(static.get("gate", "error")),
            "featureCount": int(metrics.get("feature_count", len(feature_entries)) or 0),
            "documentCount": int(metrics.get("document_count", 0) or 0),
            "findingCount": len(findings),
            "severityCounts": {severity: severity_counts[severity] for severity in SEVERITIES},
            "ruleCounts": dict(sorted(rule_counts.items())),
            "evidence": {
                "claimCount": int(evidence_metrics.get("claim_count", 0) or 0),
                "resolvedClaimCount": int(evidence_metrics.get("resolved_claim_count", 0) or 0),
                "coverage": float(evidence_metrics.get("evidence_coverage", 0.0) or 0.0),
            },
            "findings": [self._finding(finding) for finding in findings],
        }

    @staticmethod
    def _level(value: Any) -> dict[str, str]:
        value = value if isinstance(value, dict) else {}
        return {"id": str(value.get("id", "")), "title": str(value.get("title", ""))}

    @staticmethod
    def _finding(value: dict[str, Any]) -> dict[str, Any]:
        site_fields = ("rule_id", "severity", "message", "path", "line", "feat_id", "recommendation")
        return {key: value[key] for key in site_fields if value.get(key) not in (None, "")}

    @staticmethod
    def _docs(function_entry: dict[str, Any], feature_entries: list[dict[str, Any]]) -> list[dict[str, str]]:
        documents: list[dict[str, str]] = []
        design = function_entry.get("design")
        if design:
            documents.append({"label": "Design", "docId": str(Path(str(design)).with_suffix(""))})
        for feature in feature_entries:
            spec = feature.get("spec")
            if spec:
                label = f"{feature.get('id', '')} {feature.get('title', '')}".strip()
                documents.append({"label": label, "docId": str(Path(str(spec)).with_suffix(""))})
        return documents
