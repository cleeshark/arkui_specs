"""Deterministic normalization for evaluator protocol 0.2.0 (design L2).

Everything the model must not own happens here: stable evidence ID
assignment, content hash computation against frozen files, claim row ordering
against the initialized template, derived fields, canonical finding IDs,
secondary criterion derivation, and the expansion of a judgment payload plus
template into the historical published document shape consumed by
aggregation-context, score and the frozen semantic-result schema.

The normalizer is idempotent and never mutates its inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import contracts as K
from .aggregation_context import criteria_by_id, criterion_evidence_catalog
from .errors import FATAL_INPUT, MODEL_CORRECTION, TypedError
from .evidence_paths import EvidencePathError, FrozenEvidencePathResolver

DEFECT_KEY = re.compile(K.DEFECT_KEY_PATTERN)
SEMANTIC_FINDING_IDENTITY_VERSION = 1
OUTCOME_POLICY_BASIS_CRITERIA = K.POLICY_BASIS_CRITERION_IDS
FINDING_SEVERITY_TO_PUBLISHED = {
    "CRITICAL": "Critical",
    "MAJOR": "Major",
    "MINOR": "Minor",
}
PUBLISHED_EVIDENCE_FIELDS = {
    "evidence_id", "type", "path", "line_start", "line_end",
    "source_revision", "content_hash", "claim_id", "description",
}


def _normalize_defect_key(raw: Any) -> str | None:
    """Canonicalize a defect_key value to lowercase; return None if empty/null."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip().lower()


def _repair_defect_key(key: str, valid_keys: set[str]) -> str | None:
    """Try to match *key* to the whitelist by removing a scope prefix.

    The model sometimes adds (``feat-01.trace-rule-orphan``) or removes
    (``trace-rule-orphan``) the work-item scope prefix that was applied during
    aggregation-context construction.  If exactly one valid key ends with the
    unscoped tail (or starts with the key as a prefix), return it.
    """
    # 1. key has extra prefix: "x.feat-01.trace-rule-orphan" -> "feat-01.trace-rule-orphan"
    parts = key.split(".", 1)
    if len(parts) == 2:
        tail = parts[1]
        if tail in valid_keys:
            return tail
    # 2. key is missing prefix: "trace-rule-orphan" -> "feat-01.trace-rule-orphan"
    candidates = [vk for vk in valid_keys if vk.endswith("." + key)]
    if len(candidates) == 1:
        return candidates[0]
    return None


@dataclass(frozen=True)
class NormalizationResult:
    """Output of one normalization pass.

    ``errors`` carries model-owned declaration errors that must enter the one
    correction turn. ``fatal`` is reserved for damaged frozen inputs or
    templates. ``changes`` records SERVICE_NORMALIZATION fixes. The document
    is None when either errors or fatal is set.
    """

    document: dict[str, Any] | None
    changes: list[str] = field(default_factory=list)
    errors: list[TypedError] = field(default_factory=list)
    fatal: list[TypedError] = field(default_factory=list)
    evidence_catalog: list[dict[str, Any]] = field(default_factory=list)


