"""Aggregate, freeze and compare Function evaluation baselines."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from spec_eval.models.finding import (
    FINDING_IDENTITY_VERSION,
    enrich_finding_identity,
    normalize_finding_message,
    normalize_finding_path,
)


BASELINE_SCHEMA_VERSION = 1


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

    def build_manifest(self, result_root: Path, site_report: Path | None = None) -> dict[str, Any]:
        """Build a compact identity manifest from one or more static results."""

        results = self._load_results(result_root)
        if not results:
            raise ValueError(f"no static-result.json found under {result_root}")
        metadata = self._result_metadata(results)
        site_value = self._load_site_report(site_report)
        complete = self._is_complete_site_report(site_value, metadata, len(results))

        compacted: dict[tuple[str, str, str], dict[str, Any]] = {}
        finding_count = 0
        identity_ids: set[str] = set()
        for func_id, result in sorted(results.items()):
            for raw in result.get("findings", []):
                finding_count += 1
                finding = enrich_finding_identity(raw, default_func_id=func_id)
                record = self._manifest_record(finding, func_id)
                identity_ids.add(record["finding_id"])
                key = (record["finding_id"], record["severity"], record["normalized_message"])
                if key in compacted:
                    compacted[key]["count"] += 1
                else:
                    compacted[key] = record

        return {
            "schema_version": BASELINE_SCHEMA_VERSION,
            "identity_version": FINDING_IDENTITY_VERSION,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_revision": metadata["source_revision"],
            "tool_version": metadata["tool_version"],
            "rule_version": metadata["rule_version"],
            "complete": complete,
            "scope": {
                "function_count": len(results),
                "func_ids": sorted(results),
            },
            "finding_count": finding_count,
            "unique_finding_count": len(identity_ids),
            "findings": sorted(
                compacted.values(),
                key=lambda item: (
                    item["func_id"],
                    item["finding_id"],
                    item["severity"],
                    item["normalized_message"],
                ),
            ),
        }

    @staticmethod
    def write_manifest(value: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def compare(self, current_root: Path, baseline_root: Path) -> dict[str, Any]:
        """Compare a current result/manifest against a complete frozen baseline."""

        current = self._load_manifest_or_results(current_root, require_complete=False)
        baseline = self._load_manifest_or_results(baseline_root, require_complete=True)
        self._validate_compatibility(current, baseline)

        current_scope = set(current.get("scope", {}).get("func_ids", []))
        current_groups = self._group_records(current.get("findings", []))
        baseline_groups = self._group_records(baseline.get("findings", []))
        current_records = self._record_index(current.get("findings", []))
        baseline_records = self._record_index(baseline.get("findings", []))
        functions: dict[str, Any] = {}
        summary = {"added": 0, "reclassified": 0, "resolved": 0, "unchanged": 0}

        # A current result directory may intentionally contain only changed
        # Functions. Baseline-only Functions outside that scope are not resolved.
        for func_id in sorted(current_scope):
            function_delta = self._compare_function(
                current_groups.get(func_id, {}),
                baseline_groups.get(func_id, {}),
            )
            self._attach_delta_metadata(
                function_delta,
                func_id,
                current_records,
                baseline_records,
            )
            functions[func_id] = function_delta
            summary["added"] += sum(item["count"] for item in function_delta["added"])
            summary["reclassified"] += sum(item["count"] for item in function_delta["reclassified"])
            summary["resolved"] += sum(item["count"] for item in function_delta["resolved"])
            summary["unchanged"] += function_delta["unchanged"]

        return {
            "schema_version": 1,
            "identity_version": FINDING_IDENTITY_VERSION,
            "baseline_revision": baseline.get("source_revision"),
            "current_revision": current.get("source_revision"),
            "rule_version": current.get("rule_version"),
            "scope": {"function_count": len(current_scope), "func_ids": sorted(current_scope)},
            "summary": summary,
            "functions": functions,
        }

    def _load_manifest_or_results(self, path: Path, *, require_complete: bool) -> dict[str, Any]:
        if path.is_file():
            value = json.loads(path.read_text(encoding="utf-8"))
            if "identity_version" not in value or "findings" not in value or "scope" not in value:
                raise ValueError(f"not a baseline manifest: {path}")
        elif path.is_dir():
            site_report = next(
                (
                    candidate
                    for candidate in (path / "site-report.json", path.parent / "site-report.json")
                    if candidate.is_file()
                ),
                None,
            )
            value = self.build_manifest(path, site_report)
        else:
            raise ValueError(f"baseline input does not exist: {path}")
        if require_complete and not value.get("complete"):
            raise ValueError("baseline is incomplete; freeze it from a complete site report before comparison")
        return value

    @staticmethod
    def _validate_compatibility(current: dict[str, Any], baseline: dict[str, Any]) -> None:
        if current.get("identity_version") != baseline.get("identity_version"):
            raise ValueError(
                "identity version mismatch: "
                f"current={current.get('identity_version')} baseline={baseline.get('identity_version')}"
            )
        if current.get("rule_version") != baseline.get("rule_version"):
            raise ValueError(
                "rule version mismatch: "
                f"current={current.get('rule_version')} baseline={baseline.get('rule_version')}"
            )

    @staticmethod
    def _compare_function(
        current: dict[str, Counter[tuple[str, str]]],
        baseline: dict[str, Counter[tuple[str, str]]],
    ) -> dict[str, Any]:
        added: list[dict[str, Any]] = []
        resolved: list[dict[str, Any]] = []
        reclassified: list[dict[str, Any]] = []
        unchanged = 0

        for finding_id in sorted(set(current) | set(baseline)):
            after = current.get(finding_id, Counter()).copy()
            before = baseline.get(finding_id, Counter()).copy()
            for classification in sorted(set(after) & set(before)):
                matched = min(after[classification], before[classification])
                unchanged += matched
                after[classification] -= matched
                before[classification] -= matched

            before_items = BaselineReporter._expanded_classifications(before)
            after_items = BaselineReporter._expanded_classifications(after)
            paired = min(len(before_items), len(after_items))
            paired_counts: Counter[tuple[tuple[str, str], tuple[str, str]]] = Counter(
                zip(before_items[:paired], after_items[:paired])
            )
            for (old, new), count in sorted(paired_counts.items()):
                reclassified.append(
                    {
                        "finding_id": finding_id,
                        "count": count,
                        "before": BaselineReporter._classification_record(old),
                        "after": BaselineReporter._classification_record(new),
                    }
                )
            added.extend(
                BaselineReporter._delta_records(finding_id, Counter(after_items[paired:]))
            )
            resolved.extend(
                BaselineReporter._delta_records(finding_id, Counter(before_items[paired:]))
            )

        return {
            "added": added,
            "reclassified": reclassified,
            "resolved": resolved,
            "unchanged": unchanged,
        }

    @staticmethod
    def _expanded_classifications(value: Counter[tuple[str, str]]) -> list[tuple[str, str]]:
        return [item for item in sorted(value) for _ in range(max(0, value[item]))]

    @staticmethod
    def _classification_record(value: tuple[str, str]) -> dict[str, str]:
        severity, message = value
        return {"severity": severity, "message": message}

    @staticmethod
    def _delta_records(
        finding_id: str,
        values: Counter[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "finding_id": finding_id,
                "count": count,
                **BaselineReporter._classification_record(classification),
            }
            for classification, count in sorted(values.items())
            if count > 0
        ]

    @staticmethod
    def _group_records(
        findings: Iterable[dict[str, Any]],
    ) -> dict[str, dict[str, Counter[tuple[str, str]]]]:
        grouped: dict[str, dict[str, Counter[tuple[str, str]]]] = defaultdict(
            lambda: defaultdict(Counter)
        )
        for finding in findings:
            func_id = str(finding.get("func_id", ""))
            finding_id = str(finding.get("finding_id", ""))
            classification = (
                str(finding.get("severity", "Info")),
                str(finding.get("normalized_message") or normalize_finding_message(finding.get("message"))),
            )
            grouped[func_id][finding_id][classification] += int(finding.get("count", 1))
        return grouped

    @staticmethod
    def _record_index(findings: Iterable[dict[str, Any]]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
        result: dict[tuple[str, str, str, str], dict[str, Any]] = {}
        for finding in findings:
            key = (
                str(finding.get("func_id", "")),
                str(finding.get("finding_id", "")),
                str(finding.get("severity", "Info")),
                str(finding.get("normalized_message") or normalize_finding_message(finding.get("message"))),
            )
            result[key] = finding
        return result

    @staticmethod
    def _attach_delta_metadata(
        delta: dict[str, Any],
        func_id: str,
        current: dict[tuple[str, str, str, str], dict[str, Any]],
        baseline: dict[tuple[str, str, str, str], dict[str, Any]],
    ) -> None:
        for name, index in (("added", current), ("resolved", baseline)):
            for item in delta[name]:
                key = (func_id, item["finding_id"], item["severity"], item["message"])
                item.update(BaselineReporter._record_summary(index.get(key, {})))
        for item in delta["reclassified"]:
            before = item["before"]
            after = item["after"]
            before_key = (func_id, item["finding_id"], before["severity"], before["message"])
            after_key = (func_id, item["finding_id"], after["severity"], after["message"])
            before.update(BaselineReporter._record_summary(baseline.get(before_key, {})))
            after.update(BaselineReporter._record_summary(current.get(after_key, {})))
            item.update(BaselineReporter._record_summary(current.get(after_key) or baseline.get(before_key, {})))

    @staticmethod
    def _record_summary(value: dict[str, Any]) -> dict[str, Any]:
        return {
            name: value[name]
            for name in ("rule_id", "path", "feat_id", "claim_id")
            if value.get(name) not in (None, "")
        }

    @staticmethod
    def _manifest_record(finding: dict[str, Any], func_id: str) -> dict[str, Any]:
        record = {
            "finding_id": str(finding["finding_id"]),
            "rule_id": str(finding.get("rule_id", "UNKNOWN")),
            "func_id": str(finding.get("func_id") or func_id),
            "path": normalize_finding_path(str(finding.get("path", ""))),
            "severity": str(finding.get("severity", "Info")),
            "normalized_message": normalize_finding_message(finding.get("message")),
            "count": 1,
        }
        for name in ("feat_id", "claim_id"):
            if finding.get(name) not in (None, ""):
                record[name] = finding[name]
        return record

    @staticmethod
    def _load_results(root: Path) -> dict[str, dict[str, Any]]:
        if root.is_file() and root.name == "static-result.json":
            paths = [root]
        elif root.is_dir():
            paths = sorted(root.rglob("static-result.json"))
        else:
            paths = []
        results: dict[str, dict[str, Any]] = {}
        for path in paths:
            value = json.loads(path.read_text(encoding="utf-8"))
            func_id = str(value.get("func_id", ""))
            if not func_id:
                continue
            if func_id in results:
                raise ValueError(f"duplicate static result for Function {func_id}")
            results[func_id] = value
        return results

    @staticmethod
    def _result_metadata(results: dict[str, dict[str, Any]]) -> dict[str, str]:
        metadata: dict[str, str] = {}
        for name in ("source_revision", "tool_version", "rule_version"):
            values = {str(value.get(name, "")) for value in results.values()}
            if len(values) != 1 or not next(iter(values)):
                raise ValueError(f"static results have inconsistent or missing {name}")
            metadata[name] = next(iter(values))
        return metadata

    @staticmethod
    def _load_site_report(path: Path | None) -> dict[str, Any] | None:
        if path is None:
            return None
        if not path.is_file():
            raise ValueError(f"site report does not exist: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _is_complete_site_report(
        site: dict[str, Any] | None,
        metadata: dict[str, str],
        result_count: int,
    ) -> bool:
        if not site:
            return False
        summary = site.get("summary", {})
        registered = int(summary.get("registeredFunctionCount", -1))
        completed = int(summary.get("completedFunctionCount", -1))
        errors = int(summary.get("errorCount", -1))
        return (
            str(site.get("sourceRevision", "")) == metadata["source_revision"]
            and str(site.get("ruleVersion", "")) == metadata["rule_version"]
            and registered == completed == result_count
            and errors == 0
        )
