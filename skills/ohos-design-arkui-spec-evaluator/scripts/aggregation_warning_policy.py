"""Shared non-blocking aggregation warning policy for assemble/final stages."""

from __future__ import annotations

import json
from pathlib import Path


# These are bounded semantic-quality warnings rather than structural damage.
# The report remains consumable because Criterion findings, evidence, and the
# final schema are intact. Keep all other aggregation validation errors
# blocking.
OWNERSHIP_WARNING_MARKERS = (
    "one defect may produce at most one Critical Finding",
    "a Critical Finding must belong to the primary Criterion",
    # A correction may retain a non-empty primary Criterion that does not
    # occur among the Finding rows.  The report still has complete Findings;
    # preserve the ownership inconsistency as a bounded warning.
    "must own one mapped Finding",
    "expected one of observation owners",
)
OWNERSHIP_WARNING_CODE = "OWNERSHIP_CRITICALITY"
OWNERSHIP_WARNING_DEDUCTION = 20
MAPPING_WARNING_MARKER = ".claim_ids: not mapped to Criterion:"
MAPPING_WARNING_CODE = "MAPPING_CLAIM_UNMAPPED"
MAPPING_WARNING_DEDUCTION = 5
FINDING_EVIDENCE_WARNING_MARKER = (
    "service-warning:FINDING_EVIDENCE_UNKNOWN:"
)
FINDING_EVIDENCE_WARNING_CODE = "FINDING_EVIDENCE_UNKNOWN"
FINDING_EVIDENCE_WARNING_DEDUCTION = 20
CONTRADICTION_BASIS_WARNING_MARKERS = (
    "basis defects must cover every CONTRADICTED Criterion",
    # A model correction can assign the same root defect to two basis rows.
    # This is representational duplication, not loss of Criterion evidence.
    "primary_defect_key: duplicate contradiction basis",
    # An unresolved root-defect mapping does not invalidate the Criterion
    # results or their Findings; retain it as a bounded quality warning after
    # the single Correction turn.
    "primary_defect_key: unknown defect",
    "primary_defect_key: defect does not affect any CONTRADICTED Criterion",
)
CONTRADICTION_BASIS_WARNING_CODE = "CONTRADICTION_BASIS_INVALID"
CONTRADICTION_BASIS_WARNING_DEDUCTION = 5
# A Criterion whose evidence is present but of the wrong type for its required
# evidence types is a bounded data-quality gap, not structural damage. The model
# cannot fabricate a compliant evidence type without violating the evidence
# allowlist, and the kernel classifies EVIDENCE_TYPE_MISSING as a non-blocking
# (MAJOR) confidence deduction. Downgrade the final-gate error so the report can
# still be published with reduced confidence instead of terminating.
EVIDENCE_TYPE_WARNING_MARKER = "evidence must include one of"
EVIDENCE_TYPE_WARNING_CODE = "EVIDENCE_TYPE_MISSING"
EVIDENCE_TYPE_WARNING_DEDUCTION = 20
# A claim published with empty ``criterion_ids`` means no observation mapped a
# Criterion onto it.  The Criterion results and Findings are still intact — this
# is a bounded coverage gap, semantically identical to the aggregation-side
# ``MAPPING_CLAIM_UNMAPPED`` (an unmapped Claim), so it warrants the same MINOR
# deduction rather than terminating the whole job at the aggregation preflight.
# Unlike the unit-review markers below, this error is emitted by the skill
# validator itself and is never pre-registered in post-correction-warnings.json,
# so it is downgraded unconditionally (see split_claim_coverage_warnings).
CLAIM_COVERAGE_WARNING_MARKER = "criterion_ids: at least one Criterion is required"
CLAIM_COVERAGE_WARNING_CODE = "OBSERVATION_CLAIM_COVERAGE"
CLAIM_COVERAGE_WARNING_DEDUCTION = 5
# A NOT_VERIFIABLE claim that references no review_record evidence means the
# model could not locate an existing inspection record to cite.  The correction
# model is also unable to fabricate one.  The observation conclusion is still
# semantically valid; downgrade unconditionally (MINOR -5) rather than blocking
# the whole job.  Both the claim_review and unit_review paths use the same
# marker suffix so one check covers both.
NV_INSPECTION_WARNING_MARKER = "NOT_VERIFIABLE must reference review_record inspection evidence"
NV_INSPECTION_WARNING_CODE = "NV_INSPECTION_EVIDENCE_MISSING"
NV_INSPECTION_WARNING_DEDUCTION = 5
# A correction patch can add a raw evidence row (e.g. review_record) directly
# into observation.evidence without assigning a canonical evidence_id or path,
# bypassing the EV-* resolution path.  The row is structurally incomplete, but
# the rest of the observation and its claim mappings are intact.  Downgrade
# unconditionally (MINOR -5) so the preflight does not terminate the whole job.
EVIDENCE_FIELD_WARNING_MARKERS = (
    ".evidence_id: expected a non-empty string",
    ".path: expected a non-empty string",
)
EVIDENCE_FIELD_WARNING_CODE = "OBSERVATION_EVIDENCE_FIELD_INVALID"
EVIDENCE_FIELD_WARNING_DEDUCTION = 5
POST_CORRECTION_WARNING_FILE = "post-correction-warnings.json"
OBSERVATION_WARNING_MARKERS = {
    "UNIT_ROW_INVALID": (
        ".unit_reviews: expected at least one atomic unit review",
        ".reviewed_units: enumerate the checked scope units",
        ".unit_reviews: unit IDs must exactly match reviewed_units in order",
    ),
    "UNIT_CLAIM_OUTCOME_CONFLICT": (
        ".unit_reviews: at least one unit must carry claim outcome",
        ".unit_reviews: a supported claim requires all units supported",
        ".unit_reviews: an inapplicable claim requires all units inapplicable",
    ),
}


