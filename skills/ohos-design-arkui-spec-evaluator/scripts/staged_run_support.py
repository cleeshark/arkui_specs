#!/usr/bin/env python3
"""Shared contracts and validation helpers for staged semantic evaluation runs."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from create_pilot_template import DEFAULT_EVALUATOR_VERSION, EVALUATION_ROOT, SPECS_ROOT


TOOLS_ROOT = SPECS_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from spec_eval.protocol_validator import (  # noqa: E402
    FINDING_REQUIRED_CONCLUSIONS,
    validate_protocol,
    validate_semantic_result,
)


STAGED_SCHEMA_VERSION = 2
SUPPORTED_STAGED_SCHEMA_VERSIONS = {STAGED_SCHEMA_VERSION}
AGGREGATION_CONTEXT_SCHEMA_VERSION = 1
SEMANTIC_FINDING_IDENTITY_VERSION = 1
OUTCOME_POLICY_BASIS_CRITERIA = [
    "SPEC-AC-TESTABILITY",
    "SPEC-TRACEABILITY",
    "DESIGN-IMPACT-COVERAGE",
    "DESIGN-VERIFICATION-PLAN",
    "COMPATIBILITY-API-VERSION",
    "COMPATIBILITY-MULTI-DEVICE",
]
POLICY_CONTENT_STATUSES = {"PRESENT", "PLACEHOLDER_ONLY", "ABSENT", "NOT_APPLICABLE"}
POLICY_EVIDENCE_STATUSES = {"VERIFIED", "PARTIAL", "UNAVAILABLE", "NOT_APPLICABLE"}
POLICY_CONFLICT_SCOPES = {"NONE", "LOCAL", "CORE", "NOT_APPLICABLE"}
FEATURE_REQUIRED_CHECKS = [
    "claim_source_support",
    "boundary_state",
    "ac_testability",
    "rule_completeness",
    "runtime_design",
    "compatibility_scope",
    "feat_ownership",
    "evidence_reproducibility",
]
FUNCTION_REQUIRED_CHECKS = [
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
]
LOCAL_OUTCOMES = {
    "SUPPORTED",
    "CONFLICT",
    "MISSING",
    "NOT_APPLICABLE",
    "NOT_VERIFIABLE",
}
OBSERVATION_EVIDENCE_MIN_ITEMS = {
    outcome: 1 for outcome in sorted(LOCAL_OUTCOMES)
}
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
BREADTHS = {"local", "feat_core", "function_shared"}
UNIT_FACET_TYPES = {
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
}
FUNCTION_MODELING_CRITERIA = {
    "FUNCTION-FEAT-COVERAGE",
    "FUNCTION-FEAT-DECOMPOSITION",
    "FUNCTION-FEAT-BOUNDARY",
}
MODELING_ISSUE_TYPES = {
    "unowned_capability",
    "ownership_overlap",
    "oversized_feat",
    "fragmented_feat",
    "ambiguous_boundary",
}
PLACEHOLDER_TEXT = "待评价人"
LOW_INFORMATION_REVIEW_TEXT = {
    "supported",
    "conflict",
    "missing",
    "notapplicable",
    "notverifiable",
    "支持",
    "通过",
    "冲突",
    "缺失",
    "不适用",
    "不可验证",
}
OBSERVATION_ID = re.compile(r"^OBS-[A-Za-z0-9._-]+$")
EVIDENCE_ID = re.compile(r"^EV-[A-Za-z0-9._-]+$")
HASH_VALUE = re.compile(r"^sha256:[0-9a-f]{64}$")
DEFECT_KEY = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def semantic_finding_id(
    *,
    func_id: str,
    defect_key: str,
    criterion_id: str,
    claim_id: str | None,
) -> str:
    """Return the stable semantic Finding identity for one owned defect projection."""
    identity = {
        "identity_version": SEMANTIC_FINDING_IDENTITY_VERSION,
        "func_id": func_id,
        "defect_key": defect_key,
        "criterion_id": criterion_id,
        "claim_id": claim_id,
    }
    encoded = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "SEM-" + hashlib.sha256(encoded).hexdigest()[:24]


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def write_object(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def protocol() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    return validate_protocol(EVALUATION_ROOT)


def criterion_order(rubric: dict[str, Any]) -> list[str]:
    return [
        criterion["id"]
        for dimension in rubric.get("dimensions", [])
        for criterion in dimension.get("criteria", [])
    ]


def staged_output_contract(
    *, source_revision: str, evaluator_version: str = DEFAULT_EVALUATOR_VERSION
) -> dict[str, Any]:
    """Return the machine-readable executor contract owned by this Skill version."""
    rubric, _, errors = protocol()
    if errors:
        raise ValueError("cannot build staged output contract: " + "; ".join(errors))
    rubric_path = EVALUATION_ROOT / "rubric.yaml"
    criteria = criterion_order(rubric)
    rubric_evidence_types = tuple(
        rubric.get("evidence_policy", {}).get("evidence_types", [])
    )
    if rubric_evidence_types != EVIDENCE_TYPES:
        raise ValueError(
            "cannot build staged output contract: validator evidence types differ from Rubric"
        )
    evidence_contract = {
        "required_fields": [
            "evidence_id",
            "type",
            "path",
            "source_revision",
            "content_hash",
            "description",
        ],
        "type_enum": list(rubric_evidence_types),
        "evidence_id_pattern": EVIDENCE_ID.pattern,
        "content_hash_pattern": HASH_VALUE.pattern,
        "rules": [
            "Use one stable EV- prefixed evidence_id and update every evidence_ids reference when it changes.",
            "Use the frozen source revision exactly as source_revision.",
            "content_hash is lowercase SHA-256 with the literal sha256: prefix.",
            "Select type from type_enum; never omit it or invent a new type.",
        ],
        "format_example_only": {
            "evidence_id": "EV-contract-format-example",
            "type": "spec_location",
            "path": "specs/evaluation/rubric.yaml",
            "source_revision": source_revision,
            "content_hash": content_hash(rubric_path),
            "description": "Format example only; do not reuse unless this file proves the fact.",
        },
    }
    aggregation_payload = {
        "payload_fields": [
            "cross_feat_contracts_reviewed",
            "contradiction_bases",
            "defect_ownership",
            "outcome_policy_bases",
            "criterion_results",
            "notes",
        ],
        "criterion_order": criteria,
        "conclusion_enum": list(rubric.get("semantic_conclusions", [])),
        "policy_content_status_enum": sorted(POLICY_CONTENT_STATUSES),
        "policy_evidence_status_enum": sorted(POLICY_EVIDENCE_STATUSES),
        "policy_conflict_scope_enum": sorted(POLICY_CONFLICT_SCOPES),
    }
    aggregation_payload["mapping_context"] = {
        "schema_version": AGGREGATION_CONTEXT_SCHEMA_VERSION,
        "path_field": "aggregation_context_path",
        "mapping_authority": {
            "observations": "Map each observation through observations[].criterion_ids.",
            "claims": "Map each claim through claim_reviews[].criterion_ids.",
            "atomic_units": "Each unit_review inherits the Criterion IDs of its parent claim review.",
            "criterion_result_claim_ids": (
                "criterion_results[].claim_ids may cite only claims already mapped to that "
                "Criterion; it never defines or narrows aggregate scope."
            ),
        },
        "mixed_outcome_policy": [
            "SUPPORTED requires every applicable mapped unit to be verified and no mapped CONFLICT, MISSING or NOT_VERIFIABLE unit.",
            "When mapped units contain NOT_VERIFIABLE but no CONFLICT or MISSING, conclude NOT_VERIFIABLE.",
            "When any mapped observation, claim or atomic unit is CONFLICT or MISSING, do not conclude SUPPORTED or NOT_APPLICABLE; apply breadth and the frozen Rubric outcome policy.",
            "NOT_APPLICABLE is invalid when any mapped unit is applicable.",
            "New aggregation evidence may explain a conclusion but may not silently override a published mapped outcome.",
        ],
    }
    semantic_schema = load_object(
        EVALUATION_ROOT / "schemas" / "semantic-result.schema.json"
    )
    schema_defs = semantic_schema.get("$defs", {})
    final_contract = {
        "semantic_finding_schema": copy.deepcopy(schema_defs["semantic_finding"]),
        "criterion_result_schema": copy.deepcopy(schema_defs["criterion_result"]),
        "conditional_fields": {
            "NOT_APPLICABLE": {
                "required": ["applicability_reason"],
                "evidence_min_items": 1,
            },
            "NOT_VERIFIABLE": {"required": ["missing_evidence"]},
            "FINDING_CARDINALITY": {
                "required_for_conclusions": sorted(FINDING_REQUIRED_CONCLUSIONS),
                "findings_min_items": 1,
                "evidence_backed": True,
                "rule": (
                    "Every PARTIALLY_SUPPORTED, CONTRADICTED or MISSING Criterion "
                    "must contain at least one Finding whose evidence_ids reference "
                    "that Criterion's evidence."
                ),
            },
        },
        "finding_identity": {
            "identity_version": SEMANTIC_FINDING_IDENTITY_VERSION,
            "prefix": "SEM-",
            "hex_length": 24,
            "hash": "sha256",
            "canonical_json": {
                "sort_keys": True,
                "separators": [",", ":"],
                "ensure_ascii": False,
            },
            "fields": [
                "identity_version",
                "func_id",
                "defect_key",
                "criterion_id",
                "claim_id",
            ],
            "rule": (
                "SEM- + first 24 lowercase hex characters of SHA-256 over canonical "
                "JSON of the declared identity fields. Classification and prose fields "
                "do not participate in identity."
            ),
        },
    }
    final_contract["finding_identity"].update({
        "executor_input": {
            "role": "provisional_correlation_key",
            "requirements": ["non-empty string", "unique within aggregation"],
            "canonical_hash_required": False,
        },
        "published_output": {
            "service_derived": True,
            "pattern": schema_defs["semantic_finding"]["properties"][
                "finding_id"
            ]["pattern"],
        },
        "rule": (
            "The executor supplies only a unique provisional correlation key. The "
            "service publishes SEM- plus the first 24 lowercase hex characters of "
            "SHA-256 over canonical JSON of the declared identity fields. "
            "Classification and prose fields do not participate in identity."
        ),
    })
    final_contract["defect_ownership"] = {
        "finding_ids": {
            "executor_input": "References provisional Finding correlation keys.",
            "published_output": "Rewritten to service-canonical Finding IDs.",
        },
        "secondary_criterion_ids": {
            "service_derived": True,
            "formula": (
                "sorted(unique Criterion IDs of Findings referenced by finding_ids "
                "minus primary_criterion_id)"
            ),
            "semantic_rule": (
                "A secondary Criterion must be represented by an actual Finding "
                "owned by the same defect record."
            ),
        },
    }
    aggregation_payload["final_contract"] = final_contract
    return {
        "schema_version": 1,
        "staged_schema_version": STAGED_SCHEMA_VERSION,
        "evaluator_version": evaluator_version,
        "valid_criterion_ids": criteria,
        "common": {
            "local_outcome_enum": sorted(LOCAL_OUTCOMES),
            "breadth_enum": sorted(BREADTHS),
            "unit_facet_type_enum": sorted(UNIT_FACET_TYPES),
            "evidence": evidence_contract,
        },
        "observation_payload": {
            "payload_fields": ["claim_reviews", "observations", "open_questions", "notes"],
            "claim_reviews": {
                "required_fields": [
                    "claim_id",
                    "status",
                    "local_outcome",
                    "reviewed_units",
                    "unit_reviews",
                    "criterion_ids",
                    "evidence_ids",
                    "defect_keys",
                    "reason",
                ],
                "ordering": "Exactly one row per expected_claim_ids entry, in initialized order.",
                "criterion_ids": criteria,
                "defect_keys_rule": {
                    "required_when_local_outcome": ["CONFLICT", "MISSING"],
                    "must_be_empty_for_all_other_outcomes": True,
                },
                "quality_rule": {
                    "reason_and_unit_fact_must_be_evidence_specific": True,
                    "forbidden_outcome_only_text": sorted(LOW_INFORMATION_REVIEW_TEXT),
                    "not_verifiable_requires_review_record": True,
                    "not_verifiable_explanation": (
                        "Name the checked scope, the missing evidence, and why the gap "
                        "is insufficient for a defensible judgment."
                    ),
                    "not_verifiable_required_signals": [
                        "checked_scope",
                        "missing_evidence",
                        "verification_consequence",
                    ],
                    "not_verifiable_expression_examples": {
                        "checked_scope": [
                            "checked", "inspection", "reviewed", "searched",
                        ],
                        "missing_evidence": [
                            "missing", "absence", "without", "does not include",
                            "no relevant source content",
                        ],
                        "verification_consequence": [
                            "cannot verify", "cannot be verified",
                            "prevents verifying", "unable to determine",
                        ],
                    },
                },
                "dangling_evidence_repair": {
                    "mode": "repair_claim_evidence_references",
                    "target_identity": "claim_id",
                    "defined_evidence_only": True,
                    "allowed_outcome_change": "target Claim/unit to NOT_VERIFIABLE only",
                    "preserved_fields": [
                        "observations",
                        "non-target claim_reviews",
                        "claim and Criterion mappings",
                        "reviewed_units and facet types",
                        "defects",
                        "array ordering",
                    ],
                },
            },
            "observations": {
                "required_fields": [
                    "observation_id",
                    "criterion_ids",
                    "check_ids",
                    "claim_ids",
                    "local_outcome",
                    "breadth",
                    "contract_family",
                    "fact",
                    "evidence",
                ],
                "observation_id_pattern": OBSERVATION_ID.pattern,
                "criterion_ids": criteria,
                "defect_ownership_rule": {
                    "required_fields_when_local_outcome_is_conflict_or_missing": [
                        "defect_key",
                        "primary_criterion_id",
                    ],
                    "fields_must_be_absent_for_all_other_outcomes": [
                        "defect_key",
                        "primary_criterion_id",
                    ],
                },
                "evidence_cardinality": {
                    "minimum_items_by_local_outcome": dict(
                        OBSERVATION_EVIDENCE_MIN_ITEMS
                    ),
                    "rule": (
                        "Every observation carries at least one evidence object. "
                        "NOT_VERIFIABLE cites review_record inspection evidence for the "
                        "scope that was checked but remained insufficient. NOT_APPLICABLE "
                        "cites reproducible evidence that proves the checked unit is "
                        "inapplicable; fact text is not evidence."
                    ),
                    "not_applicable_example_only": {
                        "local_outcome": "NOT_APPLICABLE",
                        "fact": (
                            "The frozen applicability policy proves the checked unit does "
                            "not apply."
                        ),
                        "evidence": [{
                            **evidence_contract["format_example_only"],
                            "evidence_id": "EV-not-applicable-format-example",
                            "description": (
                                "Example shape only: cite the actual frozen scope or policy "
                                "that proves the evaluated unit is inapplicable."
                            ),
                        }],
                    },
                },
                "evidence": evidence_contract,
            },
        },
        "aggregation_payload": aggregation_payload,
    }


def build_aggregation_context(
    state: dict[str, Any], work_items: dict[str, Any]
) -> dict[str, Any]:
    """Build the run-derived Criterion mapping consumed by aggregation and validation."""
    rubric, _, errors = protocol()
    if errors:
        raise ValueError("cannot build aggregation context: " + "; ".join(errors))
    criteria = criterion_order(rubric)
    allow_not_applicable = {
        criterion["id"]: bool(criterion.get("allow_not_applicable"))
        for dimension in rubric.get("dimensions", [])
        for criterion in dimension.get("criteria", [])
        if isinstance(criterion, dict) and isinstance(criterion.get("id"), str)
    }
    mappings: dict[str, dict[str, Any]] = {
        criterion_id: {
            "criterion_id": criterion_id,
            "allow_not_applicable": allow_not_applicable.get(criterion_id, False),
            "observations": [],
            "claims": [],
            "atomic_units": [],
            "mapped_claim_ids": [],
        }
        for criterion_id in criteria
    }
    source_observations: list[dict[str, Any]] = []

    for item in work_items.get("items", []):
        if not isinstance(item, dict):
            continue
        work_item_id = item.get("id")
        output_path = item.get("output_path")
        if not isinstance(work_item_id, str) or not isinstance(output_path, str):
            continue
        path = Path(output_path)
        document = load_object(path)
        source_observations.append({
            "work_item_id": work_item_id,
            "path": output_path,
            "content_hash": content_hash(path),
        })

        for observation in document.get("observations", []):
            if not isinstance(observation, dict):
                continue
            criterion_ids = list(
                dict.fromkeys(
                    criterion_id
                    for criterion_id in observation.get("criterion_ids", [])
                    if criterion_id in mappings
                )
            )
            claim_ids = [
                claim_id
                for claim_id in observation.get("claim_ids", [])
                if isinstance(claim_id, str) and claim_id
            ]
            entry = {
                "work_item_id": work_item_id,
                "observation_id": observation.get("observation_id"),
                "local_outcome": observation.get("local_outcome"),
                "breadth": observation.get("breadth"),
                "contract_family": observation.get("contract_family"),
                "claim_ids": claim_ids,
            }
            for optional in ("defect_key", "primary_criterion_id"):
                if isinstance(observation.get(optional), str):
                    entry[optional] = observation[optional]
            for criterion_id in criterion_ids:
                mapping = mappings[criterion_id]
                mapping["observations"].append(copy.deepcopy(entry))

        for claim_review in document.get("claim_reviews", []):
            if not isinstance(claim_review, dict):
                continue
            criterion_ids = list(
                dict.fromkeys(
                    criterion_id
                    for criterion_id in claim_review.get("criterion_ids", [])
                    if criterion_id in mappings
                )
            )
            claim_id = claim_review.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id:
                continue
            claim_entry = {
                "work_item_id": work_item_id,
                "claim_id": claim_id,
                "local_outcome": claim_review.get("local_outcome"),
                "defect_keys": [
                    key
                    for key in claim_review.get("defect_keys", [])
                    if isinstance(key, str) and key
                ],
            }
            unit_entries = []
            for unit in claim_review.get("unit_reviews", []):
                if not isinstance(unit, dict):
                    continue
                unit_entries.append({
                    "work_item_id": work_item_id,
                    "claim_id": claim_id,
                    "unit_id": unit.get("unit_id"),
                    "facet_type": unit.get("facet_type"),
                    "local_outcome": unit.get("local_outcome"),
                })
            for criterion_id in criterion_ids:
                mapping = mappings[criterion_id]
                mapping["claims"].append(copy.deepcopy(claim_entry))
                mapping["atomic_units"].extend(copy.deepcopy(unit_entries))
                _extend_unique(mapping["mapped_claim_ids"], [claim_id])

    for mapping in mappings.values():
        units = [
            ("observation", entry) for entry in mapping["observations"]
        ] + [
            ("claim", entry) for entry in mapping["claims"]
        ] + [
            ("atomic_unit", entry) for entry in mapping["atomic_units"]
        ]
        counts = {outcome: 0 for outcome in sorted(LOCAL_OUTCOMES)}
        adverse_refs: list[str] = []
        unverifiable_refs: list[str] = []
        applicable_refs: list[str] = []
        for kind, entry in units:
            outcome = entry.get("local_outcome")
            if outcome in counts:
                counts[outcome] += 1
            ref = _aggregation_unit_ref(kind, entry)
            if outcome in {"CONFLICT", "MISSING"}:
                adverse_refs.append(ref)
            if outcome == "NOT_VERIFIABLE":
                unverifiable_refs.append(ref)
            if outcome in {"SUPPORTED", "CONFLICT", "MISSING", "NOT_VERIFIABLE"}:
                applicable_refs.append(ref)
        forbidden: list[str] = []
        if adverse_refs:
            forbidden.extend(["SUPPORTED", "NOT_APPLICABLE"])
        elif unverifiable_refs:
            forbidden.append("SUPPORTED")
        if applicable_refs and "NOT_APPLICABLE" not in forbidden:
            forbidden.append("NOT_APPLICABLE")
        mapping["outcome_counts"] = counts
        mapping["constraints"] = {
            "adverse_unit_refs": adverse_refs,
            "unverifiable_unit_refs": unverifiable_refs,
            "applicable_unit_refs": applicable_refs,
            "forbidden_conclusions": forbidden,
            "required_conclusion_when_no_adverse": (
                "NOT_VERIFIABLE" if unverifiable_refs and not adverse_refs else None
            ),
        }

    return {
        "schema_version": AGGREGATION_CONTEXT_SCHEMA_VERSION,
        "staged_schema_version": state.get("schema_version"),
        "evaluator_version": state.get("evaluator_version"),
        "func_id": state.get("func_id"),
        "source_revision": state.get("source_revision"),
        "run_id": state.get("run_id"),
        "source_observations": source_observations,
        "criterion_mappings": list(mappings.values()),
    }


def _extend_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def _aggregation_unit_ref(kind: str, entry: dict[str, Any]) -> str:
    work_item_id = entry.get("work_item_id", "unknown")
    if kind == "observation":
        identity = entry.get("observation_id", "unknown")
    elif kind == "claim":
        identity = entry.get("claim_id", "unknown")
    else:
        identity = f"{entry.get('claim_id', 'unknown')}/{entry.get('unit_id', 'unknown')}"
    return f"{kind}:{work_item_id}:{identity}={entry.get('local_outcome', 'unknown')}"


def _format_mapping_refs(value: Any, limit: int = 8) -> str:
    refs = [item for item in value if isinstance(item, str)] if isinstance(value, list) else []
    visible = refs[:limit]
    suffix = f" (+{len(refs) - limit} more)" if len(refs) > limit else ""
    return f"{visible}{suffix}"


def load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    return load_object(run_dir / "run-state.json"), load_object(run_dir / "work-items.json")


def validate_identity(
    document: dict[str, Any], state: dict[str, Any], label: str, errors: list[str]
) -> None:
    expected = {
        "schema_version": state.get("schema_version"),
        "func_id": state.get("func_id"),
        "source_revision": state.get("source_revision"),
        "run_id": state.get("run_id"),
        "evaluator_version": state.get("evaluator_version"),
    }
    for key, value in expected.items():
        if document.get(key) != value:
            errors.append(f"{label}.{key}: expected {value!r}, got {document.get(key)!r}")
    schema_version = state.get("schema_version")
    if schema_version not in SUPPORTED_STAGED_SCHEMA_VERSIONS:
        errors.append(f"run-state.schema_version: unsupported value {schema_version!r}")


def validate_input_hashes(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    artifacts = state.get("input_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return ["run-state.input_artifacts: expected a non-empty list"]
    for index, artifact in enumerate(artifacts):
        label = f"run-state.input_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{label}: expected an object")
            continue
        path_value = artifact.get("path")
        expected_hash = artifact.get("content_hash")
        if not isinstance(path_value, str) or not path_value:
            errors.append(f"{label}.path: expected a non-empty string")
            continue
        path = Path(path_value)
        if not path.is_file():
            errors.append(f"{label}: input artifact is missing: {path}")
            continue
        actual_hash = content_hash(path)
        if actual_hash != expected_hash:
            errors.append(
                f"{label}: input artifact drifted: expected {expected_hash}, got {actual_hash}"
            )
    return errors


def _validate_string_list(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{label}: expected a list of non-empty strings")
        return []
    if len(value) != len(set(value)):
        errors.append(f"{label}: duplicate values are not allowed")
    return value


def _validate_evidence(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label}: expected an evidence object")
        return
    required = ("evidence_id", "type", "path", "source_revision", "content_hash", "description")
    for key in required:
        if not isinstance(value.get(key), str) or not value.get(key):
            errors.append(f"{label}.{key}: expected a non-empty string")
    if isinstance(value.get("evidence_id"), str) and not EVIDENCE_ID.fullmatch(value["evidence_id"]):
        errors.append(f"{label}.evidence_id: invalid evidence ID")
    if isinstance(value.get("content_hash"), str) and not HASH_VALUE.fullmatch(value["content_hash"]):
        errors.append(f"{label}.content_hash: expected sha256:<64 lowercase hex digits>")
    if value.get("type") not in EVIDENCE_TYPES:
        errors.append(f"{label}.type: unsupported evidence type {value.get('type')!r}")


def _is_low_information_review_text(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()
    return normalized in LOW_INFORMATION_REVIEW_TEXT


_NV_CHECKED_PATTERNS = (
    re.compile(
        r"\b(?:check(?:ed|ing)?|inspect(?:ed|ing|ion)?|review(?:ed|ing)?|"
        r"examin(?:e|ed|ing|ation)|search(?:ed|ing)?|scan(?:ned|ning)?)\b"
    ),
)
_NV_MISSING_PATTERNS = (
    re.compile(r"\b(?:missing|absent|absence|unavailable|insufficient|lacks?|lacking)\b"),
    re.compile(r"\bnot\s+(?:present|found|available|included)\b"),
    re.compile(r"\bwithout(?:\s+the)?\b"),
    re.compile(r"\b(?:does|do|did)\s+not\s+(?:include|contain|provide|cover)\b"),
    re.compile(
        r"\bno\b[^.;:\n]{0,120}\b(?:evidence|proof|source|content|implementation|"
        r"record|test|coverage|artifact|file|path|data)\b"
    ),
)
_NV_CONSEQUENCE_PATTERNS = (
    re.compile(
        r"\b(?:cannot|can\s+not|unable\s+to)\s+(?:\w+\s+){0,3}"
        r"verif(?:y|ied|iable)\b"
    ),
    re.compile(r"\bnot\s+verifiable\b"),
    re.compile(
        r"\b(?:cannot|can\s+not|unable\s+to)\s+(?:\w+\s+){0,3}"
        r"determin(?:e|ed)\b"
    ),
    re.compile(
        r"\bprevent(?:s|ed|ing)?\s+(?:\w+\s+){0,3}"
        r"(?:verif(?:y|ying|ication)|determin(?:e|ing|ation))\b"
    ),
    re.compile(r"\binsufficient\s+to\b"),
)


def _matches_any_pattern(value: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(value) is not None for pattern in patterns)


def _has_unverifiable_gap_explanation(
    value: Any, *, expression_families: bool = False
) -> bool:
    """Require NV prose to name both the inspected scope and the evidence gap."""
    if not isinstance(value, str) or len(value.strip()) < 24:
        return False
    normalized = re.sub(r"\s+", " ", value.casefold())
    checked_terms = ("checked", "inspected", "reviewed", "examined", "检查", "审查")
    missing_terms = (
        "missing", "absent", "unavailable", "insufficient", "not present",
        "缺少", "缺失", "不足", "不可用",
    )
    consequence_terms = (
        "cannot verify", "not verifiable", "insufficient to", "cannot determine",
        "无法验证", "不能验证", "不足以", "无法判断",
    )
    if not expression_families:
        return (
            any(term in normalized for term in checked_terms)
            and any(term in normalized for term in missing_terms)
            and any(term in normalized for term in consequence_terms)
        )
    return (
        (
            _matches_any_pattern(normalized, _NV_CHECKED_PATTERNS)
            or any(term in normalized for term in ("检查", "审查"))
        )
        and (
            _matches_any_pattern(normalized, _NV_MISSING_PATTERNS)
            or any(term in normalized for term in ("缺少", "缺失", "不足", "不可用"))
        )
        and (
            _matches_any_pattern(normalized, _NV_CONSEQUENCE_PATTERNS)
            or any(term in normalized for term in ("无法验证", "不能验证", "不足以", "无法判断"))
        )
    )


def _observation_evidence_minimums(evaluator_version: Any) -> dict[str, int]:
    return OBSERVATION_EVIDENCE_MIN_ITEMS


def validate_observation_document(
    document: dict[str, Any],
    item: dict[str, Any],
    state: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    item_id = str(item.get("id", ""))
    label = f"observation[{item_id}]"
    validate_identity(document, state, label, errors)
    if document.get("observation_id") != item_id:
        errors.append(
            f"{label}.observation_id: expected {item_id!r}, got {document.get('observation_id')!r}"
        )
    if document.get("observation_type") != item.get("type"):
        errors.append(
            f"{label}.observation_type: expected {item.get('type')!r}, "
            f"got {document.get('observation_type')!r}"
        )
    if document.get("status") != "complete":
        errors.append(f"{label}.status: set to 'complete' after finishing this work item")

    strict = state.get("schema_version") == STAGED_SCHEMA_VERSION
    deep_contract = True
    claim_review_quality = True
    nv_inspection_required = True
    nv_expression_families = True
    rubric, _, protocol_errors = protocol()
    errors.extend(protocol_errors)
    valid_criteria = set(criterion_order(rubric)) if not protocol_errors else set()

    expected_claims = _validate_string_list(
        item.get("expected_claim_ids", []), f"work-item[{item_id}].expected_claim_ids", errors
    )
    document_expected = _validate_string_list(
        document.get("expected_claim_ids"), f"{label}.expected_claim_ids", errors
    )
    if document_expected != expected_claims:
        errors.append(f"{label}.expected_claim_ids: do not change the initialized claim list")
    reviewed = _validate_string_list(
        document.get("reviewed_claim_ids"), f"{label}.reviewed_claim_ids", errors
    )

    required_checks = _validate_string_list(
        item.get("required_checks", []), f"work-item[{item_id}].required_checks", errors
    )
    completed_checks = _validate_string_list(
        document.get("completed_checks"), f"{label}.completed_checks", errors
    )

    observations = document.get("observations")
    if not isinstance(observations, list) or not observations:
        errors.append(f"{label}.observations: expected at least one evidence-backed observation")
        return errors
    observation_ids: set[str] = set()
    covered_claims: set[str] = set()
    mapped_checks: set[str] = set()
    available_evidence_ids: set[str] = set()
    evidence_types_by_id: dict[str, str] = {}
    available_defect_keys: set[str] = set()
    for index, observation in enumerate(observations):
        entry = f"{label}.observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{entry}: expected an object")
            continue
        observation_id = observation.get("observation_id")
        if not isinstance(observation_id, str) or not OBSERVATION_ID.fullmatch(observation_id):
            errors.append(f"{entry}.observation_id: invalid observation ID")
        elif observation_id in observation_ids:
            errors.append(f"{entry}.observation_id: duplicate {observation_id}")
        else:
            observation_ids.add(observation_id)
        criterion_ids = _validate_string_list(
            observation.get("criterion_ids"), f"{entry}.criterion_ids", errors
        )
        unknown_criteria = sorted(set(criterion_ids) - valid_criteria)
        if unknown_criteria:
            errors.append(f"{entry}.criterion_ids: unknown criteria {unknown_criteria}")
        claim_ids = _validate_string_list(observation.get("claim_ids"), f"{entry}.claim_ids", errors)
        covered_claims.update(claim_ids)
        if strict and item.get("type") == "feature":
            unknown_claims = sorted(set(claim_ids) - set(expected_claims))
            if unknown_claims:
                errors.append(f"{entry}.claim_ids: unknown Feature claims {unknown_claims}")
        if observation.get("local_outcome") not in LOCAL_OUTCOMES:
            errors.append(f"{entry}.local_outcome: unsupported value")
        if observation.get("breadth") not in BREADTHS:
            errors.append(f"{entry}.breadth: unsupported value")
        for key in ("contract_family", "fact"):
            if not isinstance(observation.get(key), str) or not observation.get(key):
                errors.append(f"{entry}.{key}: expected a non-empty string")
        evidence = observation.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{entry}.evidence: expected a list")
            continue
        minimum_evidence = _observation_evidence_minimums(
            state.get("evaluator_version")
        ).get(
            observation.get("local_outcome"), 0
        )
        if len(evidence) < minimum_evidence:
            errors.append(f"{entry}.evidence: evidence is required for this local outcome")
        for evidence_index, evidence_item in enumerate(evidence):
            _validate_evidence(evidence_item, f"{entry}.evidence[{evidence_index}]", errors)
            if isinstance(evidence_item, dict) and isinstance(evidence_item.get("evidence_id"), str):
                available_evidence_ids.add(evidence_item["evidence_id"])
                if isinstance(evidence_item.get("type"), str):
                    evidence_types_by_id[evidence_item["evidence_id"]] = evidence_item["type"]
        if (
            nv_inspection_required
            and observation.get("local_outcome") == "NOT_VERIFIABLE"
            and not any(
                isinstance(evidence_item, dict)
                and evidence_item.get("type") == "review_record"
                for evidence_item in evidence
            )
        ):
            errors.append(
                f"{entry}.evidence: NOT_VERIFIABLE requires review_record inspection evidence"
            )
        if strict:
            check_ids = _validate_string_list(
                observation.get("check_ids"), f"{entry}.check_ids", errors
            )
            unknown_checks = sorted(set(check_ids) - set(required_checks))
            if unknown_checks:
                errors.append(f"{entry}.check_ids: unknown checks {unknown_checks}")
            mapped_checks.update(check_ids)
            local_outcome = observation.get("local_outcome")
            defect_key = observation.get("defect_key")
            primary_criterion = observation.get("primary_criterion_id")
            if local_outcome in {"CONFLICT", "MISSING"}:
                if not isinstance(defect_key, str) or not DEFECT_KEY.fullmatch(defect_key):
                    errors.append(f"{entry}.defect_key: required for conflict or missing observations")
                else:
                    available_defect_keys.add(defect_key)
                if primary_criterion not in criterion_ids:
                    errors.append(
                        f"{entry}.primary_criterion_id: must be one of the observation Criterion IDs"
                    )
                if deep_contract and set(criterion_ids) & FUNCTION_MODELING_CRITERIA:
                    basis = observation.get("modeling_basis")
                    if not isinstance(basis, dict):
                        errors.append(
                            f"{entry}.modeling_basis: required for Function modeling defects"
                        )
                    else:
                        issue_type = basis.get("issue_type")
                        if issue_type not in MODELING_ISSUE_TYPES:
                            errors.append(f"{entry}.modeling_basis.issue_type: unsupported value")
                        for key in ("capability", "why_dependency_or_detail_is_insufficient"):
                            if not isinstance(basis.get(key), str) or not basis.get(key):
                                errors.append(
                                    f"{entry}.modeling_basis.{key}: expected a non-empty string"
                                )
                        roles = basis.get("feat_roles")
                        if not isinstance(roles, list) or not roles:
                            errors.append(f"{entry}.modeling_basis.feat_roles: expected a non-empty list")
                            roles = []
                        owner_roles = []
                        for role_index, role in enumerate(roles):
                            role_label = f"{entry}.modeling_basis.feat_roles[{role_index}]"
                            if not isinstance(role, dict):
                                errors.append(f"{role_label}: expected an object")
                                continue
                            if not isinstance(role.get("feat_id"), str) or not role.get("feat_id"):
                                errors.append(f"{role_label}.feat_id: expected a non-empty string")
                            if role.get("role") not in {"owner", "consumer", "context"}:
                                errors.append(f"{role_label}.role: unsupported value")
                            claim_ids = _validate_string_list(
                                role.get("acceptance_claim_ids"),
                                f"{role_label}.acceptance_claim_ids",
                                errors,
                            )
                            if role.get("role") == "owner":
                                owner_roles.append((role, claim_ids))
                        if issue_type in {"ownership_overlap", "ambiguous_boundary"}:
                            if len(owner_roles) < 2 or any(not claims for _, claims in owner_roles):
                                errors.append(
                                    f"{entry}.modeling_basis: overlap requires two Feats with "
                                    "independent acceptance claims"
                                )
                            incompatible = _validate_string_list(
                                basis.get("incompatible_contracts"),
                                f"{entry}.modeling_basis.incompatible_contracts",
                                errors,
                            )
                            if basis.get("independent_acceptance_conflict") is not True:
                                errors.append(
                                    f"{entry}.modeling_basis.independent_acceptance_conflict: "
                                    "must be true for overlap"
                                )
                            if not incompatible and basis.get("ambiguous_owner") is not True:
                                errors.append(
                                    f"{entry}.modeling_basis: overlap requires incompatible "
                                    "contracts or a genuinely ambiguous owner"
                                )
            elif defect_key is not None or primary_criterion is not None:
                errors.append(
                    f"{entry}: defect ownership fields are only valid for CONFLICT or MISSING"
                )

    if strict:
        claim_reviews = document.get("claim_reviews")
        if not isinstance(claim_reviews, list):
            errors.append(f"{label}.claim_reviews: expected a list")
            claim_reviews = []
        claim_review_ids: list[str] = []
        for index, claim_review in enumerate(claim_reviews):
            entry = f"{label}.claim_reviews[{index}]"
            if not isinstance(claim_review, dict):
                errors.append(f"{entry}: expected an object")
                continue
            claim_id = claim_review.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id:
                errors.append(f"{entry}.claim_id: expected a non-empty string")
                continue
            claim_review_ids.append(claim_id)
            if claim_review.get("status") != "complete":
                errors.append(f"{entry}.status: set to 'complete' after atomic claim review")
            local_outcome = claim_review.get("local_outcome")
            if local_outcome not in LOCAL_OUTCOMES:
                errors.append(f"{entry}.local_outcome: unsupported value")
            reviewed_units = _validate_string_list(
                claim_review.get("reviewed_units"), f"{entry}.reviewed_units", errors
            )
            if not reviewed_units:
                errors.append(f"{entry}.reviewed_units: enumerate the checked scope units")
            criterion_ids = _validate_string_list(
                claim_review.get("criterion_ids"), f"{entry}.criterion_ids", errors
            )
            unknown_criteria = sorted(set(criterion_ids) - valid_criteria)
            if unknown_criteria:
                errors.append(f"{entry}.criterion_ids: unknown criteria {unknown_criteria}")
            if not criterion_ids:
                errors.append(f"{entry}.criterion_ids: at least one Criterion is required")
            evidence_ids = _validate_string_list(
                claim_review.get("evidence_ids"), f"{entry}.evidence_ids", errors
            )
            missing_evidence = sorted(set(evidence_ids) - available_evidence_ids)
            if missing_evidence:
                errors.append(f"{entry}.evidence_ids: unknown evidence {missing_evidence}")
            inspection_evidence = {
                evidence_id
                for evidence_id in evidence_ids
                if evidence_types_by_id.get(evidence_id) == "review_record"
            }
            if local_outcome == "NOT_VERIFIABLE" and nv_inspection_required:
                if not evidence_ids:
                    errors.append(
                        f"{entry}.evidence_ids: inspection evidence is required for NOT_VERIFIABLE"
                    )
                elif not inspection_evidence:
                    errors.append(
                        f"{entry}.evidence_ids: NOT_VERIFIABLE must reference review_record inspection evidence"
                    )
            elif local_outcome != "NOT_VERIFIABLE" and not evidence_ids:
                errors.append(f"{entry}.evidence_ids: evidence is required for this outcome")
            reason = claim_review.get("reason")
            if not isinstance(reason, str) or not reason or PLACEHOLDER_TEXT in reason:
                errors.append(f"{entry}.reason: replace the initialized placeholder")
            elif claim_review_quality and _is_low_information_review_text(reason):
                errors.append(f"{entry}.reason: expected an evidence-specific explanation")
            elif (
                local_outcome == "NOT_VERIFIABLE"
                and nv_inspection_required
                and not _has_unverifiable_gap_explanation(
                    reason, expression_families=nv_expression_families
                )
            ):
                errors.append(
                    f"{entry}.reason: expected checked scope, missing evidence and insufficiency explanation"
                )
            defect_keys = _validate_string_list(
                claim_review.get("defect_keys"), f"{entry}.defect_keys", errors
            )
            if local_outcome in {"CONFLICT", "MISSING"}:
                if not defect_keys:
                    errors.append(f"{entry}.defect_keys: required for conflict or missing claims")
                unknown_defects = sorted(set(defect_keys) - available_defect_keys)
                if unknown_defects:
                    errors.append(f"{entry}.defect_keys: unknown defects {unknown_defects}")
            elif defect_keys:
                errors.append(f"{entry}.defect_keys: only conflict or missing claims may own defects")
            if deep_contract:
                unit_reviews = claim_review.get("unit_reviews")
                if not isinstance(unit_reviews, list) or not unit_reviews:
                    errors.append(f"{entry}.unit_reviews: expected at least one atomic unit review")
                    unit_reviews = []
                unit_ids: list[str] = []
                unit_outcomes: list[str] = []
                for unit_index, unit in enumerate(unit_reviews):
                    unit_label = f"{entry}.unit_reviews[{unit_index}]"
                    if not isinstance(unit, dict):
                        errors.append(f"{unit_label}: expected an object")
                        continue
                    unit_id = unit.get("unit_id")
                    if not isinstance(unit_id, str) or not unit_id:
                        errors.append(f"{unit_label}.unit_id: expected a non-empty string")
                    else:
                        unit_ids.append(unit_id)
                    if unit.get("facet_type") not in UNIT_FACET_TYPES:
                        errors.append(f"{unit_label}.facet_type: unsupported value")
                    unit_outcome = unit.get("local_outcome")
                    if unit_outcome not in LOCAL_OUTCOMES:
                        errors.append(f"{unit_label}.local_outcome: unsupported value")
                    else:
                        unit_outcomes.append(unit_outcome)
                    unit_evidence = _validate_string_list(
                        unit.get("evidence_ids"), f"{unit_label}.evidence_ids", errors
                    )
                    unknown_unit_evidence = sorted(set(unit_evidence) - available_evidence_ids)
                    if unknown_unit_evidence:
                        errors.append(
                            f"{unit_label}.evidence_ids: unknown evidence {unknown_unit_evidence}"
                        )
                    unit_inspection_evidence = {
                        evidence_id
                        for evidence_id in unit_evidence
                        if evidence_types_by_id.get(evidence_id) == "review_record"
                    }
                    if unit_outcome == "NOT_VERIFIABLE" and nv_inspection_required:
                        if not unit_evidence:
                            errors.append(
                                f"{unit_label}.evidence_ids: inspection evidence is required for NOT_VERIFIABLE"
                            )
                        elif not unit_inspection_evidence:
                            errors.append(
                                f"{unit_label}.evidence_ids: NOT_VERIFIABLE must reference review_record inspection evidence"
                            )
                    elif unit_outcome != "NOT_VERIFIABLE" and not unit_evidence:
                        errors.append(f"{unit_label}.evidence_ids: evidence is required")
                    fact = unit.get("fact")
                    if not isinstance(fact, str) or not fact or PLACEHOLDER_TEXT in fact:
                        errors.append(f"{unit_label}.fact: expected a resolved atomic fact")
                    elif claim_review_quality and _is_low_information_review_text(fact):
                        errors.append(f"{unit_label}.fact: expected an evidence-specific atomic fact")
                    elif (
                        unit_outcome == "NOT_VERIFIABLE"
                        and nv_inspection_required
                        and not _has_unverifiable_gap_explanation(
                            fact, expression_families=nv_expression_families
                        )
                    ):
                        errors.append(
                            f"{unit_label}.fact: expected checked scope, missing evidence and insufficiency explanation"
                        )
                if unit_ids != reviewed_units:
                    errors.append(
                        f"{entry}.unit_reviews: unit IDs must exactly match reviewed_units in order"
                    )
                if local_outcome in {"CONFLICT", "MISSING", "NOT_VERIFIABLE"}:
                    if local_outcome not in unit_outcomes:
                        errors.append(
                            f"{entry}.unit_reviews: at least one unit must carry claim outcome "
                            f"{local_outcome}"
                        )
                elif local_outcome == "SUPPORTED" and any(
                    outcome != "SUPPORTED" for outcome in unit_outcomes
                ):
                    errors.append(
                        f"{entry}.unit_reviews: a supported claim requires all units supported"
                    )
                elif local_outcome == "NOT_APPLICABLE" and any(
                    outcome != "NOT_APPLICABLE" for outcome in unit_outcomes
                ):
                    errors.append(
                        f"{entry}.unit_reviews: an inapplicable claim requires all units inapplicable"
                    )
        if claim_review_ids != expected_claims:
            errors.append(
                f"{label}.claim_reviews: must contain every expected claim exactly once in initialized order"
            )
        if reviewed != claim_review_ids:
            errors.append(
                f"{label}.reviewed_claim_ids: must equal the derived claim-review IDs in order"
            )
        if set(mapped_checks) != set(required_checks):
            missing = sorted(set(required_checks) - mapped_checks)
            extra = sorted(mapped_checks - set(required_checks))
            errors.append(f"{label}.observations.check_ids: missing={missing} extra={extra}")
        if set(completed_checks) != mapped_checks:
            errors.append(
                f"{label}.completed_checks: must equal the checks mapped by observations"
            )
    else:
        if set(reviewed) != set(expected_claims):
            missing = sorted(set(expected_claims) - set(reviewed))
            extra = sorted(set(reviewed) - set(expected_claims))
            errors.append(f"{label}.reviewed_claim_ids: missing={missing} extra={extra}")
        if set(completed_checks) != set(required_checks):
            missing = sorted(set(required_checks) - set(completed_checks))
            extra = sorted(set(completed_checks) - set(required_checks))
            errors.append(f"{label}.completed_checks: missing={missing} extra={extra}")
        missing_coverage = sorted(set(expected_claims) - covered_claims)
        if missing_coverage:
            errors.append(f"{label}.observations: expected claims not represented: {missing_coverage}")
    return errors


def validate_aggregation_document(
    document: dict[str, Any],
    state: dict[str, Any],
    work_items: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    validate_identity(document, state, "aggregation", errors)
    if document.get("status") != "complete":
        errors.append("aggregation.status: set to 'complete' after Function-level aggregation")
    expected_sources = [item["id"] for item in work_items.get("items", [])]
    sources = _validate_string_list(
        document.get("source_observation_ids"), "aggregation.source_observation_ids", errors
    )
    if sources != expected_sources:
        errors.append("aggregation.source_observation_ids: must list every work item in order")
    if document.get("cross_feat_contracts_reviewed") is not True:
        errors.append("aggregation.cross_feat_contracts_reviewed: must be true")
    results = document.get("criterion_results")
    if not isinstance(results, list):
        errors.append("aggregation.criterion_results: expected a list")
        return errors
    rubric, _, protocol_errors = protocol()
    errors.extend(protocol_errors)
    expected_order = criterion_order(rubric) if not protocol_errors else []
    actual_order = [item.get("criterion_id") for item in results if isinstance(item, dict)]
    if actual_order != expected_order:
        errors.append(
            f"aggregation.criterion_results: expected Criterion order {expected_order}, got {actual_order}"
        )
    findings_by_id: dict[str, dict[str, Any]] = {}
    contradicted_criteria: list[str] = []
    for index, result in enumerate(results):
        label = f"aggregation.criterion_results[{index}]"
        if not isinstance(result, dict):
            errors.append(f"{label}: expected an object")
            continue
        if PLACEHOLDER_TEXT in str(result.get("reason", "")):
            errors.append(f"{label}.reason: replace the template placeholder")
        conclusion = result.get("conclusion")
        findings = result.get("findings", [])
        if conclusion in FINDING_REQUIRED_CONCLUSIONS and not findings:
            errors.append(
                f"{result.get('criterion_id')}: {conclusion} requires an evidence-backed finding"
            )
        if conclusion in {"SUPPORTED", "NOT_APPLICABLE"} and findings:
            errors.append(
                f"{result.get('criterion_id')}: {conclusion} must not contain defect findings"
            )
        if result.get("conclusion") == "CONTRADICTED" and isinstance(
            result.get("criterion_id"), str
        ):
            contradicted_criteria.append(result["criterion_id"])
        evidence_ids = {
            evidence.get("evidence_id")
            for evidence in result.get("evidence", [])
            if isinstance(evidence, dict)
        }
        for finding_index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            finding_id = finding.get("finding_id")
            if not isinstance(finding_id, str) or not finding_id:
                errors.append(f"{label}.findings[{finding_index}].finding_id: required")
            elif finding_id in findings_by_id:
                errors.append(f"{label}.findings[{finding_index}].finding_id: duplicate {finding_id}")
            else:
                findings_by_id[finding_id] = finding
            missing = sorted(set(finding.get("evidence_ids", [])) - evidence_ids)
            if missing:
                errors.append(
                    f"{label}.findings[{finding_index}].evidence_ids: not present in Criterion "
                    f"evidence: {missing}"
                )
            if conclusion in FINDING_REQUIRED_CONCLUSIONS and not finding.get("evidence_ids"):
                errors.append(
                    f"{label}.findings[{finding_index}].evidence_ids: at least one evidence ID "
                    "is required for an evidence-backed Finding"
                )
    if state.get("schema_version") != STAGED_SCHEMA_VERSION:
        return errors

    try:
        aggregation_context = build_aggregation_context(state, work_items)
    except ValueError as exc:
        errors.append(f"aggregation: cannot build mapped-unit context: {exc}")
        aggregation_context = {"criterion_mappings": []}
    mappings_by_id = {
        mapping.get("criterion_id"): mapping
        for mapping in aggregation_context.get("criterion_mappings", [])
        if isinstance(mapping, dict) and isinstance(mapping.get("criterion_id"), str)
    }

    observed_defects: dict[str, str] = {}
    adverse_criteria: set[str] = set()
    unverifiable_criteria: set[str] = set()
    for criterion_id, mapping in mappings_by_id.items():
        for observation in mapping.get("observations", []):
            if not isinstance(observation, dict):
                continue
            if observation.get("local_outcome") in {"CONFLICT", "MISSING"}:
                adverse_criteria.add(criterion_id)
            if observation.get("local_outcome") == "NOT_VERIFIABLE":
                unverifiable_criteria.add(criterion_id)
            defect_key = observation.get("defect_key")
            primary = observation.get("primary_criterion_id")
            if not isinstance(defect_key, str):
                continue
            if defect_key in observed_defects and observed_defects[defect_key] != primary:
                errors.append(
                    f"aggregation: defect {defect_key!r} has conflicting observation primary Criteria"
                )
            elif isinstance(primary, str):
                observed_defects[defect_key] = primary
        if any(
            isinstance(claim, dict) and claim.get("local_outcome") == "NOT_VERIFIABLE"
            for claim in mapping.get("claims", [])
        ) or any(
            isinstance(unit, dict) and unit.get("local_outcome") == "NOT_VERIFIABLE"
            for unit in mapping.get("atomic_units", [])
        ):
            unverifiable_criteria.add(criterion_id)

    mapping_guard = True
    for result in results:
        if not isinstance(result, dict):
            continue
        criterion_id = result.get("criterion_id")
        conclusion = result.get("conclusion")
        mapping = mappings_by_id.get(criterion_id, {})
        constraints = mapping.get("constraints", {}) if isinstance(mapping, dict) else {}
        if mapping_guard:
            mapped_claim_ids = set(mapping.get("mapped_claim_ids", []))
            result_claim_ids = result.get("claim_ids")
            if isinstance(result_claim_ids, list):
                unmapped_claim_ids = sorted(
                    claim_id
                    for claim_id in result_claim_ids
                    if isinstance(claim_id, str) and claim_id not in mapped_claim_ids
                )
                if unmapped_claim_ids:
                    errors.append(
                        f"aggregation.criterion_results[{criterion_id}].claim_ids: not mapped to "
                        f"Criterion: {unmapped_claim_ids}"
                    )
            adverse_refs = constraints.get("adverse_unit_refs", [])
            unverifiable_refs = constraints.get("unverifiable_unit_refs", [])
            applicable_refs = constraints.get("applicable_unit_refs", [])
            required = constraints.get("required_conclusion_when_no_adverse")
            if required and conclusion != required:
                errors.append(
                    f"aggregation.criterion_results[{criterion_id}]: mapped NOT_VERIFIABLE units "
                    f"{_format_mapping_refs(unverifiable_refs)} require {required} when no adverse "
                    f"unit is mapped, got {conclusion}"
                )
            elif adverse_refs and conclusion in {"SUPPORTED", "NOT_APPLICABLE"}:
                errors.append(
                    f"aggregation.criterion_results[{criterion_id}]: mapped adverse units "
                    f"{_format_mapping_refs(adverse_refs)} may not aggregate to {conclusion}"
                )
            elif applicable_refs and conclusion == "NOT_APPLICABLE":
                errors.append(
                    f"aggregation.criterion_results[{criterion_id}]: mapped applicable units "
                    f"{_format_mapping_refs(applicable_refs)} may not aggregate to NOT_APPLICABLE"
                )

    policy_bases = document.get("outcome_policy_bases")
    if not isinstance(policy_bases, list):
        errors.append("aggregation.outcome_policy_bases: expected a list")
        policy_bases = []
    actual_policy_order: list[str] = []
    results_by_id = {
        result.get("criterion_id"): result for result in results if isinstance(result, dict)
    }
    for index, basis in enumerate(policy_bases):
        label = f"aggregation.outcome_policy_bases[{index}]"
        if not isinstance(basis, dict):
            errors.append(f"{label}: expected an object")
            continue
        criterion_id = basis.get("criterion_id")
        if not isinstance(criterion_id, str) or not criterion_id:
            errors.append(f"{label}.criterion_id: required")
            continue
        actual_policy_order.append(criterion_id)
        content_status = basis.get("content_status")
        evidence_status = basis.get("evidence_status")
        conflict_scope = basis.get("conflict_scope")
        if content_status not in POLICY_CONTENT_STATUSES:
            errors.append(f"{label}.content_status: unsupported value")
        if evidence_status not in POLICY_EVIDENCE_STATUSES:
            errors.append(f"{label}.evidence_status: unsupported value")
        if conflict_scope not in POLICY_CONFLICT_SCOPES:
            errors.append(f"{label}.conflict_scope: unsupported value")
        reason = basis.get("reason")
        if not isinstance(reason, str) or not reason or PLACEHOLDER_TEXT in reason:
            errors.append(f"{label}.reason: replace the template placeholder")

        statuses = {content_status, evidence_status, conflict_scope}
        has_not_applicable = "NOT_APPLICABLE" in statuses
        all_not_applicable = (
            content_status == evidence_status == conflict_scope == "NOT_APPLICABLE"
        )
        if has_not_applicable and not all_not_applicable:
            errors.append(f"{label}: NOT_APPLICABLE must be used by all three status fields")
            continue
        if all_not_applicable:
            expected_conclusion = "NOT_APPLICABLE"
        elif conflict_scope == "CORE":
            expected_conclusion = "CONTRADICTED"
        elif content_status in {"ABSENT", "PLACEHOLDER_ONLY"}:
            expected_conclusion = "MISSING"
        elif conflict_scope == "LOCAL":
            expected_conclusion = "PARTIALLY_SUPPORTED"
        elif evidence_status == "UNAVAILABLE":
            expected_conclusion = "NOT_VERIFIABLE"
        elif evidence_status == "PARTIAL":
            expected_conclusion = "PARTIALLY_SUPPORTED"
        else:
            expected_conclusion = "SUPPORTED"
        actual_conclusion = results_by_id.get(criterion_id, {}).get("conclusion")
        if actual_conclusion != expected_conclusion:
            errors.append(
                f"{label}: statuses require {expected_conclusion}, got {actual_conclusion}"
            )
    if actual_policy_order != OUTCOME_POLICY_BASIS_CRITERIA:
        errors.append(
            "aggregation.outcome_policy_bases: expected Criterion order "
            f"{OUTCOME_POLICY_BASIS_CRITERIA}, got {actual_policy_order}"
        )

    ownership = document.get("defect_ownership")
    if not isinstance(ownership, list):
        errors.append("aggregation.defect_ownership: expected a list")
        ownership = []
    ownership_by_key: dict[str, dict[str, Any]] = {}
    finding_owners: dict[str, list[str]] = {}
    for index, record in enumerate(ownership):
        label = f"aggregation.defect_ownership[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: expected an object")
            continue
        defect_key = record.get("defect_key")
        if not isinstance(defect_key, str) or not DEFECT_KEY.fullmatch(defect_key):
            errors.append(f"{label}.defect_key: invalid defect key")
            continue
        if defect_key in ownership_by_key:
            errors.append(f"{label}.defect_key: duplicate {defect_key}")
        else:
            ownership_by_key[defect_key] = record
        primary = record.get("primary_criterion_id")
        if primary not in actual_order:
            errors.append(f"{label}.primary_criterion_id: unknown Criterion {primary!r}")
        finding_ids = _validate_string_list(record.get("finding_ids"), f"{label}.finding_ids", errors)
        if not finding_ids:
            errors.append(f"{label}.finding_ids: at least one Finding is required")
        involved_criteria: set[str] = set()
        critical_criteria: list[str] = []
        for finding_id in finding_ids:
            finding_owners.setdefault(finding_id, []).append(defect_key)
            finding = findings_by_id.get(finding_id)
            if finding is None:
                errors.append(f"{label}.finding_ids: unknown Finding {finding_id}")
                continue
            criterion_id = finding.get("criterion_id")
            if isinstance(criterion_id, str):
                involved_criteria.add(criterion_id)
                if finding.get("severity") == "Critical":
                    critical_criteria.append(criterion_id)
        if involved_criteria and primary not in involved_criteria:
            errors.append(f"{label}.primary_criterion_id: must own one mapped Finding")
        secondary = _validate_string_list(
            record.get("secondary_criterion_ids"), f"{label}.secondary_criterion_ids", errors
        )
        expected_secondary = sorted(involved_criteria - {primary})
        if sorted(secondary) != expected_secondary:
            errors.append(
                f"{label}.secondary_criterion_ids: expected {expected_secondary}, got {sorted(secondary)}"
            )
        if len(critical_criteria) > 1:
            errors.append(f"{label}: one defect may produce at most one Critical Finding")
        if critical_criteria and critical_criteria[0] != primary:
            errors.append(f"{label}: a Critical Finding must belong to the primary Criterion")
        observed_primary = observed_defects.get(defect_key)
        if observed_primary is None:
            errors.append(f"{label}.defect_key: not defined by a validated observation")
        elif observed_primary != primary:
            errors.append(
                f"{label}.primary_criterion_id: expected observation owner {observed_primary!r}"
            )

    for finding_id in findings_by_id:
        owners = finding_owners.get(finding_id, [])
        if len(owners) != 1:
            errors.append(
                f"aggregation.defect_ownership: Finding {finding_id} must have exactly one owner; "
                f"got {owners}"
            )

    func_id = document.get("func_id")
    if isinstance(func_id, str):
        for finding_id, finding in findings_by_id.items():
            owners = finding_owners.get(finding_id, [])
            if len(owners) != 1:
                continue
            criterion_id = finding.get("criterion_id")
            claim_id = finding.get("claim_id")
            if not isinstance(criterion_id, str) or (
                claim_id is not None and not isinstance(claim_id, str)
            ):
                continue
            expected_id = semantic_finding_id(
                func_id=func_id,
                defect_key=owners[0],
                criterion_id=criterion_id,
                claim_id=claim_id,
            )
            if finding_id != expected_id:
                errors.append(
                    f"aggregation.finding_id {finding_id}: expected deterministic ID "
                    f"{expected_id}"
                )

    bases = document.get("contradiction_bases")
    if not isinstance(bases, list):
        errors.append("aggregation.contradiction_bases: expected a list")
        bases = []
    basis_criteria: list[str] = []
    for index, basis in enumerate(bases):
        label = f"aggregation.contradiction_bases[{index}]"
        if not isinstance(basis, dict):
            errors.append(f"{label}: expected an object")
            continue
        criterion_id = basis.get("criterion_id")
        if not isinstance(criterion_id, str) or not criterion_id:
            errors.append(f"{label}.criterion_id: required")
            continue
        basis_criteria.append(criterion_id)
        for key in ("core_claim", "core_scope", "why_partial_is_insufficient"):
            if not isinstance(basis.get(key), str) or not basis.get(key):
                errors.append(f"{label}.{key}: expected a non-empty string")
        affected = _validate_string_list(
            basis.get("affected_feat_ids"), f"{label}.affected_feat_ids", errors
        )
        if not affected:
            errors.append(f"{label}.affected_feat_ids: at least one affected Feat is required")
        families = _validate_string_list(
            basis.get("independent_contract_families"),
            f"{label}.independent_contract_families",
            errors,
        )
        if len(families) < 2 and basis.get("function_shared_assertion") is not True:
            errors.append(
                f"{label}: CONTRADICTED requires two independent contract families or one "
                "materially false Function-shared assertion"
            )
        if basis.get("correction_scope") != "replace_core":
            errors.append(f"{label}.correction_scope: expected 'replace_core'")
        primary_defect = basis.get("primary_defect_key")
        owner = ownership_by_key.get(primary_defect)
        if owner is None:
            errors.append(f"{label}.primary_defect_key: unknown defect {primary_defect!r}")
        else:
            owned_criteria = {
                owner.get("primary_criterion_id"),
                *owner.get("secondary_criterion_ids", []),
            }
            if criterion_id not in owned_criteria:
                errors.append(
                    f"{label}.primary_defect_key: defect does not affect Criterion {criterion_id}"
                )
    if basis_criteria != contradicted_criteria:
        errors.append(
            "aggregation.contradiction_bases: must contain every CONTRADICTED Criterion "
            f"exactly once in Criterion order; expected {contradicted_criteria}, got {basis_criteria}"
        )
    return errors


def repair_aggregation_contract(
    document: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Apply deterministic final-contract normalization once.

    The repair is deliberately structural: it does not change conclusions,
    classification, evidence, recommendations, or explanatory prose.
    """
    repaired = copy.deepcopy(document)
    changes: list[str] = []
    ownership = repaired.get("defect_ownership")
    results = repaired.get("criterion_results")
    if not isinstance(ownership, list) or not isinstance(results, list):
        raise ValueError("aggregation contract repair requires ownership and Criterion lists")

    owner_by_finding_id: dict[str, str] = {}
    for record in ownership:
        if not isinstance(record, dict):
            continue
        defect_key = record.get("defect_key")
        finding_ids = record.get("finding_ids")
        if not isinstance(defect_key, str) or not isinstance(finding_ids, list):
            continue
        for finding_id in finding_ids:
            if not isinstance(finding_id, str):
                continue
            previous = owner_by_finding_id.get(finding_id)
            if previous is not None and previous != defect_key:
                raise ValueError(
                    f"Finding {finding_id} has conflicting owners {previous!r} and {defect_key!r}"
                )
            owner_by_finding_id[finding_id] = defect_key

    func_id = repaired.get("func_id")
    if not isinstance(func_id, str) or not func_id:
        raise ValueError("aggregation contract repair requires func_id")
    rewritten_ids: dict[str, str] = {}
    canonical_ids: set[str] = set()
    for result_index, result in enumerate(results):
        if not isinstance(result, dict):
            continue
        if (
            result.get("conclusion") == "NOT_APPLICABLE"
            and not str(result.get("applicability_reason", "")).strip()
            and str(result.get("reason", "")).strip()
            and isinstance(result.get("evidence"), list)
            and result["evidence"]
        ):
            result["applicability_reason"] = result["reason"]
            changes.append(
                f"criterion_results[{result_index}].applicability_reason copied from reason"
            )
        findings = result.get("findings")
        if not isinstance(findings, list):
            continue
        for finding_index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            label = f"criterion_results[{result_index}].findings[{finding_index}]"
            problem = finding.get("problem")
            message = finding.get("message")
            if problem is not None:
                if not isinstance(problem, str) or not problem:
                    raise ValueError(f"{label}.problem must be a non-empty string")
                if message is not None and message != problem:
                    raise ValueError(
                        f"{label} contains different message and problem values"
                    )
                if message is None:
                    finding["message"] = problem
                    changes.append(f"{label}.problem migrated to message")
                else:
                    changes.append(f"{label}.problem alias removed")
                finding.pop("problem", None)
            old_id = finding.get("finding_id")
            defect_key = owner_by_finding_id.get(old_id) if isinstance(old_id, str) else None
            criterion_id = finding.get("criterion_id")
            claim_id = finding.get("claim_id")
            if defect_key is None or not isinstance(criterion_id, str):
                continue
            if claim_id is not None and not isinstance(claim_id, str):
                continue
            new_id = semantic_finding_id(
                func_id=func_id,
                defect_key=defect_key,
                criterion_id=criterion_id,
                claim_id=claim_id,
            )
            if new_id in canonical_ids:
                raise ValueError(f"{label}: deterministic Finding ID collision {new_id}")
            canonical_ids.add(new_id)
            if old_id != new_id:
                finding["finding_id"] = new_id
                rewritten_ids[old_id] = new_id
                changes.append(f"{label}.finding_id rewritten to {new_id}")

    for owner_index, record in enumerate(ownership):
        if not isinstance(record, dict) or not isinstance(record.get("finding_ids"), list):
            continue
        updated = [rewritten_ids.get(finding_id, finding_id) for finding_id in record["finding_ids"]]
        if updated != record["finding_ids"]:
            record["finding_ids"] = updated
            changes.append(f"defect_ownership[{owner_index}].finding_ids synchronized")

    findings_by_id: dict[str, dict[str, Any]] = {}
    for result in results:
        if not isinstance(result, dict) or not isinstance(result.get("findings"), list):
            continue
        for finding in result["findings"]:
            if not isinstance(finding, dict):
                continue
            finding_id = finding.get("finding_id")
            if not isinstance(finding_id, str):
                continue
            if finding_id in findings_by_id:
                raise ValueError(f"duplicate Finding correlation key {finding_id}")
            findings_by_id[finding_id] = finding

    for owner_index, record in enumerate(ownership):
        if not isinstance(record, dict):
            continue
        primary = record.get("primary_criterion_id")
        finding_ids = record.get("finding_ids")
        if not isinstance(primary, str) or not isinstance(finding_ids, list):
            continue
        owned_findings = [
            findings_by_id.get(finding_id)
            for finding_id in finding_ids
            if isinstance(finding_id, str)
        ]
        if len(owned_findings) != len(finding_ids) or any(
            finding is None for finding in owned_findings
        ):
            continue
        if any(
            not isinstance(finding, dict)
            or not isinstance(finding.get("criterion_id"), str)
            for finding in owned_findings
        ):
            continue
        expected_secondary = sorted({
            finding["criterion_id"]
            for finding in owned_findings
            if isinstance(finding, dict) and finding["criterion_id"] != primary
        })
        if record.get("secondary_criterion_ids") != expected_secondary:
            record["secondary_criterion_ids"] = expected_secondary
            changes.append(
                f"defect_ownership[{owner_index}].secondary_criterion_ids derived"
            )
    return repaired, changes