def semantic_finding_id(
    *, func_id: str, defect_key: str, criterion_id: str, claim_id: str | None
) -> str:
    """Stable semantic Finding identity for one owned defect projection."""
    identity = {
        "identity_version": SEMANTIC_FINDING_IDENTITY_VERSION,
        "func_id": func_id,
        "defect_key": defect_key,
        "criterion_id": criterion_id,
        "claim_id": claim_id,
    }
    encoded = json.dumps(
        identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "SEM-" + hashlib.sha256(encoded).hexdigest()[:24]


def _content_hash(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError:
        return None
    return f"sha256:{digest.hexdigest()}"


def _rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _unique_strings(value: Any) -> list[str]:
    """Return non-empty strings once, preserving the model's first-seen order."""
    return list(dict.fromkeys(_strings(value)))


def normalize_observation(
    template: dict[str, Any],
    judgment: dict[str, Any],
    *,
    repo_root: Path,
    evidence_resolver: FrozenEvidencePathResolver | None = None,
) -> NormalizationResult:
    """Expand one observation judgment payload into the published document.

    ``template`` is the initialized observation template (identity, expected
    claim IDs, required checks); ``judgment`` is the executor payload
    (claim_reviews / observations / open_questions / notes). ``repo_root`` is
    retained for isolated callers; production supplies ``evidence_resolver``
    with all frozen repository roots and service-data exclusions.
    """
    errors: list[TypedError] = []
    fatal: list[TypedError] = []
    changes: list[str] = []
    resolver = evidence_resolver or FrozenEvidencePathResolver.ace_engine_only(repo_root)

    # empty expected sets are legitimate (synthetic loop fixtures, empty
    # features); claim-set mismatches are the validator's job
    expected_claims = _strings(template.get("expected_claim_ids"))
    required_checks = _strings(template.get("required_checks"))

    # 1. top-level evidence declarations -> stable IDs + verified content
    #    hashes (design v3 / review §3.4: local keys are work-item scoped and
    #    live at the payload top level; publish converts them to canonical IDs)
    published: dict[str, Any] = copy.deepcopy(template)
    source_revision = str(template.get("source_revision", ""))
    evidence_by_key: dict[str, dict[str, Any]] = {}
    seen_evidence_keys: set[str] = set()
    declaration_order: list[str] = []
    for decl_index, declaration in enumerate(_rows(judgment.get("evidence_declarations"))):
        key = declaration.get("key")
        path_text = declaration.get("path")
        if not isinstance(key, str) or not isinstance(path_text, str):
            errors.append(TypedError(
                "EVIDENCE_DECLARATION_INVALID",
                f"$.evidence_declarations[{decl_index}]",
                entity_type="evidence",
                expected="string key and canonical repository-relative path",
                actual=str(declaration), repairability=MODEL_CORRECTION,
            ))
            continue
        if key in seen_evidence_keys:
            errors.append(TypedError(
                "EVIDENCE_KEY_DUPLICATED",
                f"$.evidence_declarations[{decl_index}].key",
                entity_type="evidence", entity_id=key,
                expected="unique declaration key", actual="duplicate",
                repairability=MODEL_CORRECTION,
            ))
            continue
        seen_evidence_keys.add(key)
        try:
            resolution = resolver.resolve(path_text)
        except EvidencePathError as exc:
            error = TypedError(
                exc.code,
                f"$.evidence_declarations[{decl_index}].path",
                entity_type="evidence", entity_id=key,
                expected=exc.expected, actual=path_text,
                repairability=(
                    FATAL_INPUT if exc.code == "FROZEN_EVIDENCE_UNREADABLE"
                    else MODEL_CORRECTION
                ),
            )
            if error.repairability == FATAL_INPUT:
                fatal.append(error)
            else:
                errors.append(error)
            continue
        hash_value = _content_hash(resolution.absolute_path)
        if hash_value is None:
            fatal.append(TypedError(
                "FROZEN_EVIDENCE_UNREADABLE",
                f"$.evidence_declarations[{decl_index}].path",
                entity_type="evidence", entity_id=key,
                expected="readable file already resolved inside the frozen workspace",
                actual=path_text, repairability=FATAL_INPUT,
            ))
            continue
        row = {
            "evidence_id": f"EV-{len(evidence_by_key) + 1}",
            "type": declaration.get("type"),
            "path": resolution.canonical_path,
            "source_revision": source_revision,
            "content_hash": hash_value,
            "description": declaration.get("description", ""),
        }
        evidence_by_key[key] = row
        declaration_order.append(key)
    changes.append(
        "evidence_declarations: canonical IDs assigned and hashes verified"
    )

    def _resolve_evidence_ids(raw: Any) -> list[str]:
        resolved: list[str] = []
        for item in _strings(raw):
            row = evidence_by_key.get(item)
            if row is not None:
                resolved.append(row["evidence_id"])
            else:
                # catalog references (EV-*) and unknown keys pass through; the
                # validator reports anything not defined in this document
                resolved.append(item)
        return resolved

    # 2. published observations: each carries the declared evidence rows it
    #    references; claim-only references attach to the first observation so
    #    the published invariant (claim evidence defined by observations) holds
    observations: list[dict[str, Any]] = []
    for obs_index, entry in enumerate(_rows(judgment.get("observations"))):
        evidence_rows = [
            evidence_by_key[key]
            for key in _strings(entry.get("evidence_refs"))
            if key in evidence_by_key
        ]
        raw_defect_key = entry.get("defect_key")
        norm_defect_key = _normalize_defect_key(raw_defect_key)
        if raw_defect_key and norm_defect_key and norm_defect_key != raw_defect_key:
            changes.append(
                f"defect_key: canonicalized {raw_defect_key!r} -> {norm_defect_key!r}"
            )
        local_outcome = entry.get("local_outcome")
        primary_criterion = entry.get("primary_criterion_id")
        # Auto-cleanup: clear defect ownership fields for non-adverse outcomes
        if local_outcome not in {"CONFLICT", "MISSING"}:
            if norm_defect_key is not None or primary_criterion is not None:
                changes.append(
                    f"observations[{obs_index}]: cleared defect ownership fields "
                    f"for {local_outcome} outcome"
                )
                norm_defect_key = None
                primary_criterion = None
        observations.append({
            "observation_id": f"OBS-{obs_index + 1}",
            "criterion_ids": _strings(entry.get("criterion_ids")),
            "check_ids": _strings(entry.get("check_ids")),
            "claim_ids": _strings(entry.get("claim_ids")),
            "local_outcome": local_outcome,
            "breadth": entry.get("breadth"),
            "contract_family": entry.get("contract_family", ""),
            "fact": entry.get("fact", ""),
            "defect_key": norm_defect_key,
            "primary_criterion_id": primary_criterion,
            "evidence": evidence_rows,
        })
    claim_referenced_keys: list[str] = []
    for row in _rows(judgment.get("claim_reviews")):
        claim_referenced_keys.extend(_strings(row.get("evidence_refs")))
        for unit in _rows(row.get("unit_reviews")):
            claim_referenced_keys.extend(_strings(unit.get("evidence_refs")))
    obs_referenced_keys: set[str] = {
        key
        for entry in _rows(judgment.get("observations"))
        for key in _strings(entry.get("evidence_refs"))
    }
    if observations:
        for key in declaration_order:
            if key in obs_referenced_keys:
                continue
            if key in claim_referenced_keys and evidence_by_key[key] not in observations[0]["evidence"]:
                observations[0]["evidence"].append(evidence_by_key[key])

    criteria_by_claim: dict[str, list[str]] = {}
    for entry in observations:
        for claim_id in entry["claim_ids"]:
            criteria_by_claim.setdefault(claim_id, [])
            for criterion_id in entry["criterion_ids"]:
                if criterion_id not in criteria_by_claim[claim_id]:
                    criteria_by_claim[claim_id].append(criterion_id)

    # 2. claim judgments ordered by the template's expected claim IDs
    judgments_by_id = {
        row.get("claim_id"): row
        for row in _rows(judgment.get("claim_reviews"))
        if isinstance(row.get("claim_id"), str)
    }
    claim_reviews: list[dict[str, Any]] = []
    for claim_id in expected_claims:
        row = judgments_by_id.get(claim_id)
        if row is None:
            claim_reviews.append({
                "claim_id": claim_id, "status": "pending",
                "local_outcome": K.NOT_VERIFIABLE, "reviewed_units": [],
                "unit_reviews": [], "criterion_ids": [], "evidence_ids": [],
                "defect_keys": [], "reason": "",
                "verification_gap": None,
            })
            continue
        raw_dk_list = _strings(row.get("defect_keys"))
        norm_dk_list = [k for k in (_normalize_defect_key(k) for k in raw_dk_list) if k]
        for raw_k, norm_k in zip(raw_dk_list, norm_dk_list):
            if norm_k != raw_k:
                changes.append(
                    f"claim {claim_id} defect_key: canonicalized {raw_k!r} -> {norm_k!r}"
                )
        units = _rows(row.get("unit_reviews"))
        claim_reviews.append({
            "claim_id": claim_id,
            "status": "complete",
            "local_outcome": row.get("local_outcome"),
            "reviewed_units": [
                unit.get("unit_id") for unit in units
                if isinstance(unit.get("unit_id"), str)
            ],
            "unit_reviews": [{
                "unit_id": unit.get("unit_id"),
                "facet_type": unit.get("facet_type"),
                "local_outcome": unit.get("local_outcome"),
                "evidence_ids": _resolve_evidence_ids(unit.get("evidence_refs")),
                "fact": unit.get("fact", ""),
                "verification_gap": unit.get("verification_gap"),
            } for unit in units],
            "criterion_ids": criteria_by_claim.get(claim_id, []),
            "evidence_ids": _resolve_evidence_ids(row.get("evidence_refs")),
            "defect_keys": norm_dk_list,
            "reason": row.get("reason", ""),
            "verification_gap": (
                row.get("verification_gap")
                if row.get("local_outcome") == K.NOT_VERIFIABLE else None
            ),
        })
    unexpected = sorted(set(judgments_by_id) - set(expected_claims))
    if unexpected:
        # unexpected claim judgments are dropped; the validator reports them
        changes.append(f"claim_reviews: dropped judgments outside expected set: {unexpected}")

    published["claim_reviews"] = claim_reviews
    published["observations"] = observations
    published["open_questions"] = copy.deepcopy(judgment.get("open_questions") or [])
    published["notes"] = copy.deepcopy(judgment.get("notes") or [])
    published["status"] = "complete"
    published["reviewed_claim_ids"] = [
        row["claim_id"] for row in claim_reviews if row.get("status") == "complete"
    ]
    published["completed_checks"] = sorted({
        check for entry in observations for check in entry["check_ids"]
    })
    catalog = [
        {
            "evidence_id": row["evidence_id"], "type": row["type"],
            "path": row["path"], "description": row["description"],
        }
        for row in evidence_by_key.values()
    ]
    if fatal:
        return NormalizationResult(
            document=None, changes=changes, errors=errors, fatal=fatal,
            evidence_catalog=catalog,
        )
    if errors:
        return NormalizationResult(
            document=None, changes=changes, errors=errors,
            evidence_catalog=catalog,
        )
    return NormalizationResult(
        document=published, changes=changes, evidence_catalog=catalog,
    )


def normalize_aggregation(
    template: dict[str, Any],
    judgment: dict[str, Any],
    *,
    source_observation_ids: list[str],
    aggregation_context: dict[str, Any] | None = None,
) -> NormalizationResult:
    """Expand one aggregation judgment payload into the published document.

    Deterministic only: canonical finding IDs from ownership keys, secondary
    criterion derivation, applicability_reason copy, criterion order from the
    template, and Criterion evidence copied from the aggregation context.
    Conclusions, evidence selections and prose pass through.
    """
    changes: list[str] = []
    errors: list[TypedError] = []
    fatal: list[TypedError] = []
    func_id = str(template.get("func_id", ""))
    if not func_id:
        fatal.append(TypedError(
            "TEMPLATE_MISSING_FIELD", "$.func_id", repairability=FATAL_INPUT,
        ))
        return NormalizationResult(document=None, fatal=fatal)

    ownership_rows = _rows(judgment.get("defect_ownership"))
    owner_by_finding_key: dict[str, str] = {}
    # Build defect_key whitelist from aggregation context
    valid_defect_keys: set[str] = set()
    if aggregation_context is not None:
        for key in aggregation_context.get("valid_defect_keys", []):
            if isinstance(key, str):
                valid_defect_keys.add(key)
    for record in ownership_rows:
        raw_dk = record.get("defect_key")
        defect_key = _normalize_defect_key(raw_dk)
        if raw_dk and defect_key and defect_key != raw_dk:
            changes.append(
                f"defect_ownership: canonicalized {raw_dk!r} -> {defect_key!r}"
            )
        # L2a: auto-fix defect_key not in whitelist (issue #51)
        if defect_key and valid_defect_keys and defect_key not in valid_defect_keys:
            repaired = _repair_defect_key(defect_key, valid_defect_keys)
            if repaired is not None:
                changes.append(
                    f"defect_ownership: repaired {defect_key!r} -> {repaired!r} "
                    "(matched after removing scope prefix)"
                )
                defect_key = repaired
                record["defect_key"] = repaired
        for finding_key in _strings(record.get("finding_keys")):
            previous = owner_by_finding_key.get(finding_key)
            if previous is not None and previous != defect_key:
                fatal.append(TypedError(
                    "DUPLICATE_DEFECT_OWNER", "$.defect_ownership",
                    entity_type="finding", entity_id=finding_key,
                    expected="one owner", actual=f"{previous} and {defect_key}",
                    repairability=FATAL_INPUT,
                ))
            else:
                owner_by_finding_key[finding_key] = str(defect_key or "")

    template_results = {
        row.get("criterion_id"): row
        for row in _rows(template.get("criterion_results"))
    }
    judgment_by_criterion = {
        row.get("criterion_id"): row
        for row in _rows(judgment.get("criterion_results"))
    }
    context_by_criterion = criteria_by_id(aggregation_context)
    policy_judgment = {
        row.get("criterion_id"): row
        for row in _rows(judgment.get("outcome_policy_bases"))
    }
    policy_rows = _rows(judgment.get("outcome_policy_bases"))
    policy_order = [
        row.get("criterion_id") for row in policy_rows
        if isinstance(row.get("criterion_id"), str)
    ]
    policy_basis_valid = policy_order == list(OUTCOME_POLICY_BASIS_CRITERIA)
    if policy_basis_valid:
        policy_basis_valid = all(
            K.expected_policy_conclusion(
                row.get("content_status"),
                row.get("evidence_status"),
                row.get("conflict_scope"),
            ) is not None
            for row in policy_rows
        )
    inherited_catalog: list[dict[str, Any]] = []
    inherited_ids: set[str] = set()
    for evidence in (aggregation_context or {}).get("evidence_catalog", {}).values():
        if not isinstance(evidence, dict):
            continue
        evidence_id = evidence.get("evidence_id")
        if isinstance(evidence_id, str) and evidence_id not in inherited_ids:
            inherited_catalog.append(copy.deepcopy(evidence))
            inherited_ids.add(evidence_id)
    criterion_results: list[dict[str, Any]] = []
    canonical_ids: set[str] = set()
    finding_by_key: dict[str, dict[str, Any]] = {}
    for criterion_id, template_row in template_results.items():
        row = judgment_by_criterion.get(criterion_id, {})
        conclusion = row.get("conclusion")
        reason = str(row.get("reason", ""))
        applicability_reason = row.get("applicability_reason")
        if (
            conclusion == "NOT_APPLICABLE"
            and not str(applicability_reason or "").strip()
            and reason.strip()
        ):
            applicability_reason = reason
            changes.append(f"criterion_results[{criterion_id}].applicability_reason copied")
        findings: list[dict[str, Any]] = []
        context_row = context_by_criterion.get(criterion_id, {})
        criterion_catalog = {
            evidence.get("evidence_id"): evidence
            for evidence in criterion_evidence_catalog(aggregation_context, context_row)
            if isinstance(evidence.get("evidence_id"), str)
        }
        raw_evidence_ids = _strings(row.get("evidence_ids"))
        requested_evidence_ids = _unique_strings(row.get("evidence_ids"))
        if requested_evidence_ids != raw_evidence_ids:
            changes.append(
                f"criterion_results[{criterion_id}].evidence_ids deduplicated"
            )
        # A finding's valid evidence reference is also criterion evidence. The
        # model may omit the parent reference, so close the relation here in a
        # stable order instead of sending a representational mismatch to the
        # correction turn.
        for finding in _rows(row.get("findings")):
            for evidence_id in _unique_strings(finding.get("evidence_ids")):
                if evidence_id in criterion_catalog and evidence_id not in requested_evidence_ids:
                    requested_evidence_ids.append(evidence_id)
                    changes.append(
                        f"criterion_results[{criterion_id}].evidence_ids closed over "
                        f"finding evidence {evidence_id}"
                    )
        unknown_evidence = sorted(
            set(requested_evidence_ids) - set(criterion_catalog)
        )
        if unknown_evidence:
            errors.append(TypedError(
                "CRITERION_EVIDENCE_UNKNOWN",
                f"$.criterion_results[{criterion_id}].evidence_ids",
                entity_type="criterion", entity_id=str(criterion_id),
                expected=f"one of {sorted(criterion_catalog)}",
                actual=str(unknown_evidence), repairability=MODEL_CORRECTION,
            ))
        criterion_evidence = [
            {
                key: copy.deepcopy(value)
                for key, value in criterion_catalog[evidence_id].items()
                if key in PUBLISHED_EVIDENCE_FIELDS
            }
            for evidence_id in requested_evidence_ids
            if evidence_id in criterion_catalog
        ]
        for finding in _rows(row.get("findings")):
            finding_key = finding.get("key")
            defect_key = (
                owner_by_finding_key.get(finding_key)
                if isinstance(finding_key, str) else None
            )
            claim_id = finding.get("claim_id")
            finding_id = None
            if defect_key is not None and isinstance(criterion_id, str):
                finding_id = semantic_finding_id(
                    func_id=func_id, defect_key=defect_key,
                    criterion_id=criterion_id,
                    claim_id=claim_id if isinstance(claim_id, str) else None,
                )
                if finding_id in canonical_ids:
                    fatal.append(TypedError(
                        "FINDING_ID_COLLISION",
                        f"$.criterion_results[{criterion_id}].findings",
                        entity_type="finding", entity_id=str(finding_key),
                        actual=finding_id, repairability=FATAL_INPUT,
                    ))
                    finding_id = None
                else:
                    canonical_ids.add(finding_id)
            raw_finding_evidence_ids = _strings(finding.get("evidence_ids"))
            finding_evidence_ids = _unique_strings(finding.get("evidence_ids"))
            if finding_evidence_ids != raw_finding_evidence_ids:
                changes.append(
                    f"criterion_results[{criterion_id}].findings[{finding_key}]."
                    "evidence_ids deduplicated"
                )
            published_finding = {
                "finding_id": finding_id,
                "criterion_id": criterion_id,
                "severity": FINDING_SEVERITY_TO_PUBLISHED.get(
                    finding.get("severity"), finding.get("severity")
                ),
                "conclusion": conclusion,
                "message": finding.get("message", ""),
                "evidence_ids": finding_evidence_ids,
                "recommendation": finding.get("recommendation"),
            }
            if isinstance(claim_id, str) and claim_id:
                published_finding["claim_id"] = claim_id
            findings.append(published_finding)
            if isinstance(finding_key, str):
                finding_by_key[finding_key] = published_finding
        raw_claim_ids = _strings(row.get("claim_ids"))
        claim_ids = _unique_strings(row.get("claim_ids"))
        if claim_ids != raw_claim_ids:
            changes.append(f"criterion_results[{criterion_id}].claim_ids deduplicated")
        # Auto-fix forbidden conclusion when a required conclusion exists
        context_constraints = context_row.get("constraints", {})
        forbidden = context_constraints.get("forbidden_conclusions", [])
        required_conclusion = context_constraints.get("required_conclusion_when_no_adverse")
        if conclusion in forbidden and required_conclusion:
            changes.append(
                f"criterion_results[{criterion_id}].conclusion: "
                f"{conclusion} is forbidden, auto-corrected to {required_conclusion}"
            )
            conclusion = required_conclusion
            for finding in findings:
                finding["conclusion"] = conclusion
        conclusion_basis = policy_judgment.get(criterion_id, {})
        if criterion_id in OUTCOME_POLICY_BASIS_CRITERIA and policy_basis_valid:
            derived_conclusion = K.expected_policy_conclusion(
                conclusion_basis.get("content_status"),
                conclusion_basis.get("evidence_status"),
                conclusion_basis.get("conflict_scope"),
            )
            if derived_conclusion is not None:
                if conclusion != derived_conclusion:
                    changes.append(
                        f"criterion_results[{criterion_id}].conclusion derived from "
                        "outcome_policy_bases"
                    )
                conclusion = derived_conclusion
                for finding in findings:
                    finding["conclusion"] = conclusion
        criterion_result = {
            "criterion_id": criterion_id,
            "dimension_id": template_row.get("dimension_id"),
            "conclusion": conclusion,
            "applicability": row.get("applicability", template_row.get("applicability")),
            "reason": reason,
            "evidence": criterion_evidence,
            "claim_ids": claim_ids,
            "findings": findings,
        }
        if isinstance(applicability_reason, str) and applicability_reason.strip():
            criterion_result["applicability_reason"] = applicability_reason
        missing_evidence = row.get("missing_evidence")
        if isinstance(missing_evidence, str) and missing_evidence.strip():
            criterion_result["missing_evidence"] = missing_evidence
        criterion_results.append(criterion_result)
        if findings:
            changes.append(
                f"criterion_results[{criterion_id}]: canonical finding IDs assigned"
            )
    extra = sorted(set(judgment_by_criterion) - set(template_results))
    if extra:
        changes.append(f"criterion_results: dropped unexpected criteria: {extra}")

    # map canonical finding IDs for ownership and validator lookups
    findings_by_id: dict[str, dict[str, Any]] = {}
    for result in criterion_results:
        for finding in result["findings"]:
            fid = finding.get("finding_id")
            if isinstance(fid, str):
                findings_by_id[fid] = finding

    defect_ownership: list[dict[str, Any]] = []
    for record in ownership_rows:
        defect_key = _normalize_defect_key(record.get("defect_key")) or ""
        primary = record.get("primary_criterion_id")
        finding_ids = [
            finding_by_key[key]["finding_id"]
            for key in _strings(record.get("finding_keys"))
            if key in finding_by_key and finding_by_key[key].get("finding_id")
        ]
        owned = [
            findings_by_id[fid] for fid in finding_ids if fid in findings_by_id
        ]
        expected_secondary = sorted({
            finding["criterion_id"] for finding in owned
            if isinstance(finding.get("criterion_id"), str)
            and finding["criterion_id"] != primary
        })
        defect_ownership.append({
            "defect_key": defect_key,
            "primary_criterion_id": primary,
            "finding_ids": finding_ids,
            "secondary_criterion_ids": expected_secondary,
            "rationale": record.get("rationale", ""),
        })
        changes.append(f"defect_ownership[{defect_key}]: secondary criteria derived")

    outcome_policy_bases = copy.deepcopy(policy_rows)

    contradiction_bases = copy.deepcopy(judgment.get("contradiction_bases") or [])
    for basis in contradiction_bases:
        raw_pdk = basis.get("primary_defect_key")
        norm_pdk = _normalize_defect_key(raw_pdk)
        if norm_pdk and norm_pdk != raw_pdk:
            basis["primary_defect_key"] = norm_pdk
            changes.append(
                f"contradiction_basis: canonicalized primary_defect_key "
                f"{raw_pdk!r} -> {norm_pdk!r}"
            )

    published = copy.deepcopy(template)
    published.update({
        "status": "complete",
        "source_observation_ids": list(source_observation_ids),
        "cross_feat_contracts_reviewed": judgment.get("cross_feat_contracts_reviewed"),
        "contradiction_bases": contradiction_bases,
        "defect_ownership": defect_ownership,
        "outcome_policy_bases": outcome_policy_bases,
        "criterion_results": criterion_results,
        "notes": copy.deepcopy(judgment.get("notes") or []),
    })
    if fatal:
        return NormalizationResult(
            document=None, changes=changes, errors=errors, fatal=fatal,
            evidence_catalog=inherited_catalog,
        )
    if errors:
        return NormalizationResult(
            document=None, changes=changes, errors=errors,
            evidence_catalog=inherited_catalog,
        )
    return NormalizationResult(
        document=published, changes=changes, evidence_catalog=inherited_catalog,
    )


def assemble_semantic_result(
    semantic_template: dict[str, Any], aggregation: dict[str, Any]
) -> dict[str, Any]:
    """Assemble the final semantic-result document (published shape)."""
    candidate = copy.deepcopy(semantic_template)
    results = copy.deepcopy(aggregation["criterion_results"])
    candidate["criterion_results"] = results
    candidate["coverage"] = {
        "expected_criteria": len(results),
        "evaluated_criteria": len(results),
        "applicable_criteria": sum(
            item.get("applicability") == "APPLICABLE" for item in results
        ),
        "not_applicable_criteria": sum(
            item.get("conclusion") == "NOT_APPLICABLE" for item in results
        ),
        "not_verifiable_criteria": sum(
            item.get("conclusion") == "NOT_VERIFIABLE" for item in results
        ),
    }
    notes = list(candidate.get("execution", {}).get("notes", []))
    notes.append(
        "Staged execution: Feature and Function-global observations were "
        "checkpointed before final aggregation."
    )
    candidate["execution"] = {
        "static_complete": True,
        "evidence_complete": True,
        "semantic_complete": True,
        "notes": notes,
    }
    return candidate
