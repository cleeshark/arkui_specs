"""Machine contracts injected into executor prompts (protocol 0.2.0).

Generated from :mod:`.contracts` — the prompt no longer hand-repeats field
rules. The contract tells the model exactly which judgment fields it owns,
which reference spaces are legal (expected claims/checks, evidence catalog),
and the few semantic rules the schema cannot express.
"""

from __future__ import annotations

from typing import Any, Iterable

from . import contracts as K


def _common() -> dict[str, Any]:
    return {
        "evaluation_protocol_version": K.EVALUATION_PROTOCOL_VERSION,
        "envelope_schema_version": K.ENVELOPE_SCHEMA_VERSION,
        "local_outcome_enum": list(K.LOCAL_OUTCOMES),
        "unit_facet_type_enum": list(K.UNIT_FACET_TYPES),
        "breadth_enum": list(K.BREADTHS),
        "evidence_type_enum": list(K.EVIDENCE_TYPES),
        "judgment_rules": [
            "Provide judgments only: outcomes, reasons/facts, evidence declarations "
            "and references, defect descriptions and NOT_VERIFIABLE gaps.",
            "Do not echo document identity, ordering, derived fields or hashes; the "
            "service owns them.",
            "verification_gap is required (non-null) exactly when local_outcome is "
            "NOT_VERIFIABLE, both at claim and unit level; null otherwise.",
            "Every NOT_VERIFIABLE observation, claim and unit must reference "
            "review_record inspection evidence.",
            "Reference evidence only with keys you declared in this payload or IDs "
            "listed in evidence_catalog; never invent EV- IDs.",
        ],
    }


def build_observation_machine_contract(
    *,
    expected_claim_ids: Iterable[str],
    required_checks: Iterable[str],
    valid_criterion_ids: Iterable[str],
    evidence_catalog: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Contract for one observation work item.

    ``evidence_catalog`` lists evidence already published in the candidate
    (stable EV- IDs with type/path/description) so a correction turn can
    reference prior evidence without re-declaring it.
    """
    claims = list(expected_claim_ids)
    checks = list(required_checks)
    return {
        **_common(),
        "payload_fields": list(K.OBSERVATION_JUDGMENT_FIELDS),
        "claim_judgment_fields": list(K.CLAIM_JUDGMENT_FIELDS),
        "unit_judgment_fields": list(K.UNIT_JUDGMENT_FIELDS),
        "verification_gap_fields": list(K.VERIFICATION_GAP_FIELDS),
        "evidence_declaration_fields": list(K.EVIDENCE_DECLARATION_FIELDS),
        "expected_claim_ids": claims,
        "required_checks": checks,
        "valid_criterion_ids": list(valid_criterion_ids),
        "coverage_rule": (
            "claim_reviews must contain exactly one judgment per expected_claim_ids "
            "entry; observations[].check_ids together must cover every required "
            "check exactly once."
        ),
        "defect_rule": (
            "defect_keys may only be non-empty for CONFLICT or MISSING claims; the "
            "keys must be defined as defects by a CONFLICT/MISSING observation."
        ),
        "evidence_cardinality": {
            "minimum_items_by_local_outcome": dict(
                K.OBSERVATION_EVIDENCE_MIN_ITEMS
            ),
        },
        "evidence_catalog": list(evidence_catalog),
    }


def build_aggregation_machine_contract(
    *,
    valid_criterion_ids: Iterable[str],
    aggregation_context_path: str | None = None,
) -> dict[str, Any]:
    """Contract for the aggregation work item."""
    return {
        **_common(),
        "payload_fields": list(K.AGGREGATION_JUDGMENT_FIELDS),
        "criterion_judgment_fields": list(K.CRITERION_JUDGMENT_FIELDS),
        "finding_judgment_fields": list(K.FINDING_JUDGMENT_FIELDS),
        "defect_ownership_fields": list(K.DEFECT_OWNERSHIP_FIELDS),
        "contradiction_basis_fields": list(K.CONTRADICTION_BASIS_FIELDS),
        "policy_basis_fields": list(K.POLICY_BASIS_FIELDS),
        "semantic_conclusion_enum": list(K.SEMANTIC_CONCLUSIONS),
        "applicability_enum": list(K.APPLICABILITY_VALUES),
        "finding_severity_enum": list(K.FINDING_SEVERITIES),
        "policy_content_status_enum": list(K.POLICY_CONTENT_STATUSES),
        "policy_evidence_status_enum": list(K.POLICY_EVIDENCE_STATUSES),
        "policy_conflict_scope_enum": list(K.POLICY_CONFLICT_SCOPES),
        "valid_criterion_ids": list(valid_criterion_ids),
        "aggregation_context_path": aggregation_context_path,
        "mapping_rule": (
            "aggregation-context.json (when provided) is authoritative for "
            "criterion scope and mapped unit outcomes; criterion_results[].claim_ids "
            "are citations only and may not narrow the mapped scope."
        ),
        "finding_cardinality_rule": (
            "every criterion whose conclusion is PARTIALLY_SUPPORTED, CONTRADICTED "
            "or MISSING must contain at least one evidence-backed finding; SUPPORTED "
            "and NOT_APPLICABLE criteria must contain none."
        ),
        "ownership_rule": (
            "findings link to defects through temporary keys; the service derives "
            "canonical finding IDs and secondary criterion sets. At most one finding "
            "may be CRITICAL and it must belong to the primary criterion."
        ),
    }
