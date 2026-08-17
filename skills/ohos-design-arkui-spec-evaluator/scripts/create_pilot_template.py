#!/usr/bin/env python3
"""Create one run-local semantic-result template for a frozen Pilot Function."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


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
REPO_ROOT = SPECS_ROOT.parent
TOOLS_ROOT = SPECS_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from spec_eval.config import EvaluationConfig  # noqa: E402
from spec_eval.evaluation_validator import build_evaluation_template  # noqa: E402
from spec_eval.protocol_validator import validate_protocol  # noqa: E402


EVALUATION_ROOT = SPECS_ROOT / "evaluation"
MANIFEST_PATH = EVALUATION_ROOT / "golden" / "manifest.yaml"
REVIEWS_ROOT = (EVALUATION_ROOT / "reviews").resolve()
DEFAULT_EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.2.0"


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def _validate_input_dir(input_dir: Path, func_id: str, source_revision: str) -> None:
    required = {
        "function-context.json": _load_object,
        "static-result.json": _load_object,
        "evidence-manifest.json": _load_object,
    }
    documents: dict[str, dict[str, Any]] = {}
    for filename, loader in required.items():
        path = input_dir / filename
        if not path.is_file():
            raise ValueError(f"missing required Function input: {path}")
        documents[filename] = loader(path)
    for filename, document in documents.items():
        if document.get("func_id") != func_id:
            raise ValueError(
                f"{filename}: FuncID mismatch, expected {func_id}, got {document.get('func_id')!r}"
            )
        if document.get("source_revision") != source_revision:
            raise ValueError(
                f"{filename}: source revision mismatch, expected {source_revision}, "
                f"got {document.get('source_revision')!r}"
            )
    if documents["static-result.json"].get("gate") == "error":
        raise ValueError("static-result.json reports a tool error; semantic evaluation is blocked")
    manifest = documents["evidence-manifest.json"]
    shards = manifest.get("shards")
    if not isinstance(shards, list) or not shards:
        raise ValueError("evidence-manifest.json must declare at least one evidence shard")
    for shard in shards:
        relative = shard.get("path") if isinstance(shard, dict) else None
        if not isinstance(relative, str) or not relative:
            raise ValueError("evidence-manifest.json contains a shard without a path")
        path = input_dir / "evidence" / relative
        if not path.is_file():
            raise ValueError(f"missing declared evidence shard: {path}")
        _load_object(path)


def _output_is_forbidden(path: Path) -> bool:
    resolved = path.resolve()
    return resolved == REVIEWS_ROOT or REVIEWS_ROOT in resolved.parents


def _scope_notes(sample: dict[str, Any]) -> list[str]:
    scope = sample.get("evaluation_scope")
    if not isinstance(scope, dict):
        return []
    labels = (
        ("include", "Pilot evaluation scope include"),
        ("exclude", "Pilot evaluation scope exclude"),
        ("non_findings", "Pilot evaluation scope non-finding"),
    )
    notes: list[str] = []
    for key, label in labels:
        values = scope.get(key, [])
        if isinstance(values, list):
            notes.extend(f"{label}: {value}" for value in values if isinstance(value, str))
    return notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a semantic-result JSON template for one frozen NEXT-007 Pilot Function"
    )
    parser.add_argument("--func-id", required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--evaluation-mode", choices=("golden", "automated"), default="golden"
    )
    parser.add_argument("--source-revision")
    return parser


def create_semantic_template(
    func_id: str,
    input_dir: Path,
    run_id: str,
    evaluator_version: str = DEFAULT_EVALUATOR_VERSION,
    *,
    source_revision: str | None = None,
    allow_non_pilot: bool = False,
) -> dict[str, Any]:
    rubric, complexity, errors = validate_protocol(EVALUATION_ROOT)
    if errors:
        raise ValueError("; ".join(errors))
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"{MANIFEST_PATH}: expected a YAML mapping")
    sample = next(
        (item for item in manifest.get("pilot_functions", []) if item.get("func_id") == func_id),
        None,
    )
    if sample is None and not allow_non_pilot:
        raise LookupError(
            f"{func_id} is outside the frozen NEXT-007 Pilot; "
            "general Function templates are not enabled in the MVP framework"
        )
    golden_revision = str(manifest.get("revisions", {}).get("ace_engine", ""))
    if allow_non_pilot:
        if not source_revision:
            raise ValueError("automated evaluation requires an explicit source revision")
        effective_revision = source_revision
    else:
        if source_revision is not None and source_revision != golden_revision:
            raise ValueError(
                f"golden evaluation requires source revision {golden_revision}, got {source_revision}"
            )
        effective_revision = golden_revision
    _validate_input_dir(input_dir.resolve(), func_id, effective_revision)
    evaluation = build_evaluation_template(
        manifest,
        EvaluationConfig.discover(),
        rubric,
        complexity,
        func_id,
        "skill-framework",
        source_revision=effective_revision,
        require_pilot=not allow_non_pilot,
    )
    semantic = evaluation["semantic_result"]
    semantic["evaluator_version"] = evaluator_version
    semantic["run_id"] = run_id
    semantic["execution"] = {
        "static_complete": True,
        "evidence_complete": True,
        "semantic_complete": False,
        "notes": [
            "NEXT-007 Skill template: complete all 20 Criteria before setting semantic_complete=true.",
            "Blind mode: do not read confirmed Reviews or historical NEXT-007 runs before validating this result.",
            *_scope_notes(sample or {}),
        ],
    }
    return semantic


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if _output_is_forbidden(args.output):
        print("ERROR: automatic Skill output may not be written under evaluation/reviews", file=sys.stderr)
        return 2
    try:
        semantic = create_semantic_template(
            args.func_id,
            args.input_dir,
            args.run_id,
            source_revision=args.source_revision,
            allow_non_pilot=args.evaluation_mode == "automated",
        )
    except LookupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(semantic, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"semantic template written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