def build_final_candidate(
    semantic_template: dict[str, Any], aggregation: dict[str, Any]
) -> dict[str, Any]:
    candidate = copy.deepcopy(semantic_template)
    results = copy.deepcopy(aggregation["criterion_results"])
    candidate["criterion_results"] = results
    candidate["coverage"] = {
        "expected_criteria": len(results),
        "evaluated_criteria": len(results),
        "applicable_criteria": sum(
            item.get("applicability") == "APPLICABLE" for item in results
        ),
        "not_applicable_criteria": sum(
            item.get("conclusion") == "NOT_APPLICABLE" for item in results
        ),
        "not_verifiable_criteria": sum(
            item.get("conclusion") == "NOT_VERIFIABLE" for item in results
        ),
    }
    notes = list(candidate.get("execution", {}).get("notes", []))
    notes.append(
        "Staged execution: Feature and Function-global observations were checkpointed before final aggregation."
    )
    candidate["execution"] = {
        "static_complete": True,
        "evidence_complete": True,
        "semantic_complete": True,
        "notes": notes,
    }
    return candidate


def validate_final_candidate(
    candidate: dict[str, Any], aggregation: dict[str, Any]
) -> list[str]:
    rubric, complexity, errors = protocol()
    errors.extend(
        validate_semantic_result(candidate, rubric, complexity, EVALUATION_ROOT / "schemas")
    )
    if candidate.get("criterion_results") != aggregation.get("criterion_results"):
        errors.append("semantic-result.criterion_results: does not match aggregation.json")
    return errors


