#!/usr/bin/env python3
"""Validate one evaluator semantic-result JSON against the frozen protocol."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def _discover_specs_root() -> Path:
    candidates = [SKILL_ROOT.parents[1], Path.cwd(), Path.cwd() / "specs"]
    for parent in Path.cwd().parents:
        candidates.extend((parent, parent / "specs"))
    visited: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in visited:
            continue
        visited.add(resolved)
        if (resolved / "tools" / "spec_eval").is_dir() and (
            resolved / "evaluation" / "rubric.yaml"
        ).is_file():
            return resolved
    raise RuntimeError(
        "cannot locate specs root; run from the ace_engine repository root or its specs directory"
    )


SPECS_ROOT = _discover_specs_root()
TOOLS_ROOT = SPECS_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from spec_eval.protocol_validator import validate_protocol, validate_semantic_result  # noqa: E402


EVALUATION_ROOT = SPECS_ROOT / "evaluation"
EXPECTED_EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.3.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate semantic-result JSON for the ArkUI Function evaluator Skill"
    )
    parser.add_argument("result", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        instance = json.loads(args.result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read {args.result}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(instance, dict):
        print(f"ERROR: {args.result}: expected a JSON object", file=sys.stderr)
        return 2
    if instance.get("evaluator_version") != EXPECTED_EVALUATOR_VERSION:
        print(
            "ERROR: unsupported evaluator_version: expected "
            f"{EXPECTED_EVALUATOR_VERSION!r}, got {instance.get('evaluator_version')!r}",
            file=sys.stderr,
        )
        return 1
    rubric, complexity, errors = validate_protocol(EVALUATION_ROOT)
    errors.extend(
        validate_semantic_result(
            instance,
            rubric,
            complexity,
            EVALUATION_ROOT / "schemas",
        )
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"semantic result valid: func_id={instance['func_id']} "
        f"run_id={instance['run_id']} criteria={len(instance['criterion_results'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
