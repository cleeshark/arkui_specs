"""Deterministically summarize repeated semantic evaluation stability."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

from spec_eval.protocol_validator import validate_protocol
from spec_eval.score import (
    AGGREGATOR_PROTOCOL_VERSION,
    AGGREGATOR_VERSION,
    ScoreInputError,
    build_score_result,
)


STABILITY_SCHEMA_VERSION = 1
STABILITY_VERSION = "spec-eval-stability@0.1.0"
MINIMUM_RUN_COUNT = 3
CONSENSUS_NUMERATOR = 2
CONSENSUS_DENOMINATOR = 3
OUTLIER_MIN_DEVIATION_RATE = Decimal("0.2")
OUTLIER_MIN_DEVIATION_GAP = 2
RAW_RANGE_OBSERVATION_LIMIT = Decimal(10)
_CONCLUSION_ORDER = {
    value: index
    for index, value in enumerate(
        (
            "SUPPORTED",
            "PARTIALLY_SUPPORTED",
            "CONTRADICTED",
            "MISSING",
            "NOT_APPLICABLE",
            "NOT_VERIFIABLE",
        )
    )
}


class StabilityInputError(ValueError):
    """Raised when repeated semantic results cannot be compared safely."""


def _number(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # Decimal raises input-specific subclasses
        raise StabilityInputError(f"expected a numeric value, got {value!r}") from exc


def _rounded(value: Decimal, precision: int = 2) -> Decimal:
    quantum = Decimal(1).scaleb(-precision)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def _json_number(value: Decimal) -> int | float:
    normalized = value.normalize()
    return int(normalized) if normalized == normalized.to_integral() else float(normalized)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StabilityInputError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StabilityInputError(f"{path}: expected a JSON object")
    return value


def _hash_file(path: Path) -> str:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise StabilityInputError(f"cannot hash input {path}: {exc}") from exc
    return f"sha256:{digest}"


def _criterion_ids(rubric: dict[str, Any]) -> list[str]:
    return [
        criterion["id"]
        for dimension in rubric["dimensions"]
        for criterion in dimension["criteria"]
    ]


def _validate_artifact(item: Any, label: str) -> dict[str, str]:
    if not isinstance(item, dict):
        raise StabilityInputError(f"input_artifacts.{label} must be an object")
    path = item.get("path")
    content_hash = item.get("content_hash")
    if not isinstance(path, str) or not path:
        raise StabilityInputError(f"input_artifacts.{label}.path must be non-empty")
    if not isinstance(content_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", content_hash):
        raise StabilityInputError(
            f"input_artifacts.{label}.content_hash must be a sha256 digest"
        )
    return {"path": path, "content_hash": content_hash}


def _validate_artifacts(
    input_artifacts: dict[str, Any], run_ids: set[str]
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "static_result": _validate_artifact(
            input_artifacts.get("static_result"), "static_result"
        ),
        "evidence_manifest": _validate_artifact(
            input_artifacts.get("evidence_manifest"), "evidence_manifest"
        ),
    }
    semantic_artifacts = input_artifacts.get("semantic_results")
    if not isinstance(semantic_artifacts, list):
        raise StabilityInputError("input_artifacts.semantic_results must be a list")
    normalized: list[dict[str, str]] = []
    for item in semantic_artifacts:
        if not isinstance(item, dict):
            raise StabilityInputError("semantic result artifact must be an object")
        run_id = item.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise StabilityInputError("semantic result artifact run_id must be non-empty")
        artifact = _validate_artifact(item, f"semantic_results.{run_id}")
        normalized.append({"run_id": run_id, **artifact})
    actual_ids = {item["run_id"] for item in normalized}
    if actual_ids != run_ids or len(normalized) != len(actual_ids):
        raise StabilityInputError(
            f"semantic artifact run set mismatch: expected={sorted(run_ids)} "
            f"actual={sorted(actual_ids)}"
        )
    result["semantic_results"] = sorted(normalized, key=lambda item: item["run_id"])
    return result


def _validate_run_set(
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    semantic_results: list[dict[str, Any]],
    selected_run_id: str,
) -> tuple[str, str, str, list[dict[str, Any]]]:
    if len(semantic_results) < MINIMUM_RUN_COUNT:
        raise StabilityInputError(
            f"at least {MINIMUM_RUN_COUNT} semantic results are required for stability analysis"
        )
    run_ids = [item.get("run_id") for item in semantic_results]
    if any(not isinstance(run_id, str) or not run_id for run_id in run_ids):
        raise StabilityInputError("every semantic result must have a non-empty run_id")
    if len(set(run_ids)) != len(run_ids):
        raise StabilityInputError(f"semantic run_id values must be unique: {run_ids}")
    if selected_run_id not in run_ids:
        raise StabilityInputError(
            f"selected_run_id {selected_run_id!r} is not present in semantic results"
        )
    base_identity = {
        "func_id": static_result.get("func_id"),
        "source_revision": static_result.get("source_revision"),
    }
    for source, value in (("evidence", evidence_manifest),):
        for key, expected in base_identity.items():
            if value.get(key) != expected:
                raise StabilityInputError(
                    f"{key} mismatch: static={expected!r} {source}={value.get(key)!r}"
                )
    version_fields = (
        "rubric_version",
        "complexity_rules_version",
        "evaluator_protocol_version",
        "evaluator_version",
    )
    expected_versions = {key: semantic_results[0].get(key) for key in version_fields}
    for semantic in semantic_results:
        for key, expected in base_identity.items():
            if semantic.get(key) != expected:
                raise StabilityInputError(
                    f"{key} mismatch in {semantic.get('run_id')}: "
                    f"expected={expected!r} actual={semantic.get(key)!r}"
                )
        for key, expected in expected_versions.items():
            if semantic.get(key) != expected:
                raise StabilityInputError(
                    f"{key} mismatch in {semantic.get('run_id')}: "
                    f"expected={expected!r} actual={semantic.get(key)!r}"
                )
    return (
        str(base_identity["func_id"]),
        str(base_identity["source_revision"]),
        str(expected_versions["evaluator_version"]),
        sorted(semantic_results, key=lambda item: item["run_id"]),
    )


def _score_runs(
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    semantic_results: list[dict[str, Any]],
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    schemas_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    runs: list[dict[str, Any]] = []
    conclusions: dict[str, dict[str, str]] = {}
    for semantic in semantic_results:
        run_id = semantic["run_id"]
        try:
            score = build_score_result(
                static_result=static_result,
                evidence_manifest=evidence_manifest,
                semantic_result=semantic,
                rubric=rubric,
                complexity_rules=complexity_rules,
                schemas_root=schemas_root,
            )
        except ScoreInputError as exc:
            raise StabilityInputError(f"cannot score semantic run {run_id}: {exc}") from exc
        run_conclusions = {
            item["criterion_id"]: item["conclusion"]
            for item in semantic["criterion_results"]
        }
        conclusions[run_id] = run_conclusions
        runs.append(
            {
                "run_id": run_id,
                "evaluator_version": semantic["evaluator_version"],
                "raw_score": score["raw_score"],
                "published_score": score["published_score"],
                "confidence": score["confidence"]["score"],
                "gate": score["gate"]["effective"],
                "admission": score["admission"]["status"],
            }
        )
    return runs, conclusions


def _criterion_consensus(
    criterion_ids: list[str],
    run_ids: list[str],
    conclusions: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    result: list[dict[str, Any]] = []
    consensus_by_id: dict[str, str] = {}
    for criterion_id in criterion_ids:
        run_values = {run_id: conclusions[run_id][criterion_id] for run_id in run_ids}
        counts = Counter(run_values.values())
        ordered_counts = sorted(
            counts.items(), key=lambda item: (-item[1], _CONCLUSION_ORDER[item[0]])
        )
        top_conclusion, top_count = ordered_counts[0]
        has_consensus = (
            top_count * CONSENSUS_DENOMINATOR
            >= len(run_ids) * CONSENSUS_NUMERATOR
        )
        consensus_conclusion = top_conclusion if has_consensus else None
        if consensus_conclusion is not None:
            consensus_by_id[criterion_id] = consensus_conclusion
        result.append(
            {
                "criterion_id": criterion_id,
                "status": "CONSENSUS" if has_consensus else "NO_CONSENSUS",
                "consensus_conclusion": consensus_conclusion,
                "consensus_count": top_count if has_consensus else 0,
                "consensus_ratio": _json_number(
                    _rounded(Decimal(top_count) / Decimal(len(run_ids)), 6)
                ),
                "conclusion_counts": {
                    conclusion: counts[conclusion]
                    for conclusion in sorted(counts, key=lambda value: _CONCLUSION_ORDER[value])
                },
                "run_conclusions": run_values,
                "dissenting_run_ids": sorted(
                    run_id
                    for run_id, conclusion in run_values.items()
                    if consensus_conclusion is not None
                    and conclusion != consensus_conclusion
                ),
            }
        )
    return result, consensus_by_id


def _peer_agreement(
    run_id: str,
    run_ids: list[str],
    criterion_ids: list[str],
    conclusions: dict[str, dict[str, str]],
) -> Decimal:
    peers = [peer for peer in run_ids if peer != run_id]
    total = len(peers) * len(criterion_ids)
    matching = sum(
        conclusions[run_id][criterion_id] == conclusions[peer][criterion_id]
        for peer in peers
        for criterion_id in criterion_ids
    )
    return Decimal(matching) / Decimal(total) if total else Decimal(1)


def _annotate_runs(
    runs: list[dict[str, Any]],
    criterion_ids: list[str],
    conclusions: dict[str, dict[str, str]],
    consensus_by_id: dict[str, str],
    artifacts: dict[str, Any],
) -> list[str]:
    run_ids = [item["run_id"] for item in runs]
    artifact_by_run = {
        item["run_id"]: item for item in artifacts["semantic_results"]
    }
    deviations: dict[str, int] = {}
    for run in runs:
        run_id = run["run_id"]
        deviations[run_id] = sum(
            conclusions[run_id][criterion_id] != consensus
            for criterion_id, consensus in consensus_by_id.items()
        )
        run["criterion_deviation_count"] = deviations[run_id]
        run["criterion_deviation_rate"] = _json_number(
            _rounded(Decimal(deviations[run_id]) / Decimal(len(criterion_ids)), 6)
        )
        run["average_peer_agreement"] = _json_number(
            _rounded(_peer_agreement(run_id, run_ids, criterion_ids, conclusions), 6)
        )
        run["semantic_result"] = {
            "path": artifact_by_run[run_id]["path"],
            "content_hash": artifact_by_run[run_id]["content_hash"],
        }
        run["outlier_status"] = "INLIER"
        run["outlier_reasons"] = []

    ordered = sorted(deviations.items(), key=lambda item: (-item[1], item[0]))
    highest_run, highest_count = ordered[0]
    second_count = ordered[1][1]
    unique_highest = sum(count == highest_count for count in deviations.values()) == 1
    deviation_rate = Decimal(highest_count) / Decimal(len(criterion_ids))
    gap = highest_count - second_count
    outlier_ids: list[str] = []
    if (
        unique_highest
        and deviation_rate >= OUTLIER_MIN_DEVIATION_RATE
        and gap >= OUTLIER_MIN_DEVIATION_GAP
    ):
        outlier_ids.append(highest_run)
        outlier = next(item for item in runs if item["run_id"] == highest_run)
        outlier["outlier_status"] = "OUTLIER"
        outlier["outlier_reasons"] = [
            "unique highest Criterion consensus deviation: "
            f"{highest_count}/{len(criterion_ids)}, gap to next run={gap}"
        ]
    return outlier_ids


def _score_statistics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    values = [_number(item["raw_score"]) for item in runs]
    count = Decimal(len(values))
    mean = sum(values, Decimal(0)) / count
    variance = sum(((value - mean) ** 2 for value in values), Decimal(0)) / count
    population_stddev = variance.sqrt()
    minimum = min(values)
    maximum = max(values)
    return {
        "count": len(values),
        "minimum": _json_number(minimum),
        "maximum": _json_number(maximum),
        "range": _json_number(maximum - minimum),
        "mean": _json_number(_rounded(mean)),
        "population_stddev": _json_number(_rounded(population_stddev)),
    }


def build_stability_result(
    *,
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    semantic_results: list[dict[str, Any]],
    selected_run_id: str,
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    schemas_root: Path,
    input_artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Build repeated-run metadata without modifying the selected run score."""

    func_id, source_revision, evaluator_version, ordered_semantic = _validate_run_set(
        static_result, evidence_manifest, semantic_results, selected_run_id
    )
    run_ids = [item["run_id"] for item in ordered_semantic]
    artifacts = _validate_artifacts(input_artifacts, set(run_ids))
    runs, conclusions = _score_runs(
        static_result,
        evidence_manifest,
        ordered_semantic,
        rubric,
        complexity_rules,
        schemas_root,
    )
    criterion_ids = _criterion_ids(rubric)
    criterion_consensus, consensus_by_id = _criterion_consensus(
        criterion_ids, run_ids, conclusions
    )
    outlier_ids = _annotate_runs(
        runs, criterion_ids, conclusions, consensus_by_id, artifacts
    )
    statistics = _score_statistics(runs)
    consensus_count = len(consensus_by_id)
    selected = next(item for item in runs if item["run_id"] == selected_run_id)
    return {
        "schema_version": STABILITY_SCHEMA_VERSION,
        "stability_version": STABILITY_VERSION,
        "func_id": func_id,
        "source_revision": source_revision,
        "versions": {
            "static_tool_version": static_result["tool_version"],
            "static_rule_version": static_result["rule_version"],
            "evaluator_protocol_version": ordered_semantic[0]["evaluator_protocol_version"],
            "evaluator_version": evaluator_version,
            "rubric_version": ordered_semantic[0]["rubric_version"],
            "complexity_rules_version": ordered_semantic[0]["complexity_rules_version"],
            "aggregator_protocol_version": AGGREGATOR_PROTOCOL_VERSION,
            "aggregator_version": AGGREGATOR_VERSION,
        },
        "policy": {
            "minimum_run_count": MINIMUM_RUN_COUNT,
            "criterion_consensus_ratio": _json_number(
                _rounded(
                    Decimal(CONSENSUS_NUMERATOR) / Decimal(CONSENSUS_DENOMINATOR), 6
                )
            ),
            "outlier_min_deviation_rate": _json_number(OUTLIER_MIN_DEVIATION_RATE),
            "outlier_min_deviation_gap": OUTLIER_MIN_DEVIATION_GAP,
            "raw_range_observation_limit": _json_number(RAW_RANGE_OBSERVATION_LIMIT),
        },
        "input_artifacts": artifacts,
        "score_statistics": statistics,
        "criterion_consensus": criterion_consensus,
        "consensus_summary": {
            "criterion_count": len(criterion_ids),
            "consensus_count": consensus_count,
            "no_consensus_count": len(criterion_ids) - consensus_count,
            "consensus_rate": _json_number(
                _rounded(Decimal(consensus_count) / Decimal(len(criterion_ids)), 6)
            ),
        },
        "runs": runs,
        "outlier_run_ids": outlier_ids,
        "selected_run": {
            "run_id": selected_run_id,
            "selection_method": "explicit",
            "raw_score": selected["raw_score"],
            "published_score": selected["published_score"],
            "gate": selected["gate"],
            "semantic_result": selected["semantic_result"],
            "consensus_does_not_override_selection": True,
        },
        "assessment": {
            "raw_range_within_observation_limit": _number(statistics["range"])
            <= RAW_RANGE_OBSERVATION_LIMIT,
            "has_outlier": bool(outlier_ids),
            "has_no_consensus_criteria": consensus_count != len(criterion_ids),
        },
    }


