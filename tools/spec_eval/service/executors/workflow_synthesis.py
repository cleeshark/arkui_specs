"""Workflow-shards observation synthesis for the Claude executor.

This module assembles a canonical observation envelope from per-claim and
per-criterion shard files written by a Claude session running the
workflow-shards observation protocol.  It is purely deterministic — no LLM
calls, no network access — and is the only place that knows how individual
shards map to the final ``observationPayload`` schema.

Design reference: .evaluator/claude-workflow-observation-design.md §4–§6.

Contract
--------
* Input  : a ``_manifest.json`` that names every expected shard file plus the
  output rules that drove the Claude session.
* Output : either a validated canonical envelope dict ready to write to
  ``executor_result_path``, or a :class:`SynthesisError` that lists exactly
  which units are missing or invalid so callers can trigger per-unit retries.
* Format : the assembled envelope is *byte-level schema-compatible* with the
  envelope produced by the Codex / StructuredOutput path.  ``_validate_result``
  in ``claude_cli.py`` runs the same ``JsonSchemaSubsetValidator`` on both.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from spec_eval.kernel.contracts import (
    ENVELOPE_SCHEMA_VERSION,
    CLAIM_JUDGMENT_FIELDS,
    OBSERVATION_JUDGMENT_ENTRY_FIELDS,
    EVIDENCE_DECLARATION_FIELDS,
)


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------

@dataclass
class ShardError:
    """A single shard-level validation failure."""
    unit_id: str          # claim_id or criterion_id
    unit_type: str        # "claim" | "criterion" | "aux"
    file: str             # relative path from manifest
    reason: str           # human-readable description


@dataclass
class SynthesisError(Exception):
    """Raised when synthesis cannot produce a valid envelope."""
    message: str
    shard_errors: list[ShardError] = field(default_factory=list)

    def __str__(self) -> str:
        lines = [self.message]
        for e in self.shard_errors:
            lines.append(f"  [{e.unit_type}] {e.unit_id}: {e.reason} ({e.file})")
        return "\n".join(lines)


@dataclass
class SynthesisResult:
    """Successful synthesis result."""
    envelope: dict[str, Any]          # ready to json.dumps → executor_result_path
    claim_count: int
    observation_count: int
    evidence_count: int


# ---------------------------------------------------------------------------
# Manifest schema (mirrors §5.2 of design doc)
# ---------------------------------------------------------------------------

_MANIFEST_REQUIRED = frozenset({"feat_id", "schema_version", "claim_units",
                                 "criterion_units", "output_rules"})
_CLAIM_UNIT_REQUIRED = frozenset({"claim_id", "file"})
_CRITERION_UNIT_REQUIRED = frozenset({"criterion_id", "file"})


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load and minimally validate the manifest."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SynthesisError(f"cannot read manifest {manifest_path}: {exc}")
    missing = _MANIFEST_REQUIRED - set(data)
    if missing:
        raise SynthesisError(
            f"manifest missing required keys: {sorted(missing)}"
        )
    return data


# ---------------------------------------------------------------------------
# Shard validation helpers
# ---------------------------------------------------------------------------

_CLAIM_FIELDS = frozenset(CLAIM_JUDGMENT_FIELDS)
_OBSERVATION_FIELDS = frozenset(OBSERVATION_JUDGMENT_ENTRY_FIELDS)
_EVIDENCE_FIELDS = frozenset(EVIDENCE_DECLARATION_FIELDS)


class _ShardDecodeError(Exception):
    """Internal signal: shard file exists but JSON is invalid."""
    def __init__(self, reason: str) -> None:
        self.reason = reason


def _load_shard(
    shard_dir: Path,
    rel_file: str,
) -> dict[str, Any] | list[Any] | None:
    """
    Load a shard JSON file.

    Returns:
        None when the file does not exist (caller records a "missing" ShardError).
        The parsed value (dict or list) on success.

    Raises:
        _ShardDecodeError when the file exists but is not valid JSON.
            Callers catch this and convert it into a ShardError so that all
            failing units are collected in one pass rather than aborting early.
    """
    path = shard_dir / rel_file
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise _ShardDecodeError(
            f"shard file exists but is not valid JSON: "
            f"line {exc.lineno} col {exc.colno}: {exc.msg}"
        )


def _check_claim_shard(
    data: dict[str, Any],
    expected_claim_id: str,
) -> str | None:
    """Return an error string, or None if the claim shard is valid."""
    missing = _CLAIM_FIELDS - set(data)
    if missing:
        return f"missing fields: {sorted(missing)}"
    if data.get("claim_id") != expected_claim_id:
        return (
            f"claim_id mismatch: expected {expected_claim_id!r}, "
            f"got {data.get('claim_id')!r}"
        )
    outcome = data.get("local_outcome")
    if not isinstance(outcome, str) or not outcome:
        return f"local_outcome must be a non-empty string, got {outcome!r}"
    return None


def _check_observation_shard(
    items: list[Any],
    expected_criterion_id: str,
) -> str | None:
    """
    Return an error string, or None if the criterion shard is valid.
    A criterion shard is a JSON array of observationJudgment objects.
    """
    if not isinstance(items, list):
        return "criterion shard must be a JSON array of observationJudgment objects"
    if not items:
        # An empty list means NOT_APPLICABLE — acceptable.
        return None
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return f"item[{i}] is not an object"
        missing = _OBSERVATION_FIELDS - set(item)
        if missing:
            return f"item[{i}] missing fields: {sorted(missing)}"
        crit_ids = item.get("criterion_ids", [])
        if not isinstance(crit_ids, list) or not crit_ids:
            return f"item[{i}].criterion_ids must be a non-empty array"
        if expected_criterion_id not in crit_ids:
            return (
                f"item[{i}].criterion_ids {crit_ids!r} "
                f"does not include {expected_criterion_id!r}"
            )
    return None


def _check_evidence_item(item: Any, index: int) -> str | None:
    """Return an error string, or None if the evidence declaration is valid."""
    if not isinstance(item, dict):
        return f"evidence_declarations[{index}] is not an object"
    missing = _EVIDENCE_FIELDS - set(item)
    if missing:
        return f"evidence_declarations[{index}] missing fields: {sorted(missing)}"
    return None


# ---------------------------------------------------------------------------
# Core synthesis
# ---------------------------------------------------------------------------

def synthesize(
    manifest_path: Path | str,
    work_item_id: str,
) -> SynthesisResult:
    """
    Assemble a canonical observation envelope from workflow shard files.

    Parameters
    ----------
    manifest_path:
        Absolute path to ``_manifest.json`` written by the service before
        the Claude session started.
    work_item_id:
        The ``work_item_id`` to embed in the canonical envelope
        (e.g. ``"feature:Feat-01"``).

    Returns
    -------
    SynthesisResult
        On success: ``envelope`` is a fully assembled, schema-compatible dict.

    Raises
    ------
    SynthesisError
        On any missing or invalid shard.  ``shard_errors`` lists every failing
        unit so callers can request per-unit retries.
    """
    manifest_path = Path(manifest_path)
    shard_dir = manifest_path.parent

    manifest = _load_manifest(manifest_path)
    feat_id: str = manifest["feat_id"]
    claim_units: list[dict] = manifest["claim_units"]
    criterion_units: list[dict] = manifest["criterion_units"]

    errors: list[ShardError] = []

    # ------------------------------------------------------------------
    # 1. Collect claim_reviews (per-claim shards)
    # ------------------------------------------------------------------
    claim_reviews: list[dict[str, Any]] = []
    for cu in claim_units:
        missing_keys = _CLAIM_UNIT_REQUIRED - set(cu)
        if missing_keys:
            errors.append(ShardError(
                unit_id=cu.get("claim_id", "<unknown>"),
                unit_type="claim",
                file=cu.get("file", ""),
                reason=f"manifest claim_unit missing keys: {sorted(missing_keys)}",
            ))
            continue

        claim_id: str = cu["claim_id"]
        rel_file: str = cu["file"]

        try:
            data = _load_shard(shard_dir, rel_file)
        except _ShardDecodeError as exc:
            errors.append(ShardError(
                unit_id=claim_id,
                unit_type="claim",
                file=rel_file,
                reason=exc.reason,
            ))
            continue
        if data is None:
            errors.append(ShardError(
                unit_id=claim_id,
                unit_type="claim",
                file=rel_file,
                reason="shard file not found",
            ))
            continue

        err = _check_claim_shard(data, claim_id)
        if err:
            errors.append(ShardError(
                unit_id=claim_id,
                unit_type="claim",
                file=rel_file,
                reason=err,
            ))
            continue

        claim_reviews.append(data)

    # ------------------------------------------------------------------
    # 2. Collect observations (per-criterion shards)
    # ------------------------------------------------------------------
    observations: list[dict[str, Any]] = []
    for cru in criterion_units:
        missing_keys = _CRITERION_UNIT_REQUIRED - set(cru)
        if missing_keys:
            errors.append(ShardError(
                unit_id=cru.get("criterion_id", "<unknown>"),
                unit_type="criterion",
                file=cru.get("file", ""),
                reason=f"manifest criterion_unit missing keys: {sorted(missing_keys)}",
            ))
            continue

        criterion_id: str = cru["criterion_id"]
        rel_file = cru["file"]

        try:
            data = _load_shard(shard_dir, rel_file)
        except _ShardDecodeError as exc:
            errors.append(ShardError(
                unit_id=criterion_id,
                unit_type="criterion",
                file=rel_file,
                reason=exc.reason,
            ))
            continue
        if data is None:
            errors.append(ShardError(
                unit_id=criterion_id,
                unit_type="criterion",
                file=rel_file,
                reason="shard file not found",
            ))
            continue

        err = _check_observation_shard(data, criterion_id)
        if err:
            errors.append(ShardError(
                unit_id=criterion_id,
                unit_type="criterion",
                file=rel_file,
                reason=err,
            ))
            continue

        # data is a list; extend the flat observations list
        observations.extend(data)

    # ------------------------------------------------------------------
    # 3. Load aux shard (evidence_declarations, open_questions, notes)
    # ------------------------------------------------------------------
    evidence_declarations: list[dict[str, Any]] = []
    open_questions: list[str] = []
    notes: list[str] = []

    aux_rel = manifest.get("aux_file", "aux.json")
    aux_data = _load_shard(shard_dir, aux_rel)
    if aux_data is not None:
        raw_ev = aux_data.get("evidence_declarations", [])
        if not isinstance(raw_ev, list):
            errors.append(ShardError(
                unit_id=feat_id,
                unit_type="aux",
                file=aux_rel,
                reason="evidence_declarations must be an array",
            ))
        else:
            for i, item in enumerate(raw_ev):
                ev_err = _check_evidence_item(item, i)
                if ev_err:
                    errors.append(ShardError(
                        unit_id=feat_id,
                        unit_type="aux",
                        file=aux_rel,
                        reason=ev_err,
                    ))
                else:
                    evidence_declarations.append(item)

        raw_oq = aux_data.get("open_questions", [])
        if isinstance(raw_oq, list):
            open_questions = [str(q) for q in raw_oq]

        raw_notes = aux_data.get("notes", [])
        if isinstance(raw_notes, list):
            notes = [str(n) for n in raw_notes]
    # aux is optional: absent aux.json means empty evidence/questions/notes

    # ------------------------------------------------------------------
    # 4. Fail fast if any shard had errors
    # ------------------------------------------------------------------
    if errors:
        raise SynthesisError(
            f"synthesis failed for {feat_id}: "
            f"{len(errors)} shard error(s); see shard_errors for per-unit detail",
            shard_errors=errors,
        )

    # ------------------------------------------------------------------
    # 5. Assemble observationPayload
    # ------------------------------------------------------------------
    payload: dict[str, Any] = {
        "evidence_declarations": evidence_declarations,
        "claim_reviews": claim_reviews,
        "observations": observations,
        "open_questions": open_questions,
        "notes": notes,
    }

    # ------------------------------------------------------------------
    # 6. Wrap in canonical envelope (same shape as _wrap_payload_root)
    # ------------------------------------------------------------------
    envelope: dict[str, Any] = {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "work_item_id": work_item_id,
        "status": "completed",
        "payload": payload,
        "notes": [],
        "error": None,
    }

    return SynthesisResult(
        envelope=envelope,
        claim_count=len(claim_reviews),
        observation_count=len(observations),
        evidence_count=len(evidence_declarations),
    )
