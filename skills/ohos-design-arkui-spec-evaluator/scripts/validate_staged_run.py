#!/usr/bin/env python3
"""Validate resumable observation, aggregation, and final stages of one run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from aggregation_warning_policy import (
    record_aggregation_warnings,
    record_claim_coverage_warning,
    record_evidence_type_warning,
    record_nv_inspection_warning,
    split_aggregation_warnings,
    split_claim_coverage_warnings,
    split_final_candidate_warnings,
    split_nv_inspection_warnings,
    split_observation_warnings,
)
from staged_run_support import (
    build_final_candidate,
    load_object,
    load_run,
    update_progress,
    validate_aggregation_document,
    validate_final_candidate,
    validate_identity,
    validate_input_hashes,
    validate_observation_document,
)
from create_pilot_template import DEFAULT_EVALUATOR_VERSION


def validate_stage(
    run_dir: Path,
    stage: str,
    work_item_id: str | None = None,
    candidate_path: Path | None = None,
) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    try:
        state, work_items = load_run(run_dir)
    except ValueError as exc:
        return [str(exc)], {}, {}
    validate_identity(work_items, state, "work-items", errors)
    if state.get("evaluator_version") != DEFAULT_EVALUATOR_VERSION:
        errors.append(
            "run-state.evaluator_version: unsupported value "
            f"{state.get('evaluator_version')!r}; expected {DEFAULT_EVALUATOR_VERSION!r}"
        )
    if state.get("schema_version") != 2:
        errors.append(
            "run-state.schema_version: protocol 0.2.0 requires schema_version=2"
        )
    errors.extend(validate_input_hashes(state))
    items = work_items.get("items")
    if not isinstance(items, list) or not items:
        errors.append("work-items.items: expected a non-empty list")
        return errors, state, work_items
    selected = items
    if work_item_id is not None:
        selected = [item for item in items if item.get("id") == work_item_id]
        if not selected:
            errors.append(f"unknown work item: {work_item_id}")
            return errors, state, work_items
    if stage in {"observations", "aggregation", "final"}:
        for item in selected if stage == "observations" else items:
            output_value = item.get("output_path") if isinstance(item, dict) else None
            if not isinstance(output_value, str) or not output_value:
                errors.append(f"work-item {item!r}: missing output_path")
                continue
            try:
                document_path = (
                    candidate_path
                    if candidate_path is not None
                    and stage == "observations"
                    and work_item_id == item.get("id")
                    else Path(output_value)
                )
                document = load_object(document_path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            errors.extend(validate_observation_document(document, item, state))
        errors, observation_warnings = split_observation_warnings(run_dir, errors)
        errors, coverage_warnings = split_claim_coverage_warnings(errors)
        errors, nv_inspection_warnings = split_nv_inspection_warnings(errors)
        record_claim_coverage_warning(run_dir, coverage_warnings)
        record_nv_inspection_warning(run_dir, nv_inspection_warnings)
        for warning in (*observation_warnings, *coverage_warnings, *nv_inspection_warnings):
            print(f"WARNING: {warning}", file=sys.stderr)
    if stage in {"aggregation", "final"}:
        try:
            aggregation = load_object(
                candidate_path if stage == "aggregation" and candidate_path else run_dir / "aggregation.json"
            )
        except ValueError as exc:
            errors.append(str(exc))
        else:
            errors.extend(validate_aggregation_document(aggregation, state, work_items))
            if stage == "aggregation" and not errors:
                try:
                    semantic_template = load_object(run_dir / "semantic-template.json")
                    final_candidate = build_final_candidate(semantic_template, aggregation)
                except (KeyError, ValueError) as exc:
                    errors.append(f"aggregation: cannot build final candidate: {exc}")
                else:
                    errors.extend(validate_final_candidate(final_candidate, aggregation))
    else:
        aggregation = {}
    if stage == "final":
        try:
            semantic = load_object(run_dir / "semantic-result.json")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            errors.extend(validate_final_candidate(semantic, aggregation))
    return errors, state, work_items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate a staged semantic evaluation run")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=("observations", "aggregation", "final"),
        default="observations",
    )
    parser.add_argument("--work-item")
    parser.add_argument(
        "--candidate",
        type=Path,
        help="validate this candidate document without replacing the initialized run file",
    )
    parser.add_argument("--update-state", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.work_item and args.stage != "observations":
        print("ERROR: --work-item is only valid for the observations stage", file=sys.stderr)
        return 2
    if args.candidate and args.stage == "observations" and not args.work_item:
        print("ERROR: an observation --candidate requires --work-item", file=sys.stderr)
        return 2
    if args.candidate and args.stage == "final":
        print("ERROR: --candidate is not valid for the final stage", file=sys.stderr)
        return 2
    if args.candidate and args.update_state:
        print("ERROR: --candidate validation may not update run state", file=sys.stderr)
        return 2
    run_dir = args.run_dir.resolve()
    candidate = args.candidate.resolve() if args.candidate else None
    errors, state, work_items = validate_stage(run_dir, args.stage, args.work_item, candidate)
    if args.stage == "final":
        errors, warnings = split_aggregation_warnings(errors)
        errors, evidence_type_warnings = split_final_candidate_warnings(errors)
        warnings.extend(evidence_type_warnings)
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        record_aggregation_warnings(run_dir, warnings)
        record_evidence_type_warning(run_dir, evidence_type_warnings)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.update_state:
        update_progress(
            run_dir,
            state,
            work_items,
            stage=args.stage,
            work_item_id=args.work_item,
        )
    target = args.work_item or args.stage
    print(f"staged run valid: target={target} run_dir={run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
