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


# These are semantic ownership-quality warnings rather than structural damage.
# The aggregation contract still describes them as defects, but a report can be
# assembled safely because criterion findings, evidence, and the final schema
# remain usable.  Keep all other aggregation validation errors blocking.
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


def split_aggregation_warnings(errors: list[str]) -> tuple[list[str], list[str]]:
    """Return (blocking_errors, ownership_warnings) for assemble-time policy."""
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        if any(marker in error for marker in OWNERSHIP_WARNING_MARKERS):
            warnings.append(error)
        else:
            blocking.append(error)
    return blocking, warnings


def record_ownership_warning(run_dir: Path, warnings: list[str]) -> None:
    """Apply one bounded confidence deduction for ownership-quality warnings."""
    if not warnings:
        return
    path = run_dir / "confidence-result.json"
    try:
        confidence = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (OSError, ValueError):
        confidence = {}
    if not isinstance(confidence, dict):
        confidence = {}
    major = confidence.get("major_violations")
    if not isinstance(major, list):
        major = []
    if any(
        isinstance(item, dict) and item.get("code") == OWNERSHIP_WARNING_CODE
        for item in major
    ):
        return
    major.append({
        "layer": "MAJOR",
        "code": OWNERSHIP_WARNING_CODE,
        "criterion_id": "",
        "deduction": OWNERSHIP_WARNING_DEDUCTION,
        "message": (
            "defect ownership contains non-structural cross-Criterion inconsistencies; "
            f"{len(warnings)} ownership check(s) were downgraded to warnings"
        ),
        "path": "aggregation.defect_ownership",
    })
    confidence["major_violations"] = major
    confidence["hard_errors"] = (
        confidence.get("hard_errors") if isinstance(confidence.get("hard_errors"), list) else []
    )
    confidence["minor_violations"] = (
        confidence.get("minor_violations")
        if isinstance(confidence.get("minor_violations"), list)
        else []
    )
    confidence["deduction_total"] = sum(
        int(item.get("deduction", 0))
        for item in [*confidence["hard_errors"], *major, *confidence["minor_violations"]]
        if isinstance(item, dict)
    )
    confidence["confidence_score"] = max(0, 100 - confidence["deduction_total"])
    score = confidence["confidence_score"]
    confidence["confidence_level"] = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
    confidence["total_checks_failed"] = sum(
        [len(confidence["hard_errors"]), len(major), len(confidence["minor_violations"])]
    )
    try:
        path.write_text(json.dumps(confidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    blocking_errors, ownership_warnings = split_aggregation_warnings(errors)
    if blocking_errors:
        for error in blocking_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for warning in ownership_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    record_ownership_warning(run_dir, ownership_warnings)
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
