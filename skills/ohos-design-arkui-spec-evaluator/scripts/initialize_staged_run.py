#!/usr/bin/env python3
"""Initialize a resumable, progressively loaded Function semantic evaluation run."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from create_pilot_template import (
    DEFAULT_EVALUATOR_VERSION,
    EVALUATION_ROOT,
    REPO_ROOT,
    _output_is_forbidden,
    create_semantic_template,
)
from staged_run_support import (
    FEATURE_REQUIRED_CHECKS,
    FUNCTION_REQUIRED_CHECKS,
    STAGED_SCHEMA_VERSION,
    OUTCOME_POLICY_BASIS_CRITERIA,
    content_hash,
    load_object,
    staged_output_contract,
    write_object,
)


def _claim_ids(shard: dict[str, Any], path: Path) -> list[str]:
    claims = shard.get("claims")
    if not isinstance(claims, list):
        raise ValueError(f"{path}: expected a claims list")
    result: list[str] = []
    for index, claim in enumerate(claims):
        claim_id = claim.get("claim_id") if isinstance(claim, dict) else None
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError(f"{path}: claims[{index}] has no claim_id")
        result.append(claim_id)
    if len(result) != len(set(result)):
        raise ValueError(f"{path}: duplicate claim IDs")
    return result


def _repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def _artifact(path: Path, kind: str) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"missing {kind} input: {path}")
    return {"kind": kind, "path": str(path), "content_hash": content_hash(path)}


def _input_resource(path: Path, role: str, *, citable: bool) -> dict[str, Any]:
    """Describe one executor input without making every input evidence."""
    resolved = path.resolve()
    resource: dict[str, Any] = {
        "path": str(resolved),
        "role": role,
        "citable": citable,
    }
    if citable:
        try:
            resource["canonical_path"] = resolved.relative_to(REPO_ROOT).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"citable input is outside the frozen ace_engine repository: {resolved}"
            ) from exc
    return resource


def _source_scope_paths(
    *documents: dict[str, Any], findings: list[dict[str, Any]] = ()
) -> list[Path]:
    """Collect already-resolved frozen source/SDK/build/test paths.

    Evidence and static reports are navigation indexes.  We expose only paths
    that are present in the frozen repository, and keep them non-citable so a
    worker must still cite the concrete file it inspected.  Spec/evidence
    paths are intentionally excluded; the document itself is declared
    separately as the citable input.
    """
    candidates: set[str] = set()

    def visit(value: Any, key: str = "") -> None:
        if isinstance(value, dict):
            for name, child in value.items():
                visit(child, str(name))
        elif isinstance(value, list):
            for child in value:
                visit(child, key)
        elif isinstance(value, str) and key in {
            "source_path", "path", "raw", "file", "build_path", "test_path",
        }:
            raw = value.strip().split(":", 1)[0]
            if raw.startswith((
                "frameworks/", "adapter/", "interfaces/", "interface/sdk-js/",
                "interface/sdk_c/", "test/", "tests/",
            )):
                candidates.add(raw)

    for document in documents:
        visit(document)
    for finding in findings:
        visit(finding)

    result: list[Path] = []
    for raw in sorted(candidates):
        path = _repo_path(raw)
        if path.is_file() or path.is_dir():
            result.append(path)
    return result


def _static_summary(findings: list[dict[str, Any]], slice_path: Path) -> dict[str, Any]:
    return {
        "count": len(findings),
        "slice_path": str(slice_path),
        "by_severity": dict(sorted(Counter(str(item.get("severity")) for item in findings).items())),
        "by_rule": dict(sorted(Counter(str(item.get("rule_id")) for item in findings).items())),
        "finding_ids": [item.get("finding_id") for item in findings],
    }


def _observation_template(
    *,
    semantic: dict[str, Any],
    item_id: str,
    observation_type: str,
    feat_id: str | None,
    input_paths: list[str],
    expected_claim_ids: list[str],
    required_checks: list[str],
    observation_profile: str,
) -> dict[str, Any]:
    document: dict[str, Any] = {
        "schema_version": STAGED_SCHEMA_VERSION,
        "evaluator_version": semantic["evaluator_version"],
        "func_id": semantic["func_id"],
        "source_revision": semantic["source_revision"],
        "run_id": semantic["run_id"],
        "observation_id": item_id,
        "observation_type": observation_type,
        "observation_profile": observation_profile,
        "status": "pending",
        "input_paths": input_paths,
        "expected_claim_ids": expected_claim_ids,
        "reviewed_claim_ids": [],
        "claim_reviews": [
            {
                "claim_id": claim_id,
                "status": "pending",
                "local_outcome": "NOT_VERIFIABLE",
                "reviewed_units": [],
                "unit_reviews": [],
                "criterion_ids": [],
                "evidence_ids": [],
                "defect_keys": [],
                "reason": "待评价人逐Claim填写",
            }
            for claim_id in expected_claim_ids
        ],
        "completed_checks": [],
        "observations": [],
        "open_questions": [],
        "notes": [],
    }
    if feat_id is not None:
        document["feat_id"] = feat_id
    return document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize a staged NEXT-007 semantic evaluation run"
    )
    parser.add_argument("--func-id", required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--evaluation-mode", choices=("golden", "automated"), default="golden"
    )
    parser.add_argument("--source-revision")
    parser.add_argument("--evaluator-version", default=DEFAULT_EVALUATOR_VERSION)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    run_dir = args.run_dir.resolve()
    if _output_is_forbidden(run_dir):
        print("ERROR: automatic Skill output may not be written under evaluation/reviews", file=sys.stderr)
        return 2
    if run_dir.exists() and any(run_dir.iterdir()):
        print(f"ERROR: staged run directory must be empty: {run_dir}", file=sys.stderr)
        return 2
    input_dir = args.input_dir.resolve()
    try:
        semantic = create_semantic_template(
            args.func_id,
            input_dir,
            args.run_id,
            args.evaluator_version,
            source_revision=args.source_revision,
            allow_non_pilot=args.evaluation_mode == "automated",
        )
        context = load_object(input_dir / "function-context.json")
        static_result = load_object(input_dir / "static-result.json")
        evidence_manifest = load_object(input_dir / "evidence-manifest.json")
        entries = [
            entry
            for entry in context.get("feature_registry_entries", [])
            if isinstance(entry, dict) and str(entry.get("status", "")).lower() != "deprecated"
        ]
        if not entries:
            raise ValueError("function-context.json has no non-Deprecated Feature entries")
        shard_entries = {
            item.get("name"): item
            for item in evidence_manifest.get("shards", [])
            if isinstance(item, dict)
        }
        findings = static_result.get("findings")
        if not isinstance(findings, list):
            raise ValueError("static-result.json must contain a findings list")
        design_path_value = context.get("design_path")
        if not isinstance(design_path_value, str) or not design_path_value:
            raise ValueError("function-context.json has no design_path")
        design_path = _repo_path(design_path_value)
        design_shard_entry = shard_entries.get("design")
        if not isinstance(design_shard_entry, dict):
            raise ValueError("evidence-manifest.json has no design shard")
        design_shard_path = input_dir / "evidence" / str(design_shard_entry.get("path", ""))
        design_claim_ids = _claim_ids(load_object(design_shard_path), design_shard_path)
    except (LookupError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    run_dir.mkdir(parents=True, exist_ok=True)
    observations_dir = run_dir / "observations"
    slices_dir = run_dir / "slices"
    observations_dir.mkdir()
    slices_dir.mkdir()

    try:
        output_contract_path = run_dir / "output-contract.json"
        write_object(
            output_contract_path,
            staged_output_contract(
                source_revision=str(semantic["source_revision"]),
                evaluator_version=str(semantic["evaluator_version"]),
            ),
        )
        artifacts = [
            _artifact(input_dir / "function-context.json", "function_context"),
            _artifact(input_dir / "static-result.json", "static_result"),
            _artifact(input_dir / "evidence-manifest.json", "evidence_manifest"),
            _artifact(input_dir / "report.md", "navigation_report"),
            _artifact(EVALUATION_ROOT / "rubric.yaml", "rubric"),
            _artifact(EVALUATION_ROOT / "complexity_rules.yaml", "complexity_rules"),
            _artifact(EVALUATION_ROOT / "design_completeness_rules.yaml", "design_rules"),
            _artifact(design_path, "design"),
            _artifact(design_shard_path, "design_evidence_shard"),
            _artifact(output_contract_path, "staged_output_contract"),
        ]
        items: list[dict[str, Any]] = []
        feature_ids: list[str] = []
        static_index: dict[str, Any] = {
            "schema_version": STAGED_SCHEMA_VERSION,
            "func_id": semantic["func_id"],
            "source_revision": semantic["source_revision"],
            "total_findings": len(findings),
            "features": {},
        }
        for entry in entries:
            feat_id = str(entry.get("id", ""))
            spec_value = entry.get("spec")
            shard_entry = shard_entries.get(feat_id)
            if not feat_id or not isinstance(spec_value, str) or not spec_value:
                raise ValueError(f"invalid Feature Registry entry: {entry}")
            if not isinstance(shard_entry, dict):
                raise ValueError(f"evidence-manifest.json has no shard for {feat_id}")
            shard_path = input_dir / "evidence" / str(shard_entry.get("path", ""))
            spec_path = _repo_path(f"specs/{spec_value}")
            shard_document = load_object(shard_path)
            claim_ids = _claim_ids(shard_document, shard_path)
            feature_findings = [item for item in findings if item.get("feat_id") == feat_id]
            static_slice_path = slices_dir / f"static-{feat_id}.json"
            write_object(
                static_slice_path,
                {
                    "schema_version": STAGED_SCHEMA_VERSION,
                    "func_id": semantic["func_id"],
                    "source_revision": semantic["source_revision"],
                    "feat_id": feat_id,
                    "findings": feature_findings,
                },
            )
            static_index["features"][feat_id] = _static_summary(
                feature_findings, static_slice_path
            )
            artifacts.extend(
                (
                    _artifact(spec_path, f"feature_spec:{feat_id}"),
                    _artifact(shard_path, f"evidence_shard:{feat_id}"),
                )
            )
            item_id = f"feature:{feat_id}"
            output_path = observations_dir / f"{feat_id}.json"
            input_resources = [
                _input_resource(
                    input_dir / "function-context.json", "semantic_input",
                    citable=False,
                ),
                _input_resource(spec_path, "frozen_evidence", citable=True),
                _input_resource(shard_path, "semantic_input", citable=False),
                *[
                    _input_resource(path, "source_scope", citable=False)
                    for path in _source_scope_paths(
                        shard_document, findings=feature_findings
                    )
                ],
                _input_resource(static_slice_path, "semantic_input", citable=False),
                _input_resource(output_contract_path, "machine_contract", citable=False),
            ]
            input_paths = [resource["path"] for resource in input_resources]
            item = {
                "id": item_id,
                "type": "feature",
                "observation_profile": "feature",
                "feat_id": feat_id,
                "status": "pending",
                "input_paths": input_paths,
                "input_resources": input_resources,
                "output_path": str(output_path),
                "expected_claim_ids": claim_ids,
                "required_checks": FEATURE_REQUIRED_CHECKS,
            }
            items.append(item)
            feature_ids.append(feat_id)
            write_object(
                output_path,
                _observation_template(
                    semantic=semantic,
                    item_id=item_id,
                    observation_type="feature",
                    feat_id=feat_id,
                    input_paths=input_paths,
                    expected_claim_ids=claim_ids,
                    required_checks=FEATURE_REQUIRED_CHECKS,
                    observation_profile="feature",
                ),
            )

        global_findings = [item for item in findings if item.get("feat_id") not in feature_ids]
        global_slice_path = slices_dir / "static-function-global.json"
        write_object(
            global_slice_path,
            {
                "schema_version": STAGED_SCHEMA_VERSION,
                "func_id": semantic["func_id"],
                "source_revision": semantic["source_revision"],
                "findings": global_findings,
            },
        )
        static_index["function_global"] = _static_summary(global_findings, global_slice_path)
        static_index_path = slices_dir / "static-index.json"
        write_object(static_index_path, static_index)
        design_document = load_object(design_shard_path)

        global_item_id = "function-global"
        global_output = observations_dir / "function-global.json"
        global_resources = [
            _input_resource(
                input_dir / "function-context.json", "semantic_input",
                citable=False,
            ),
            _input_resource(design_path, "frozen_evidence", citable=True),
            _input_resource(design_shard_path, "semantic_input", citable=False),
            *[
                _input_resource(
                    _repo_path(f"specs/{entry.get('spec')}"),
                    "cross_feature_context",
                    citable=True,
                )
                for entry in entries
                if isinstance(entry.get("spec"), str) and entry.get("spec")
            ],
            *[
                _input_resource(path, "source_scope", citable=False)
                for path in _source_scope_paths(
                    design_document, findings=global_findings
                )
            ],
            _input_resource(static_index_path, "semantic_input", citable=False),
            _input_resource(global_slice_path, "semantic_input", citable=False),
            _input_resource(
                EVALUATION_ROOT / "rubric.yaml", "evaluation_rule", citable=True,
            ),
            _input_resource(
                EVALUATION_ROOT / "design_completeness_rules.yaml",
                "evaluation_rule", citable=True,
            ),
            _input_resource(output_contract_path, "machine_contract", citable=False),
        ]
        global_inputs = [resource["path"] for resource in global_resources]
        items.append(
            {
                "id": global_item_id,
                "type": "function_global",
                "observation_profile": "function_global",
                "status": "pending",
                "input_paths": global_inputs,
                "input_resources": global_resources,
                "output_path": str(global_output),
                "expected_claim_ids": design_claim_ids,
                "required_checks": FUNCTION_REQUIRED_CHECKS,
            }
        )
        write_object(
            global_output,
            _observation_template(
                semantic=semantic,
                item_id=global_item_id,
                observation_type="function_global",
                feat_id=None,
                input_paths=global_inputs,
                expected_claim_ids=design_claim_ids,
                required_checks=FUNCTION_REQUIRED_CHECKS,
                observation_profile="function_global",
            ),
        )

        work_items = {
            "schema_version": STAGED_SCHEMA_VERSION,
            "evaluator_version": semantic["evaluator_version"],
            "func_id": semantic["func_id"],
            "source_revision": semantic["source_revision"],
            "run_id": semantic["run_id"],
            "phase_order": [
                "feature_observations",
                "function_global",
                "aggregation",
                "final_validation",
            ],
            "items": items,
        }
        run_state = {
            "schema_version": STAGED_SCHEMA_VERSION,
            "evaluator_version": semantic["evaluator_version"],
            "func_id": semantic["func_id"],
            "source_revision": semantic["source_revision"],
            "run_id": semantic["run_id"],
            "input_dir": str(input_dir),
            "run_dir": str(run_dir),
            "current_phase": "feature_observations",
            "validated_work_items": [],
            "aggregation_validated": False,
            "semantic_validated": False,
            "input_artifacts": artifacts,
        }
        aggregation = {
            "schema_version": STAGED_SCHEMA_VERSION,
            "evaluator_version": semantic["evaluator_version"],
            "func_id": semantic["func_id"],
            "source_revision": semantic["source_revision"],
            "run_id": semantic["run_id"],
            "status": "pending",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": False,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": [
                {
                    "criterion_id": criterion_id,
                    "content_status": "PENDING",
                    "evidence_status": "PENDING",
                    "conflict_scope": "PENDING",
                    "reason": "待评价人按Criterion outcome policy填写",
                }
                for criterion_id in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": semantic["criterion_results"],
            "notes": [],
        }
        write_object(run_dir / "semantic-template.json", semantic)
        write_object(run_dir / "aggregation.json", aggregation)
        write_object(run_dir / "work-items.json", work_items)
        write_object(run_dir / "run-state.json", run_state)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        f"staged run initialized: func_id={semantic['func_id']} features={len(feature_ids)} "
        f"claims={sum(len(item['expected_claim_ids']) for item in items)} run_dir={run_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
