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
    if output_transport not in {
        "canonical_envelope", "payload_root", "workflow_shards"
    }:
        raise ValueError(f"unknown output transport: {output_transport!r}")
    if output_transport == "workflow_shards":
        # Claude-only observation path: disk-driven workflow, not a single
        # final structured payload.  Fully isolated from the codex /
        # payload_root paths below so their behaviour is unchanged (C1/C3).
        return _build_workflow_shards_prompt(work)
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
        if observation_profile == "aggregation":
            constraints = [
                "Correct one invalid Aggregation candidate; do not perform a second full Aggregation review.",
                "Read the candidate at result_contract.candidate_path, every typed error, and the projected aggregation-correction-context.json only.",
                "Treat aggregation-correction-context.json as authoritative for the target Criteria, mapped Observation/Claim/Unit rows, and Criterion Evidence allowlists.",
                "Apply every relevant machine_contract repair recipe and preserve all dependency_rules, including parent Criterion/Finding Evidence closure and Finding/ownership consistency.",
                "The global Evidence catalog is lookup-only; an EV- ID is selectable only when the target Criterion lists it in criteria[].evidence_ids.",
                "Do not modify inherited Observation facts or outcomes, non-target Criteria, canonical Finding IDs, scores, confidence, gates, or admission.",
                "The service owns candidate merge, normalization, derived fields, and final validation.",
                "Return only RFC-6902-style add/remove/replace patches and notes.",
                patch_target,
                "Change only paths allowed by result_contract.correction_contract.",
                "NEVER read SKILL.md, evaluator references, or the full aggregation-context.json during Correction.",
                "Treat the top-level machine_contract and correction_contract as normative.",
                "Write only the structured final result.",
                *tool_output_constraints,
                language_constraint,
            ]
        else:
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
        elif observation_profile != "aggregation":
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


# ---------------------------------------------------------------------------
# Claude-only: workflow-shards observation prompt
# ---------------------------------------------------------------------------
#
# This path is used ONLY by the Claude executor for feature/function-global
# Observation.  Instead of asking the model to emit one large structured
# payload at the end (which truncates for large claim sets), it drives a
# disk-based workflow: the model verifies each claim/criterion in turn, writes
# a small shard file per unit, and the service synthesizes the final envelope
# off-session (see workflow_synthesis.py / workflow_manifest.py).
#
# It shares NO code path with the codex / payload_root prompt above, so those
# executors' behaviour is unchanged (design C1/C3).

# Directory convention shared with the Claude adapter (P4) and manifest
# generator (P2): <run_dir>/observations/<feat_id>/
_WORKFLOW_SHARD_SUBDIR = "observations"


def workflow_shard_dir(run_dir: str, feat_id: str) -> str:
    """Absolute shard directory for one feature's workflow observation.

    Single source of truth for the path convention, imported by the Claude
    adapter and the manifest generator so the prompt, the on-disk manifest,
    and synthesis all agree.
    """
    from pathlib import PurePosixPath

    return str(PurePosixPath(run_dir) / _WORKFLOW_SHARD_SUBDIR / feat_id)


def _workflow_recovery_rules() -> list[str]:
    """Top-priority self-recovery rules (survive context compression)."""
    return [
        "DISK IS THE ONLY SOURCE OF TRUTH. Do not rely on this conversation's "
        "history for progress or rules; it may be compressed at any time.",
        "At the start of EVERY unit, first run: `cat <manifest>` to re-read the "
        "full todo list and output rules, then `ls <shard_dir>/claims` and "
        "`ls <shard_dir>/criteria` to see which units are already written.",
        "The next unit to process is the first manifest entry whose shard file "
        "does not yet exist on disk. Never redo a unit whose valid shard exists.",
        "You are DONE when every claim_unit and criterion_unit file in the "
        "manifest exists on disk and the aux file is written.",
    ]