def build_stability_result_from_paths(
    *,
    static_result_path: Path,
    evidence_manifest_path: Path,
    semantic_result_paths: list[Path],
    selected_run_id: str,
    evaluation_root: Path,
) -> dict[str, Any]:
    rubric, complexity, errors = validate_protocol(evaluation_root)
    if errors:
        raise StabilityInputError(
            "evaluation protocol is invalid:\n" + "\n".join(f"- {item}" for item in errors)
        )
    static_result = _load_json_object(static_result_path)
    evidence_manifest = _load_json_object(evidence_manifest_path)
    semantic_results = [_load_json_object(path) for path in semantic_result_paths]
    semantic_artifacts = [
        {
            "run_id": semantic["run_id"],
            "path": path.as_posix(),
            "content_hash": _hash_file(path),
        }
        for path, semantic in zip(semantic_result_paths, semantic_results)
    ]
    return build_stability_result(
        static_result=static_result,
        evidence_manifest=evidence_manifest,
        semantic_results=semantic_results,
        selected_run_id=selected_run_id,
        rubric=rubric,
        complexity_rules=complexity,
        schemas_root=evaluation_root / "schemas",
        input_artifacts={
            "static_result": {
                "path": static_result_path.as_posix(),
                "content_hash": _hash_file(static_result_path),
            },
            "evidence_manifest": {
                "path": evidence_manifest_path.as_posix(),
                "content_hash": _hash_file(evidence_manifest_path),
            },
            "semantic_results": semantic_artifacts,
        },
    )


def write_stability_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
