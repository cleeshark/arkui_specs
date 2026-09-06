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
* Repair: shard files whose JSON syntax is a near-miss (unescaped inner
  quotes, trailing commas, BOM) are repaired deterministically before the
  strict re-parse; successful repairs are persisted next to the shard (with a
  ``.bad`` backup) and reported on :attr:`SynthesisResult.repairs`.
* Degrade: per the "usable report first" principle, a shard that is missing,
  unrepairable, or structurally incomplete never fails synthesis.  It is
  replaced by a service-owned ``NOT_VERIFIABLE`` placeholder row (claim) or a
  placeholder observation (criterion) whose verification gap names the cause.
  Placeholder rows reference one synthetic ``review_record`` evidence
  declaration anchored at a frozen repository path from
  ``output_rules.placeholder_anchor_path`` so the published invariant "claim
  evidence is defined by observations" still holds.  Every degradation is
  reported on :attr:`SynthesisResult.placeholders` and appended to the
  payload ``notes``.
* Output : either a validated canonical envelope dict ready to write to
  ``executor_result_path``, or a :class:`SynthesisError` raised only when the
  service-owned manifest itself is damaged (a fatal-input condition, not a
  model-output defect).
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
    LOCAL_OUTCOMES,
    NOT_VERIFIABLE,
    OBSERVATION_JUDGMENT_ENTRY_FIELDS,
    PLACEHOLDER_TEXT,
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
    repairs: list[dict[str, str]] = field(default_factory=list)
    placeholders: list["ShardError"] = field(default_factory=list)


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

_OBSERVATION_FIELDS = frozenset(OBSERVATION_JUDGMENT_ENTRY_FIELDS)
_EVIDENCE_FIELDS = frozenset(EVIDENCE_DECLARATION_FIELDS)

# Anchor evidence key for degradation placeholders; suffixed on collision.
# The payload schema requires evidence keys to match ^e[0-9]+$; the high
# number stays clear of any realistic model-declared key range.
_PLACEHOLDER_EVIDENCE_KEY = "e9001"


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
# Degradation placeholders (service-owned NOT_VERIFIABLE rows)
# ---------------------------------------------------------------------------

def _verification_gap(cause: str) -> dict[str, Any]:
    return {
        "checked_scope": [
            "服务端合成阶段的分片清点、JSON 语法确定性修复与结构校验",
        ],
        "missing_evidence": [f"该单元对应的评审分片内容（{cause}）"],
        "consequence": (
            "本次运行无法给出该单元的核验结论，"
            "已按 NOT_VERIFIABLE 降级发布以保留其余评审结果"
        ),
    }


def _placeholder_claim(
    claim_id: str,
    cause: str,
    anchor_key: str | None,
) -> dict[str, Any]:
    """Build the service-owned NOT_VERIFIABLE row for one lost claim shard.

    The reason/fact embed the claim id so the QUALITY duplicate-text gate sees
    distinct texts across multiple placeholders.
    """
    gap = _verification_gap(cause)
    refs = [anchor_key] if anchor_key else []
    return {
        "claim_id": claim_id,
        "local_outcome": NOT_VERIFIABLE,
        "evidence_refs": list(refs),
        "reason": (
            f"服务降级占位：{claim_id} 的评审分片在执行器输出中缺失或损坏（{cause}），"
            "本次运行无法完成该 Claim 的证据核验，按 NOT_VERIFIABLE 发布。"
        ),
        "verification_gap": gap,
        "defect_keys": [],
        "unit_reviews": [{
            "unit_id": f"{claim_id.replace('/', '-')}-svc-lost",
            "facet_type": "condition",
            "local_outcome": NOT_VERIFIABLE,
            "evidence_refs": list(refs),
            "fact": (
                f"服务降级占位：{claim_id} 的评审分片缺失或损坏（{cause}），"
                "本次运行未产生可核验的事实。"
            ),
            "verification_gap": gap,
        }],
    }


