"""Workflow manifest generator for the Claude executor's workflow-shards protocol.

This module is the P2 implementation described in
``.evaluator/claude-workflow-observation-design.md`` §5.2.

It produces ``_manifest.json`` — the pre-generated, disk-resident "待办清单 +
输出规则卡" that the Claude session reads at the start of every turn to recover
its progress and output rules without relying on conversation history.

Design decisions
----------------
* ``claim_units`` are derived directly from ``work_item.expected_claim_ids`` in
  their original order.
* ``criterion_units`` are the full set of ``valid_criterion_ids`` from
  ``output-contract.json`` (the fixed 20-dimension set, confirmed identical to
  ``semantic-template.json``).  The Claude session produces an empty list for
  criteria it deems NOT_APPLICABLE, so no check→criterion mapping is needed.
* File names are made filesystem-safe by replacing ``/`` with ``__``.
* The ``aux_file`` key names the single shard for evidence_declarations,
  open_questions, and notes.
* ``output_rules`` duplicates the core formatting constraints from ``_prompt.py``
  in disk-resident form so the session can re-read them after context compression.

No LLM calls, no network.  Pure input/output over Path objects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workflow_shard_schema import (
    CLAIM_SCHEMA_FILE,
    CRITERION_ITEM_SCHEMA_FILE,
    VALIDATE_SCRIPT_FILE,
    write_shard_schemas,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ManifestSpec:
    """Parameters required to generate a manifest for one feature work-item."""
    feat_id: str
    work_item_id: str
    expected_claim_ids: list[str]
    valid_criterion_ids: list[str]       # from output-contract.json
    output_rules: dict[str, Any]         # forwarded verbatim into manifest


def safe_filename(raw_id: str) -> str:
    """Make a claim/criterion ID safe for use as a filename component.

    Replaces ``/`` with ``__`` and strips any remaining path separators.
    Examples::

        "Feat-01/AC-1.1"                 -> "Feat-01__AC-1.1"
        "CORRECTNESS-SOURCE-SUPPORT"     -> "CORRECTNESS-SOURCE-SUPPORT"
    """
    return raw_id.replace("/", "__").replace("\\", "__")


def build_manifest(spec: ManifestSpec) -> dict[str, Any]:
    """Return a manifest dict (not yet written to disk)."""
    claim_units = [
        {
            "claim_id": cid,
            "file": f"claims/claim-{safe_filename(cid)}.json",
        }
        for cid in spec.expected_claim_ids
    ]
    criterion_units = [
        {
            "criterion_id": crid,
            "file": f"criteria/obs-{safe_filename(crid)}.json",
        }
        for crid in spec.valid_criterion_ids
    ]
    return {
        "feat_id": spec.feat_id,
        "work_item_id": spec.work_item_id,
        "schema_version": 1,
        "claim_units": claim_units,
        "criterion_units": criterion_units,
        "aux_file": "aux.json",
        # Authoritative per-shard schemas + validation script (written by
        # write_manifest). The session MUST validate every shard against these
        # rather than a self-authored field-name check.
        "shard_schemas": {
            "claim_schema": CLAIM_SCHEMA_FILE,
            "criterion_item_schema": CRITERION_ITEM_SCHEMA_FILE,
            "validate_script": VALIDATE_SCRIPT_FILE,
        },
        "output_rules": spec.output_rules,
    }


def write_manifest(
    shard_dir: Path,
    spec: ManifestSpec,
) -> Path:
    """Generate the manifest and create the shard sub-directories.

    Creates::

        <shard_dir>/
          _manifest.json
          claims/       (empty directory)
          criteria/     (empty directory)

    Returns the path to the written ``_manifest.json``.
    """
    shard_dir.mkdir(parents=True, exist_ok=True)
    (shard_dir / "claims").mkdir(exist_ok=True)
    (shard_dir / "criteria").mkdir(exist_ok=True)

    # Write the authoritative per-shard schemas + validation script so the
    # session validates each shard against the real nested schema on disk.
    write_shard_schemas(shard_dir)

    manifest = build_manifest(spec)
    manifest_path = shard_dir / "_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


# ---------------------------------------------------------------------------
# Convenience factory: build ManifestSpec from live pipeline objects
# ---------------------------------------------------------------------------

_DEFAULT_OUTPUT_RULES: dict[str, Any] = {
    "language": (
        "Write every natural-language judgment field in Simplified Chinese "
        "(简体中文). Keep all machine identifiers and enumerations verbatim "
        "and untranslated: claim_id, criterion_id, local_outcome, breadth, "
        "evidence key/path, check_ids, contract_family."
    ),
    "claim_shard": {
        "description": (
            "One claimJudgment object (not an array). Its exact schema — "
            "including nested field TYPES — is in shard_schemas.claim_schema. "
            "Note verification_gap.checked_scope and verification_gap."
            "missing_evidence are ARRAYS of strings (not strings); "
            "verification_gap is required (non-null) only when local_outcome "
            "is NOT_VERIFIABLE, null otherwise."
        ),
        "required_fields": [
            "claim_id", "local_outcome", "evidence_refs",
            "reason", "verification_gap", "defect_keys", "unit_reviews",
        ],
    },
    "criterion_shard": {
        "description": (
            "A JSON array of observationJudgment objects for this criterion. "
            "Empty array [] when the criterion is NOT_APPLICABLE. Each item's "
            "exact schema is in shard_schemas.criterion_item_schema."
        ),
        "required_fields": [
            "criterion_ids", "check_ids", "claim_ids", "local_outcome",
            "breadth", "contract_family", "fact", "defect_key",
            "primary_criterion_id", "evidence_refs",
        ],
    },
    "aux_shard": {
        "description": (
            "An object with keys evidence_declarations (array), "
            "open_questions (array of strings), notes (array of strings)."
        ),
    },
    "self_recovery": (
        "At the start of every unit, run: "
        "  cat _manifest.json && ls claims/ && ls criteria/ "
        "to re-read the full todo list and determine which units are already done. "
        "Disk state is the only source of truth; do not rely on conversation history."
    ),
    "write_protocol": (
        "Write each shard as <file>.tmp then rename to <file> atomically. "
        "Immediately after renaming, validate it with the AUTHORITATIVE script: "
        "  python3 shard_schemas.validate_script claim claims/<file>       (claim shard) "
        "  python3 shard_schemas.validate_script criterion criteria/<file> (criterion shard) "
        "The script prints OK or the exact schema errors; a shard is only done "
        "when it prints OK. Do NOT rely on your own field-name check — it misses "
        "type errors (e.g. array vs string)."
    ),
    "no_dump_large_json": True,
}


def make_spec_from_work_item(
    work_item: dict[str, Any],
    valid_criterion_ids: list[str],
    output_rules: dict[str, Any] | None = None,
) -> ManifestSpec:
    """Build a :class:`ManifestSpec` from a staged work-item dict.

    Parameters
    ----------
    work_item:
        One item from ``work-items.json`` (the ``items`` list), already
        loaded as a Python dict.
    valid_criterion_ids:
        The ``valid_criterion_ids`` list from ``output-contract.json``.
    output_rules:
        Override the default output rules embedded in the manifest.
        When ``None`` the module-level ``_DEFAULT_OUTPUT_RULES`` are used.
    """
    feat_id: str = work_item["feat_id"]
    work_item_id: str = work_item["id"]
    expected_claim_ids: list[str] = list(work_item["expected_claim_ids"])
    return ManifestSpec(
        feat_id=feat_id,
        work_item_id=work_item_id,
        expected_claim_ids=expected_claim_ids,
        valid_criterion_ids=list(valid_criterion_ids),
        output_rules=output_rules if output_rules is not None else _DEFAULT_OUTPUT_RULES,
    )
