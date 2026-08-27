#!/usr/bin/env python3
"""Assemble and validate semantic-result.json from a completed staged run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aggregation_warning_policy import (
    record_aggregation_warnings,
    record_contradiction_basis_warning,
    record_finding_evidence_warning,
    record_mapping_warning,
    record_ownership_warning,
    split_aggregation_warnings,
)
from staged_run_support import (
    build_final_candidate,
    load_object,
    repair_aggregation_contract,
    repair_missing_finding_evidence,
    update_progress,
    validate_final_candidate,
    write_object,
)
from validate_staged_run import validate_stage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble semantic-result.json from completed observations and aggregation"
    )
    parser.add_argument("--run-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir.resolve()
    # Repair only deterministic final-contract omissions before the staged
    # validator runs.  In particular, a model Correction may leave an
    # ownership row with Findings but no primary Criterion; the repair helper
    # infers it from the owned Finding(s), while any remaining ownership
    # disagreement is retained as a confidence warning.
    aggregation_path = run_dir / "aggregation.json"
    try:
        aggregation = load_object(aggregation_path)
        repaired_aggregation, repair_changes = repair_aggregation_contract(
            aggregation
        )
        # Insert documented-gap placeholders for evidence-required Findings that
        # are genuinely evidence-less, so a data-quality gap the kernel already
        # treats as non-blocking does not make the whole report un-publishable.
        repaired_aggregation, gap_changes = repair_missing_finding_evidence(
            repaired_aggregation
        )
        repair_changes = list(repair_changes) + list(gap_changes)
        if repair_changes:
            write_object(aggregation_path, repaired_aggregation)
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors, state, work_items = validate_stage(run_dir, "aggregation")
    blocking_errors, aggregation_warnings = split_aggregation_warnings(errors)
    if blocking_errors:
        for error in blocking_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for warning in aggregation_warnings:
        print(f"WARNING: {warning}", file=sys.stderr)
    record_aggregation_warnings(run_dir, aggregation_warnings)
    if gap_changes:
        # A documented-gap placeholder was inserted: deduct confidence so the
        # data-quality gap stays visible in the published report.
        for change in gap_changes:
            print(f"WARNING: {change}", file=sys.stderr)
        record_finding_evidence_warning(run_dir, gap_changes)
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