def _placeholder_observation(
    criterion_id: str,
    check_ids: list[Any],
    expected_claim_ids: list[str],
    anchor_key: str | None,
    cause: str,
) -> dict[str, Any]:
    """Build the service-owned NOT_VERIFIABLE entry for one lost criterion shard.

    ``check_ids`` comes from the manifest (D3: the model does not own the
    check set), and ``claim_ids`` covers every expected claim so claim
    coverage and the exact required-check set survive the loss.
    """
    return {
        "criterion_ids": [criterion_id],
        "check_ids": [str(c) for c in check_ids],
        "claim_ids": list(expected_claim_ids),
        "local_outcome": NOT_VERIFIABLE,
        "breadth": "feat_core",
        "contract_family": "service-shard-loss",
        "fact": (
            f"服务降级占位：Criterion {criterion_id} 的评审分片缺失或损坏（{cause}），"
            "本次运行无法完成该维度的核验。"
        ),
        "defect_key": None,
        "primary_criterion_id": None,
        "evidence_refs": [anchor_key] if anchor_key else [],
    }


def _anchor_evidence_declaration(anchor_path: str, key: str) -> dict[str, Any]:
    return {
        "key": key,
        "type": "review_record",
        "path": anchor_path,
        "lines": "",
        "description": (
            "服务降级占位检查记录：锚定本次运行实际输入的冻结仓库路径，"
            "用于关联因评审分片丢失而降级为 NOT_VERIFIABLE 的占位行。"
        ),
    }


def _normalize_claim_row(
    data: Any,
    expected_claim_id: str,
    fixes: list[str],
) -> tuple[dict[str, Any] | None, str | None]:
    """
    Mechanically normalize one loaded claim shard.

    Returns ``(row, None)`` when the shard yields a structurally complete
    claim row, or ``(None, cause)`` when the row must degrade to a service
    placeholder.  Only mechanical repairs happen here (identity re-anchor to
    the manifest's claim id, structural defaults, dropping invalid unit rows,
    deriving the documented unit→claim outcome); review content is never
    invented.
    """
    if not isinstance(data, dict):
        return None, "shard is not a JSON object"
    row = dict(data)
    if row.get("claim_id") != expected_claim_id:
        fixes.append(
            f"claim_id re-identified to {expected_claim_id} "
            f"(was {row.get('claim_id')!r})"
        )
        row["claim_id"] = expected_claim_id

    units_raw = row.get("unit_reviews")
    valid_units: list[dict[str, Any]] = []
    if isinstance(units_raw, list):
        for index, unit in enumerate(units_raw):
            if not isinstance(unit, dict):
                fixes.append(f"unit_reviews[{index}] dropped: not an object")
                continue
            unit_row = dict(unit)
            unit_id = unit_row.get("unit_id")
            outcome = unit_row.get("local_outcome")
            fact = unit_row.get("fact")
            if not (isinstance(unit_id, str) and unit_id.strip()):
                fixes.append(f"unit_reviews[{index}] dropped: missing unit_id")
                continue
            if outcome not in LOCAL_OUTCOMES:
                fixes.append(
                    f"unit_reviews[{index}] dropped: invalid local_outcome {outcome!r}"
                )
                continue
            if not (isinstance(fact, str) and fact.strip()):
                fixes.append(f"unit_reviews[{index}] dropped: empty fact")
                continue
            if not (
                isinstance(unit_row.get("facet_type"), str)
                and unit_row["facet_type"].strip()
            ):
                unit_row["facet_type"] = "condition"
                fixes.append(
                    f"unit_reviews[{index}].facet_type defaulted to 'condition'"
                )
            if not isinstance(unit_row.get("evidence_refs"), list):
                unit_row["evidence_refs"] = []
                fixes.append(f"unit_reviews[{index}].evidence_refs defaulted to []")
            if "verification_gap" not in unit_row:
                unit_row["verification_gap"] = None
            valid_units.append(unit_row)
    else:
        fixes.append("unit_reviews defaulted (missing or not a list)")
    if not valid_units:
        return None, "no structurally valid unit_reviews rows"

    outcome = row.get("local_outcome")
    if outcome not in LOCAL_OUTCOMES:
        unit_outcomes = {u["local_outcome"] for u in valid_units}
        if len(unit_outcomes) == 1:
            # Contract-documented derivation: the claim outcome comes from
            # its units when every unit agrees.
            outcome = next(iter(unit_outcomes))
            fixes.append(
                "local_outcome derived from unit_reviews "
                f"(was {row.get('local_outcome')!r})"
            )
        else:
            return None, f"invalid local_outcome {row.get('local_outcome')!r}"
    row["local_outcome"] = outcome

    reason = row.get("reason")
    if not (
        isinstance(reason, str) and reason.strip() and PLACEHOLDER_TEXT not in reason
    ):
        row["reason"] = "；".join(str(u["fact"]) for u in valid_units)
        fixes.append("reason summarized from unit_reviews facts")
        if not row["reason"].strip():
            return None, "empty reason and no unit facts to summarize"

    if not isinstance(row.get("evidence_refs"), list):
        fixes.append("evidence_refs defaulted to []")
        row["evidence_refs"] = []
    if not isinstance(row.get("verification_gap"), (dict, type(None))):
        fixes.append("verification_gap defaulted to null")
        row["verification_gap"] = None
    elif "verification_gap" not in row:
        row["verification_gap"] = None
    if not isinstance(row.get("defect_keys"), list):
        fixes.append("defect_keys defaulted to []")
        row["defect_keys"] = []
    row["unit_reviews"] = valid_units
    return row, None


