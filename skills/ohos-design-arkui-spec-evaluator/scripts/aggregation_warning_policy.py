"""Shared non-blocking aggregation warning policy for assemble/final stages."""

from __future__ import annotations

import json
from pathlib import Path


# These are bounded semantic-quality warnings rather than structural damage.
# The report remains consumable because Criterion findings, evidence, and the
# final schema are intact. Keep all other aggregation validation errors
# blocking.
OWNERSHIP_WARNING_MARKERS = (
    "one defect may produce at most one Critical Finding",
    "a Critical Finding must belong to the primary Criterion",
    "expected one of observation owners",
)
OWNERSHIP_WARNING_CODE = "OWNERSHIP_CRITICALITY"
OWNERSHIP_WARNING_DEDUCTION = 20
MAPPING_WARNING_MARKER = ".claim_ids: not mapped to Criterion:"
MAPPING_WARNING_CODE = "MAPPING_CLAIM_UNMAPPED"
MAPPING_WARNING_DEDUCTION = 5


def split_aggregation_warnings(errors: list[str]) -> tuple[list[str], list[str]]:
    """Return ``(blocking_errors, downgraded_warnings)`` for report policy."""
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        if (
            any(marker in error for marker in OWNERSHIP_WARNING_MARKERS)
            or MAPPING_WARNING_MARKER in error
        ):
            warnings.append(error)
        else:
            blocking.append(error)
    return blocking, warnings


def record_aggregation_warnings(run_dir: Path, warnings: list[str]) -> None:
    """Idempotently apply confidence deductions for downgraded warnings."""
    ownership_warnings = [
        warning for warning in warnings
        if any(marker in warning for marker in OWNERSHIP_WARNING_MARKERS)
    ]
    mapping_warnings = [
        warning for warning in warnings
        if MAPPING_WARNING_MARKER in warning
    ]
    record_ownership_warning(run_dir, ownership_warnings)
    record_mapping_warning(run_dir, mapping_warnings)


def record_ownership_warning(run_dir: Path, warnings: list[str]) -> None:
    """Apply one bounded confidence deduction for ownership-quality warnings."""
    _record_confidence_warning(
        run_dir, warnings,
        code=OWNERSHIP_WARNING_CODE,
        layer="MAJOR",
        deduction=OWNERSHIP_WARNING_DEDUCTION,
        message=(
            "defect ownership contains non-structural cross-Criterion "
            "inconsistencies"
        ),
        warning_path="aggregation.defect_ownership",
    )


def record_mapping_warning(run_dir: Path, warnings: list[str]) -> None:
    """Apply one bounded deduction for post-Correction unmapped Claims."""
    _record_confidence_warning(
        run_dir, warnings,
        code=MAPPING_WARNING_CODE,
        layer="MINOR",
        deduction=MAPPING_WARNING_DEDUCTION,
        message="aggregation retains Claim IDs outside the Criterion mapping",
        warning_path="aggregation.criterion_results[].claim_ids",
    )


def _record_confidence_warning(
    run_dir: Path,
    warnings: list[str],
    *,
    code: str,
    layer: str,
    deduction: int,
    message: str,
    warning_path: str,
) -> None:
    """Idempotently add one confidence warning entry."""
    if not warnings:
        return
    confidence_path = run_dir / "confidence-result.json"
    try:
        confidence = (
            json.loads(confidence_path.read_text(encoding="utf-8"))
            if confidence_path.is_file() else {}
        )
    except (OSError, ValueError):
        confidence = {}
    if not isinstance(confidence, dict):
        confidence = {}
    target_key = "major_violations" if layer == "MAJOR" else "minor_violations"
    target = confidence.get(target_key)
    if not isinstance(target, list):
        target = []
    if any(
        isinstance(item, dict) and item.get("code") == code
        for item in target
    ):
        return
    target.append({
        "layer": layer,
        "code": code,
        "criterion_id": "",
        "deduction": deduction,
        "message": f"{message}; {len(warnings)} check(s) downgraded to warnings",
        "path": warning_path,
    })
    confidence[target_key] = target
    confidence["hard_errors"] = (
        confidence.get("hard_errors")
        if isinstance(confidence.get("hard_errors"), list) else []
    )
    major = confidence.get("major_violations")
    if not isinstance(major, list):
        major = []
    confidence["major_violations"] = major
    minor = confidence.get("minor_violations")
    if not isinstance(minor, list):
        minor = []
    confidence["minor_violations"] = minor
    confidence["deduction_total"] = sum(
        int(item.get("deduction", 0))
        for item in [*confidence["hard_errors"], *major, *minor]
        if isinstance(item, dict)
    )
    confidence["confidence_score"] = max(0, 100 - confidence["deduction_total"])
    score = confidence["confidence_score"]
    confidence["confidence_level"] = (
        "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
    )
    confidence["total_checks_failed"] = sum(
        [len(confidence["hard_errors"]), len(major), len(minor)]
    )
    try:
        confidence_path.write_text(
            json.dumps(confidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        # Confidence is advisory; inability to persist it must not prevent the
        # already-valid semantic report from being assembled or finalized.
        pass