def update_progress(
    run_dir: Path,
    state: dict[str, Any],
    work_items: dict[str, Any],
    *,
    stage: str,
    work_item_id: str | None = None,
) -> None:
    validated = set(state.get("validated_work_items", []))
    if work_item_id is not None:
        validated.add(work_item_id)
    elif stage in {"observations", "aggregation", "final"}:
        validated.update(item["id"] for item in work_items.get("items", []))
    state["validated_work_items"] = [
        item["id"] for item in work_items.get("items", []) if item["id"] in validated
    ]
    for item in work_items.get("items", []):
        item["status"] = "complete" if item["id"] in validated else "pending"
    if stage in {"aggregation", "final"}:
        state["aggregation_validated"] = True
    if stage == "final":
        state["semantic_validated"] = True

    feature_ids = [
        item["id"] for item in work_items.get("items", []) if item.get("type") == "feature"
    ]
    function_ids = [
        item["id"]
        for item in work_items.get("items", [])
        if item.get("type") == "function_global"
    ]
    if any(item_id not in validated for item_id in feature_ids):
        phase = "feature_observations"
    elif any(item_id not in validated for item_id in function_ids):
        phase = "function_global"
    elif not state.get("aggregation_validated"):
        phase = "aggregation"
    elif not state.get("semantic_validated"):
        phase = "final_validation"
    else:
        phase = "complete"
    state["current_phase"] = phase
    write_object(run_dir / "work-items.json", work_items)
    write_object(run_dir / "run-state.json", state)