def split_observation_warnings(
    run_dir: Path,
    errors: list[str],
) -> tuple[list[str], list[str]]:
    """Downgrade only observation errors recorded after bounded Correction."""
    try:
        document = json.loads(
            (run_dir / POST_CORRECTION_WARNING_FILE).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return list(errors), []
    records = document.get("warnings") if isinstance(document, dict) else None
    if not isinstance(records, list):
        return list(errors), []
    eligible: set[tuple[str, str]] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        work_item_id = record.get("work_item_id")
        typed = record.get("error")
        code = typed.get("code") if isinstance(typed, dict) else None
        if (
            isinstance(work_item_id, str)
            and work_item_id
            and code in OBSERVATION_WARNING_MARKERS
        ):
            eligible.add((work_item_id, code))
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        downgraded = any(
            error.startswith(f"observation[{work_item_id}]")
            and any(marker in error for marker in OBSERVATION_WARNING_MARKERS[code])
            for work_item_id, code in eligible
        )
        (warnings if downgraded else blocking).append(error)
    return blocking, warnings


def split_evidence_field_warnings(
    errors: list[str],
) -> tuple[list[str], list[str]]:
    """Downgrade evidence-row missing-field errors unconditionally.

    A correction patch can add a raw evidence row (e.g. review_record) directly
    into observation.evidence without a canonical evidence_id or path.  The rest
    of the observation and its claim mappings remain intact, so downgrade
    unconditionally (MINOR -5) rather than terminating the whole job.
    """
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        (
            warnings if any(m in error for m in EVIDENCE_FIELD_WARNING_MARKERS)
            else blocking
        ).append(error)
    return blocking, warnings


def split_nv_inspection_warnings(
    errors: list[str],
) -> tuple[list[str], list[str]]:
    """Downgrade NOT_VERIFIABLE missing-inspection-evidence errors unconditionally.

    A NOT_VERIFIABLE claim that references no review_record evidence means no
    inspection record was ever declared — a bounded quality gap the model cannot
    fix after the fact.  Downgrade unconditionally (MINOR -5) so the job can
    still produce a report.
    """
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        (warnings if NV_INSPECTION_WARNING_MARKER in error else blocking).append(
            error
        )
    return blocking, warnings


def split_claim_coverage_warnings(
    errors: list[str],
) -> tuple[list[str], list[str]]:
    """Downgrade observation claim-coverage errors unconditionally.

    An empty-``criterion_ids`` claim review is a bounded coverage gap, not
    structural damage: every Criterion result and Finding is intact.  Because
    the skill validator raises this error directly (it is never recorded in
    ``post-correction-warnings.json``), it cannot be gated by the eligibility
    check in :func:`split_observation_warnings`; it is downgraded whenever the
    marker appears.
    """
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        (warnings if CLAIM_COVERAGE_WARNING_MARKER in error else blocking).append(
            error
        )
    return blocking, warnings


def split_aggregation_warnings(errors: list[str]) -> tuple[list[str], list[str]]:
    """Return ``(blocking_errors, downgraded_warnings)`` for report policy."""
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        if (
            any(marker in error for marker in OWNERSHIP_WARNING_MARKERS)
            or MAPPING_WARNING_MARKER in error
            or FINDING_EVIDENCE_WARNING_MARKER in error
            or any(
                marker in error
                for marker in CONTRADICTION_BASIS_WARNING_MARKERS
            )
            or EVIDENCE_TYPE_WARNING_MARKER in error
        ):
            warnings.append(error)
        else:
            blocking.append(error)
    return blocking, warnings


def split_final_candidate_warnings(
    errors: list[str],
) -> tuple[list[str], list[str]]:
    """Return ``(blocking_errors, downgraded_warnings)`` for the final gate.

    The final-candidate protocol validator re-checks required evidence types.
    A Criterion carrying evidence of the wrong type is a bounded data-quality
    gap the kernel treats as a non-blocking confidence deduction, and the model
    cannot fabricate a compliant type without violating the evidence allowlist.
    Downgrade it so a report that passed the aggregation gate is not re-blocked
    here for a gap that only warrants reduced confidence.
    """
    blocking: list[str] = []
    warnings: list[str] = []
    for error in errors:
        if EVIDENCE_TYPE_WARNING_MARKER in error:
            warnings.append(error)
        else:
            blocking.append(error)
    return blocking, warnings


def record_aggregation_warnings(run_dir: Path, warnings: list[str]) -> None:
    """Idempotently apply confidence deductions for downgraded warnings."""
    ownership_warnings = [
        warning for warning in warnings
        if any(marker in warning for marker in OWNERSHIP_WARNING_MARKERS)
    ]
    mapping_warnings = [
        warning for warning in warnings
        if MAPPING_WARNING_MARKER in warning
    ]
    record_ownership_warning(run_dir, ownership_warnings)
    record_mapping_warning(run_dir, mapping_warnings)
    record_finding_evidence_warning(run_dir, [
        warning for warning in warnings
        if FINDING_EVIDENCE_WARNING_MARKER in warning
    ])
    record_contradiction_basis_warning(run_dir, [
        warning for warning in warnings
        if any(
            marker in warning
            for marker in CONTRADICTION_BASIS_WARNING_MARKERS
        )
    ])
    record_evidence_type_warning(run_dir, [
        warning for warning in warnings
        if EVIDENCE_TYPE_WARNING_MARKER in warning
    ])


def record_ownership_warning(run_dir: Path, warnings: list[str]) -> None:
    """Apply one bounded confidence deduction for ownership-quality warnings."""
    _record_confidence_warning(
        run_dir, warnings,
        code=OWNERSHIP_WARNING_CODE,
        layer="MAJOR",
        deduction=OWNERSHIP_WARNING_DEDUCTION,
        message=(
            "defect ownership contains non-structural cross-Criterion "
            "inconsistencies"
        ),
        warning_path="aggregation.defect_ownership",
    )


def record_mapping_warning(run_dir: Path, warnings: list[str]) -> None:
    """Apply one bounded deduction for post-Correction unmapped Claims."""
    _record_confidence_warning(
        run_dir, warnings,
        code=MAPPING_WARNING_CODE,
        layer="MINOR",
        deduction=MAPPING_WARNING_DEDUCTION,
        message="aggregation retains Claim IDs outside the Criterion mapping",
        warning_path="aggregation.criterion_results[].claim_ids",
    )


def record_claim_coverage_warning(run_dir: Path, warnings: list[str]) -> None:
    """Deduct confidence for claims left without a mapped Criterion."""
    _record_confidence_warning(
        run_dir, warnings,
        code=CLAIM_COVERAGE_WARNING_CODE,
        layer="MINOR",
        deduction=CLAIM_COVERAGE_WARNING_DEDUCTION,
        message=(
            "observation retains a Claim not covered by any Criterion "
            "(empty criterion_ids)"
        ),
        warning_path="observation.claim_reviews[].criterion_ids",
    )


def record_nv_inspection_warning(run_dir: Path, warnings: list[str]) -> None:
    """Deduct confidence when a NOT_VERIFIABLE claim lacks review_record evidence."""
    _record_confidence_warning(
        run_dir, warnings,
        code=NV_INSPECTION_WARNING_CODE,
        layer="MINOR",
        deduction=NV_INSPECTION_WARNING_DEDUCTION,
        message=(
            "NOT_VERIFIABLE claim references no review_record inspection evidence; "
            "no inspection record was declared for this observation"
        ),
        warning_path="observation.claim_reviews[].evidence_ids",
    )


def record_evidence_field_warning(run_dir: Path, warnings: list[str]) -> None:
    """Deduct confidence for evidence rows missing required fields."""
    _record_confidence_warning(
        run_dir, warnings,
        code=EVIDENCE_FIELD_WARNING_CODE,
        layer="MINOR",
        deduction=EVIDENCE_FIELD_WARNING_DEDUCTION,
        message=(
            "observation evidence row is missing evidence_id or path "
            "(injected by correction without canonical resolution)"
        ),
        warning_path="observation.observations[].evidence[]",
    )


def record_finding_evidence_warning(
    run_dir: Path, warnings: list[str]
) -> None:
    """Deduct confidence after removing unknown Finding evidence refs."""
    _record_confidence_warning(
        run_dir, warnings,
        code=FINDING_EVIDENCE_WARNING_CODE,
        layer="MAJOR",
        deduction=FINDING_EVIDENCE_WARNING_DEDUCTION,
        message=(
            "service removed Finding evidence references absent from the "
            "frozen Criterion catalog"
        ),
        warning_path="aggregation.criterion_results[].findings[].evidence_ids",
    )


def record_evidence_type_warning(run_dir: Path, warnings: list[str]) -> None:
    """Deduct confidence when a Criterion lacks its required evidence types."""
    _record_confidence_warning(
        run_dir, warnings,
        code=EVIDENCE_TYPE_WARNING_CODE,
        layer="MAJOR",
        deduction=EVIDENCE_TYPE_WARNING_DEDUCTION,
        message=(
            "aggregation retains a Criterion whose evidence does not include a "
            "required evidence type"
        ),
        warning_path="aggregation.criterion_results[].evidence",
    )


def record_contradiction_basis_warning(
    run_dir: Path, warnings: list[str]
) -> None:
    """Deduct confidence when root-defect basis coverage is incomplete."""
    _record_confidence_warning(
        run_dir, warnings,
        code=CONTRADICTION_BASIS_WARNING_CODE,
        layer="MINOR",
        deduction=CONTRADICTION_BASIS_WARNING_DEDUCTION,
        message=(
            "contradiction root-defect basis does not cover every contradicted "
            "Criterion"
        ),
        warning_path="aggregation.contradiction_bases",
    )


def _record_confidence_warning(
    run_dir: Path,
    warnings: list[str],
    *,
    code: str,
    layer: str,
    deduction: int,
    message: str,
    warning_path: str,
) -> None:
    """Idempotently add one confidence warning entry."""
    if not warnings:
        return
    confidence_path = run_dir / "confidence-result.json"
    try:
        confidence = (
            json.loads(confidence_path.read_text(encoding="utf-8"))
            if confidence_path.is_file() else {}
        )
    except (OSError, ValueError):
        confidence = {}
    if not isinstance(confidence, dict):
        confidence = {}
    target_key = "major_violations" if layer == "MAJOR" else "minor_violations"
    target = confidence.get(target_key)
    if not isinstance(target, list):
        target = []
    if any(
        isinstance(item, dict) and item.get("code") == code
        for item in target
    ):
        return
    target.append({
        "layer": layer,
        "code": code,
        "criterion_id": "",
        "deduction": deduction,
        "message": f"{message}; {len(warnings)} check(s) downgraded to warnings",
        "path": warning_path,
    })
    confidence[target_key] = target
    confidence["hard_errors"] = (
        confidence.get("hard_errors")
        if isinstance(confidence.get("hard_errors"), list) else []
    )
    major = confidence.get("major_violations")
    if not isinstance(major, list):
        major = []
    confidence["major_violations"] = major
    minor = confidence.get("minor_violations")
    if not isinstance(minor, list):
        minor = []
    confidence["minor_violations"] = minor
    confidence["deduction_total"] = sum(
        int(item.get("deduction", 0))
        for item in [*confidence["hard_errors"], *major, *minor]
        if isinstance(item, dict)
    )
    confidence["confidence_score"] = max(0, 100 - confidence["deduction_total"])
    score = confidence["confidence_score"]
    confidence["confidence_level"] = (
        "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
    )
    confidence["total_checks_failed"] = sum(
        [len(confidence["hard_errors"]), len(major), len(minor)]
    )
    try:
        confidence_path.write_text(
            json.dumps(confidence, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        # Confidence is advisory; inability to persist it must not prevent the
        # already-valid semantic report from being assembled or finalized.
        pass
