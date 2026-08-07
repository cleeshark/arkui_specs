"""Single-entry Function evaluation template generation and validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import yaml

from spec_eval.config import EvaluationConfig
from spec_eval.discovery import FunctionLocator
from spec_eval.protocol_validator import (
    JsonSchemaSubsetValidator,
    aggregate_function_complexity,
    validate_protocol,
    validate_semantic_result,
)


def _git_revision(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _sha256_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _number(value: Any) -> Decimal:
    return Decimal(str(value))


def _rounded(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _plain_number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


def function_input_snapshot(config: EvaluationConfig, func_id: str) -> dict[str, Any]:
    """Build a deterministic fingerprint from Registry, Spec and Design inputs."""

    context = FunctionLocator(config).locate(func_id)
    documents = []
    for path in sorted(context.all_documents(), key=lambda item: item.as_posix()):
        relative = config.repo_relative(path)
        content_hash = _sha256_bytes(path.read_bytes()) if path.is_file() else None
        documents.append({"path": relative, "content_hash": content_hash})
    payload = {
        "func_id": func_id,
        "function_registry_entry": context.function_registry_entry,
        "feature_registry_entries": list(context.feature_registry_entries),
        "documents": documents,
    }
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "func_id": func_id,
        "function_path": config.repo_relative(context.function_path),
        "design_path": config.repo_relative(context.design_path) if context.design_path else None,
        "feature_count": len(context.feature_specs),
        "documents": documents,
        "input_fingerprint": _sha256_bytes(serialized),
    }


def _complexity_values(config: EvaluationConfig, func_id: str) -> dict[str, str | None]:
    context = FunctionLocator(config).locate(func_id)
    values: dict[str, str | None] = {}
    for entry in context.feature_registry_entries:
        feat_id = str(entry.get("id"))
        raw_value = None
        if entry.get("spec"):
            path = config.specs_root / str(entry["spec"])
            if path.is_file():
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                    if len(cells) >= 2 and cells[0] == "复杂度":
                        raw_value = cells[1]
                        break
        values[feat_id] = raw_value
    return values


def validate_evaluation_manifest(
    manifest: dict[str, Any],
    config: EvaluationConfig,
    complexity_rules: dict[str, Any],
    schemas_root: Path,
    *,
    check_revisions: bool = True,
) -> list[str]:
    errors = JsonSchemaSubsetValidator(schemas_root).validate_file(
        manifest, schemas_root / "golden-manifest.schema.json"
    )
    pilot = manifest.get("pilot_functions", [])
    expected_size = manifest.get("selection_requirements", {}).get("pilot_size")
    if len(pilot) != expected_size:
        errors.append(f"evaluation Pilot must contain {expected_size} Functions, got {len(pilot)}")
    func_ids = [item.get("func_id") for item in pilot]
    if len(func_ids) != len(set(func_ids)):
        errors.append("evaluation Pilot FuncIDs must be unique")
    l1_ids = {item.get("l1", {}).get("id") for item in pilot}
    if len(l1_ids) < manifest.get("selection_requirements", {}).get("minimum_l1_domains", 0):
        errors.append("evaluation Pilot does not cover enough first-level domains")
    levels = {item.get("complexity") for item in pilot}
    if levels != {"simple", "standard", "complex", "critical"}:
        errors.append(f"evaluation Pilot must cover all complexity levels, got {sorted(levels)}")
    required_scenarios = set(manifest.get("selection_requirements", {}).get("required_scenarios", []))
    actual_scenarios = {tag for item in pilot for tag in item.get("scenario_tags", [])}
    missing_scenarios = required_scenarios - actual_scenarios
    if missing_scenarios:
        errors.append(f"evaluation Pilot is missing scenarios: {sorted(missing_scenarios)}")
    if manifest.get("status") != "proposed":
        confirmation = manifest.get("confirmation", {})
        if not confirmation.get("confirmed_by") or not confirmation.get("confirmed_at"):
            errors.append("ready evaluation Pilot requires one recorded confirmation")

    for item in pilot:
        func_id = item.get("func_id")
        if not isinstance(func_id, str):
            continue
        try:
            snapshot = function_input_snapshot(config, func_id)
        except Exception as exc:  # report all sample problems together
            errors.append(f"{func_id}: cannot build input snapshot: {exc}")
            continue
        if snapshot["feature_count"] != item.get("feature_count"):
            errors.append(
                f"{func_id}: feature_count changed from {item.get('feature_count')} "
                f"to {snapshot['feature_count']}"
            )
        if snapshot["input_fingerprint"] != item.get("input_fingerprint"):
            errors.append(f"{func_id}: input fingerprint changed; refresh and reconfirm the evaluation")
        normalized = aggregate_function_complexity(_complexity_values(config, func_id), complexity_rules)
        if normalized["function_level"] != item.get("complexity"):
            errors.append(
                f"{func_id}: complexity changed from {item.get('complexity')} "
                f"to {normalized['function_level']}"
            )

    if check_revisions:
        revisions = manifest.get("revisions", {})
        actual_revisions = {
            "ace_engine": config.git_revision(),
            "specs": _git_revision(config.specs_root),
            "sdk_js": _git_revision(config.oh_root / "interface" / "sdk-js"),
            "sdk_c": _git_revision(config.oh_root / "interface" / "sdk_c"),
        }
        for key, actual in actual_revisions.items():
            expected = revisions.get(key)
            if expected != actual:
                errors.append(f"revision mismatch for {key}: expected {expected}, got {actual}")
    return errors


def build_evaluation_template(
    manifest: dict[str, Any],
    config: EvaluationConfig,
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    func_id: str,
    evaluator_id: str,
) -> dict[str, Any]:
    """Create one draft evaluation for one Function."""

    sample = next(
        (item for item in manifest.get("pilot_functions", []) if item.get("func_id") == func_id),
        None,
    )
    if sample is None:
        raise ValueError(f"FuncID is not registered in the evaluation Pilot: {func_id}")
    snapshot = function_input_snapshot(config, func_id)
    complexity = aggregate_function_complexity(_complexity_values(config, func_id), complexity_rules)
    criterion_results = []
    for dimension in rubric["dimensions"]:
        for criterion in dimension["criteria"]:
            criterion_results.append(
                {
                    "criterion_id": criterion["id"],
                    "dimension_id": dimension["id"],
                    "applicability": "APPLICABLE",
                    "conclusion": "NOT_VERIFIABLE",
                    "reason": "待评价人根据冻结输入和证据填写",
                    "missing_evidence": "待评价人说明缺少的证据，或改为可验证结论",
                    "claim_ids": [],
                    "evidence": [],
                    "findings": [],
                }
            )
    return {
        "schema_version": 1,
        "evaluation_version": manifest["evaluation_set_version"],
        "evaluation_id": f"EVAL-{func_id}",
        "func_id": func_id,
        "input_fingerprint": snapshot["input_fingerprint"],
        "source_revision": manifest["revisions"]["ace_engine"],
        "status": "draft",
        "evaluator": {"evaluator_id": evaluator_id, "evaluated_at": None},
        "semantic_result": {
            "schema_version": 1,
            "rubric_version": rubric["rubric_version"],
            "complexity_rules_version": complexity_rules["complexity_rules_version"],
            "evaluator_protocol_version": "0.3.0",
            "evaluator_version": f"human:{evaluator_id}",
            "func_id": func_id,
            "source_revision": manifest["revisions"]["ace_engine"],
            "run_id": f"evaluation-{func_id}",
            "complexity": complexity,
            "criterion_results": criterion_results,
            "coverage": {
                "expected_criteria": len(criterion_results),
                "evaluated_criteria": len(criterion_results),
                "applicable_criteria": len(criterion_results),
                "not_applicable_criteria": 0,
                "not_verifiable_criteria": len(criterion_results),
            },
            "execution": {
                "static_complete": True,
                "evidence_complete": True,
                "semantic_complete": False,
                "notes": ["Draft template: Criterion conclusions and scores are pending."],
            },
        },
        "scores": {
            "dimensions": {dimension["id"]: None for dimension in rubric["dimensions"]},
            "raw_score": None,
            "published_score": None,
            "confidence": None,
            "admission": "NOT_READY",
        },
        "confirmation": {
            "confirmed_by": None,
            "confirmed_at": None,
            "conclusion": "pending",
            "notes": [],
        },
        "notes": [
            f"完成{len(criterion_results)}个Criterion后填写精确分数并进行一次确认。",
            "Critical/Major Finding必须包含冻结revision下的可复现证据。",
        ],
    }


def calculate_semantic_scores(
    semantic_result: dict[str, Any], rubric: dict[str, Any]
) -> tuple[dict[str, Decimal], Decimal, Decimal]:
    """Calculate deterministic dimension/raw scores and the semantic publishing cap."""

    results = {item.get("criterion_id"): item for item in semantic_result.get("criterion_results", [])}
    dimensions: dict[str, Decimal] = {}
    highest_severity = "None"
    severity_rank = {"None": 0, "Info": 0, "Minor": 1, "Major": 2, "Critical": 3}
    for dimension in rubric["dimensions"]:
        earned = Decimal(0)
        applicable_max = Decimal(0)
        for criterion in dimension["criteria"]:
            result = results.get(criterion["id"], {})
            conclusion = result.get("conclusion")
            for finding in result.get("findings", []):
                severity = finding.get("severity", "None")
                if severity_rank.get(severity, -1) > severity_rank[highest_severity]:
                    highest_severity = severity
            if conclusion == "NOT_APPLICABLE":
                continue
            maximum = _number(criterion["max_score"])
            deduction = _number(criterion.get("outcomes", {}).get(conclusion, {}).get("deduction", 0))
            applicable_max += maximum
            earned += max(Decimal(0), maximum - deduction)
        weight = _number(dimension["weight"])
        score = _rounded(earned / applicable_max * weight) if applicable_max else Decimal(0)
        dimensions[dimension["id"]] = score
    raw_score = _rounded(sum(dimensions.values(), Decimal(0)))
    cap = _number(rubric["publishing_caps"]["caps"].get(highest_severity, 100))
    return dimensions, raw_score, cap


def validate_function_evaluation(
    evaluation: dict[str, Any],
    manifest: dict[str, Any],
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    schemas_root: Path,
) -> list[str]:
    semantic = evaluation.get("semantic_result", {})
    expected_versions = {
        "rubric_version": rubric.get("rubric_version"),
        "complexity_rules_version": complexity_rules.get("complexity_rules_version"),
        "evaluator_protocol_version": rubric.get("protocol_compatibility", {}).get(
            "evaluator_protocol_versions", [None]
        )[0],
    }
    actual_versions = {field: semantic.get(field) for field in expected_versions}
    if actual_versions != expected_versions:
        return [
            f"{evaluation.get('func_id')}: review protocol is stale "
            f"(actual={actual_versions}, expected={expected_versions}); "
            "regenerate drafts or re-evaluate confirmed reviews under the current Rubric"
        ]
    errors = JsonSchemaSubsetValidator(schemas_root).validate_file(
        evaluation, schemas_root / "function-evaluation.schema.json"
    )
    func_id = evaluation.get("func_id")
    sample = next(
        (item for item in manifest.get("pilot_functions", []) if item.get("func_id") == func_id),
        None,
    )
    if sample is None:
        errors.append(f"evaluation FuncID is not registered in the Pilot: {func_id}")
    elif evaluation.get("input_fingerprint") != sample.get("input_fingerprint"):
        errors.append(f"{func_id}: evaluation input fingerprint does not match the frozen input")
    if evaluation.get("evaluation_version") != manifest.get("evaluation_set_version"):
        errors.append("evaluation version does not match the Pilot manifest")
    if evaluation.get("source_revision") != manifest.get("revisions", {}).get("ace_engine"):
        errors.append("evaluation source revision does not match the Pilot manifest")

    errors.extend(validate_semantic_result(semantic, rubric, complexity_rules, schemas_root))
    if semantic.get("func_id") != func_id:
        errors.append("evaluation and semantic_result FuncIDs must match")
    if semantic.get("source_revision") != evaluation.get("source_revision"):
        errors.append("evaluation and semantic_result source revisions must match")
    evaluator_id = evaluation.get("evaluator", {}).get("evaluator_id")
    if semantic.get("evaluator_version") != f"human:{evaluator_id}":
        errors.append("semantic evaluator_version must identify the evaluation evaluator_id")

    if evaluation.get("status") != "confirmed":
        return errors

    if not evaluation.get("evaluator", {}).get("evaluated_at"):
        errors.append("confirmed evaluation requires evaluator.evaluated_at")
    if evaluator_id in {None, "", "EVALUATOR_ID"}:
        errors.append("confirmed evaluation requires a real evaluator_id")
    execution = semantic.get("execution", {})
    required_execution = ("static_complete", "evidence_complete", "semantic_complete")
    if not all(execution.get(field) is True for field in required_execution):
        errors.append("confirmed evaluation requires static/evidence/semantic execution complete")
    coverage = semantic.get("coverage", {})
    if coverage.get("not_verifiable_criteria") == coverage.get("expected_criteria"):
        errors.append("confirmed evaluation cannot leave every Criterion NOT_VERIFIABLE")

    confirmation = evaluation.get("confirmation", {})
    if confirmation.get("conclusion") != "accepted":
        errors.append("confirmed evaluation requires confirmation.conclusion=accepted")
    if not confirmation.get("confirmed_by") or not confirmation.get("confirmed_at"):
        errors.append("confirmed evaluation requires confirmed_by and confirmed_at")

    dimensions, raw_score, semantic_cap = calculate_semantic_scores(semantic, rubric)
    score_block = evaluation.get("scores", {})
    actual_dimensions = score_block.get("dimensions", {})
    for dimension_id, expected in dimensions.items():
        actual = actual_dimensions.get(dimension_id)
        if actual is None or _number(actual) != expected:
            errors.append(f"scores.dimensions.{dimension_id} must be {_plain_number(expected)}")
    actual_raw = score_block.get("raw_score")
    if actual_raw is None or _number(actual_raw) != raw_score:
        errors.append(f"scores.raw_score must be {_plain_number(raw_score)}")
    published = score_block.get("published_score")
    if published is None:
        errors.append("confirmed evaluation requires scores.published_score")
    elif _number(published) > min(raw_score, semantic_cap):
        errors.append(
            "scores.published_score may not exceed raw score or the semantic severity cap "
            f"{_plain_number(min(raw_score, semantic_cap))}"
        )
    confidence = score_block.get("confidence")
    if confidence is None:
        errors.append("confirmed evaluation requires scores.confidence")
    elif published is not None:
        published_value = _number(published)
        confidence_value = _number(confidence)
        allowed_rank = 0
        if published_value >= Decimal(80) and confidence_value >= Decimal("0.8"):
            allowed_rank = 1
        if published_value >= Decimal(90) and confidence_value >= Decimal("0.85"):
            allowed_rank = 2
        admission_rank = {"NOT_READY": 0, "BASELINED": 1, "HIGH_QUALITY": 2}
        actual_admission = score_block.get("admission")
        if admission_rank.get(actual_admission, 99) > allowed_rank:
            errors.append(f"scores.admission {actual_admission} exceeds score/confidence thresholds")
    return errors


def validate_registered_evaluations(
    reviews_root: Path,
    manifest: dict[str, Any],
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    schemas_root: Path,
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for path in sorted(reviews_root.glob("*.yaml")):
        evaluation = yaml.safe_load(path.read_text(encoding="utf-8"))
        func_id = evaluation.get("func_id") if isinstance(evaluation, dict) else None
        if path.name != f"{func_id}.yaml":
            errors.append(f"{path.name}: evaluation filename must be {func_id}.yaml")
        if func_id in seen:
            errors.append(f"duplicate Function evaluation: {func_id}")
        seen.add(func_id)
        errors.extend(
            f"{path.name}: {item}"
            for item in validate_function_evaluation(
                evaluation, manifest, rubric, complexity_rules, schemas_root
            )
        )
    expected = {item.get("func_id") for item in manifest.get("pilot_functions", [])}
    missing = expected - seen
    if missing:
        errors.append(f"missing Pilot Function evaluations: {sorted(missing)}")
    return errors


def refresh_draft_evaluations(
    reviews_root: Path,
    manifest: dict[str, Any],
    config: EvaluationConfig,
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Regenerate existing draft reviews with the current protocol.

    Confirmed and superseded records are deliberately left untouched because a
    protocol upgrade requires a fresh semantic judgment, not a mechanical score
    conversion.
    """

    refreshed: list[str] = []
    skipped: list[str] = []
    for sample in manifest.get("pilot_functions", []):
        func_id = sample.get("func_id")
        path = reviews_root / f"{func_id}.yaml"
        if not path.is_file():
            skipped.append(f"{func_id}: missing review file")
            continue
        evaluation = yaml.safe_load(path.read_text(encoding="utf-8"))
        status = evaluation.get("status") if isinstance(evaluation, dict) else None
        if status != "draft":
            skipped.append(f"{func_id}: status={status}")
            continue
        evaluator_id = evaluation.get("evaluator", {}).get("evaluator_id")
        if not evaluator_id:
            skipped.append(f"{func_id}: missing evaluator_id")
            continue
        template = build_evaluation_template(
            manifest, config, rubric, complexity_rules, func_id, evaluator_id
        )
        path.write_text(
            yaml.safe_dump(template, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        refreshed.append(func_id)
    return refreshed, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate and validate single Function evaluations")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "evaluation" / "golden" / "manifest.yaml",
    )
    parser.add_argument(
        "--no-revision-check",
        action="store_true",
        help="Validate structure and fingerprints without requiring current Git revisions",
    )
    parser.add_argument("--show-input", metavar="FUNC_ID", help="Print one Function input snapshot")
    parser.add_argument("--template", metavar="FUNC_ID", help="Print one draft Function evaluation")
    parser.add_argument("--evaluator-id", help="Evaluator identifier used with --template")
    parser.add_argument("--evaluation", type=Path, help="Validate one Function evaluation file")
    parser.add_argument(
        "--refresh-drafts",
        action="store_true",
        help="Regenerate existing draft reviews with the current protocol; confirmed reviews are untouched",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = EvaluationConfig.discover()
    if args.show_input:
        print(json.dumps(function_input_snapshot(config, args.show_input), ensure_ascii=False, indent=2))
        return 0
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    evaluation_root = args.manifest.parents[1]
    rubric, complexity, errors = validate_protocol(evaluation_root)
    schemas_root = evaluation_root / "schemas"
    if args.refresh_drafts:
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        refreshed, skipped = refresh_draft_evaluations(
            evaluation_root / "reviews", manifest, config, rubric, complexity
        )
        print(f"draft reviews refreshed: {len(refreshed)}")
        for item in skipped:
            print(f"SKIP: {item}")
        return 0
    if args.template:
        if not args.evaluator_id:
            parser.error("--template requires --evaluator-id")
        template = build_evaluation_template(
            manifest, config, rubric, complexity, args.template, args.evaluator_id
        )
        print(yaml.safe_dump(template, allow_unicode=True, sort_keys=False))
        return 0
    if args.evaluation:
        evaluation = yaml.safe_load(args.evaluation.read_text(encoding="utf-8"))
        errors.extend(
            validate_function_evaluation(evaluation, manifest, rubric, complexity, schemas_root)
        )
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print(f"Function evaluation valid: {evaluation['evaluation_id']} status={evaluation['status']}")
        return 0
    errors.extend(
        validate_evaluation_manifest(
            manifest,
            config,
            complexity,
            schemas_root,
            check_revisions=not args.no_revision_check,
        )
    )
    errors.extend(
        validate_registered_evaluations(
            evaluation_root / "reviews", manifest, rubric, complexity, schemas_root
        )
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"evaluation protocol valid: status={manifest['status']} "
        f"pilot_functions={len(manifest['pilot_functions'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
