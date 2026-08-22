"""Declarative contracts for evaluator protocol 0.2.0 judgment payloads.

This module is the single source of truth for what the executor model emits.
The strict structured-output schema (:mod:`.schema_gen`), the machine contract
injected into prompts (:mod:`.machine_contract`) and the typed validator
(:mod:`.validate`) all derive from the constants and shapes declared here.

Ownership split (design §2.2):

- model: outcomes, reasons/facts, evidence declarations and references,
  defect descriptions, NV verification gaps, observation groupings;
- service (normalizer): document identity, stable evidence IDs and content
  hashes, claim row ordering, derived fields, canonical finding IDs,
  secondary criterion derivation, published document assembly.
"""

from __future__ import annotations

# The evaluation protocol implemented by this kernel. Executor transport,
# judgment payload shape and validation semantics change together at this
# version; no historical compatibility is retained (design D1).
EVALUATION_PROTOCOL_VERSION = "0.2.0"
# The installed evaluator skill is part of the immutable run identity.  D1
# intentionally accepts one exact version instead of a compatibility range.
EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.3.0"

ENVELOPE_SCHEMA_VERSION = 3

DEFECT_KEY_PATTERN = r"^[a-z0-9][a-z0-9._-]*$"

LOCAL_OUTCOMES = (
    "SUPPORTED",
    "CONFLICT",
    "MISSING",
    "NOT_APPLICABLE",
    "NOT_VERIFIABLE",
)
NOT_VERIFIABLE = "NOT_VERIFIABLE"

BREADTHS = ("local", "feat_core", "function_shared")

# Observation work-item profiles share one transport/state machine but have
# different source scope and correction risk.
OBSERVATION_PROFILES = ("feature", "function_global")

UNIT_FACET_TYPES = (
    "condition",
    "input",
    "data_field",
    "state_transition",
    "observable_result",
    "failure_recovery",
    "timing_performance",
    "compatibility",
    "ownership",
    "traceability",
    "design_claim",
)

EVIDENCE_TYPES = (
    "source_citation",
    "sdk_declaration",
    "spec_location",
    "design_location",
    "static_finding",
    "registry_entry",
    "test_evidence",
    "review_record",
)
REVIEW_RECORD = "review_record"

# Minimum observation-level evidence items per local outcome. NOT_VERIFIABLE
# observations must still record their inspection evidence (issue #22 rule,
# carried over as a typed check instead of a repair mode).
OBSERVATION_EVIDENCE_MIN_ITEMS = {
    outcome: 1 for outcome in LOCAL_OUTCOMES
}

FEATURE_REQUIRED_CHECKS = (
    "claim_source_support",
    "boundary_state",
    "ac_testability",
    "rule_completeness",
    "runtime_design",
    "compatibility_scope",
    "feat_ownership",
    "evidence_reproducibility",
)
FUNCTION_REQUIRED_CHECKS = (
    "registry_and_cross_doc",
    "traceability_graph",
    "architecture_and_layers",
    "shared_algorithm_state",
    "design_decisions",
    "build_deployment_impact",
    "verification_plan",
    "api_version_and_sdk_scope",
    "system_and_device_impact",
    "feat_coverage_decomposition_boundary",
    "cross_feat_contract_families",
)

POLICY_CONTENT_STATUSES = ("PRESENT", "PLACEHOLDER_ONLY", "ABSENT", "NOT_APPLICABLE")
POLICY_EVIDENCE_STATUSES = ("VERIFIED", "PARTIAL", "UNAVAILABLE", "NOT_APPLICABLE")
POLICY_CONFLICT_SCOPES = ("NONE", "LOCAL", "CORE", "NOT_APPLICABLE")

# The policy basis is the model-owned semantic input for the six fixed policy
# criteria.  The conclusion is derived by the service so the model cannot
# produce two inconsistent representations of the same judgment.
POLICY_CONCLUSION_RULES = (
    ("all statuses are NOT_APPLICABLE", "NOT_APPLICABLE"),
    ("conflict_scope is CORE", "CONTRADICTED"),
    ("content_status is ABSENT or PLACEHOLDER_ONLY", "MISSING"),
    ("conflict_scope is LOCAL", "PARTIALLY_SUPPORTED"),
    ("evidence_status is UNAVAILABLE", "NOT_VERIFIABLE"),
    ("evidence_status is PARTIAL", "PARTIALLY_SUPPORTED"),
    ("otherwise", "SUPPORTED"),
)


def expected_policy_conclusion(
    content_status: str,
    evidence_status: str,
    conflict_scope: str,
) -> str | None:
    """Derive a policy conclusion from its three atomic status fields.

    ``None`` means that the basis is not structurally valid yet (for example,
    a mixed ``NOT_APPLICABLE`` tuple); the typed validator owns that error.
    Keeping this function in the declarative contract makes schema prompts,
    normalization and validation use the same precedence table.
    """
    statuses = {content_status, evidence_status, conflict_scope}
    if "NOT_APPLICABLE" in statuses and len(statuses) > 1:
        return None
    if statuses == {"NOT_APPLICABLE"}:
        return "NOT_APPLICABLE"
    if conflict_scope == "CORE":
        return "CONTRADICTED"
    if content_status in {"ABSENT", "PLACEHOLDER_ONLY"}:
        return "MISSING"
    if conflict_scope == "LOCAL":
        return "PARTIALLY_SUPPORTED"
    if evidence_status == "UNAVAILABLE":
        return "NOT_VERIFIABLE"
    if evidence_status == "PARTIAL":
        return "PARTIALLY_SUPPORTED"
    return "SUPPORTED"

