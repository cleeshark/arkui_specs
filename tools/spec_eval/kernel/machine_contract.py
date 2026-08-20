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
    }


def _observation_judgment_rules() -> list[str]:
    return [
        "Provide judgments only: outcomes, reasons/facts, evidence declarations "
        "and references, defect descriptions and NOT_VERIFIABLE gaps.",
        "Do not echo document identity, ordering, derived fields or hashes; the "
        "service owns them.",
        "Declare every piece of evidence exactly once in the top-level "
        "evidence_declarations array with a unique local key (e1, e2, ...); "
        "claim, unit and observation rows reference declarations through "
        "evidence_refs. The service converts local keys to canonical EV- IDs "
        "at publish time; never emit EV- IDs yourself.",
        "verification_gap is required (non-null) exactly when local_outcome is "
        "NOT_VERIFIABLE, both at claim and unit level; null otherwise.",
        "Every NOT_VERIFIABLE observation, claim and unit must reference "
        "review_record inspection evidence.",
        "Every NOT_VERIFIABLE claim reason and unit fact must describe the "
        "gap; the structured verification_gap object (checked_scope, "
        "missing_evidence, consequence) is validated by the service.",
    ]


def build_observation_machine_contract(
    *,
    expected_claim_ids: Iterable[str],
    required_checks: Iterable[str],
    valid_criterion_ids: Iterable[str],
    evidence_catalog: Iterable[dict[str, Any]] = (),
    citable_input_paths: Iterable[str] = (),
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
        "judgment_rules": _observation_judgment_rules(),
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
            "check exactly once; when expected claims exist, every observation "
            "must reference at least one expected claim and their union must cover "
            "all expected_claim_ids."
        ),
        "defect_rule": (
            "defect_keys may only be non-empty for CONFLICT or MISSING claims; the "
            "keys must be defined as defects by a CONFLICT/MISSING observation. "
            "Every defect_key value must be lowercase and match the pattern "
            f"{K.DEFECT_KEY_PATTERN} (lowercase alphanumeric, dots, underscores "
            "and hyphens; e.g. 'missing.verification_assets', 'trace-rule-orphan')."
        ),
        "defect_ownership_rule": (
            "observations[].defect_key and observations[].primary_criterion_id are "
            "defect ownership fields. Set them ONLY when local_outcome is CONFLICT "
            "or MISSING. For SUPPORTED, NOT_VERIFIABLE, and NOT_APPLICABLE outcomes, "
            "both fields must be null (omitted or explicitly null)."
        ),
        "evidence_cardinality": {
            "minimum_items_by_local_outcome": dict(
                K.OBSERVATION_EVIDENCE_MIN_ITEMS
            ),
        },
        "evidence_path_policy": {
            "format": "canonical repository-relative POSIX path",
            "frozen_repository_namespaces": [
                "ace_engine (frameworks/..., adapter/..., interfaces/..., specs/...)",
                "sdk-js (interface/sdk-js/...)",
                "sdk_c (interface/sdk_c/...)",
            ],
            "citable_input_paths": list(citable_input_paths),
            "rules": [
                "An input resource with citable=false is semantic context only and "
                "must never be copied into evidence_declarations.",
                "Never declare an absolute path, a path containing '.' or '..', "
                "or a service job path such as evidence/... or runs/... .",
                "Source and SDK files discovered from frozen inputs may be cited "
                "using their canonical repository-relative path.",
            ],
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
        "judgment_rules": [
            "Provide aggregation judgments only; document identity, ordering, "
            "canonical evidence rows and finding IDs are service-owned.",
            "Read aggregation-context.json and use only the canonical EV- evidence "
            "IDs listed for each Criterion. Do not emit local evidence keys such as "
            "e1, do not declare evidence, and do not guess EV- IDs.",
            "criterion_results[].evidence_ids selects the inherited evidence attached "
            "to that Criterion; the service closes this parent set over every valid "
            "finding evidence reference, and every finding evidence_ids entry must "
            "be a subset.",
            "For the six outcome-policy criteria, content_status/evidence_status/"
            "conflict_scope are the semantic inputs; the service derives conclusion "
            "from the fixed policy precedence table. Do not try to repair a derived "
            "conclusion without correcting the policy basis that produces it.",
        ],
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
        "policy_conclusion_rule": {
            "derived_from": [
                "content_status", "evidence_status", "conflict_scope"
            ],
            "precedence": [
                {"when": when, "conclusion": conclusion}
                for when, conclusion in K.POLICY_CONCLUSION_RULES
            ],
        },
        "valid_criterion_ids": list(valid_criterion_ids),
        "aggregation_context_path": aggregation_context_path,
        "mapping_rule": (
            "aggregation-context.json (when provided) is authoritative for "
            "criterion scope and mapped unit outcomes; criterion_results[].claim_ids "
            "are citations only and may not narrow the mapped scope."
        ),
        "forbidden_conclusions_rule": (
            "aggregation-context.json specifies constraints.forbidden_conclusions "
            "for each Criterion — a list of conclusions that are structurally "
            "impossible given the observation evidence. If a conclusion appears "
            "in forbidden_conclusions, do not use it for that Criterion. Also "
            "check constraints.required_conclusion_when_no_adverse: when set, "
            "the Criterion conclusion must be exactly that value."
        ),
        "finding_cardinality_rule": (
            "every criterion whose conclusion is PARTIALLY_SUPPORTED, CONTRADICTED "
            "or MISSING must contain at least one evidence-backed finding; SUPPORTED "
            "and NOT_APPLICABLE criteria must contain none."
        ),
        "not_applicable_rule": (
            "aggregation-context.json specifies allow_not_applicable for each "
            "Criterion; NOT_APPLICABLE conclusion is only valid when "
            "allow_not_applicable is true. When false, you must use one of the "
            "other conclusions (SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, "
            "MISSING, or NOT_VERIFIABLE)."
        ),
        "severity_floor_rule": (
            "aggregation-context.json specifies outcomes[conclusion].severity_floor "
            "for conclusions that require findings (PARTIALLY_SUPPORTED, CONTRADICTED, "
            "MISSING). Each finding under that conclusion must have severity >= "
            "severity_floor. For example, if PARTIALLY_SUPPORTED has severity_floor "
            "Major, all findings must be Major or Critical, not Minor or Info."
        ),
        "evidence_type_rule": (
            "aggregation-context.json specifies required_evidence_types for each "
            "Criterion. When conclusion requires evidence (SUPPORTED, "
            "PARTIALLY_SUPPORTED, CONTRADICTED, MISSING), at least one selected "
            "evidence item must have a type from required_evidence_types. Choose "
            "evidence from the Criterion evidence_catalog that satisfies this "
            "constraint."
        ),
        "criterion_evidence_rule": (
            "criterion_results[].evidence_ids may contain only canonical IDs from "
            "that Criterion's aggregation-context evidence_catalog; finding "
            "evidence_ids must be a subset of the selected Criterion evidence IDs."
        ),
        "ownership_rule": (
            "findings link to defects through temporary keys; the service derives "
            "canonical finding IDs and secondary criterion sets. At most one finding "
            "may be CRITICAL and it must belong to the primary criterion."
        ),
        "defect_key_reference_rule": (
            "aggregation-context.json provides valid_defect_keys — the exhaustive "
            "whitelist of defect_key values defined by validated observations. "
            "defect_ownership[].defect_key must exactly match one entry in this "
            "whitelist; do not add prefixes, rename, derive, or create new keys. "
            "These keys are already scoped by work item (e.g. feat-01.trace-rule-orphan)."
        ),
    }