def _workflow_write_rules() -> list[str]:
    """How each shard is produced and self-checked."""
    return [
        "For each claim_unit: verify the claim against frozen source, then Write "
        "the shard to its manifest `file` path as ONE claimJudgment object "
        "(not an array) matching shard_schemas.claim_schema EXACTLY, including "
        "nested field types.",
        "verification_gap.checked_scope and verification_gap.missing_evidence "
        "are ARRAYS of strings (not a single string); verification_gap is a "
        "non-null object only when local_outcome is NOT_VERIFIABLE, else null.",
        "For each criterion_unit: read back the already-written claim shards it "
        "depends on (use targeted sed/head, never dump whole files), then Write "
        "the shard as a JSON ARRAY of observationJudgment objects matching "
        "shard_schemas.criterion_item_schema. Write an empty array [] when the "
        "criterion is NOT_APPLICABLE.",
        "Write each shard atomically: Write to `<file>.tmp`, then move it to "
        "`<file>`. Immediately validate it with the AUTHORITATIVE script named "
        "in shard_schemas.validate_script: "
        "`python3 <validate_script> claim <file>` for a claim shard or "
        "`python3 <validate_script> criterion <file>` for a criterion shard. "
        "The shard is done only when the script prints OK; if it prints schema "
        "errors, fix the shard and re-validate. Do NOT rely on your own "
        "field-name check — it misses type errors like array-vs-string.",
        "After all claim and criterion shards exist, Write the aux shard "
        "(evidence_declarations, open_questions, notes) named by manifest.aux_file. "
        "evidence_declarations paths must be canonical repository-relative paths "
        "inside ace_engine, sdk-js, or sdk_c — NEVER a specs/ path — and each "
        "path must point at a file that ACTUALLY EXISTS. Verify with ls/find "
        "before declaring it; do not guess directory levels. "
        "After writing, validate: `python3 <validate_script> aux aux.json`. "
        "This also checks every evidence path exists in the frozen repos; if it "
        "reports EVIDENCE_PATH_NOT_FOUND, find the correct path and fix it. "
        "The shard is done only when the script prints OK.",
        "Natural-language fields (reason, fact, ...) in Simplified Chinese; keep "
        "all IDs and enums verbatim (claim_id, criterion_id, local_outcome, ...).",
        "Never print, cat, tee or otherwise dump a complete shard or the "
        "assembled payload to stdout; keep each tool command output small.",
    ]


def _build_workflow_shards_prompt(work: C.WorkItemInput) -> str:
    """Build the Claude workflow-shards observation prompt.

    The manifest and empty shard directories are pre-created by the service
    (workflow_manifest.write_manifest) BEFORE this session starts, so the
    model only consumes them.  The final structured output is a tiny result
    signal (see the ``output`` block); the real product is the shard files.
    """
    contract = dict(work.prompt_extras)
    machine_contract = contract.get("machine_contract", {})
    observation_profile = contract.get(
        "observation_profile",
        machine_contract.get("observation_profile", "feature"),
    )
    phase_references = list(contract.get("phase_references", []))
    feat_id = str(work.work_item.get("feat_id", work.work_item_id))

    shard_dir = workflow_shard_dir(work.run_dir, feat_id)
    manifest_path = f"{shard_dir}/_manifest.json"

    reference_constraint = (
        "The phase_references contents are already loaded in this prompt; "
        "follow them as phase instructions and do not reread their source paths."
        if phase_references else
        "Follow only the declared machine contract and explicitly allowed "
        "input paths."
    )

    constraints = [
        reference_constraint,
        "Treat input_resources.citable=false files as context only; never "
        "declare them as evidence.",
        "Evidence paths must be canonical repository-relative POSIX paths. "
        "Never emit absolute paths, '..', evidence/... or runs/... service paths.",
        "Do not read paths in forbidden_paths (confirmed reviews or other runs).",
        "Do not modify any formal Spec, Design, Registry, source or test file.",
        "Do not modify the manifest; the service owns it.",
        "Provide judgments only; treat the top-level machine_contract as normative.",
        *_workflow_recovery_rules(),
        *_workflow_write_rules(),
    ]
    if observation_profile == "function_global":
        constraints.append(
            "This is Function-global Observation; keep judgments at Function scope."
        )
    else:
        constraints.append(
            "This is Feature Observation; keep judgments local to the current "
            "Feature claims."
        )

    # Duplicate-field trimming mirrors the main path so the prompt stays compact.
    prompt_work_item = dict(work.work_item)
    for duplicated_field in (
        "input_paths", "input_resources", "output_path",
    ):
        prompt_work_item.pop(duplicated_field, None)

    result_contract = {
        key: value for key, value in contract.items()
        if key not in {"machine_contract", "phase_references"}
    }
    result_contract["output_transport"] = "workflow_shards"

    # The final structured output is a tiny completion signal, NOT the payload.
    # It only lets the service cross-check reported vs. on-disk shard files and
    # detect model-reported failure; synthesis reads the shard files directly.
    output = {
        "transport": "workflow_shards",
        "shard_dir": shard_dir,
        "manifest_path": manifest_path,
        "requirement": (
            "Do NOT emit the observation payload as structured output. Instead, "
            "write one shard file per manifest unit as instructed, then finish by "
            "returning ONLY the tiny completion signal object with fields: "
            "status ('completed' or 'failed'), written_claim_files (array of the "
            "claim shard paths you wrote), written_criterion_files (array of the "
            "criterion shard paths you wrote), aux_written (the aux file path or "
            "empty string), and error (a non-empty string when status='failed', "
            "else null). The service assembles and validates the canonical "
            "envelope from the shard files on disk."
        ),
    }

    payload: dict[str, Any] = {
        "task": (
            "Produce the feature observation by writing one shard file per "
            "manifest unit (disk-driven workflow), then return the completion "
            "signal."
        ),
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
        "manifest": {
            "path": manifest_path,
            "shard_dir": shard_dir,
            "note": (
                "Pre-generated by the service. It lists claim_units, "
                "criterion_units, aux_file, and output_rules. Re-read it at the "
                "start of every unit."
            ),
        },
        "output": output,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