SEMANTIC_CONCLUSIONS = (
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "CONTRADICTED",
    "MISSING",
    "NOT_APPLICABLE",
    "NOT_VERIFIABLE",
)
FINDING_REQUIRED_CONCLUSIONS = (
    "PARTIALLY_SUPPORTED",
    "CONTRADICTED",
    "MISSING",
)
FINDING_FORBIDDEN_CONCLUSIONS = ("SUPPORTED", "NOT_APPLICABLE")
APPLICABILITY_VALUES = ("APPLICABLE", "NOT_APPLICABLE")
FINDING_SEVERITIES = ("CRITICAL", "MAJOR", "MINOR")

PLACEHOLDER_TEXT = "待评价人"
LOW_INFORMATION_REVIEW_TEXT = frozenset({
    "supported",
    "conflict",
    "missing",
    "notapplicable",
    "notverifiable",
    "partiallysupported",
    "contradicted",
    "支持",
    "通过",
    "冲突",
    "缺失",
    "不适用",
    "不可验证",
})

# Judgment payload field names (executor-owned). The published documents keep
# the historical shape consumed by aggregation-context, score and the frozen
# semantic-result schema; only the transport payload is new.
#
# Evidence namespace (design v3, review §3.4): declarations live at the
# payload top level with work-item-scoped local keys; claim/unit/observation
# rows reference them through ``evidence_refs``. The normalizer converts
# local keys to canonical evidence IDs at publish time, so aggregation and
# every downstream consumer only ever see canonical IDs.
OBSERVATION_JUDGMENT_FIELDS = (
    "evidence_declarations",
    "claim_reviews",
    "observations",
    "open_questions",
    "notes",
)

# Correction turns return a bounded RFC-6902 patch against the normalized
# candidate.  The service merges and validates the patch; the model never
# rewrites the staged document.
CORRECTION_JUDGMENT_FIELDS = ("patches", "notes")
CLAIM_JUDGMENT_FIELDS = (
    "claim_id",
    "local_outcome",
    "evidence_refs",
    "reason",
    "verification_gap",
    "defect_keys",
    "unit_reviews",
)
UNIT_JUDGMENT_FIELDS = (
    "unit_id",
    "facet_type",
    "local_outcome",
    "evidence_refs",
    "fact",
    "verification_gap",
)
VERIFICATION_GAP_FIELDS = (
    "checked_scope",
    "missing_evidence",
    "consequence",
)
EVIDENCE_DECLARATION_FIELDS = (
    "key",
    "type",
    "path",
    "lines",
    "description",
)
OBSERVATION_JUDGMENT_ENTRY_FIELDS = (
    "criterion_ids",
    "check_ids",
    "claim_ids",
    "local_outcome",
    "breadth",
    "contract_family",
    "fact",
    "defect_key",
    "primary_criterion_id",
    "evidence_refs",
)

AGGREGATION_JUDGMENT_FIELDS = (
    "cross_feat_contracts_reviewed",
    "contradiction_bases",
    "defect_ownership",
    "outcome_policy_bases",
    "criterion_results",
    "notes",
)
CRITERION_JUDGMENT_FIELDS = (
    "criterion_id",
    "conclusion",
    "applicability",
    "reason",
    "applicability_reason",
    "missing_evidence",
    "claim_ids",
    "evidence_ids",
    "findings",
)
FINDING_JUDGMENT_FIELDS = (
    "key",
    "criterion_id",
    "claim_id",
    "severity",
    "message",
    "evidence_ids",
    "recommendation",
)
DEFECT_OWNERSHIP_FIELDS = (
    "defect_key",
    "primary_criterion_id",
    "finding_keys",
    "rationale",
)
CONTRADICTION_BASIS_FIELDS = (
    "statement",
    "left_assertion",
    "right_assertion",
    "affected_feat_ids",
    "correction_scope",
    "function_shared_assertion",
    "primary_defect_key",
)
POLICY_BASIS_FIELDS = (
    "criterion_id",
    "content_status",
    "evidence_status",
    "conflict_scope",
    "reason",
)

# Historical published-document field order preserved by the normalizer.
PUBLISHED_CLAIM_FIELDS = (
    "claim_id",
    "status",
    "local_outcome",
    "reviewed_units",
    "unit_reviews",
    "criterion_ids",
    "evidence_ids",
    "defect_keys",
    "reason",
)
PUBLISHED_UNIT_FIELDS = (
    "unit_id",
    "facet_type",
    "local_outcome",
    "evidence_ids",
    "fact",
)
PUBLISHED_EVIDENCE_FIELDS = (
    "evidence_id",
    "type",
    "path",
    "source_revision",
    "content_hash",
    "description",
)
PUBLISHED_OBSERVATION_FIELDS = (
    "observation_id",
    "criterion_ids",
    "check_ids",
    "claim_ids",
    "local_outcome",
    "breadth",
    "contract_family",
    "fact",
    "defect_key",
    "primary_criterion_id",
    "evidence",
)
FUNCTION_MODELING_CRITERIA = frozenset({
    "FUNCTION-FEAT-COVERAGE",
    "FUNCTION-FEAT-DECOMPOSITION",
    "FUNCTION-FEAT-BOUNDARY",
})
MODELING_ISSUE_TYPES = frozenset({
    "unowned_capability",
    "ownership_overlap",
    "oversized_feat",
    "fragmented_feat",
    "ambiguous_boundary",
})
MODELING_FEAT_ROLES = frozenset({"owner", "consumer", "context"})
