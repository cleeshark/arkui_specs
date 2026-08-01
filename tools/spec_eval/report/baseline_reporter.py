"""Aggregate and compare Function result directories."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class BaselineReporter:
    def aggregate(self, result_paths: list[Path]) -> dict[str, Any]:
        functions = []
        gate_counts: Counter[str] = Counter()
        rule_counts: Counter[str] = Counter()
        for path in sorted(result_paths):
            value = json.loads(path.read_text(encoding="utf-8"))
            gate_counts[value.get("gate", "error")] += 1
            for finding in value.get("findings", []):
                rule_counts[finding.get("rule_id", "UNKNOWN")] += 1
            functions.append(
                {
                    "func_id": value.get("func_id"),
                    "gate": value.get("gate"),
                    "finding_count": len(value.get("findings", [])),
                }
            )
        return {
            "function_count": len(functions),
            "gate_counts": dict(sorted(gate_counts.items())),
            "rule_counts": dict(sorted(rule_counts.items())),
            "functions": functions,
        }

    def compare(self, current_root: Path, baseline_root: Path) -> dict[str, Any]:
        current = self._load_by_func(current_root)
        baseline = self._load_by_func(baseline_root)
        result: dict[str, Any] = {"functions": {}}
        for func_id in sorted(set(current) | set(baseline)):
            current_findings = self._finding_keys(current.get(func_id, {}))
            baseline_findings = self._finding_keys(baseline.get(func_id, {}))
            result["functions"][func_id] = {
                "added": sorted(current_findings - baseline_findings),
                "resolved": sorted(baseline_findings - current_findings),
                "unchanged": len(current_findings & baseline_findings),
            }
        return result

    @staticmethod
    def _load_by_func(root: Path) -> dict[str, dict[str, Any]]:
        result = {}
        for path in root.rglob("static-result.json") if root.is_dir() else []:
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("func_id"):
                result[str(value["func_id"])] = value
        return result

    @staticmethod
    def _finding_keys(value: dict[str, Any]) -> set[str]:
        return {
            f"{item.get('rule_id')}|{item.get('path')}|{item.get('line', '')}|{item.get('message')}"
            for item in value.get("findings", [])
        }