class _ShardDecodeError(Exception):
    """Internal signal: shard file exists but JSON is invalid."""
    def __init__(self, reason: str) -> None:
        self.reason = reason


# ---------------------------------------------------------------------------
# Deterministic JSON syntax repair
# ---------------------------------------------------------------------------

# A quote inside a string is only accepted as the closing delimiter when the
# next non-whitespace character is structural; anything else means the model
# emitted a literal quote (e.g. Chinese-emphasis quoting) that must be escaped.
_STRING_CLOSE_FOLLOW = frozenset({",", ":", "}", "]"})


def _repair_json_text(raw: str) -> str | None:
    """
    Best-effort repair of common LLM JSON syntax slips in shard files.

    Scope is deliberately narrow; anything else stays a hard synthesis error:

    * a leading UTF-8 BOM;
    * unescaped ASCII double quotes inside string literals (the
      ``满足"基础图形标签已注册"触发条件`` class of quoting);
    * trailing commas before ``]`` / ``}``.

    Returns the repaired text, or None when no rule applies, the text would be
    unchanged, or the result is structurally hopeless (unterminated string,
    dangling escape).  Callers must re-parse the result strictly.
    """
    text = raw.lstrip("\ufeff")
    out: list[str] = []
    in_string = False
    i = 0
    n = len(text)
    changed = False
    while i < n:
        ch = text[i]
        if not in_string:
            if ch == '"':
                in_string = True
            elif ch == ",":
                j = i + 1
                while j < n and text[j] in " \t\r\n":
                    j += 1
                if j < n and text[j] in "}]":
                    changed = True   # drop the trailing comma
                    i += 1
                    continue
            out.append(ch)
            i += 1
            continue
        # Inside a string literal.
        if ch == "\\":
            if i + 1 >= n:
                return None          # dangling escape: not repairable here
            out.append(text[i:i + 2])
            i += 2
            continue
        if ch == '"':
            j = i + 1
            while j < n and text[j] in " \t\r\n":
                j += 1
            if j < n and text[j] in _STRING_CLOSE_FOLLOW:
                in_string = False    # genuine closing delimiter
                out.append(ch)
            else:
                out.append('\\"')    # literal quote inside the value
                changed = True
            i += 1
            continue
        if ch in "\r\n":
            return None              # raw newline inside a string: not repairable
        out.append(ch)
        i += 1
    if in_string:
        return None                  # unterminated string
    if not changed:
        return None
    return "".join(out)


