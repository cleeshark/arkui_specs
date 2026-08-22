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
    compact work-item context, embedded phase references, one authoritative
    machine contract, and output requirements.  Protocol fields already
    represented elsewhere in the prompt are omitted from the descriptive
    work-item copy to avoid duplicate prompt tokens.
    """
    contract = dict(work.prompt_extras)
    mode = contract.get("mode", "observe")
    correcting = mode == "correct"
    machine_contract = contract.get("machine_contract", {})
    phase_references = (
        list(contract.get("phase_references", [])) if not correcting else []
    )
    result_kind = contract.get("result_kind", "staged_judgments")
    payload_fields = contract.get("payload_fields", [])
    declares_evidence = "evidence_declarations" in payload_fields
    reference_constraint = (
        "The phase_references contents are already loaded in this prompt; "
        "follow them as phase instructions and do not reread their source paths."
        if phase_references else
        "Follow only the declared machine contract and explicitly allowed "
        "input paths."
    )
    constraints = [
        reference_constraint,
        "Read only the declared input_paths and frozen source/SDK files.",
        "Treat input_resources.citable=false files as context only; never "
        "declare them as evidence.",
        "Evidence paths must be canonical repository-relative POSIX paths. "
        "Never emit absolute paths, '..', evidence/... or runs/... service paths.",
        "Do not read paths in forbidden_paths (confirmed reviews or other runs).",
        "Do not modify any formal Spec, Design, Registry, source or test file.",
        "Do not modify the initialized staged template; the service owns and publishes it.",
        "Provide judgments only; treat the top-level machine_contract as normative.",
        "Write only the structured final result.",
        "EFFICIENCY: To verify presence of a symbol, target, or config in a "
        "large file, use Grep or Bash(grep -n 'pattern' file) instead of "
        "reading the entire file with Read. Use Read with offset+limit when "
        "only a specific line range is needed. Minimize total tokens read.",
    ]
    if correcting:
        constraints = [
            "Correct one invalid evaluation candidate.",
            "Read the candidate at result_contract.candidate_path and every "
            "entry of result_contract.typed_errors.",
            "The service owns the candidate merge and final validation.",
            "Return only RFC-6902-style add/remove/replace patches and notes.",
            "Patch the published candidate; do not rewrite the complete document.",
            "Change only paths allowed by result_contract.correction_contract.",
            "Do not change document identity, source revision, ordering, canonical IDs, "
            "hashes or derived fields.",
            "NEVER read SKILL.md or search any skill directory during Correction.",
            "Treat the top-level machine_contract and correction_contract as normative.",
            "Write only the structured final result.",
        ]
    payload_field_text = json.dumps(payload_fields, ensure_ascii=False)
    if correcting:
        evidence_requirement = (
            "Return payload.patches as an array of add/remove/replace operations "
            "against the published candidate; the service applies and validates "
            "them. Encode each patch value as a JSON string (use \"null\" for remove)."
        )
    else:
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
    # ``machine_contract`` is authoritative and is emitted once at the prompt
    # top level.  ``contract`` is the service/result metadata and should not
    # carry a second nested copy of the same contract.
    result_contract = {
        key: value for key, value in contract.items()
        if key not in {"machine_contract", "phase_references"}
    }
    prompt_work_item = dict(work.work_item)
    for duplicated_field in (
        "expected_claim_ids", "required_checks", "input_paths",
        "input_resources", "output_path",
    ):
        prompt_work_item.pop(duplicated_field, None)

    payload: dict[str, Any] = {
        "task": task,
        "constraints": constraints,
        "func_id": work.func_id,
        "run_id": work.run_id,
        "work_item": prompt_work_item,
        "phase_references": phase_references,
        "input_paths": list(work.input_paths),
        "input_resources": list(work.work_item.get("input_resources", [])),
        "forbidden_paths": list(work.forbidden_paths),
        "skill_version": work.skill_version,
        "protocol_version": work.protocol_version,
        "result_contract": result_contract,
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
