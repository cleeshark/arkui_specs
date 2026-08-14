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


def observation_prompt_contract(template_path: Path) -> dict[str, Any]:
    return {
        "result_kind": "staged_observation_payload",
        "template_path": str(template_path),
        "payload_fields": list(OBSERVATION_PAYLOAD_FIELDS),
        "service_derived_fields": ["status", "reviewed_claim_ids", "completed_checks"],
    }


def aggregation_prompt_contract(template_path: Path) -> dict[str, Any]:
    return {
        "result_kind": "staged_aggregation_payload",
        "template_path": str(template_path),
        "payload_fields": list(AGGREGATION_PAYLOAD_FIELDS),
        "service_derived_fields": ["status", "source_observation_ids"],
    }


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
