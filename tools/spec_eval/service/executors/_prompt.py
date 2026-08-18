"""Shared prompt builder for CLI executor adapters.

Both the Codex and Claude adapters send the same structured JSON prompt to
the model; only the CLI invocation and result capture differ. Keeping the
prompt construction here avoids duplicating it across adapters.
"""

from __future__ import annotations

import json
from typing import Any

from . import contract as C


def build_executor_prompt(work: C.WorkItemInput) -> str:
    """Build the JSON prompt sent to a CLI executor via stdin.

    The prompt is mode-aware (``observe`` vs ``correct``) and includes the
    full work-item context, machine contract, and output requirements.
    """
    contract = dict(work.prompt_extras)
    mode = contract.get("mode", "observe")
    correcting = mode == "correct"
    machine_contract = contract.get("machine_contract", {})
    result_kind = contract.get("result_kind", "staged_judgments")
    payload_fields = contract.get("payload_fields", [])
    declares_evidence = "evidence_declarations" in payload_fields
    constraints = [
        "Follow the declared evaluator Skill and the staged-run contract.",
        "Read only the declared input_paths and frozen source/SDK files.",
        "Treat input_resources.citable=false files as context only; never "
        "declare them as evidence.",
        "Evidence paths must be canonical repository-relative POSIX paths. "
        "Never emit absolute paths, '..', evidence/... or runs/... service paths.",
        "Do not read paths in forbidden_paths (confirmed reviews or other runs).",
        "Do not modify any formal Spec, Design, Registry, source or test file.",
        "Do not modify the initialized staged template; the service owns and publishes it.",
        "Provide judgments only; treat result_contract.machine_contract as normative.",
        "Write only the structured final result.",
    ]
    if correcting:
        evidence_correction = (
            "Re-declare every piece of evidence you keep or add in "
            "evidence_declarations; the service re-verifies hashes and "
            "re-assigns canonical IDs."
            if declares_evidence else
            "Do not declare evidence or use local evidence keys. Use only "
            "canonical evidence IDs listed for each Criterion in "
            "aggregation-context.json."
        )
        constraints = [
            "Correct one invalid evaluation candidate.",
            "Read the candidate at result_contract.candidate_path and every "
            "entry of result_contract.typed_errors.",
            "Fix the reported judgments; the typed errors carry code, path, "
            "entity and expected/actual values.",
            "Do not change document identity, ordering, derived fields or "
            "evidence you cannot verify from the frozen inputs.",
            evidence_correction,
            "Treat input_resources.citable=false files as context only. "
            "Replace rejected paths with canonical frozen repository paths.",
            "Treat result_contract.machine_contract as normative.",
            "Write only the structured final result.",
        ]
    payload_field_text = json.dumps(payload_fields, ensure_ascii=False)
    evidence_requirement = (
        "Local evidence keys (e1, e2, ...) are declared once in "
        "evidence_declarations and referenced via evidence_refs; never emit "
        "canonical EV- IDs."
        if declares_evidence else
        "For aggregation, do not emit evidence_declarations, evidence_refs, "
        "or local evidence keys. criterion_results[].evidence_ids and each "
        "finding evidence_ids must use canonical EV- IDs listed for that "
        "Criterion in aggregation-context.json."
    )
    task = (
        f"Correct one {result_kind} candidate after typed validation failure."
        if correcting else
        f"Produce one complete {result_kind} payload for the declared work item."
    )
    payload: dict[str, Any] = {
        "task": task,
        "constraints": constraints,
        "func_id": work.func_id,
        "run_id": work.run_id,
        "work_item": work.work_item,
        "input_paths": list(work.input_paths),
        "input_resources": list(work.work_item.get("input_resources", [])),
        "forbidden_paths": list(work.forbidden_paths),
        "skill_version": work.skill_version,
        "protocol_version": work.protocol_version,
        "result_contract": contract,
        "machine_contract": machine_contract,
        "output": {
            "path": work.executor_result_path,
            "schema": contract.get("schema_path"),
            "requirement": (
                "Return every envelope field. Use schema_version=3. For a "
                "completed work item set status=completed, error=null, and "
                f"payload to one {result_kind} object containing exactly "
                f"these fields: {payload_field_text}, fully constrained by "
                f"the declared schema. {evidence_requirement} Local "
                "NOT_VERIFIABLE outcomes still use envelope status=completed. "
                "Use status=failed only when no complete payload can be "
                "produced; then set payload=null and provide a non-empty error."
            ),
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
