"""Typed validator for evaluator protocol 0.2.0 (design L3).

Validates the *published* documents produced by :mod:`.normalize` plus the
frozen aggregation context. Structure, ID patterns, hashes and ordering are
owned by the normalizer and are not re-checked here; this layer enforces the
semantic rules the structured-output schema cannot express, and reports every
failure as a :class:`~spec_eval.kernel.errors.TypedError` with a registered
code and closed repairability.

The degenerate-output quality gate (issue #22 successor) is folded in as
``QUALITY_*`` codes instead of a separate retry mode.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable

from . import contracts as K
from .errors import MODEL_CORRECTION, SERVICE_NORMALIZATION, TypedError
from .normalize import DEFECT_KEY, OUTCOME_POLICY_BASIS_CRITERIA

# Quality gate thresholds (carried over from the 0.1.18 degenerate detector).
_MIN_CLAIMS = 10
_HIGH_NV_RATIO = 0.60
_EVIDENCE_COLLAPSE_RATIO = 0.80
_MIN_INSPECTION_COVERAGE = 0.20
_REPETITIVE_TEXT_RATIO = 0.50


def _err(code: str, path: str, **kwargs: Any) -> TypedError:
    return TypedError(code=code, path=path, **kwargs)


def _rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _is_low_information(text: Any) -> bool:
    if not isinstance(text, str):
        return True
    normalized = re.sub(r"[\W_]+", "", text, flags=re.UNICODE).casefold()
    return normalized in K.LOW_INFORMATION_REVIEW_TEXT


def validate_observation_document(
    document: dict[str, Any],
    *,
    valid_criterion_ids: Iterable[str],
    required_checks: Iterable[str] | None = None,
) -> list[TypedError]:
    """Validate one published observation document against protocol 0.2.0.

    ``required_checks`` comes from the work item; when omitted the document's
    own field is used (CLI checks on published documents).
    """
    errors: list[TypedError] = []
    label = "observation"
    expected_claims = _strings(document.get("expected_claim_ids"))
    required_checks = (
        list(required_checks)
        if required_checks is not None
        else _strings(document.get("required_checks"))
    )
    known_criteria = set(valid_criterion_ids)

    claim_rows = _rows(document.get("claim_reviews"))
    claim_ids = [
        row.get("claim_id") for row in claim_rows
        if isinstance(row.get("claim_id"), str)
    ]
    if claim_ids != expected_claims:
        missing = sorted(set(expected_claims) - set(claim_ids))
        extra = sorted(set(claim_ids) - set(expected_claims))
        errors.append(_err(
            "CLAIM_SET_MISMATCH", f"{label}.claim_reviews",
            entity_type="document",
            expected=f"exactly {expected_claims}",
            actual=f"missing={missing} extra={extra} pending_rows="
            f"{sum(1 for row in claim_rows if row.get('status') != 'complete')}",
        ))
        return errors

    observations = _rows(document.get("observations"))
    defined_evidence_ids = {
        evidence.get("evidence_id")
        for entry in observations
        for evidence in _rows(entry.get("evidence"))
        if isinstance(evidence.get("evidence_id"), str)
    }
    inspection_evidence_ids = {
        evidence.get("evidence_id")
        for entry in observations
        for evidence in _rows(entry.get("evidence"))
        if evidence.get("type") == K.REVIEW_RECORD
        and isinstance(evidence.get("evidence_id"), str)
    }
    defined_defects: dict[str, str] = {}
    observed_claims: set[str] = set()

    for obs_index, entry in enumerate(observations):
        obs_label = f"{label}.observations[{obs_index}]"
        outcome = entry.get("local_outcome")
        observation_claim_ids = _strings(entry.get("claim_ids"))
        if expected_claims and not observation_claim_ids:
            errors.append(_err(
                "OBSERVATION_CLAIM_IDS_EMPTY", f"{obs_label}.claim_ids",
                entity_type="observation", entity_id=str(entry.get("observation_id")),
                expected="at least one expected claim ID",
            ))
        evidence_count = len(_rows(entry.get("evidence")))
        minimum = K.OBSERVATION_EVIDENCE_MIN_ITEMS.get(outcome)
        if minimum is not None and evidence_count < minimum:
            errors.append(_err(
                "EVIDENCE_CARDINALITY_VIOLATED", f"{obs_label}.evidence",
                entity_type="observation", entity_id=str(entry.get("observation_id")),
                expected=f">= {minimum} evidence items for {outcome}",
                actual=f"{evidence_count}",
            ))
        if outcome == K.NOT_VERIFIABLE and not (
            {e.get("evidence_id") for e in _rows(entry.get("evidence"))}
            & inspection_evidence_ids
        ):
            errors.append(_err(
                "NV_INSPECTION_EVIDENCE_MISSING", f"{obs_label}.evidence",
                entity_type="observation", entity_id=str(entry.get("observation_id")),
                expected="review_record inspection evidence",
            ))
        unknown_criteria = sorted(
            set(_strings(entry.get("criterion_ids"))) - known_criteria
        )
        if unknown_criteria:
            errors.append(_err(
                "CRITERION_UNKNOWN", f"{obs_label}.criterion_ids",
                entity_type="observation", entity_id=str(entry.get("observation_id")),
                actual=str(unknown_criteria),
            ))
        for claim_id in observation_claim_ids:
            if claim_id not in expected_claims:
                errors.append(_err(
                    "OBSERVATION_CLAIM_UNEXPECTED", f"{obs_label}.claim_ids",
                    entity_type="claim", entity_id=claim_id,
                ))
            else:
                observed_claims.add(claim_id)
        defect_key = entry.get("defect_key")
        primary = entry.get("primary_criterion_id")
        if outcome in {"CONFLICT", "MISSING"}:
            if not isinstance(defect_key, str) or not DEFECT_KEY.fullmatch(defect_key):
                errors.append(_err(
                    "DEFECT_KEYS_INVALID", f"{obs_label}.defect_key",
                    entity_type="observation", entity_id=str(entry.get("observation_id")),
                    expected="snake_case defect key for adverse outcome",
                ))
            elif not isinstance(primary, str):
                errors.append(_err(
                    "DEFECT_KEYS_INVALID", f"{obs_label}.primary_criterion_id",
                    entity_type="defect", entity_id=defect_key,
                    expected="primary criterion for adverse outcome",
                ))
            else:
                conflict = defined_defects.get(defect_key)
                if conflict is not None and conflict != primary:
                    # Same defect observed from different criterion dimensions;
                    # aggregation selects the final primary (issue #53).
                    pass
                else:
                    defined_defects[defect_key] = primary
        elif defect_key is not None or primary is not None:
            errors.append(_err(
                "DEFECT_KEYS_INVALID", f"{obs_label}.defect_key",
                entity_type="observation", entity_id=str(entry.get("observation_id")),
                expected="defect_key and primary_criterion_id must be null for non-adverse outcome",
                actual=f"defect_key={defect_key}, primary={primary}",
                repairability=SERVICE_NORMALIZATION,
            ))

    if expected_claims and observed_claims != set(expected_claims):
        errors.append(_err(
            "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE", f"{label}.observations.claim_ids",
            entity_type="document",
            expected=f"exactly {expected_claims}",
            actual=f"missing={sorted(set(expected_claims) - observed_claims)} "
            f"extra={sorted(observed_claims - set(expected_claims))}",
        ))

    mapped_checks: set[str] = set()
    for entry in observations:
        mapped_checks.update(_strings(entry.get("check_ids")))
    if mapped_checks != set(required_checks):
        errors.append(_err(
            "CHECK_COVERAGE_INCOMPLETE", f"{label}.observations.check_ids",
            entity_type="document",
            expected=f"exactly {sorted(required_checks)}",
            actual=f"missing={sorted(set(required_checks) - mapped_checks)} "
            f"extra={sorted(mapped_checks - set(required_checks))}",
        ))

    for index, row in enumerate(claim_rows):
        claim_id = str(row.get("claim_id"))
        row_label = f"{label}.claim_reviews[{index}]"
        outcome = row.get("local_outcome")
        if outcome not in K.LOCAL_OUTCOMES:
            errors.append(_err(
                "CLAIM_OUTCOME_INVALID", f"{row_label}.local_outcome",
                entity_type="claim", entity_id=claim_id, actual=str(outcome),
            ))
        unknown = sorted(set(_strings(row.get("evidence_ids"))) - defined_evidence_ids)
        if unknown:
            errors.append(_err(
                "EVIDENCE_KEY_UNKNOWN", f"{row_label}.evidence_ids",
                entity_type="claim", entity_id=claim_id, actual=str(unknown),
            ))
        reason = row.get("reason")
        if not isinstance(reason, str) or not reason.strip() or K.PLACEHOLDER_TEXT in reason:
            errors.append(_err(
                "REASON_PLACEHOLDER", f"{row_label}.reason",
                entity_type="claim", entity_id=claim_id,
            ))
        elif _is_low_information(reason):
            errors.append(_err(
                "REASON_LOW_INFORMATION", f"{row_label}.reason",
                entity_type="claim", entity_id=claim_id,
            ))
        gap = row.get("verification_gap")
        if outcome == K.NOT_VERIFIABLE:
            if not isinstance(gap, dict):
                errors.append(_err(
                    "GAP_MISSING_FOR_NV", f"{row_label}.verification_gap",
                    entity_type="claim", entity_id=claim_id,
                    expected="checked_scope, missing_evidence, consequence",
                ))
            else:
                for field, value in gap.items():
                    if field not in K.VERIFICATION_GAP_FIELDS:
                        continue
                    if isinstance(value, list) and not value:
                        errors.append(_err(
                            "GAP_FIELD_INSUFFICIENT",
                            f"{row_label}.verification_gap.{field}",
                            entity_type="claim", entity_id=claim_id,
                            expected="at least one entry",
                        ))
                    elif isinstance(value, str) and not value.strip():
                        errors.append(_err(
                            "GAP_FIELD_INSUFFICIENT",
                            f"{row_label}.verification_gap.{field}",
                            entity_type="claim", entity_id=claim_id,
                        ))
            if not (set(_strings(row.get("evidence_ids"))) & inspection_evidence_ids):
                errors.append(_err(
                    "NV_INSPECTION_EVIDENCE_MISSING", f"{row_label}.evidence_ids",
                    entity_type="claim", entity_id=claim_id,
                    expected="review_record inspection evidence",
                ))
        elif gap is not None:
            errors.append(_err(
                "GAP_UNEXPECTED_FOR_NON_NV", f"{row_label}.verification_gap",
                entity_type="claim", entity_id=claim_id,
                repairability=SERVICE_NORMALIZATION,
            ))
        defect_keys = _strings(row.get("defect_keys"))
        if outcome not in {"CONFLICT", "MISSING"} and defect_keys:
            errors.append(_err(
                "DEFECT_KEYS_INVALID", f"{row_label}.defect_keys",
                entity_type="claim", entity_id=claim_id,
                expected="empty for non-adverse outcome",
            ))
        for defect_key in defect_keys:
            if defect_key not in defined_defects:
                errors.append(_err(
                    "DEFECT_KEY_UNDEFINED", f"{row_label}.defect_keys",
                    entity_type="defect", entity_id=defect_key,
                    expected="defined by a CONFLICT/MISSING observation",
                ))

        units = _rows(row.get("unit_reviews"))
        reviewed_units = _strings(row.get("reviewed_units"))
        unit_ids = [
            unit.get("unit_id") for unit in units
            if isinstance(unit.get("unit_id"), str)
        ]
        if not units:
            errors.append(_err(
                "UNIT_ROW_INVALID", f"{row_label}.unit_reviews",
                entity_type="claim", entity_id=claim_id,
                expected="at least one atomic unit review",
            ))
        if not reviewed_units:
            errors.append(_err(
                "UNIT_ROW_INVALID", f"{row_label}.reviewed_units",
                entity_type="claim", entity_id=claim_id,
                expected="non-empty ordered unit IDs",
            ))
        elif unit_ids != reviewed_units:
            errors.append(_err(
                "UNIT_ROW_INVALID", f"{row_label}.unit_reviews",
                entity_type="claim", entity_id=claim_id,
                expected="unit IDs exactly match reviewed_units in order",
                actual=str(unit_ids),
            ))
        unit_outcomes = [unit.get("local_outcome") for unit in units]
        if outcome in {"CONFLICT", "MISSING", K.NOT_VERIFIABLE}:
            if outcome not in unit_outcomes:
                errors.append(_err(
                    "UNIT_CLAIM_OUTCOME_CONFLICT", f"{row_label}.unit_reviews",
                    entity_type="claim", entity_id=claim_id,
                    expected=f"at least one unit carries {outcome}",
                ))
        elif outcome == "SUPPORTED" and any(o != "SUPPORTED" for o in unit_outcomes):
            errors.append(_err(
                "UNIT_CLAIM_OUTCOME_CONFLICT", f"{row_label}.unit_reviews",
                entity_type="claim", entity_id=claim_id,
                expected="all units supported",
            ))
        elif outcome == "NOT_APPLICABLE" and any(
            o != "NOT_APPLICABLE" for o in unit_outcomes
        ):
            errors.append(_err(
                "UNIT_CLAIM_OUTCOME_CONFLICT", f"{row_label}.unit_reviews",
                entity_type="claim", entity_id=claim_id,
                expected="all units inapplicable",
            ))
        for unit_index, unit in enumerate(units):
            unit_label = f"{row_label}.unit_reviews[{unit_index}]"
            unit_id = str(unit.get("unit_id"))
            unknown = sorted(
                set(_strings(unit.get("evidence_ids"))) - defined_evidence_ids
            )
            if unknown:
                errors.append(_err(
                    "EVIDENCE_KEY_UNKNOWN", f"{unit_label}.evidence_ids",
                    entity_type="unit", entity_id=unit_id, actual=str(unknown),
                ))
            fact = unit.get("fact")
            if not isinstance(fact, str) or not fact.strip() or K.PLACEHOLDER_TEXT in fact:
                errors.append(_err(
                    "REASON_PLACEHOLDER", f"{unit_label}.fact",
                    entity_type="unit", entity_id=unit_id,
                ))
            elif _is_low_information(fact):
                errors.append(_err(
                    "REASON_LOW_INFORMATION", f"{unit_label}.fact",
                    entity_type="unit", entity_id=unit_id,
                ))
            unit_outcome = unit.get("local_outcome")
            unit_gap = unit.get("verification_gap")
            if unit_outcome == K.NOT_VERIFIABLE:
                if not isinstance(unit_gap, dict):
                    errors.append(_err(
                        "GAP_MISSING_FOR_NV", f"{unit_label}.verification_gap",
                        entity_type="unit", entity_id=unit_id,
                    ))
                if not (
                    set(_strings(unit.get("evidence_ids"))) & inspection_evidence_ids
                ):
                    errors.append(_err(
                        "NV_INSPECTION_EVIDENCE_MISSING",
                        f"{unit_label}.evidence_ids", entity_type="unit",
                        entity_id=unit_id,
                    ))

    errors.extend(_quality_gate(claim_rows, observations))
    return errors


def _quality_gate(
    claim_rows: list[dict[str, Any]], observations: list[dict[str, Any]]
) -> list[TypedError]:
    """Fold the issue #22 degenerate detector into typed QUALITY_* errors."""
    nv_claims = [row for row in claim_rows if row.get("local_outcome") == K.NOT_VERIFIABLE]
    claim_count = len(claim_rows)
    nv_count = len(nv_claims)
    inspection_ids = {
        evidence.get("evidence_id")
        for entry in observations
        for evidence in _rows(entry.get("evidence"))
        if evidence.get("type") == K.REVIEW_RECORD
        and isinstance(evidence.get("evidence_id"), str)
    }
    inspected = sum(
        bool(set(_strings(row.get("evidence_ids"))) & inspection_ids)
        for row in nv_claims
    )
    texts = [
        text for text in (
            *[row.get("reason") for row in nv_claims],
            *[
                unit.get("fact")
                for row in nv_claims
                for unit in _rows(row.get("unit_reviews"))
                if unit.get("local_outcome") == K.NOT_VERIFIABLE
            ],
        ) if isinstance(text, str) and text.strip()
    ]
    normalized = [
        re.sub(r"[\W_]+", "", text, flags=re.UNICODE).casefold()
        for text in texts
    ]
    normalized = [value for value in normalized if value]
    repeated_ratio = (
        max(Counter(normalized).values()) / len(normalized) if normalized else 0.0
    )
    decisive = sum(
        row.get("local_outcome") in {"SUPPORTED", "CONFLICT"} for row in claim_rows
    )
    nv_ratio = nv_count / claim_count if claim_count else 0.0
    coverage = inspected / nv_count if nv_count else 0.0

    quality: list[TypedError] = []
    high_nv = claim_count >= _MIN_CLAIMS and nv_ratio >= _HIGH_NV_RATIO
    evidence_collapse = (
        coverage < _MIN_INSPECTION_COVERAGE if nv_count else False
    )
    corroborating = (
        (repeated_ratio >= _REPETITIVE_TEXT_RATIO)
        or (claim_count > 0 and decisive == 0)
        or (claim_count >= _MIN_CLAIMS and len(observations) <= max(5, claim_count // 10))
    )
    if high_nv and evidence_collapse and corroborating:
        if repeated_ratio >= _REPETITIVE_TEXT_RATIO:
            quality.append(_err(
                "QUALITY_DUPLICATE_TEXT", "$.claim_reviews",
                entity_type="document",
                actual=f"repeated_review_text_ratio={repeated_ratio:.4f}",
            ))
        if claim_count >= _MIN_CLAIMS and len(observations) <= max(5, claim_count // 10):
            quality.append(_err(
                "QUALITY_OBSERVATION_DENSITY", "$.observations",
                entity_type="document",
                actual=f"observation_count={len(observations)} claims={claim_count}",
            ))
        if not quality:
            quality.append(_err(
                "QUALITY_HIGH_NV_RATIO", "$.claim_reviews",
                entity_type="document",
                actual=f"nv_ratio={nv_ratio:.4f} inspection_coverage={coverage:.4f}",
            ))
    return quality


def validate_aggregation_document(
    document: dict[str, Any],
    *,
    criterion_order: list[str],
    aggregation_context: dict[str, Any] | None = None,
) -> list[TypedError]:
    """Validate one published aggregation document against protocol 0.2.0."""
    errors: list[TypedError] = []
    label = "aggregation"
    results = _rows(document.get("criterion_results"))
    actual_order = [
        row.get("criterion_id") for row in results
        if isinstance(row.get("criterion_id"), str)
    ]
    if actual_order != criterion_order:
        errors.append(_err(
            "CRITERION_SET_MISMATCH", f"{label}.criterion_results",
            entity_type="document", expected=str(criterion_order),
            actual=str(actual_order),
        ))
    if document.get("cross_feat_contracts_reviewed") is not True:
        errors.append(_err(
            "CROSS_FEAT_NOT_REVIEWED", f"{label}.cross_feat_contracts_reviewed",
            entity_type="document", expected="true",
        ))

    findings_by_id: dict[str, dict[str, Any]] = {}
    contradicted_criteria: list[str] = []
    results_by_id = {row.get("criterion_id"): row for row in results}
    for index, result in enumerate(results):
        row_label = f"{label}.criterion_results[{index}]"
        criterion_id = str(result.get("criterion_id"))
        conclusion = result.get("conclusion")
        findings = _rows(result.get("findings"))
        if conclusion in K.FINDING_REQUIRED_CONCLUSIONS and not findings:
            errors.append(_err(
                "FINDING_CARDINALITY_VIOLATED", f"{row_label}.findings",
                entity_type="criterion", entity_id=criterion_id,
                expected=f"at least one finding for {conclusion}",
            ))
        if conclusion in K.FINDING_FORBIDDEN_CONCLUSIONS and findings:
            errors.append(_err(
                "FINDING_CARDINALITY_VIOLATED", f"{row_label}.findings",
                entity_type="criterion", entity_id=criterion_id,
                expected=f"no findings for {conclusion}",
            ))
        if conclusion == "CONTRADICTED":
            contradicted_criteria.append(criterion_id)
        if K.PLACEHOLDER_TEXT in str(result.get("reason", "")):
            errors.append(_err(
                "REASON_PLACEHOLDER", f"{row_label}.reason",
                entity_type="criterion", entity_id=criterion_id,
            ))
        criterion_evidence = {
            evidence.get("evidence_id")
            for evidence in _rows(result.get("evidence"))
            if isinstance(evidence.get("evidence_id"), str)
        }
        for finding_index, finding in enumerate(findings):
            finding_label = f"{row_label}.findings[{finding_index}]"
            missing = sorted(
                set(_strings(finding.get("evidence_ids"))) - criterion_evidence
            )
            if missing:
                errors.append(_err(
                    "FINDING_EVIDENCE_UNKNOWN", f"{finding_label}.evidence_ids",
                    entity_type="finding",
                    entity_id=str(finding.get("finding_id") or finding.get("key")),
                    expected=f"subset of Criterion evidence IDs {sorted(criterion_evidence)}",
                    actual=str(missing),
                ))
            if (
                conclusion in K.FINDING_REQUIRED_CONCLUSIONS
                and not _strings(finding.get("evidence_ids"))
            ):
                errors.append(_err(
                    "FINDING_EVIDENCE_UNKNOWN", f"{finding_label}.evidence_ids",
                    entity_type="finding",
                    entity_id=str(finding.get("finding_id") or finding.get("key")),
                    expected="at least one evidence ID",
                ))
            finding_id = finding.get("finding_id")
            if isinstance(finding_id, str) and finding_id:
                if finding_id in findings_by_id:
                    errors.append(_err(
                        "FINDING_MULTI_OWNED", f"{finding_label}.finding_id",
                        entity_type="finding", entity_id=finding_id,
                        expected="unique finding identity", actual="duplicate",
                    ))
                else:
                    findings_by_id[finding_id] = finding

    if aggregation_context is not None:
        mappings_by_id = {
            row.get("criterion_id"): row
            for row in _rows(aggregation_context.get("criterion_mappings"))
        }
        for result in results:
            criterion_id = str(result.get("criterion_id"))
            conclusion = result.get("conclusion")
            mapping = mappings_by_id.get(criterion_id)
            if not isinstance(mapping, dict):
                continue
            constraints = mapping.get("constraints", {})
            mapped_claim_ids = set(_strings(mapping.get("mapped_claim_ids")))
            unmapped = sorted(
                claim_id for claim_id in _strings(result.get("claim_ids"))
                if claim_id not in mapped_claim_ids
            )
            if unmapped:
                errors.append(_err(
                    "MAPPING_CLAIM_UNMAPPED",
                    f"{label}.criterion_results[{criterion_id}].claim_ids",
                    entity_type="criterion", entity_id=criterion_id,
                    actual=str(unmapped),
                ))
            required = constraints.get("required_conclusion_when_no_adverse")
            forbidden = constraints.get("forbidden_conclusions", [])
            if required and conclusion != required:
                errors.append(_err(
                    "MAPPING_NV_REQUIRED",
                    f"{label}.criterion_results[{criterion_id}]",
                    entity_type="criterion", entity_id=criterion_id,
                    expected=required, actual=str(conclusion),
                ))
            elif conclusion in forbidden:
                errors.append(_err(
                    "MAPPING_CONCLUSION_FORBIDDEN",
                    f"{label}.criterion_results[{criterion_id}]",
                    entity_type="criterion", entity_id=criterion_id,
                    expected=f"conclusion not in forbidden_conclusions {forbidden}",
                    actual=str(conclusion),
                ))
            # Check allow_not_applicable constraint (issue #50)
            if conclusion == "NOT_APPLICABLE" and not mapping.get("allow_not_applicable"):
                errors.append(_err(
                    "NOT_APPLICABLE_FORBIDDEN",
                    f"{label}.criterion_results[{criterion_id}].conclusion",
                    entity_type="criterion", entity_id=criterion_id,
                    expected="allow_not_applicable is false; use SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, MISSING, or NOT_VERIFIABLE",
                    actual="NOT_APPLICABLE",
                ))
            # Check severity floor constraint (issue #50)
            outcomes = mapping.get("outcomes", {})
            if isinstance(outcomes, dict) and conclusion in outcomes:
                outcome_constraint = outcomes.get(conclusion, {})
                expected_severity = outcome_constraint.get("severity_floor")
                if expected_severity:
                    severity_rank = {"Info": 0, "Minor": 1, "Major": 2, "Critical": 3}
                    findings = _rows(result.get("findings"))
                    for finding in findings:
                        finding_severity = finding.get("severity")
                        if severity_rank.get(finding_severity, -1) < severity_rank.get(expected_severity, 0):
                            errors.append(_err(
                                "SEVERITY_BELOW_FLOOR",
                                f"{label}.criterion_results[{criterion_id}].findings[].severity",
                                entity_type="finding",
                                entity_id=str(finding.get("finding_id") or finding.get("key")),
                                expected=f"severity >= {expected_severity} for conclusion {conclusion}",
                                actual=str(finding_severity),
                            ))
            # Check required_evidence_types constraint (issue #52)
            required_evidence_types = mapping.get("required_evidence_types", [])
            if (
                required_evidence_types
                and conclusion in {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "MISSING"}
            ):
                criterion_evidence = _rows(result.get("evidence"))
                if not criterion_evidence:
                    errors.append(_err(
                        "EVIDENCE_REQUIRED_MISSING",
                        f"{label}.criterion_results[{criterion_id}].evidence",
                        entity_type="criterion", entity_id=criterion_id,
                        expected=f"at least one evidence item for {conclusion}",
                        actual="empty",
                    ))
                else:
                    actual_types = {ev.get("type") for ev in criterion_evidence if isinstance(ev.get("type"), str)}
                    if set(required_evidence_types).isdisjoint(actual_types):
                        errors.append(_err(
                            "EVIDENCE_TYPE_MISSING",
                            f"{label}.criterion_results[{criterion_id}].evidence",
                            entity_type="criterion", entity_id=criterion_id,
                            expected=f"at least one evidence of type {required_evidence_types}",
                            actual=str(sorted(actual_types)),
                        ))

    policy_bases = _rows(document.get("outcome_policy_bases"))
    policy_order = [
        row.get("criterion_id") for row in policy_bases
        if isinstance(row.get("criterion_id"), str)
    ]
    if policy_order != list(OUTCOME_POLICY_BASIS_CRITERIA):
        errors.append(_err(
            "POLICY_BASIS_INVALID", f"{label}.outcome_policy_bases",
            entity_type="document", expected=str(list(OUTCOME_POLICY_BASIS_CRITERIA)),
            actual=str(policy_order),
        ))
    for index, basis in enumerate(policy_bases):
        row_label = f"{label}.outcome_policy_bases[{index}]"
        criterion_id = str(basis.get("criterion_id"))
        content_status = basis.get("content_status")
        evidence_status = basis.get("evidence_status")
        conflict_scope = basis.get("conflict_scope")
        if (
            content_status not in K.POLICY_CONTENT_STATUSES
            or evidence_status not in K.POLICY_EVIDENCE_STATUSES
            or conflict_scope not in K.POLICY_CONFLICT_SCOPES
        ):
            errors.append(_err(
                "POLICY_BASIS_INVALID", row_label,
                entity_type="policy_basis", entity_id=criterion_id,
            ))
            continue
        reason = basis.get("reason")
        if not isinstance(reason, str) or not reason.strip() or K.PLACEHOLDER_TEXT in reason:
            errors.append(_err(
                "REASON_PLACEHOLDER", f"{row_label}.reason",
                entity_type="policy_basis", entity_id=criterion_id,
            ))
        expected_conclusion = K.expected_policy_conclusion(
            content_status, evidence_status, conflict_scope,
        )
        if expected_conclusion is None:
            actual_conclusion = results_by_id.get(criterion_id, {}).get("conclusion")
            errors.append(_err(
                "POLICY_BASIS_INVALID", row_label,
                entity_type="policy_basis", entity_id=criterion_id,
                expected=(
                    f"policy_basis status fields are inconsistent (mixed NOT_APPLICABLE); "
                    f"either set ALL THREE to NOT_APPLICABLE, or set NONE to NOT_APPLICABLE. "
                    f"Do NOT change the criterion conclusion"
                    f" (currently {actual_conclusion})" if actual_conclusion else ""
                ),
                actual=f"content_status={content_status}, evidence_status={evidence_status}, conflict_scope={conflict_scope}",
            ))
            continue
        if criterion_id not in results_by_id:
            continue
        actual_conclusion = results_by_id[criterion_id].get("conclusion")
        if actual_conclusion != expected_conclusion:
            errors.append(_err(
                "POLICY_BASIS_INVALID", row_label,
                entity_type="policy_basis", entity_id=criterion_id,
                expected=(
                    f"conclusion={expected_conclusion} derived from "
                    f"content_status={content_status}, "
                    f"evidence_status={evidence_status}, "
                    f"conflict_scope={conflict_scope}; "
                    "correct the policy basis to change the conclusion"
                ),
                actual=str(actual_conclusion),
            ))

    ownership = _rows(document.get("defect_ownership"))
    finding_owners: dict[str, list[str]] = {}
    for index, record in enumerate(ownership):
        row_label = f"{label}.defect_ownership[{index}]"
        defect_key = str(record.get("defect_key", ""))
        if not DEFECT_KEY.fullmatch(defect_key):
            errors.append(_err(
                "DEFECT_KEYS_INVALID", f"{row_label}.defect_key",
                entity_type="defect", entity_id=defect_key,
            ))
            continue
        # Check defect_key against aggregation-context whitelist (issue #51)
        if aggregation_context is not None:
            valid_defect_keys = set(aggregation_context.get("valid_defect_keys", []))
            if valid_defect_keys and defect_key not in valid_defect_keys:
                errors.append(_err(
                    "DEFECT_KEY_UNDEFINED", f"{row_label}.defect_key",
                    entity_type="defect", entity_id=defect_key,
                    expected=f"one of valid_defect_keys: {sorted(valid_defect_keys)}",
                    actual=defect_key,
                ))
        primary = record.get("primary_criterion_id")
        if primary not in actual_order:
            errors.append(_err(
                "CRITERION_UNKNOWN", f"{row_label}.primary_criterion_id",
                entity_type="defect", entity_id=defect_key, actual=str(primary),
            ))
        finding_ids = _strings(record.get("finding_ids"))
        if not finding_ids:
            errors.append(_err(
                "FINDING_OWNER_UNKNOWN", f"{row_label}.finding_ids",
                entity_type="defect", entity_id=defect_key,
                expected="at least one finding",
            ))
        for finding_id in finding_ids:
            finding_owners.setdefault(finding_id, []).append(defect_key)
            finding = findings_by_id.get(finding_id)
            if finding is None:
                errors.append(_err(
                    "FINDING_OWNER_UNKNOWN", f"{row_label}.finding_ids",
                    entity_type="finding", entity_id=finding_id,
                ))
            elif finding.get("criterion_id") == primary and finding.get("severity") == "CRITICAL":
                pass  # critical finding owned by its primary criterion is legal
    for finding_id, owners in finding_owners.items():
        if len(owners) > 1:
            errors.append(_err(
                "FINDING_MULTI_OWNED", f"{label}.defect_ownership",
                entity_type="finding", entity_id=finding_id,
                expected="exactly one owner", actual=str(owners),
            ))
    for finding_id, finding in findings_by_id.items():
        if finding.get("severity") == "CRITICAL" and finding_id not in finding_owners:
            errors.append(_err(
                "FINDING_OWNER_UNKNOWN", f"{label}.defect_ownership",
                entity_type="finding", entity_id=finding_id,
                expected="CRITICAL findings must be owned",
            ))

    contradictions = _rows(document.get("contradiction_bases"))
    contradiction_criteria: list[str] = []
    for index, basis in enumerate(contradictions):
        row_label = f"{label}.contradiction_bases[{index}]"
        for field in ("statement", "left_assertion", "right_assertion"):
            if not str(basis.get(field, "")).strip():
                errors.append(_err(
                    "CONTRADICTION_BASIS_INVALID", f"{row_label}.{field}",
                    entity_type="contradiction_basis", entity_id=str(index),
                ))
        if not _strings(basis.get("affected_feat_ids")):
            errors.append(_err(
                "CONTRADICTION_BASIS_INVALID", f"{row_label}.affected_feat_ids",
                entity_type="contradiction_basis", entity_id=str(index),
            ))
        defect_key = basis.get("primary_defect_key")
        if not isinstance(defect_key, str) or defect_key not in finding_owners:
            errors.append(_err(
                "CONTRADICTION_BASIS_INVALID", f"{row_label}.primary_defect_key",
                entity_type="contradiction_basis", entity_id=str(index),
                actual=str(defect_key),
            ))
    contradiction_criteria = [
        str(basis.get("primary_criterion_id"))
        for basis in contradictions
    ]
    return errors
