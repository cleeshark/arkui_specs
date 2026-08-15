#!/usr/bin/env python3
"""Apply the bounded evaluator-owned aggregation final-contract repair."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from staged_run_support import load_object, repair_aggregation_contract, write_object


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        candidate = load_object(args.candidate.resolve())
        repaired, changes = repair_aggregation_contract(candidate)
        if not changes:
            raise ValueError("candidate contains no eligible final-contract drift")
        write_object(args.output.resolve(), repaired)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"aggregation contract repaired: changes={len(changes)} output={args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
