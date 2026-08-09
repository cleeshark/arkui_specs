#!/usr/bin/env python3
"""Print one compact pending work item without loading the full plan into model context."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from staged_run_support import load_run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show one staged evaluation work item")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--work-item")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        state, work_items = load_run(args.run_dir.resolve())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    items = work_items.get("items")
    if not isinstance(items, list):
        print("ERROR: work-items.items must be a list", file=sys.stderr)
        return 2
    validated = set(state.get("validated_work_items", []))
    if args.work_item:
        selected = next((item for item in items if item.get("id") == args.work_item), None)
        if selected is None:
            print(f"ERROR: unknown work item: {args.work_item}", file=sys.stderr)
            return 2
    else:
        selected = next((item for item in items if item.get("id") not in validated), None)
    if selected is None:
        payload = {
            "current_phase": state.get("current_phase"),
            "next_action": "Complete aggregation.json and assemble semantic-result.json.",
            "validated_work_items": state.get("validated_work_items", []),
        }
    else:
        payload = {
            "current_phase": state.get("current_phase"),
            "work_item": selected,
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