def _try_repair_shard(
    path: Path,
    rel_file: str,
    raw: str,
) -> tuple[Any, dict[str, str]] | None:
    """
    Attempt a deterministic syntax repair of one shard file.

    On success the repaired text is persisted back over the shard (original
    kept as ``<file>.bad``) and an audit entry is returned alongside the
    parsed value.  Persistence failures keep the in-memory repaired value —
    the strict envelope schema gate downstream still applies.
    """
    text = _repair_json_text(raw)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    entry: dict[str, str] = {
        "file": rel_file,
        "action": "json_syntax_repair",
        "detail": (
            "unescaped inner quotes / trailing comma repaired deterministically "
            "before strict re-parse"
        ),
    }
    backup = Path(str(path) + ".bad")
    try:
        if not backup.exists():
            backup.write_text(raw, encoding="utf-8")
            entry["backup"] = backup.name
        tmp = Path(str(path) + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
        entry["persisted"] = "true"
    except OSError:
        entry["persisted"] = "false"
    return data, entry


def _load_shard(
    shard_dir: Path,
    rel_file: str,
    repairs: list[dict[str, str]] | None = None,
) -> dict[str, Any] | list[Any] | None:
    """
    Load a shard JSON file.

    Returns:
        None when the file does not exist (caller records a "missing" ShardError).
        The parsed value (dict or list) on success — including after a
        successful deterministic syntax repair of a near-miss file.

    Raises:
        _ShardDecodeError when the file exists but is not valid JSON and no
        deterministic repair applies.  Callers catch this and convert it into
        a ShardError so that all failing units are collected in one pass
        rather than aborting early.
    """
    path = shard_dir / rel_file
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        reason = (
            f"shard file exists but is not valid JSON: "
            f"line {exc.lineno} col {exc.colno}: {exc.msg}"
        )
    if repairs is not None:
        repaired = _try_repair_shard(path, rel_file, raw)
        if repaired is not None:
            data, entry = repaired
            repairs.append(entry)
            return data
    raise _ShardDecodeError(reason)


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
        Shard-level damage never fails synthesis: it degrades to service
        placeholders reported on ``placeholders`` and ``repairs``.

    Raises
    ------
    SynthesisError
        Only when the service-owned manifest itself is damaged (unreadable or
        missing required keys) — a fatal-input condition, not a model-output
        defect.
    """
    manifest_path = Path(manifest_path)
    shard_dir = manifest_path.parent

    manifest = _load_manifest(manifest_path)
    feat_id: str = manifest["feat_id"]
    claim_units: list[dict] = manifest["claim_units"]
    criterion_units: list[dict] = manifest["criterion_units"]
    output_rules: dict[str, Any] = (
        manifest["output_rules"]
        if isinstance(manifest.get("output_rules"), dict)
        else {}
    )

    repairs: list[dict[str, str]] = []
    placeholders: list[ShardError] = []
    degradation_notes: list[str] = []

    # Manifest integrity is service-owned: missing unit keys mean the staged
    # run was damaged outside the executor session (fatal-input semantics).
    for cu in claim_units:
        missing = _CLAIM_UNIT_REQUIRED - set(cu)
        if missing:
            raise SynthesisError(
                f"manifest claim_unit missing keys: {sorted(missing)}"
            )
    for cru in criterion_units:
        missing = _CRITERION_UNIT_REQUIRED - set(cru)
        if missing:
            raise SynthesisError(
                f"manifest criterion_unit missing keys: {sorted(missing)}"
            )
    expected_claim_ids: list[str] = [cu["claim_id"] for cu in claim_units]

    # ------------------------------------------------------------------
    # 1. Aux shard first: its declarations also seed the anchor fallback.
    #    aux.json is optional; a lost aux degrades to empty declarations.
    # ------------------------------------------------------------------
    aux_rel = manifest.get("aux_file", "aux.json")
    try:
        aux_data = _load_shard(shard_dir, aux_rel, repairs)
    except _ShardDecodeError as exc:
        aux_data = None
        placeholders.append(ShardError(feat_id, "aux", aux_rel, exc.reason))
        degradation_notes.append(f"aux.json unreadable and unrepairable: {exc.reason}")
    aux_declarations: list[dict[str, Any]] = []
    aux_open_questions: list[str] = []
    aux_notes: list[str] = []
    if isinstance(aux_data, dict):
        raw_ev = aux_data.get("evidence_declarations", [])
        if isinstance(raw_ev, list):
            for i, item in enumerate(raw_ev):
                ev_err = _check_evidence_item(item, i)
                if ev_err:
                    degradation_notes.append(
                        f"aux evidence_declarations[{i}] dropped: {ev_err}"
                    )
                    continue
                aux_declarations.append(item)
        else:
            degradation_notes.append("aux evidence_declarations not a list; ignored")
        raw_oq = aux_data.get("open_questions", [])
        if isinstance(raw_oq, list):
            aux_open_questions = [str(q) for q in raw_oq]
        raw_notes = aux_data.get("notes", [])
        if isinstance(raw_notes, list):
            aux_notes = [str(n) for n in raw_notes]

    # ------------------------------------------------------------------
    # 2. Anchor path for placeholder inspection evidence.  Preference:
    #    the service-provided frozen source-tree path, then a path already
    #    declared by the session (both resolve inside the frozen repos).
    # ------------------------------------------------------------------
    anchor_path = output_rules.get("placeholder_anchor_path")
    if not (isinstance(anchor_path, str) and anchor_path):
        anchor_path = next(
            (
                d.get("path")
                for d in aux_declarations
                if isinstance(d.get("path"), str) and d.get("path")
            ),
            None,
        )
    anchor_key: str | None = None
    if anchor_path:
        anchor_key = _PLACEHOLDER_EVIDENCE_KEY
        suffix = 2
        existing_keys = {d.get("key") for d in aux_declarations}
        while anchor_key in existing_keys:
            anchor_key = f"{_PLACEHOLDER_EVIDENCE_KEY}-{suffix}"
            suffix += 1

    # ------------------------------------------------------------------
    # 3. Collect claim_reviews (per-claim shards); lost or structurally
    #    incomplete shards degrade to NOT_VERIFIABLE placeholders.
    # ------------------------------------------------------------------
    claim_reviews: list[dict[str, Any]] = []
    for cu in claim_units:
        claim_id: str = cu["claim_id"]
        rel_file: str = cu["file"]
        try:
            data = _load_shard(shard_dir, rel_file, repairs)
            cause = None if data is not None else "shard file not found"
        except _ShardDecodeError as exc:
            data, cause = None, exc.reason

        row: dict[str, Any] | None = None
        if data is not None:
            row_fixes: list[str] = []
            row, norm_cause = _normalize_claim_row(data, claim_id, row_fixes)
            for fix in row_fixes:
                repairs.append({
                    "file": rel_file,
                    "action": "claim_row_normalize",
                    "detail": fix,
                })
            cause = norm_cause
        if row is None:
            placeholders.append(ShardError(
                unit_id=claim_id,
                unit_type="claim",
                file=rel_file,
                reason=cause or "unavailable",
            ))
            degradation_notes.append(
                f"claim {claim_id}: degraded to NOT_VERIFIABLE placeholder ({cause})"
            )
            claim_reviews.append(
                _placeholder_claim(claim_id, cause or "unavailable", anchor_key)
            )
            continue
        claim_reviews.append(row)

    # ------------------------------------------------------------------
    # 4. Collect observations (per-criterion shards); a lost or invalid
    #    criterion shard degrades to one placeholder observation carrying
    #    the manifest's check_ids so required-check coverage is preserved.
    # ------------------------------------------------------------------
    observations: list[dict[str, Any]] = []
    for cru in criterion_units:
        criterion_id: str = cru["criterion_id"]
        rel_file = cru["file"]
        try:
            data = _load_shard(shard_dir, rel_file, repairs)
            cause = None if data is not None else "shard file not found"
        except _ShardDecodeError as exc:
            data, cause = None, exc.reason

        items: list[Any] | None = None
        if data is not None:
            if isinstance(data, list):
                err = _check_observation_shard(data, criterion_id)
                if err is None:
                    items = data
                else:
                    cause = err
            else:
                cause = "criterion shard is not a JSON array"
        if items is None:
            placeholders.append(ShardError(
                unit_id=criterion_id,
                unit_type="criterion",
                file=rel_file,
                reason=cause or "unavailable",
            ))
            degradation_notes.append(
                f"criterion {criterion_id}: degraded to NOT_VERIFIABLE "
                f"placeholder ({cause})"
            )
            observations.append(_placeholder_observation(
                criterion_id,
                cru.get("check_ids", []) if isinstance(cru.get("check_ids"), list) else [],
                expected_claim_ids,
                anchor_key,
                cause or "unavailable",
            ))
            continue
        observations.extend(items)

    # ------------------------------------------------------------------
    # 5. Anchor evidence declaration for degraded rows.  normalize attaches
    #    claim-only evidence references to the first published observation,
    #    which keeps the "claim evidence defined by observations" invariant
    #    and the NV inspection-evidence check satisfiable without inventing
    #    any review content.
    # ------------------------------------------------------------------
    evidence_declarations = list(aux_declarations)
    degraded_rows = [p for p in placeholders if p.unit_type in ("claim", "criterion")]
    if degraded_rows and anchor_key and anchor_path:
        evidence_declarations.append(
            _anchor_evidence_declaration(anchor_path, anchor_key)
        )

    # ------------------------------------------------------------------
    # 6. Assemble observationPayload + canonical envelope
    # ------------------------------------------------------------------
    payload: dict[str, Any] = {
        "evidence_declarations": evidence_declarations,
        "claim_reviews": claim_reviews,
        "observations": observations,
        "open_questions": aux_open_questions,
        "notes": aux_notes + degradation_notes,
    }

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
        repairs=repairs,
        placeholders=placeholders,
    )
