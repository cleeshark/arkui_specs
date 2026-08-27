"""Machine contracts injected into executor prompts (protocol 0.2.0).

Generated from :mod:`.contracts` — the prompt no longer hand-repeats field
rules. The contract tells the model exactly which judgment fields it owns,
which reference spaces are legal (expected claims/checks, evidence catalog),
and the few semantic rules the schema cannot express.
"""

from __future__ import annotations

from typing import Any, Iterable

from . import contracts as K
from .errors import ERROR_REGISTRY, SERVICE_NORMALIZATION


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
        "For unit coverage, emit atomic unit_reviews and follow the injected "
        "Observation references for decomposition and Claim outcome derivation. "
        "The service derives published reviewed_units from unit_id order and "
        "validates unit presence, IDs, evidence, and outcome consistency.",
        "Treat every ID/reference list as set-like and do not repeat values. "
        "This includes criterion_ids, check_ids, claim_ids, evidence_refs and "
        "defect_keys in observation, claim and unit judgments.",
    ]


def build_observation_machine_contract(
    *,
    expected_claim_ids: Iterable[str],
    required_checks: Iterable[str],
    valid_criterion_ids: Iterable[str],
    observation_profile: str = "feature",
    evidence_catalog: Iterable[dict[str, Any]] = (),
    citable_input_paths: Iterable[str] = (),
) -> dict[str, Any]:
    """Contract for one observation work item.

    ``evidence_catalog`` lists evidence already published in the candidate
    (stable EV- IDs with type/path/description) so a correction turn can
    reference prior evidence without re-declaring it.
    """
    if observation_profile not in K.CORRECTION_PROFILES:
        raise ValueError(f"unknown correction profile: {observation_profile!r}")
    claims = list(expected_claim_ids)
    checks = list(required_checks)
    profile_rules = {
        "feature": {
            "scope": "one Feature and its local acceptance claims",
            "breadths": ["local", "feat_core"],
            "source_loading": [
                "Follow the injected Observation references for source loading. Use declared input_paths as Feature focus hints and expand within frozen repo_root when a named claim requires it.",
            ],
        },
        "function_global": {
            "scope": "Function-wide Design, Registry, and cross-Feature contracts",
            "breadths": ["function_shared", "feat_core", "local"],
            "source_loading": [
                "Follow the injected Observation references for source loading. Use declared input_paths as Function focus hints and expand within frozen repo_root when a named question requires it.",
            ],
        },
    }[observation_profile]
    return {
        **_common(),
        "observation_profile": observation_profile,
        "profile_rules": profile_rules,
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
            "or MISSING, and include primary_criterion_id in that observation's "
            "criterion_ids. For SUPPORTED, NOT_VERIFIABLE, and NOT_APPLICABLE "
            "outcomes, both fields must be null (omitted or explicitly null)."
        ),
        "modeling_basis_rule": (
            "When an observation's criterion_ids includes any Function modeling "
            "criterion (FUNCTION-FEAT-COVERAGE, FUNCTION-FEAT-DECOMPOSITION, "
            "FUNCTION-FEAT-BOUNDARY) AND local_outcome is CONFLICT or MISSING, "
            "the observation MUST include a modeling_basis object with: "
            "issue_type (one of: unowned_capability, ownership_overlap, "
            "oversized_feat, fragmented_feat, ambiguous_boundary), "
            "capability (non-empty string), "
            "why_dependency_or_detail_is_insufficient (non-empty string), "
            "feat_roles (non-empty list of {feat_id, role: owner|consumer|context, "
            "acceptance_claim_ids}). For ownership_overlap or ambiguous_boundary, "
            "at least two owner roles with acceptance_claim_ids are required, "
            "plus incompatible_contracts list and independent_acceptance_conflict=true."
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


def build_correction_machine_contract(
    *,
    payload_kind: str,
    typed_errors: Iterable[dict[str, Any]],
    observation_profile: str = "feature",
    allowed_paths: Iterable[str] = (),
    evidence_catalog: Iterable[dict[str, Any]] = (),
    valid_criterion_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Build the small contract used by a JSON Patch correction turn.

    Correction does not need the full Observation/Design contract.  The
    candidate is already normalized; the service owns patch application,
    identity, ordering, hashes and final validation.
    """
    if observation_profile not in K.CORRECTION_PROFILES:
        raise ValueError(f"unknown correction profile: {observation_profile!r}")
    errors = [dict(error) for error in typed_errors]
    profile_rules = {
        "feature": [
            "Keep patches local to the named Feature Claim/Unit/Observation paths.",
            "Do not alter cross-Feature ownership, global mappings, or non-target claims.",
        ],
        "function_global": [
            "Keep patches local to the named Function-global Claim/Unit/Observation paths.",
            "Do not alter cross-Feature ownership, boundary roles, or non-target claims unless the typed error names that exact path.",
            "Do not upgrade a global outcome without a typed semantic error and matching frozen evidence.",
        ],
        "aggregation": [
            "Keep patches local to the named Aggregation Criterion/Policy/Finding paths.",
            "Do not modify Observation source facts, non-target Criteria, or derived Finding IDs.",
            "Do not change a policy-derived conclusion without correcting its policy basis.",
        ],
    }[observation_profile]
    return {
        "evaluation_protocol_version": K.EVALUATION_PROTOCOL_VERSION,
        "mode": "correct",
        "payload_kind": payload_kind,
        "observation_profile": observation_profile,
        "output_format": "json_patch",
        "service_handled_error_codes": [
            code for code, repairability in ERROR_REGISTRY.items()
            if repairability == SERVICE_NORMALIZATION
        ],
        "model_correction_scope": [
            "evidence verification",
            "semantic outcome/reason/fact correction",
        ],
        "patch_operations": ["add", "remove", "replace"],
        "allowed_paths": list(dict.fromkeys(str(path) for path in allowed_paths)),
        "valid_criterion_ids": list(dict.fromkeys(valid_criterion_ids)),
        "typed_errors": errors,
        "rules": [
            "Patch the published candidate only; do not rewrite the complete document.",
            "Change only paths covered by typed_errors or their directly required sibling fields.",
            "Never modify document identity, source revision, ordering, canonical IDs, hashes, or derived fields.",
            "The service applies and validates the patch; do not calculate canonical IDs or hashes.",
            "Return patches and notes only. Encode every patch value as a JSON string; use \"null\" for remove.",
            *profile_rules,
        ],
        "evidence_catalog": list(evidence_catalog),
    }


def build_aggregation_correction_machine_contract(
    *,
    typed_errors: Iterable[dict[str, Any]],
    allowed_paths: Iterable[str] = (),
    evidence_catalog: Iterable[dict[str, Any]] = (),
    valid_criterion_ids: Iterable[str] = (),
    correction_context_path: str | None = None,
    target_criterion_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Build the Aggregation-specific bounded Correction contract.

    Unlike Observation Correction, Aggregation repairs relational rows:
    Criterion evidence constrains child Findings, policy bases derive
    conclusions, and Finding identities are referenced by ownership rows.
    Keep those dependency rules explicit without reinjecting the complete
    Aggregation generation contract.
    """
    errors = [dict(error) for error in typed_errors]
    error_codes = list(dict.fromkeys(
        str(error.get("code", "")) for error in errors if error.get("code")
    ))
    recipes: dict[str, list[str]] = {
        "MAPPING_CLAIM_UNMAPPED": [
            "Use criteria[].allowed_claim_ids as the only values selectable for the named Criterion claim_ids list.",
            "criteria[].claim_refs are lookup keys into claims and must never be written directly to claim_ids; allowed_claim_ids already contains the resolved claims[ref].claim_id values.",
            "Keep zero or more semantically representative allowed Claim IDs; remove every C:-prefixed lookup key.",
        ],
        "CRITERION_EVIDENCE_UNKNOWN": [
            "Use only criteria[].evidence_ids from aggregation-correction-context.json for the named Criterion.",
            "When removing or replacing parent Criterion evidence, update every child Finding that references the changed IDs so Finding evidence remains a subset.",
        ],
        "FINDING_EVIDENCE_UNKNOWN": [
            "Use only the parent Criterion evidence allowlist and keep at least one evidence ID for an adverse Finding.",
        ],
        "EVIDENCE_TYPE_MISSING": [
            "Select canonical Evidence of a required type from the target Criterion allowlist; the global catalog is not an allowlist.",
        ],
        "EVIDENCE_REQUIRED_MISSING": [
            "Select canonical Evidence from the target Criterion allowlist; never invent an EV- ID.",
        ],
        "POLICY_BASIS_INVALID": [
            "Keep the policy basis fields internally consistent and preserve the derived Criterion conclusion unless the corrected basis deterministically changes it.",
        ],
        "FINDING_CARDINALITY_VIOLATED": [
            "Keep Finding additions/removals consistent with defect_ownership references and the Criterion conclusion.",
        ],
        "OWNERSHIP_CRITICALITY": [
            "Keep each root defect's primary Criterion, Finding severity, and ownership references mutually consistent.",
        ],
    }
    contract = build_correction_machine_contract(
        payload_kind="aggregation",
        typed_errors=errors,
        observation_profile="aggregation",
        allowed_paths=allowed_paths,
        evidence_catalog=evidence_catalog,
        valid_criterion_ids=valid_criterion_ids,
    )
    contract.update({
        "correction_context_path": correction_context_path,
        "target_criterion_ids": list(dict.fromkeys(target_criterion_ids)),
        "input_authority": {
            "semantic_context": "aggregation-correction-context.json",
            "scope": "only target Criteria and their referenced Observation/Claim/Unit/Evidence rows",
            "criterion_evidence_allowlist": "criteria[].evidence_ids",
            "global_evidence_catalog_role": "lookup_only",
        },
        "dependency_rules": [
            "Every Finding evidence_ids list must remain a subset of its parent Criterion evidence selection.",
            "A policy-derived Criterion conclusion must agree with its outcome_policy_bases row.",
            "Finding key/ID changes and Finding additions/removals must keep defect_ownership references valid.",
            "Do not change inherited Observation, Claim, or atomic Unit outcomes.",
        ],
        "repair_recipes": {
            code: recipes[code] for code in error_codes if code in recipes
        },
    })
    return contract


def build_aggregation_machine_contract(
    *,
    valid_criterion_ids: Iterable[str],
    aggregation_context_path: str | None = None,
) -> dict[str, Any]:
    """Contract for the aggregation work item."""
    return {
        "evaluation_protocol_version": K.EVALUATION_PROTOCOL_VERSION,
        "envelope_schema_version": K.ENVELOPE_SCHEMA_VERSION,
        "observation_profile": "aggregation",
        "payload_fields": list(K.AGGREGATION_JUDGMENT_FIELDS),
        "criterion_judgment_fields": list(K.CRITERION_JUDGMENT_FIELDS),
        "finding_judgment_fields": list(K.FINDING_JUDGMENT_FIELDS),
        "defect_ownership_fields": list(K.DEFECT_OWNERSHIP_FIELDS),
        "contradiction_basis_fields": list(K.CONTRADICTION_BASIS_FIELDS),
        "policy_basis_fields": list(K.POLICY_BASIS_FIELDS),
        "policy_basis_criterion_ids": list(K.POLICY_BASIS_CRITERION_IDS),
        "policy_basis_order_rule": (
            "outcome_policy_bases must contain exactly the listed six "
            "policy_basis_criterion_ids in that order, once each."
        ),
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
        "input_authority": {
            "semantic_context": "aggregation-context.json",
            "criterion_mapping_fields": [
                "criteria[].observation_refs",
                "criteria[].claim_refs",
                "criteria[].unit_refs",
            ],
            "lookup_tables": [
                "observations", "claims", "units", "evidence_catalog",
            ],
        },
        "mapping_rule": (
            "aggregation-context.json is authoritative for Criterion scope and "
            "mapped outcomes. Resolve refs through the global tables; output "
            "claim_ids are citations only and may not narrow mapped scope."
        ),
        "evidence_selection": {
            "catalog_role": "lookup_only",
            "criterion_allowlist_field": "criteria[].evidence_ids",
            "criterion_by_type_field": "criteria[].evidence_ids_by_type",
            "output_selection_field": "criterion_results[].evidence_ids",
            "finding_subset_rule": (
                "Each finding evidence_ids must be a subset of its parent "
                "Criterion result evidence_ids."
            ),
            "forbidden": [
                "local Evidence keys", "Evidence declarations",
                "guessed or newly created EV- IDs",
            ],
        },
        "criterion_evidence_rule": (
            "The global evidence_catalog is lookup-only. criterion_results[]."
            "evidence_ids may contain only canonical IDs in that Criterion's "
            "criteria[].evidence_ids allowlist; finding evidence_ids are a subset."
        ),
        "conclusion_constraints": {
            "forbidden": "criteria[].constraints.forbidden_conclusions",
            "required_when_no_adverse": (
                "criteria[].constraints.required_conclusion_when_no_adverse"
            ),
            "not_applicable_guard": "criteria[].allow_not_applicable",
            "finding_required_for": [
                "PARTIALLY_SUPPORTED", "CONTRADICTED", "MISSING",
            ],
            "finding_forbidden_for": ["SUPPORTED", "NOT_APPLICABLE"],
            "finding_severity_floor": (
                "criteria[].outcomes[conclusion].severity_floor"
            ),
            "required_evidence_types": "criteria[].required_evidence_types",
        },
        "defect_ownership": {
            "valid_key_allowlist": "valid_defect_keys",
            "root_defect_rule": (
                "One actionable root defect may produce one Finding per materially "
                "affected Criterion and one shared ownership row."
            ),
            "critical_rule": (
                "At most one Finding for a root defect is Critical, on its primary "
                "Criterion."
            ),
        },
        "source_recheck": {
            "default": "inherit_validated_observation_facts",
            "allowed_when": [
                "one mapped fact is ambiguous",
                "mapped facts conflict",
                "one named Evidence gap blocks a defensible conclusion",
            ],
            "start_from": "current Criterion allowed Evidence paths",
            "boundary": "exact symbol, branch, target, declaration, or test",
            "may_not": [
                "introduce Evidence", "change an Observation outcome",
                "broadly rescan source, SDK, build, or test trees",
            ],
        },
        "service_owned": [
            "document identity", "ordering", "source Observation IDs",
            "canonical Finding IDs", "Evidence row expansion",
            "parent Evidence closure", "secondary Criterion derivation",
            "normalization", "validation", "assembly", "scoring",
            "confidence", "gate", "admission",
        ],
    }
