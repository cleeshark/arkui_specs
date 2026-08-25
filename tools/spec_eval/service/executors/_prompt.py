"""Shared prompt builder for CLI executor adapters.

Both the Codex and Claude adapters send the same structured JSON prompt to
the model; only the CLI invocation and result capture differ. Keeping the
prompt construction here avoids duplicating it across adapters.
"""

from __future__ import annotations

import json
from typing import Any

from . import contract as C


def build_executor_prompt(
    work: C.WorkItemInput,
    *,
    output_transport: str = "canonical_envelope",
) -> str:
    """Build the JSON prompt sent to a CLI executor via stdin.

    The prompt is mode-aware (``observe`` vs ``correct``) and includes the
    compact work-item context, embedded phase references, one authoritative
    machine contract, and output requirements.  Protocol fields already
    represented elsewhere in the prompt are omitted from the descriptive
    work-item copy to avoid duplicate prompt tokens.
    """
    if output_transport not in {"canonical_envelope", "payload_root"}:
        raise ValueError(f"unknown output transport: {output_transport!r}")
    payload_root = output_transport == "payload_root"
    contract = dict(work.prompt_extras)
    mode = contract.get("mode", "observe")
    correcting = mode == "correct"
    machine_contract = contract.get("machine_contract", {})
    observation_profile = contract.get(
        "observation_profile",
        machine_contract.get("observation_profile", "feature"),
    )
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
    tool_output_constraints = [
        "NEVER print, echo, cat, tee, or otherwise serialize the complete "
        "envelope or payload from a tool command. Do not use Python, jq, or "
        "shell tools to render the final JSON to stdout. Construct the "
        "complete structured result exactly once in the final response "
        "captured and validated by the CLI output schema.",
        "Keep each tool command output focused and normally below 16 KB. "
        "Use targeted rg patterns, sed ranges, head/tail, field projection, "
        "or counts, and split large inspections into smaller commands. Never "
        "dump a complete large JSON, Markdown, source, or generated file.",
        "When validating JSON or assembling judgment data with Python/jq, "
        "print only compact summaries such as counts, missing or duplicate "
        "IDs, schema errors, byte size, or hashes; never print the assembled "
        "payload itself.",
    ]
    # Natural-language judgment prose must be Simplified Chinese so the report,
    # site, CI comments and downloadable JSON read consistently in Chinese.
    # Machine identifiers and enums stay verbatim: this only governs free-text
    # explanation fields, not IDs, conclusions, severities, or evidence paths.
    language_constraint = (
        "Write every natural-language judgment field — including message, "
        "reason, rationale, recommendation, and any explanatory notes — in "
        "Simplified Chinese (简体中文). Keep all machine identifiers and "
        "enumerations verbatim and untranslated: rule_id, criterion_id, "
        "claim_id, EV-/FND- IDs, conclusion, severity, gate, admission, "
        "func_id, feat_id, and evidence paths. Do not translate quoted source "
        "identifiers, code symbols, file paths, or section names cited as "
        "evidence."
    )
    if correcting:
        correction_base = contract.get("correction_contract", {}).get(
            "base", "published_candidate"
        )
        if correction_base == "raw_payload":
            patch_target = (
                "Patch the raw judgment payload; the service will normalize it "
                "again after applying the patch."
            )
        else:
            patch_target = (
                "Patch the published candidate; do not rewrite the complete document."
            )
        constraints = [
            "Correct one invalid evaluation candidate.",
            "Read the candidate at result_contract.candidate_path and every "
            "entry of result_contract.typed_errors.",
            "The service owns the candidate merge and final validation.",
            "Return only RFC-6902-style add/remove/replace patches and notes.",
            patch_target,
            "Change only paths allowed by result_contract.correction_contract.",
            "Do not change document identity, source revision, ordering, canonical IDs, "
            "hashes or derived fields.",
            "NEVER read SKILL.md or search any skill directory during Correction.",
            "Treat the top-level machine_contract and correction_contract as normative.",
            "Write only the structured final result.",
            *tool_output_constraints,
            language_constraint,
        ]
        if observation_profile == "function_global":
            constraints.extend([
                "This is Function-global Correction: keep the patch within the named global Claim/Unit/Observation path.",
                "Do not change cross-Feature ownership, boundary roles, or the global outcome unless the typed error names that exact path and frozen evidence supports it.",
            ])
        elif observation_profile == "aggregation":
            constraints.extend([
                "This is Aggregation Correction: keep the patch within the named Criterion/Policy/Finding path.",
                "Do not modify Observation source facts, non-target Criteria, or service-derived Finding IDs.",
            ])
        else:
            constraints.append(
                "This is Feature Correction: keep the patch local to the named Feature Claim/Unit/Observation path."
            )
    elif observation_profile == "aggregation":
        constraints = [
            reference_constraint,
            "This is Aggregation and not a second source-verification pass.",
            "NEVER read SKILL.md, search a skill directory, or load references from their source paths; the two Aggregation references are already embedded above.",
            "Treat aggregation-context.json as the authoritative semantic handoff from validated Observations.",
            "The global evidence_catalog is lookup-only. For each Criterion, criteria[].evidence_ids is the exhaustive Evidence allowlist; never cite an EV- ID merely because it exists globally.",
            "Do not declare Evidence, invent EV- IDs or defect keys, or change inherited Observation outcomes.",
            "Reopen frozen source only for one named ambiguity, conflict, or Evidence gap, starting from that Criterion's allowed Evidence paths; keep the recheck bounded.",
            "Do not calculate or emit scores, deductions, confidence, gates, or admission; the service derives them deterministically.",
            "Do not read paths in forbidden_paths or modify Spec, Design, Registry, source, tests, staged templates, or Observation files.",
            "Provide semantic aggregation judgments only; treat the top-level machine_contract as normative.",
            "Write only the structured final result.",
            *tool_output_constraints,
            language_constraint,
        ]
    else:
        constraints = [
            reference_constraint,
            "Treat input_resources.citable=false files as context only; never "
            "declare them as evidence.",
            "Evidence paths must be canonical repository-relative POSIX paths. "
            "Never emit absolute paths, '..', evidence/... or runs/... service paths.",
            "Do not read paths in forbidden_paths (confirmed reviews or other runs).",
            "Do not modify any formal Spec, Design, Registry, source or test file.",
            "Do not modify the initialized staged template; the service owns and publishes it.",
            "Provide judgments only; treat the top-level machine_contract as normative.",
            "Write only the structured final result.",
            *tool_output_constraints,
            language_constraint,
        ]
        if observation_profile == "function_global":
            constraints.extend([
                "This is Function-global Observation; keep judgments at Function scope.",
            ])
        else:
            constraints.extend([
                "This is Feature Observation; keep judgments local to the current Feature claims.",
            ])
    payload_field_text = json.dumps(payload_fields, ensure_ascii=False)
    if correcting:
        evidence_requirement = (
            "Return patches as an array of add/remove/replace operations "
            "against the published candidate; the service applies and validates "
            "them. Encode each patch value as a JSON string (use \"null\" for remove)."
            if payload_root else
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
    if payload_root:
        result_contract["canonical_envelope_schema_path"] = (
            result_contract.pop("schema_path", None)
        )
        result_contract["output_transport"] = "payload_root"
    prompt_work_item = dict(work.work_item)
    for duplicated_field in (
        "expected_claim_ids", "required_checks", "input_paths",
        "input_resources", "output_path",
    ):
        prompt_work_item.pop(duplicated_field, None)

    if payload_root:
        completion_note = (
            "Criterion NOT_VERIFIABLE conclusions remain completed judgments; "
            "the executor adapter owns envelope status. "
            if observation_profile == "aggregation" and not correcting else
            "Local NOT_VERIFIABLE outcomes remain completed judgments; "
            "the executor adapter owns envelope status. "
        )
        output_requirement = (
            f"Return one {result_kind} object directly at the structured-output "
            f"root containing exactly these fields: {payload_field_text}, fully "
            f"constrained by the CLI output schema. {evidence_requirement} "
            f"{completion_note}Do not emit schema_version, work_item_id, status, "
            "payload, envelope notes, or error; the executor adapter constructs "
            "and validates the canonical envelope."
        )
    else:
        completion_note = (
            "Criterion NOT_VERIFIABLE conclusions still use envelope status=completed. "
            if observation_profile == "aggregation" and not correcting else
            "Local NOT_VERIFIABLE outcomes still use envelope status=completed. "
        )
        output_requirement = (
            "Return every envelope field. Use schema_version=3. For a "
            "completed work item set status=completed, error=null, and "
            f"payload to one {result_kind} object containing exactly "
            f"these fields: {payload_field_text}, fully constrained by "
            f"the declared schema. {evidence_requirement} {completion_note}"
            "Use status=failed only when no complete payload can be "
            "produced; then set payload=null and provide a non-empty error."
        )
    output: dict[str, Any] = {
        "path": work.executor_result_path,
        "transport": output_transport,
        "requirement": output_requirement,
    }
    if payload_root:
        output["canonical_envelope_schema"] = contract.get("schema_path")
    else:
        output["schema"] = contract.get("schema_path")

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
        "output": output,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
