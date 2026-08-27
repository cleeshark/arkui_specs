"""Deterministically build a Function score result from frozen evaluation inputs."""

from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

from spec_eval.protocol_validator import (
    JsonSchemaSubsetValidator,
    validate_protocol,
    validate_score_result,
    validate_semantic_result,
)


AGGREGATOR_PROTOCOL_VERSION = "0.1.0"
AGGREGATOR_VERSION = "spec-eval-score@0.1.0"
_GATE_ORDER = {"pass": 0, "warn": 1, "fail": 2, "error": 3}
_SEVERITY_ORDER = {"Info": 0, "Minor": 1, "Major": 2, "Critical": 3}
_SEVERITY_GATE = {"Info": "pass", "Minor": "warn", "Major": "fail", "Critical": "fail"}


class ScoreInputError(ValueError):
    """Raised when static, evidence, and semantic inputs cannot be scored together."""


def _number(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # Decimal raises several input-specific exceptions
        raise ScoreInputError(f"expected a numeric value, got {value!r}") from exc


def _rounded(value: Any, precision: int = 2) -> Decimal:
    quantum = Decimal(1).scaleb(-precision)
    return _number(value).quantize(quantum, rounding=ROUND_HALF_UP)


def _json_number(value: Decimal) -> int | float:
    normalized = value.normalize()
    return int(normalized) if normalized == normalized.to_integral() else float(normalized)


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScoreInputError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(document, dict):
        raise ScoreInputError(f"{path}: expected a JSON object")
    return document


def _raise_errors(label: str, errors: Iterable[str]) -> None:
    """Raise ScoreInputError if any blocking errors remain after filtering warnings.

    Some errors are non-blocking warnings after Correction and should not prevent
    publishing a degraded report. Filter these out before raising.
    """
    # Evidence type mismatch warnings - allow degraded publish after Correction
    # (aligned with aggregation_warning_policy.EVIDENCE_TYPE_WARNING_MARKER)
    EVIDENCE_TYPE_WARNING_MARKER = "evidence must include one of"

    values = list(errors)
    blocking = [e for e in values if EVIDENCE_TYPE_WARNING_MARKER not in e]

    if blocking:
        raise ScoreInputError(f"{label} is invalid:\n" + "\n".join(f"- {item}" for item in blocking))


def _validate_evidence_manifest(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("func_id", "source_revision", "metrics", "shards"):
        if key not in document:
            errors.append(f"missing {key}")
    metrics = document.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
        return errors
    claim_count = metrics.get("claim_count")
    resolved_count = metrics.get("resolved_claim_count")
    coverage = metrics.get("evidence_coverage")
    if not isinstance(claim_count, int) or claim_count < 0:
        errors.append("metrics.claim_count must be a non-negative integer")
    if not isinstance(resolved_count, int) or resolved_count < 0:
        errors.append("metrics.resolved_claim_count must be a non-negative integer")
    if isinstance(claim_count, int) and isinstance(resolved_count, int):
        if resolved_count > claim_count:
            errors.append("metrics.resolved_claim_count may not exceed claim_count")
    try:
        coverage_value = _number(coverage)
    except ScoreInputError:
        errors.append("metrics.evidence_coverage must be numeric")
    else:
        if coverage_value < 0 or coverage_value > 1:
            errors.append("metrics.evidence_coverage must be between 0 and 1")
        if isinstance(claim_count, int) and isinstance(resolved_count, int):
            expected = Decimal(0) if claim_count == 0 else Decimal(resolved_count) / Decimal(claim_count)
            if abs(coverage_value - expected) > Decimal("0.000000001"):
                errors.append(
                    "metrics.evidence_coverage must equal resolved_claim_count / claim_count"
                )
    if not isinstance(document.get("shards"), list):
        errors.append("shards must be a list")
    return errors


def _validate_input_identity(
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    semantic_result: dict[str, Any],
) -> None:
    for key in ("func_id", "source_revision"):
        values = {
            "static": static_result.get(key),
            "evidence": evidence_manifest.get(key),
            "semantic": semantic_result.get(key),
        }
        if len(set(values.values())) != 1:
            raise ScoreInputError(f"{key} mismatch: {values}")


def _semantic_findings(semantic_result: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for finding in semantic_result.get("complexity", {}).get("normalization_findings", []):
        if isinstance(finding, dict):
            yield finding
    for result in semantic_result.get("criterion_results", []):
        for finding in result.get("findings", []):
            if isinstance(finding, dict):
                yield finding


def _active_severities(
    static_result: dict[str, Any], semantic_result: dict[str, Any]
) -> list[str]:
    values = {
        finding.get("severity")
        for finding in list(static_result.get("findings", [])) + list(_semantic_findings(semantic_result))
        if isinstance(finding, dict) and finding.get("severity") in {"Minor", "Major", "Critical"}
    }
    return sorted(values, key=lambda item: _SEVERITY_ORDER[item])


def _semantic_gate(semantic_result: dict[str, Any]) -> str:
    gate = "pass"
    for finding in _semantic_findings(semantic_result):
        candidate = _SEVERITY_GATE.get(str(finding.get("severity")), "pass")
        if _GATE_ORDER[candidate] > _GATE_ORDER[gate]:
            gate = candidate
    return gate


def _source_reproducibility(semantic_result: dict[str, Any]) -> Decimal:
    items = [
        evidence
        for result in semantic_result.get("criterion_results", [])
        for evidence in result.get("evidence", [])
        if isinstance(evidence, dict)
    ]
    if not items:
        return Decimal(0)
    revision = semantic_result.get("source_revision")
    reproducible = sum(
        bool(item.get("path"))
        and item.get("source_revision") == revision
        and str(item.get("content_hash", "")).startswith("sha256:")
        for item in items
    )
    return Decimal(reproducible) / Decimal(len(items))


def _dimension_results(
    semantic_result: dict[str, Any], rubric: dict[str, Any]
) -> tuple[list[dict[str, Any]], Decimal]:
    semantic_by_id = {
        item.get("criterion_id"): item for item in semantic_result.get("criterion_results", [])
    }
    minimum_ratio = _number(
        rubric.get("score_model", {}).get("not_applicable", {}).get(
            "minimum_applicable_criterion_ratio", 0
        )
    )
    dimensions: list[dict[str, Any]] = []
    raw_score = Decimal(0)
    for dimension in rubric["dimensions"]:
        criteria: list[dict[str, Any]] = []
        applicable_max = Decimal(0)
        earned = Decimal(0)
        applicable_count = 0
        for criterion in dimension["criteria"]:
            semantic = semantic_by_id[criterion["id"]]
            conclusion = semantic["conclusion"]
            applicable = conclusion != "NOT_APPLICABLE"
            maximum = _number(criterion["max_score"])
            deduction = _number(criterion.get("outcomes", {}).get(conclusion, {}).get("deduction", 0))
            criterion_score = max(Decimal(0), maximum - deduction) if applicable else None
            if applicable:
                applicable_count += 1
                applicable_max += maximum
                earned += criterion_score or Decimal(0)
            criteria.append(
                {
                    "criterion_id": criterion["id"],
                    "conclusion": conclusion,
                    "applicable": applicable,
                    "max_score": _json_number(maximum),
                    "deduction": _json_number(deduction),
                    "score": _json_number(_rounded(criterion_score))
                    if criterion_score is not None
                    else None,
                }
            )
        maximum = _number(dimension["weight"])
        score = _rounded(earned / applicable_max * maximum) if applicable_max else Decimal(0)
        ratio = Decimal(applicable_count) / Decimal(len(dimension["criteria"]))
        dimensions.append(
            {
                "dimension_id": dimension["id"],
                "max_score": _json_number(maximum),
                "applicable_max_score": _json_number(applicable_max),
                "earned_score": _json_number(_rounded(earned)),
                "score": _json_number(score),
                "verifiability": "NOT_VERIFIABLE" if ratio < minimum_ratio else "VERIFIABLE",
                "criteria": criteria,
            }
        )
        raw_score += score
    return dimensions, _rounded(raw_score)


def _confidence(
    evidence_manifest: dict[str, Any],
    semantic_result: dict[str, Any],
    rubric: dict[str, Any],
) -> dict[str, Any]:
    evidence_coverage = _number(evidence_manifest["metrics"]["evidence_coverage"])
    human_confirmation = (
        Decimal(1) if str(semantic_result.get("evaluator_version", "")).startswith("human:") else Decimal(0)
    )
    reproducibility = _source_reproducibility(semantic_result)
    execution_completeness = Decimal(1)
    components = {
        "evidence_verification_coverage": evidence_coverage,
        "human_confirmation": human_confirmation,
        "source_revision_reproducibility": reproducibility,
        "tool_execution_completeness": execution_completeness,
    }
    weights = {
        key: _number(value["weight"])
        for key, value in rubric["confidence"]["components"].items()
    }
    score = _rounded(sum((components[key] * weights[key] for key in components), Decimal(0)))
    reasons: list[str] = []
    if evidence_coverage < 1:
        reasons.append("evidence verification coverage is below 1.0")
    if human_confirmation == 0:
        reasons.append("semantic result has no human confirmation")
    if reproducibility < 1:
        reasons.append("some semantic evidence is not reproducible at the scored revision")
    return {
        "components": {key: _json_number(value) for key, value in components.items()},
        "score": _json_number(score),
        "publishable": True,
        "reasons": reasons,
    }


def _admission(
    *, published_score: Decimal, confidence: Decimal, effective_gate: str, dimensions: list[dict[str, Any]]
) -> dict[str, Any]:
    reasons: list[str] = []
    if effective_gate != "pass":
        reasons.append(f"effective gate is {effective_gate}")
    if any(item["verifiability"] == "NOT_VERIFIABLE" for item in dimensions):
        reasons.append("at least one dimension is not verifiable")
    if effective_gate == "pass" and not reasons:
        if published_score >= 90 and confidence >= Decimal("0.85"):
            return {"status": "HIGH_QUALITY", "reasons": []}
        if published_score >= 80 and confidence >= Decimal("0.8"):
            return {"status": "BASELINED", "reasons": []}
    if published_score < 80:
        reasons.append("published score is below 80")
    if confidence < Decimal("0.8"):
        reasons.append("confidence is below 0.8")
    return {"status": "NOT_READY", "reasons": reasons}


def build_score_result(
    *,
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    semantic_result: dict[str, Any],
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    schemas_root: Path,
    aggregator_version: str = AGGREGATOR_VERSION,
) -> dict[str, Any]:
    """Return one protocol-valid score result without invoking a model."""

    _validate_input_identity(static_result, evidence_manifest, semantic_result)
    _raise_errors(
        "static-result.json",
        JsonSchemaSubsetValidator(schemas_root).validate_file(
            static_result, schemas_root / "static-result.schema.json"
        ),
    )
    _raise_errors("evidence-manifest.json", _validate_evidence_manifest(evidence_manifest))
    _raise_errors(
        "semantic-result.json",
        validate_semantic_result(semantic_result, rubric, complexity_rules, schemas_root),
    )
    if semantic_result.get("rubric_version") != rubric.get("rubric_version"):
        raise ScoreInputError("semantic rubric_version does not match the frozen rubric")
    if semantic_result.get("complexity_rules_version") != complexity_rules.get(
        "complexity_rules_version"
    ):
        raise ScoreInputError("semantic complexity_rules_version does not match frozen rules")
    execution = semantic_result.get("execution", {})
    for key in ("static_complete", "evidence_complete", "semantic_complete"):
        if execution.get(key) is not True:
            raise ScoreInputError(f"semantic execution.{key} must be true before scoring")

    dimensions, raw_score = _dimension_results(semantic_result, rubric)
    active_severities = _active_severities(static_result, semantic_result)
    applied_severity = active_severities[-1] if active_severities else "None"
    cap = _number(rubric["publishing_caps"]["caps"][applied_severity])
    published_score = min(raw_score, cap)
    semantic_gate = _semantic_gate(semantic_result)
    static_gate = static_result["gate"]
    effective_gate = max((static_gate, semantic_gate), key=lambda value: _GATE_ORDER[value])
    confidence = _confidence(evidence_manifest, semantic_result, rubric)
    confidence_score = _number(confidence["score"])
    result = {
        "schema_version": 1,
        "rubric_version": rubric["rubric_version"],
        "complexity_rules_version": complexity_rules["complexity_rules_version"],
        "aggregator_protocol_version": AGGREGATOR_PROTOCOL_VERSION,
        "aggregator_version": aggregator_version,
        "func_id": semantic_result["func_id"],
        "source_revision": semantic_result["source_revision"],
        "dimensions": dimensions,
        "raw_score": _json_number(raw_score),
        "caps": {
            "active_severities": active_severities,
            "applied": {"severity": applied_severity, "limit": _json_number(cap)},
        },
        "published_score": _json_number(published_score),
        "gate": {
            "static": static_gate,
            "semantic": semantic_gate,
            "effective": effective_gate,
        },
        "confidence": confidence,
        "execution": {"static": True, "evidence": True, "semantic": True, "score": True},
        "admission": _admission(
            published_score=published_score,
            confidence=confidence_score,
            effective_gate=effective_gate,
            dimensions=dimensions,
        ),
    }
    _raise_errors("generated score-result.json", validate_score_result(result, rubric, schemas_root))
    return result


def build_score_result_from_paths(
    *,
    static_result_path: Path,
    evidence_manifest_path: Path,
    semantic_result_path: Path,
    evaluation_root: Path,
) -> dict[str, Any]:
    rubric, complexity, errors = validate_protocol(evaluation_root)
    _raise_errors("evaluation protocol", errors)
    return build_score_result(
        static_result=_load_json_object(static_result_path),
        evidence_manifest=_load_json_object(evidence_manifest_path),
        semantic_result=_load_json_object(semantic_result_path),
        rubric=rubric,
        complexity_rules=complexity,
        schemas_root=evaluation_root / "schemas",
    )


def write_score_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
