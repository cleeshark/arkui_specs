"""Build compact site evaluation history and deterministic Finding deltas."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

from spec_eval.protocol_validator import JsonSchemaSubsetValidator


SITE_HISTORY_SCHEMA_VERSION = 1
SITE_HISTORY_VERSION = "spec-eval-site-history@0.1.0"
MAX_SNAPSHOTS = 52
MAX_DELTA_DETAILS = 40
DIMENSIONS = (
    "correctness",
    "spec_executability",
    "design_quality",
    "compatibility_system_impact",
    "function_modeling",
)
SEVERITIES = ("Critical", "Major", "Minor", "Info")
SEVERITY_RANK = {value: len(SEVERITIES) - index for index, value in enumerate(SEVERITIES)}


class SiteEvaluationHistoryInputError(ValueError):
    """Raised when a site history cannot be safely generated."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SiteEvaluationHistoryInputError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SiteEvaluationHistoryInputError(f"JSON input must be an object: {path}")
    return value


def _round_average(values: Iterable[Any]) -> float:
    decimals = [Decimal(str(value)) for value in values if isinstance(value, (int, float))]
    if not decimals:
        return 0.0
    result = (sum(decimals) / Decimal(len(decimals))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(result)


def _fingerprint(report: dict[str, Any]) -> str:
    canonical = json.dumps(report.get("functions", []), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _confirmed_functions(report: dict[str, Any]) -> list[dict[str, Any]]:
    functions = report.get("functions", [])
    if not isinstance(functions, list):
        raise SiteEvaluationHistoryInputError("site evaluation functions must be a list")
    return sorted(
        (item for item in functions if isinstance(item, dict) and item.get("status") == "CONFIRMED"),
        key=lambda item: str(item.get("func_id", "")),
    )


def _active_findings(functions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compacted: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for function in functions:
        func_id = str(function.get("func_id", ""))
        title = str(function.get("title", ""))
        for finding in function.get("findings", []):
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("finding_id", ""))
            source = str(finding.get("source", ""))
            if not finding_id or source not in ("static", "semantic"):
                continue
            severity = str(finding.get("severity", "Info"))
            message = str(finding.get("message", ""))
            identity_key = f"{source}:{func_id}:{finding_id}"
            classification_key = (identity_key, severity, message, str(finding.get("path", "")), str(finding.get("feat_id", "")))
            if classification_key in compacted:
                compacted[classification_key]["count"] += 1
                continue
            record = {
                "identityKey": identity_key,
                "findingId": finding_id,
                "source": source,
                "funcId": func_id,
                "title": title,
                "severity": severity,
                "message": message,
                "count": 1,
            }
            for source_name, target_name in (
                ("rule_id", "ruleId"),
                ("criterion_id", "criterionId"),
                ("path", "path"),
                ("feat_id", "featId"),
            ):
                if finding.get(source_name) not in (None, ""):
                    record[target_name] = finding[source_name]
            compacted[classification_key] = record
    return sorted(
        compacted.values(),
        key=lambda item: (
            item["funcId"], item["source"], item["findingId"], item["severity"], item["message"]
        ),
    )


def _now_iso() -> str:
    """Current UTC time as an ISO-8601 string (indirection eases test control)."""
    return datetime.now(timezone.utc).isoformat()


def _day_of(timestamp: str | None) -> str | None:
    """Extract the calendar day (YYYY-MM-DD) from an ISO-8601 timestamp."""
    if not isinstance(timestamp, str) or not timestamp:
        return None
    try:
        text = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(text).astimezone(timezone.utc).date().isoformat()
    except ValueError:
        # Best-effort fallback: an ISO string always starts with YYYY-MM-DD.
        return timestamp[:10] if len(timestamp) >= 10 else None


def _snapshot(
    report: dict[str, Any],
    functions: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    *,
    snapshot_at: str,
) -> dict[str, Any]:
    severity_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    gate_counts: Counter[str] = Counter()
    admission_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    criterion_counts: Counter[str] = Counter()
    dimension_values: dict[str, list[Any]] = defaultdict(list)
    published_scores: list[Any] = []
    confidences: list[Any] = []
    confirmed_at: list[str] = []
    function_summaries: list[dict[str, Any]] = []

    findings_by_function: Counter[str] = Counter()
    for finding in findings:
        count = int(finding.get("count", 1))
        severity_counts[str(finding.get("severity", "Info"))] += count
        source_counts[str(finding.get("source", "unknown"))] += count
        findings_by_function[str(finding.get("funcId", ""))] += count
        if finding.get("ruleId"):
            rule_counts[str(finding["ruleId"])] += count
        if finding.get("criterionId"):
            criterion_counts[str(finding["criterionId"])] += count

    for function in functions:
        func_id = str(function.get("func_id", ""))
        scores = function.get("scores", {}) if isinstance(function.get("scores"), dict) else {}
        dimensions = scores.get("dimensions", {}) if isinstance(scores.get("dimensions"), dict) else {}
        for dimension in DIMENSIONS:
            dimension_values[dimension].append(dimensions.get(dimension))
        published_scores.append(scores.get("published_score"))
        confidences.append(scores.get("confidence"))
        admission_counts[str(scores.get("admission", "UNKNOWN"))] += 1
        static_reference = function.get("static_report_reference", {})
        gate = static_reference.get("gate", "error") if isinstance(static_reference, dict) else "error"
        gate_counts[str(gate)] += 1
        confirmation = function.get("confirmation", {})
        if isinstance(confirmation, dict) and isinstance(confirmation.get("confirmed_at"), str):
            confirmed_at.append(confirmation["confirmed_at"])
        function_summaries.append({
            "funcId": func_id,
            "title": str(function.get("title", "")),
            "findingCount": findings_by_function[func_id],
            "publishedScore": scores.get("published_score"),
            "confidence": scores.get("confidence"),
            "admission": scores.get("admission", "UNKNOWN"),
            "gate": gate,
        })

    top_functions = sorted(
        function_summaries,
        key=lambda item: (-item["findingCount"], str(item["funcId"])),
    )[:10]
    return {
        "sourceRevision": report["sourceRevision"],
        "snapshotAt": snapshot_at,
        "snapshotDay": _day_of(snapshot_at),
        "fingerprint": _fingerprint(report),
        "confirmedAt": max(confirmed_at) if confirmed_at else None,
        "functionCount": len(functions),
        "findingCount": sum(int(item.get("count", 1)) for item in findings),
        "severityCounts": {key: severity_counts[key] for key in SEVERITIES},
        "sourceCounts": dict(sorted(source_counts.items())),
        "gateCounts": dict(sorted(gate_counts.items())),
        "admissionCounts": dict(sorted(admission_counts.items())),
        "publishedScoreAverage": _round_average(published_scores),
        "confidenceAverage": _round_average(confidences),
        "dimensionAverages": {key: _round_average(dimension_values[key]) for key in DIMENSIONS},
        "topRules": [
            {"ruleId": rule_id, "count": count}
            for rule_id, count in sorted(rule_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
        "topCriteria": [
            {"criterionId": criterion_id, "count": count}
            for criterion_id, count in sorted(criterion_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
        "topFunctions": top_functions,
    }


def _group_findings(findings: list[dict[str, Any]]) -> dict[str, Counter[tuple[str, str]]]:
    grouped: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    for finding in findings:
        grouped[str(finding["identityKey"])][(
            str(finding.get("severity", "Info")), str(finding.get("message", ""))
        )] += int(finding.get("count", 1))
    return grouped


def _record_index(findings: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (str(item["identityKey"]), str(item.get("severity", "Info")), str(item.get("message", ""))): item
        for item in findings
    }


def _detail(record: dict[str, Any], count: int, *, before: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {
        key: record[key]
        for key in ("findingId", "source", "funcId", "title", "severity", "message", "ruleId", "criterionId", "path", "featId")
        if record.get(key) not in (None, "")
    }
    result["count"] = count
    if before is not None:
        result["beforeSeverity"] = before.get("severity", "Info")
        result["beforeMessage"] = before.get("message", "")
    return result


def _delta(current: list[dict[str, Any]], previous: list[dict[str, Any]]) -> dict[str, Any]:
    current_groups = _group_findings(current)
    previous_groups = _group_findings(previous)
    current_index = _record_index(current)
    previous_index = _record_index(previous)
    added: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    reclassified: list[dict[str, Any]] = []
    persistent = 0

    for identity_key in sorted(set(current_groups) | set(previous_groups)):
        after = current_groups.get(identity_key, Counter()).copy()
        before = previous_groups.get(identity_key, Counter()).copy()
        for classification in sorted(set(after) & set(before)):
            matched = min(after[classification], before[classification])
            persistent += matched
            after[classification] -= matched
            before[classification] -= matched
        before_items = [item for item in sorted(before) for _ in range(max(0, before[item]))]
        after_items = [item for item in sorted(after) for _ in range(max(0, after[item]))]
        paired = min(len(before_items), len(after_items))
        for old, new in zip(before_items[:paired], after_items[:paired]):
            old_record = previous_index[(identity_key, old[0], old[1])]
            new_record = current_index[(identity_key, new[0], new[1])]
            reclassified.append(_detail(new_record, 1, before=old_record))
        for classification in after_items[paired:]:
            added.append(_detail(current_index[(identity_key, classification[0], classification[1])], 1))
        for classification in before_items[paired:]:
            resolved.append(_detail(previous_index[(identity_key, classification[0], classification[1])], 1))

    def compact(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        for item in items:
            key = json.dumps({name: value for name, value in item.items() if name != "count"}, ensure_ascii=False, sort_keys=True)
            if key in grouped:
                grouped[key]["count"] += item["count"]
            else:
                grouped[key] = dict(item)
        return sorted(
            grouped.values(),
            key=lambda item: (-SEVERITY_RANK.get(str(item.get("severity", "Info")), 0), str(item.get("funcId", "")), str(item.get("findingId", ""))),
        )

    added = compact(added)
    resolved = compact(resolved)
    reclassified = compact(reclassified)
    function_counts: dict[str, Counter[str]] = defaultdict(Counter)
    title_by_func: dict[str, str] = {}
    for name, items in (("added", added), ("resolved", resolved), ("reclassified", reclassified)):
        for item in items:
            function_counts[str(item.get("funcId", ""))][name] += int(item.get("count", 1))
            title_by_func[str(item.get("funcId", ""))] = str(item.get("title", ""))
    return {
        "summary": {
            "added": sum(int(item.get("count", 1)) for item in added),
            "resolved": sum(int(item.get("count", 1)) for item in resolved),
            "persistent": persistent,
            "reclassified": sum(int(item.get("count", 1)) for item in reclassified),
        },
        "functions": [
            {
                "funcId": func_id,
                "title": title_by_func.get(func_id, ""),
                "added": function_counts[func_id]["added"],
                "resolved": function_counts[func_id]["resolved"],
                "reclassified": function_counts[func_id]["reclassified"],
            }
            for func_id in sorted(
                function_counts,
                key=lambda value: (-sum(function_counts[value].values()), value),
            )
        ],
        "topAdded": added[:MAX_DELTA_DETAILS],
        "topResolved": resolved[:MAX_DELTA_DETAILS],
        "topReclassified": reclassified[:MAX_DELTA_DETAILS],
    }


def build_site_evaluation_history(
    *,
    current_report: dict[str, Any],
    previous_history: dict[str, Any] | None = None,
    snapshot_at: str | None = None,
) -> dict[str, Any]:
    revision = current_report.get("sourceRevision")
    if not isinstance(revision, str) or not revision:
        raise SiteEvaluationHistoryInputError("site evaluation sourceRevision must be non-empty")
    snapshot_at = snapshot_at or _now_iso()
    snapshot_day = _day_of(snapshot_at)
    functions = _confirmed_functions(current_report)
    active_findings = _active_findings(functions)
    snapshot = _snapshot(current_report, functions, active_findings, snapshot_at=snapshot_at)

    # Idempotent within a calendar day: if the most recent snapshot is for the
    # same day and the report content is unchanged (same fingerprint), leave the
    # history untouched so repeated same-day refreshes do not churn the file.
    if previous_history:
        previous_snapshots = [
            item for item in previous_history.get("snapshots", []) if isinstance(item, dict)
        ]
        last = previous_snapshots[-1] if previous_snapshots else None
        if (
            isinstance(last, dict)
            and last.get("snapshotDay") == snapshot_day
            and last.get("fingerprint") == snapshot["fingerprint"]
        ):
            return previous_history

    previous_findings = []
    baseline_revision = None
    snapshots: list[dict[str, Any]] = []
    if previous_history:
        baseline_revision = previous_history.get("currentRevision")
        previous_findings = [
            item for item in previous_history.get("activeFindings", []) if isinstance(item, dict)
        ]
        snapshots = [item for item in previous_history.get("snapshots", []) if isinstance(item, dict)]

    recent_delta = _delta(active_findings, previous_findings) if previous_history else {
        "summary": {"added": 0, "resolved": 0, "persistent": 0, "reclassified": 0},
        "functions": [], "topAdded": [], "topResolved": [], "topReclassified": [],
    }
    # Accumulate by calendar day: one point per day. A same-day rebuild replaces
    # that day's point (latest wins); a new day appends a fresh point even when
    # the revision has not moved, so a frozen revision reads as a continuous line
    # rather than collapsing to a single dot.
    snapshots = [item for item in snapshots if item.get("snapshotDay") != snapshot_day]
    snapshots.append(snapshot)
    snapshots = snapshots[-MAX_SNAPSHOTS:]
    comparison_status = "INITIAL" if not previous_history else (
        "REVIEW_UPDATED" if baseline_revision == revision else "REVISION_CHANGED"
    )
    return {
        "schemaVersion": SITE_HISTORY_SCHEMA_VERSION,
        "reportVersion": SITE_HISTORY_VERSION,
        "available": True,
        "currentRevision": revision,
        "summary": {
            "snapshotCount": len(snapshots),
            "comparisonStatus": comparison_status,
            "baselineRevision": baseline_revision,
            "currentFindingCount": snapshot["findingCount"],
            "addedFindingCount": recent_delta["summary"]["added"],
            "resolvedFindingCount": recent_delta["summary"]["resolved"],
            "persistentFindingCount": recent_delta["summary"]["persistent"],
            "reclassifiedFindingCount": recent_delta["summary"]["reclassified"],
        },
        "snapshots": snapshots,
        "recentDelta": recent_delta,
        "activeFindings": active_findings,
    }


def validate_site_evaluation_history(instance: dict[str, Any], schemas_root: Path) -> list[str]:
    return JsonSchemaSubsetValidator(schemas_root).validate_file(
        instance, schemas_root / "site-evaluation-history.schema.json"
    )


def build_site_evaluation_history_from_paths(
    *, current_report_path: Path, schemas_root: Path, previous_history_path: Path | None = None
) -> dict[str, Any]:
    current_report = _load_json(current_report_path)
    previous_history = None
    if previous_history_path is not None and previous_history_path.is_file():
        previous_history = _load_json(previous_history_path)
    result = build_site_evaluation_history(current_report=current_report, previous_history=previous_history)
    errors = validate_site_evaluation_history(result, schemas_root)
    if errors:
        raise SiteEvaluationHistoryInputError("generated site history is invalid:\n" + "\n".join(errors))
    return result


def write_site_evaluation_history(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
