"""Merge executor-owned payloads into service-owned staged templates.

The staged-run initializer owns identity, input, ordering, and derived fields.
The semantic executor only supplies the evidence-bearing mutable fields.  This
keeps model output from replacing or drifting the frozen staged-run contract.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Iterable


OBSERVATION_PAYLOAD_FIELDS = (
    "claim_reviews",
    "observations",
    "open_questions",
    "notes",
)

AGGREGATION_PAYLOAD_FIELDS = (
    "cross_feat_contracts_reviewed",
    "contradiction_bases",
    "defect_ownership",
    "outcome_policy_bases",
    "criterion_results",
    "notes",
)


def load_template(path: Path) -> dict[str, Any]:
    """Load one initialized staged document before the executor can touch it."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load initialized template {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"initialized template is not an object: {path}")
    return value


def observation_prompt_contract(
    template_path: Path, output_contract_path: Path | None = None
) -> dict[str, Any]:
    output_contract_path = output_contract_path or template_path.parents[1] / "output-contract.json"
    output_contract = _load_optional_output_contract(output_contract_path)
    return {
        "result_kind": "staged_observation_payload",
        "template_path": str(template_path),
        "output_contract_path": str(output_contract_path),
        "payload_fields": list(OBSERVATION_PAYLOAD_FIELDS),
        "service_derived_fields": ["status", "reviewed_claim_ids", "completed_checks"],
        "machine_contract": {
            "valid_criterion_ids": output_contract.get("valid_criterion_ids", []),
            "common": output_contract.get("common", {}),
            "payload": output_contract.get("observation_payload", {}),
        },
    }


def aggregation_prompt_contract(
    template_path: Path,
    output_contract_path: Path | None = None,
    aggregation_context_path: Path | None = None,
) -> dict[str, Any]:
    output_contract_path = output_contract_path or template_path.parent / "output-contract.json"
    output_contract = _load_optional_output_contract(output_contract_path)
    contract = {
        "result_kind": "staged_aggregation_payload",
        "template_path": str(template_path),
        "output_contract_path": str(output_contract_path),
        "payload_fields": list(AGGREGATION_PAYLOAD_FIELDS),
        "service_derived_fields": ["status", "source_observation_ids"],
        "service_normalized_fields": [
            "criterion_results[].findings[].finding_id",
            "defect_ownership[].finding_ids",
            "defect_ownership[].secondary_criterion_ids",
        ],
        "machine_contract": {
            "valid_criterion_ids": output_contract.get("valid_criterion_ids", []),
            "common": output_contract.get("common", {}),
            "payload": output_contract.get("aggregation_payload", {}),
        },
    }
    if aggregation_context_path is not None:
        contract["aggregation_context_path"] = str(aggregation_context_path)
    return contract


def repair_prompt_contract(
    base_contract: dict[str, Any],
    *,
    candidate_path: Path,
    validation_errors: Iterable[str],
) -> dict[str, Any]:
    """Describe one bounded mechanical repair without widening evidence access."""
    contract = copy.deepcopy(base_contract)
    contract.update({
        "mode": "repair_candidate",
        "candidate_path": str(candidate_path),
        "validation_errors": list(validation_errors),
        "repair_constraints": [
            "Preserve the candidate's semantic judgments, facts, claim coverage and ordering.",
            "Repair only the listed validation errors and linked references affected by those repairs.",
            "Do not reopen source, SDK, Spec, Design or evidence shards.",
            "Return the complete corrected executor-owned payload, not a patch.",
        ],
    })
    return contract


def observation_evidence_repair_prompt_contract(
    base_contract: dict[str, Any],
    *,
    candidate_path: Path,
    validation_errors: Iterable[str],
    target_observation_indexes: Iterable[int],
) -> dict[str, Any]:
    """Describe one evidence-backed repair without allowing semantic drift."""
    contract = copy.deepcopy(base_contract)
    contract.update({
        "mode": "complete_observation_evidence",
        "candidate_path": str(candidate_path),
        "validation_errors": list(validation_errors),
        "target_observation_indexes": list(target_observation_indexes),
        "repair_constraints": [
            "Use only the candidate and the original scoped frozen inputs.",
            "Populate evidence only for the target observation indexes.",
            "Preserve every outcome, fact, Claim/check/Criterion mapping and array ordering.",
            "Do not invent evidence or downgrade an outcome to avoid the evidence requirement.",
            "Return the complete corrected executor-owned payload, not a patch.",
        ],
    })
    return contract


def claim_evidence_repair_prompt_contract(
    base_contract: dict[str, Any],
    *,
    candidate_path: Path,
    validation_errors: Iterable[str],
    target_claim_ids: Iterable[str],
    available_evidence_ids: Iterable[str],
) -> dict[str, Any]:
    """Describe one bounded Claim evidence re-review against frozen inputs."""
    contract = copy.deepcopy(base_contract)
    contract.update({
        "mode": "repair_claim_evidence_references",
        "candidate_path": str(candidate_path),
        "validation_errors": list(validation_errors),
        "target_claim_ids": list(target_claim_ids),
        "available_evidence_ids": list(available_evidence_ids),
        "repair_constraints": [
            "Use only the candidate and the original scoped frozen inputs.",
            "Re-review only the named Claim rows and their atomic unit reviews.",
            "Reference only evidence IDs already defined by candidate observations.",
            "Replace outcome-only reason or fact text with an evidence-specific explanation.",
            "If existing evidence cannot support the current outcome, downgrade only the affected Claim or unit to NOT_VERIFIABLE, retain or reference review_record inspection evidence, and explain the checked scope, missing evidence and why it is insufficient.",
            "Do not add evidence, create defects, upgrade outcomes, or change Claim/Criteria/unit scope and ordering.",
            "Return the complete corrected executor-owned payload, not a patch.",
        ],
    })
    return contract


