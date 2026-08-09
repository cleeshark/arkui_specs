#!/usr/bin/env python3
"""Validate resumable observation, aggregation, and final stages of one run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from staged_run_support import (
    load_object,
    load_run,
    update_progress,
    validate_aggregation_document,
    validate_final_candidate,
    validate_identity,
    validate_input_hashes,
    validate_observation_document,
)


def validate_stage(
    run_dir: Path,
    stage: str,
    work_item_id: str | None = None,
) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    try:
        state, work_items = load_run(run_dir)
    except ValueError as exc:
        return [str(exc)], {}, {}
    validate_identity(work_items, state, "work-items", errors)
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
                document = load_object(Path(output_value))
            except ValueError as exc:
                errors.append(str(exc))
                continue
            errors.extend(validate_observation_document(document, item, state))
    if stage in {"aggregation", "final"}:
        try:
            aggregation = load_object(run_dir / "aggregation.json")
        except ValueError as exc:
            errors.append(str(exc))
        else:
            errors.extend(validate_aggregation_document(aggregation, state, work_items))
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
    parser.add_argument("--update-state", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.work_item and args.stage != "observations":
        print("ERROR: --work-item is only valid for the observations stage", file=sys.stderr)
        return 2
    run_dir = args.run_dir.resolve()
    errors, state, work_items = validate_stage(run_dir, args.stage, args.work_item)
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
