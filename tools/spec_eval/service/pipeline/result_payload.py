"""Executor prompt contracts for evaluator protocol 0.2.0.

Observation produces one complete judgment payload.  Correction produces a
bounded JSON Patch against the normalized candidate; the service merges and
validates that patch.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable, Sequence

from spec_eval.kernel import contracts as K
from spec_eval.kernel.schema_gen import write_envelope_schema

MODE_OBSERVE = "observe"
MODE_CORRECT = "correct"


def load_template(path: Path) -> dict[str, Any]:
    """Load one initialized staged document before the executor can touch it."""
    import json

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load initialized template {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"initialized template is not an object: {path}")
    return value


def _base_contract(
    *,
    payload_kind: str,
    result_kind: str,
    payload_fields: Sequence[str],
    schema_path: Path,
    machine_contract: dict[str, Any],
) -> dict[str, Any]:
    return {
        "evaluation_protocol_version": K.EVALUATION_PROTOCOL_VERSION,
        "mode": MODE_OBSERVE,
        "payload_kind": payload_kind,
        "result_kind": result_kind,
        "payload_fields": list(payload_fields),
        "service_derived_fields": [
            "document identity", "stable evidence IDs", "content hashes",
            "ordering", "derived fields", "canonical finding IDs",
        ],
        "schema_path": str(schema_path),
        "machine_contract": machine_contract,
    }


def observe_observation_prompt_contract(
    *,
    template_path: Path,
    schema_dir: Path,
    machine_contract: dict[str, Any],
) -> dict[str, Any]:
    """Contract for one observation work item's judgment turn."""
    schema_path = write_envelope_schema(
        "observation", schema_dir / "envelope-observation.schema.json"
    )
    contract = _base_contract(
        payload_kind="observation",
        result_kind="staged_observation_judgments",
        payload_fields=K.OBSERVATION_JUDGMENT_FIELDS,
        schema_path=schema_path,
        machine_contract=machine_contract,
    )
    contract["template_path"] = str(template_path)
    return contract


def observe_aggregation_prompt_contract(
    *,
    template_path: Path,
    schema_dir: Path,
    machine_contract: dict[str, Any],
) -> dict[str, Any]:
    """Contract for the aggregation work item's judgment turn."""
    schema_path = write_envelope_schema(
        "aggregation", schema_dir / "envelope-aggregation.schema.json"
    )
    contract = _base_contract(
        payload_kind="aggregation",
        result_kind="staged_aggregation_judgments",
        payload_fields=K.AGGREGATION_JUDGMENT_FIELDS,
        schema_path=schema_path,
        machine_contract=machine_contract,
    )
    contract["template_path"] = str(template_path)
    return contract


def correct_prompt_contract(
    base_contract: dict[str, Any],
    *,
    candidate_path: Path,
    typed_errors: Iterable[dict[str, Any]],
    schema_dir: Path,
    correction_contract: dict[str, Any],
    machine_contract: dict[str, Any],
) -> dict[str, Any]:
    """Contract for one bounded JSON Patch correction turn."""
    contract = copy.deepcopy(base_contract)
    schema_path = write_envelope_schema(
        "correction", schema_dir / "envelope-correction.schema.json"
    )
    contract.update({
        "mode": MODE_CORRECT,
        "phase_references": [],
        "payload_kind": "correction",
        "result_kind": "staged_json_patch",
        "payload_fields": list(K.CORRECTION_JUDGMENT_FIELDS),
        "schema_path": str(schema_path),
        "candidate_path": str(candidate_path),
        "typed_errors": list(typed_errors),
        "correction_contract": correction_contract,
        "machine_contract": machine_contract,
        "correction_constraints": [
            "Read the invalid candidate at candidate_path and every typed error.",
            "Return RFC-6902-style add/remove/replace patches against the published candidate.",
            "Do not return a complete replacement document.",
            "Do not read SKILL.md or search any skill directory during Correction.",
        ],
    })
    return contract
