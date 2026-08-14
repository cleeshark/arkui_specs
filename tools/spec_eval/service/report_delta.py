"""Finding and score differences between adjacent current Function reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_report_delta(
    previous_report: dict[str, Any] | None,
    current_report: dict[str, Any],
) -> dict[str, Any]:
    previous = _findings(previous_report or {})
    current = _findings(current_report)
    previous_ids = set(previous)
    current_ids = set(current)
    persistent_ids = previous_ids & current_ids
    reclassified = [
        finding_id for finding_id in sorted(persistent_ids)
        if _classification(previous[finding_id]) != _classification(current[finding_id])
    ]
    previous_summary = (previous_report or {}).get("summary", {})
    current_summary = current_report.get("summary", {})
    return {
        "schema_version": 1,
        "added": [current[item] for item in sorted(current_ids - previous_ids)],
        "resolved": [previous[item] for item in sorted(previous_ids - current_ids)],
        "persistent": [current[item] for item in sorted(persistent_ids)],
        "reclassified": [
            {"finding_id": item, "before": previous[item], "after": current[item]}
            for item in reclassified
        ],
        "summary": {
            "added": len(current_ids - previous_ids),
            "resolved": len(previous_ids - current_ids),
            "persistent": len(persistent_ids),
            "reclassified": len(reclassified),
            "published_score_delta": _number_delta(
                previous_summary.get("published_score"), current_summary.get("published_score")
            ),
            "raw_score_delta": _number_delta(
                previous_summary.get("raw_score"), current_summary.get("raw_score")
            ),
            "gate_before": previous_summary.get("gate"),
            "gate_after": current_summary.get("gate"),
            "confidence_before": previous_summary.get("confidence"),
            "confidence_after": current_summary.get("confidence"),
        },
    }


def load_archived_report(archive_path: str) -> dict[str, Any] | None:
    path = Path(archive_path) / "aggregate-report_json-evaluation-report.json"
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _findings(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            finding_id = value.get("finding_id")
            if isinstance(finding_id, str) and finding_id:
                found[finding_id] = value
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(document)
    return found


def _classification(finding: dict[str, Any]) -> tuple[Any, Any]:
    return finding.get("severity"), finding.get("message") or finding.get("reason")


def _number_delta(before: Any, after: Any) -> float | int | None:
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return None
    return after - before
