#!/usr/bin/env python3
"""Assemble and validate semantic-result.json from a completed staged run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from staged_run_support import (
    build_final_candidate,
    load_object,
    update_progress,
    validate_final_candidate,
    write_object,
)
from validate_staged_run import validate_stage


# These are bounded semantic-quality warnings rather than structural damage.
# The report remains consumable because Criterion findings, evidence, and the
# final schema are intact. Keep all other aggregation validation errors
# blocking.
OWNERSHIP_WARNING_MARKERS = (
    "one defect may produce at most one Critical Finding",
    "a Critical Finding must belong to the primary Criterion",
    "expected one of observation owners",
)
# Keep the existing code for report-consumer compatibility.  It now covers the
# bounded family of non-structural cross-Criterion ownership warnings, including
# primary-owner alignment with validated observations.
OWNERSHIP_WARNING_CODE = "OWNERSHIP_CRITICALITY"
OWNERSHIP_WARNING_DEDUCTION = 20
MAPPING_WARNING_MARKER = ".claim_ids: not mapped to Criterion:"
MAPPING_WARNING_CODE = "MAPPING_CLAIM_UNMAPPED"
MAPPING_WARNING_DEDUCTION = 5


def split_aggregation_warnings(errors: list[str]) -> tuple[list[str], list[str]]:
    """Return (blocking_errors, downgraded_warnings) for assemble-time policy."""
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
        confidence.get("hard_errors") if isinstance(confidence.get("hard_errors"), list) else []
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
    confidence["confidence_level"] = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
    confidence["total_checks_failed"] = sum(
        [len(confidence["hard_errors"]), len(major), len(confidence["minor_violations"])]
    )
    try:
        confidence_path.write_text(
            json.dumps(confidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        # Confidence is advisory; inability to persist it must not prevent the
        # already-valid semantic report from being assembled.
        pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble semantic-result.json from completed observations and aggregation"
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir.resolve()
    errors, state, work_items = validate_stage(run_dir, "aggregation")
    blocking_errors, aggregation_warnings = split_aggregation_warnings(errors)
    if blocking_errors:
        for error in blocking_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for warning in aggregation_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    ownership_warnings = [
        warning for warning in aggregation_warnings
        if any(marker in warning for marker in OWNERSHIP_WARNING_MARKERS)
    ]
    mapping_warnings = [
        warning for warning in aggregation_warnings
        if MAPPING_WARNING_MARKER in warning
    ]
    record_ownership_warning(run_dir, ownership_warnings)
    record_mapping_warning(run_dir, mapping_warnings)
    try:
        semantic_template = load_object(run_dir / "semantic-template.json")
        aggregation = load_object(run_dir / "aggregation.json")
        candidate = build_final_candidate(semantic_template, aggregation)
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_final_candidate(candidate, aggregation)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    output = run_dir / "semantic-result.json"
    write_object(output, candidate)
    update_progress(run_dir, state, work_items, stage="final")
    print(
        f"semantic result assembled: func_id={candidate['func_id']} "
        f"criteria={len(candidate['criterion_results'])} output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