def quality_retry_prompt_contract(
    base_contract: dict[str, Any],
    *,
    quality_metrics: dict[str, int | float],
    reason_codes: Iterable[str],
) -> dict[str, Any]:
    """Request one complete re-evaluation after deterministic quality rejection."""
    contract = copy.deepcopy(base_contract)
    contract.update({
        "mode": "retry_degenerate_observation",
        "quality_metrics": dict(quality_metrics),
        "quality_reason_codes": list(reason_codes),
        "quality_retry_constraints": [
            "Re-evaluate the complete original work item from the original scoped frozen inputs.",
            "Read the declared evidence shards, Spec/Design and relevant frozen source or SDK inputs before judging claims.",
            "For every NOT_VERIFIABLE result, create review_record inspection evidence and reference it from the Claim and atomic unit.",
            "State the checked scope, missing evidence and why the gap is insufficient for a defensible judgment.",
            "Do not copy or repair the rejected candidate; produce an independent complete payload.",
        ],
    })
    return contract


def aggregation_reconciliation_prompt_contract(
    base_contract: dict[str, Any],
    *,
    candidate_path: Path,
    aggregation_context_path: Path,
    validation_errors: Iterable[str],
    target_criterion_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Describe one bounded semantic reconciliation against published mappings."""
    contract = copy.deepcopy(base_contract)
    contract.update({
        "mode": "reconcile_aggregation_candidate",
        "candidate_path": str(candidate_path),
        "aggregation_context_path": str(aggregation_context_path),
        "validation_errors": list(validation_errors),
        "target_criterion_ids": list(target_criterion_ids),
        "reconciliation_constraints": [
            "Treat aggregation-context.json as the complete authoritative mapped-unit scope.",
            "Revise only Criteria named by validation_errors and directly linked findings, contradiction bases or defect ownership.",
            "For Finding-cardinality errors, add at least one evidence-backed Finding to each target Criterion without changing its conclusion.",
            "Use only evidence IDs already present in the target Criterion and defect keys already present in aggregation-context.json; never invent a defect key.",
            "Synchronize every new Finding with exactly one defect_ownership record and preserve canonical Finding identity requirements.",
            "Do not alter published observations or invent a narrower claim scope through criterion_results[].claim_ids.",
            "Do not reopen source, SDK, Spec, Design, Registry or evidence shards.",
            "Return the complete corrected executor-owned aggregation payload, not a patch.",
        ],
    })
    return contract


def _load_optional_output_contract(path: Path) -> dict[str, Any]:
    """Keep pre-0.1.12 staged runs resumable without inventing a new contract."""
    if not path.is_file():
        return {}
    return load_template(path)


def merge_observation_payload(
    initialized: dict[str, Any],
    payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a flat staged observation without accepting executor identity."""
    _require_exact_payload(payload, OBSERVATION_PAYLOAD_FIELDS, "observation")
    assert payload is not None
    candidate = copy.deepcopy(initialized)
    for field in OBSERVATION_PAYLOAD_FIELDS:
        candidate[field] = copy.deepcopy(payload[field])
    candidate["status"] = "complete"
    candidate["reviewed_claim_ids"] = _claim_review_ids(payload["claim_reviews"])
    candidate["completed_checks"] = _mapped_check_ids(payload["observations"])
    return candidate


def merge_aggregation_payload(
    initialized: dict[str, Any],
    payload: dict[str, Any] | None,
    *,
    source_observation_ids: Iterable[str],
) -> dict[str, Any]:
    """Build a flat aggregation document while retaining frozen identity."""
    _require_exact_payload(payload, AGGREGATION_PAYLOAD_FIELDS, "aggregation")
    assert payload is not None
    candidate = copy.deepcopy(initialized)
    for field in AGGREGATION_PAYLOAD_FIELDS:
        candidate[field] = copy.deepcopy(payload[field])
    candidate["status"] = "complete"
    candidate["source_observation_ids"] = list(source_observation_ids)
    return candidate


def _require_exact_payload(
    payload: dict[str, Any] | None,
    expected_fields: tuple[str, ...],
    label: str,
) -> None:
    if not isinstance(payload, dict):
        raise ValueError(f"executor result has no {label} payload object")
    missing = sorted(set(expected_fields) - set(payload))
    extra = sorted(set(payload) - set(expected_fields))
    if missing or extra:
        raise ValueError(
            f"{label} payload fields do not match the contract: "
            f"missing={missing} extra={extra}"
        )


def _claim_review_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        row["claim_id"]
        for row in value
        if isinstance(row, dict) and isinstance(row.get("claim_id"), str) and row["claim_id"]
    ]


def _mapped_check_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for observation in value:
        if not isinstance(observation, dict) or not isinstance(observation.get("check_ids"), list):
            continue
        for check_id in observation["check_ids"]:
            if isinstance(check_id, str) and check_id and check_id not in seen:
                seen.add(check_id)
                result.append(check_id)
    return result
