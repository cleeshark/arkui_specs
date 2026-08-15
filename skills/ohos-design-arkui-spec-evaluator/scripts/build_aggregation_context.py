#!/usr/bin/env python3
"""Build the deterministic run-derived mapping used by Function aggregation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from staged_run_support import (
    AGGREGATION_MAPPING_EVALUATOR_VERSIONS,
    build_aggregation_context,
    load_run,
    write_object,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build staged aggregation mapping context")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir.resolve()
    output = args.output.resolve() if args.output else run_dir / "aggregation-context.json"
    try:
        state, work_items = load_run(run_dir)
        if state.get("evaluator_version") not in AGGREGATION_MAPPING_EVALUATOR_VERSIONS:
            raise ValueError(
                "aggregation context is not defined for evaluator "
                f"{state.get('evaluator_version')!r}"
            )
        context = build_aggregation_context(state, work_items)
        write_object(output, context)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"aggregation context written: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
