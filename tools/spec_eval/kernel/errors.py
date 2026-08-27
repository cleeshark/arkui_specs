"""Typed validation errors for evaluator protocol 0.2.0.

Errors are data, not prose: every failure carries a stable code, a JSON path,
the entity it belongs to and a closed ``repairability`` classification. The
orchestrator routes on ``repairability`` only and never matches validator
message text.

Protocol 0.2.1 adds a ``confidence_layer`` per error code: HARD errors block
assembly; MAJOR/MINOR errors reduce the report confidence score but do not
prevent report generation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# Closed repairability classification. New error codes must bind to one of
# these three values at registration time.
SERVICE_NORMALIZATION = "SERVICE_NORMALIZATION"
MODEL_CORRECTION = "MODEL_CORRECTION"
FATAL_INPUT = "FATAL_INPUT"

_REPAIRABILITY = (SERVICE_NORMALIZATION, MODEL_CORRECTION, FATAL_INPUT)

# Confidence layers (0.2.1): how much a validation failure impacts the report.
LAYER_HARD = "HARD"    # structure not assemblable → block
LAYER_MAJOR = "MAJOR"  # core invariant violated → -20 confidence
LAYER_MINOR = "MINOR"  # structural completeness → -5 confidence

_LAYER_DEDUCTION = {LAYER_HARD: 0, LAYER_MAJOR: 20, LAYER_MINOR: 5}


@dataclass(frozen=True)
class TypedError:
    """One typed validation failure.

    ``code`` is a stable identifier from :data:`ERROR_REGISTRY`; ``path`` is a
    JSON path inside the validated document; ``entity_type``/``entity_id``
    identify the semantic object (claim, unit, observation, criterion,
    finding, defect); ``expected``/``actual`` carry routing-relevant values.
    """

    code: str
    path: str
    entity_type: str = ""
    entity_id: str = ""
    expected: str = ""
    actual: str = ""
    repairability: str = MODEL_CORRECTION

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(value: dict) -> "TypedError":
        return TypedError(
            code=str(value.get("code", "")),
            path=str(value.get("path", "")),
            entity_type=str(value.get("entity_type", "")),
            entity_id=str(value.get("entity_id", "")),
            expected=str(value.get("expected", "")),
            actual=str(value.get("actual", "")),
            repairability=str(value.get("repairability", MODEL_CORRECTION)),
        )


def _register(codes: dict[str, str]) -> dict[str, str]:
    for code, repairability in codes.items():
        if repairability not in _REPAIRABILITY:
            raise ValueError(
                f"error code {code} binds to unknown repairability {repairability!r}"
            )
    return codes


# Stable error code registry: code -> repairability.
#
# SERVICE_NORMALIZATION: the deterministic normalizer owns the field; the
#   orchestrator fixes it silently and re-validates (no executor call).
# MODEL_CORRECTION: only a model judgment can resolve it; the single generic
#   correction turn receives these errors.
# FATAL_INPUT: the frozen inputs/templates are damaged; the job fails and
#   keeps its artifacts.
ERROR_REGISTRY: dict[str, str] = _register({
    # --- frozen input integrity -------------------------------------------
    "TEMPLATE_MISSING_FIELD": FATAL_INPUT,
    "IDENTITY_MISMATCH": FATAL_INPUT,
    "FROZEN_EVIDENCE_UNREADABLE": FATAL_INPUT,
    "FINDING_ID_MISSING": FATAL_INPUT,
    "FINDING_ID_COLLISION": FATAL_INPUT,
    # --- coverage / mapping -------------------------------------------------
    "CLAIM_SET_MISMATCH": SERVICE_NORMALIZATION,
    "CLAIM_ROW_DUPLICATED": SERVICE_NORMALIZATION,
    "CLAIM_OUTCOME_INVALID": SERVICE_NORMALIZATION,
    "UNIT_ROW_INVALID": SERVICE_NORMALIZATION,
    "UNIT_CLAIM_OUTCOME_CONFLICT": SERVICE_NORMALIZATION,
    "CHECK_COVERAGE_INCOMPLETE": SERVICE_NORMALIZATION,
    "CRITERION_UNKNOWN": MODEL_CORRECTION,
    "OBSERVATION_CLAIM_UNEXPECTED": SERVICE_NORMALIZATION,
    "OBSERVATION_CLAIM_IDS_EMPTY": SERVICE_NORMALIZATION,
    # Attaching a missing expected Claim to an Observation is semantic: the
    # service cannot safely decide which scenario Observation owns it, and the
    # deterministic normalizer can drop extras but never invent coverage. Route
    # it to the bounded model Correction turn, mirroring MAPPING_CLAIM_UNMAPPED.
    "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE": MODEL_CORRECTION,
    "OBSERVATION_FIELD_INVALID": SERVICE_NORMALIZATION,
    "MODELING_BASIS_MISSING": MODEL_CORRECTION,
    "MODELING_BASIS_INVALID": MODEL_CORRECTION,
    # --- evidence semantics (model-owned) ----------------------------------
    "EVIDENCE_DECLARATION_INVALID": MODEL_CORRECTION,
    "EVIDENCE_KEY_DUPLICATED": MODEL_CORRECTION,
    "EVIDENCE_PATH_NOT_ALLOWED": MODEL_CORRECTION,
    "EVIDENCE_PATH_NOT_FOUND": MODEL_CORRECTION,
    "EVIDENCE_KEY_UNKNOWN": MODEL_CORRECTION,
    "EVIDENCE_CARDINALITY_VIOLATED": MODEL_CORRECTION,
    "NV_INSPECTION_EVIDENCE_MISSING": MODEL_CORRECTION,
    "GAP_MISSING_FOR_NV": MODEL_CORRECTION,
    "NV_MISSING_EVIDENCE_RECOVERED": MODEL_CORRECTION,
    "GAP_UNEXPECTED_FOR_NON_NV": SERVICE_NORMALIZATION,
    "GAP_FIELD_INSUFFICIENT": MODEL_CORRECTION,
    # --- prose quality (model-owned) ---------------------------------------
    "REASON_PLACEHOLDER": MODEL_CORRECTION,
    "REASON_LOW_INFORMATION": MODEL_CORRECTION,
    # --- defect identity/mapping (service-owned when unambiguous) ------------
    "DEFECT_KEYS_INVALID": SERVICE_NORMALIZATION,
    "DEFECT_KEY_UNDEFINED": SERVICE_NORMALIZATION,
    # --- aggregation contract (model-owned) ---------------------------------
    "CRITERION_SET_MISMATCH": SERVICE_NORMALIZATION,
    "CRITERION_EVIDENCE_UNKNOWN": MODEL_CORRECTION,
    "FINDING_CARDINALITY_VIOLATED": MODEL_CORRECTION,
    "FINDING_EVIDENCE_UNKNOWN": MODEL_CORRECTION,
    "FINDING_KEY_DUPLICATE": MODEL_CORRECTION,
    "SERVICE_DEFECT_KEY_RESERVED": MODEL_CORRECTION,
    "DUPLICATE_DEFECT_OWNER": MODEL_CORRECTION,
    "FINDING_OWNER_UNKNOWN": SERVICE_NORMALIZATION,
    "FINDING_MULTI_OWNED": SERVICE_NORMALIZATION,
    "CRITICAL_NOT_PRIMARY": SERVICE_NORMALIZATION,
    "OWNERSHIP_CRITICALITY": MODEL_CORRECTION,
    # Claim-to-Criterion ownership is semantic: the service cannot safely
    # decide whether to remove the claim or move it to another Criterion.
    "MAPPING_CLAIM_UNMAPPED": MODEL_CORRECTION,
    "MAPPING_CONCLUSION_FORBIDDEN": MODEL_CORRECTION,
    "MAPPING_NV_REQUIRED": MODEL_CORRECTION,
    "POLICY_BASIS_INVALID": MODEL_CORRECTION,
    "CONTRADICTION_BASIS_INVALID": MODEL_CORRECTION,
    "CROSS_FEAT_NOT_REVIEWED": MODEL_CORRECTION,
    # --- rubric constraint violations (model-owned) -------------------------
    # The validator provides one exact severity floor and identifies the
    # Finding. Raising a lower value to that floor is deterministic and does
    # not require a semantic re-evaluation.
    "SEVERITY_BELOW_FLOOR": SERVICE_NORMALIZATION,
    "NOT_APPLICABLE_FORBIDDEN": MODEL_CORRECTION,
    "EVIDENCE_TYPE_MISSING": MODEL_CORRECTION,
    "EVIDENCE_REQUIRED_MISSING": MODEL_CORRECTION,
    # --- quality gate (degenerate detection, issue #22 successor) -----------
    "QUALITY_HIGH_NV_RATIO": MODEL_CORRECTION,
    "QUALITY_DUPLICATE_TEXT": MODEL_CORRECTION,
    "QUALITY_OBSERVATION_DENSITY": MODEL_CORRECTION,
})


def repairability_of(code: str) -> str:
    """Return the closed repairability classification for a registered code."""
    try:
        return ERROR_REGISTRY[code]
    except KeyError as exc:
        raise ValueError(f"unregistered error code {code!r}") from exc


def blocking(errors: list[TypedError]) -> list[TypedError]:
    """Filter out errors the normalizer can fix without a model call."""
    return [error for error in errors if error.repairability != SERVICE_NORMALIZATION]


# --- Confidence layer registry (0.2.1) ----------------------------------------
#
# HARD:  structure not assemblable — block assembly entirely
# MAJOR: core observation/aggregation invariant violated — high deduction
# MINOR: completeness / consistency — low deduction

CONFIDENCE_LAYERS: dict[str, str] = {
    # HARD: structure damage
    "TEMPLATE_MISSING_FIELD": LAYER_HARD,
    "IDENTITY_MISMATCH": LAYER_HARD,
    "FROZEN_EVIDENCE_UNREADABLE": LAYER_HARD,
    "CRITERION_SET_MISMATCH": LAYER_HARD,
    "FINDING_ID_MISSING": LAYER_HARD,
    # MAJOR: core invariants
    "MAPPING_CONCLUSION_FORBIDDEN": LAYER_MAJOR,
    "MAPPING_NV_REQUIRED": LAYER_MAJOR,
    "POLICY_BASIS_INVALID": LAYER_MAJOR,
    "FINDING_CARDINALITY_VIOLATED": LAYER_MAJOR,
    "FINDING_MULTI_OWNED": LAYER_MAJOR,
    "FINDING_OWNER_UNKNOWN": LAYER_MAJOR,
    "FINDING_EVIDENCE_UNKNOWN": LAYER_MAJOR,
    "FINDING_KEY_DUPLICATE": LAYER_MAJOR,
    "SERVICE_DEFECT_KEY_RESERVED": LAYER_MAJOR,
    "OWNERSHIP_CRITICALITY": LAYER_MAJOR,
    "DEFECT_KEYS_INVALID": LAYER_MAJOR,
    "DEFECT_KEY_UNDEFINED": LAYER_MAJOR,
    "DUPLICATE_DEFECT_OWNER": LAYER_MAJOR,
    "CRITICAL_NOT_PRIMARY": LAYER_MAJOR,
    "CROSS_FEAT_NOT_REVIEWED": LAYER_MAJOR,
    "SEVERITY_BELOW_FLOOR": LAYER_MAJOR,
    "NOT_APPLICABLE_FORBIDDEN": LAYER_MAJOR,
    "EVIDENCE_TYPE_MISSING": LAYER_MAJOR,
    "EVIDENCE_REQUIRED_MISSING": LAYER_MAJOR,
    "MODELING_BASIS_MISSING": LAYER_MAJOR,
    "MODELING_BASIS_INVALID": LAYER_MAJOR,
    # MINOR: completeness / consistency
    "MAPPING_CLAIM_UNMAPPED": LAYER_MINOR,
    "CRITERION_EVIDENCE_UNKNOWN": LAYER_MINOR,
    "CRITERION_UNKNOWN": LAYER_MINOR,
    "CONTRADICTION_BASIS_INVALID": LAYER_MINOR,
    "REASON_PLACEHOLDER": LAYER_MINOR,
    "REASON_LOW_INFORMATION": LAYER_MINOR,
    "FINDING_ID_COLLISION": LAYER_MINOR,
    "QUALITY_HIGH_NV_RATIO": LAYER_MINOR,
    "QUALITY_DUPLICATE_TEXT": LAYER_MINOR,
    "QUALITY_OBSERVATION_DENSITY": LAYER_MINOR,
    "NV_MISSING_EVIDENCE_RECOVERED": LAYER_MINOR,
}


NON_BLOCKING_WARNING_CODES = frozenset({
    # Stable consumer-facing code for the bounded family of ownership-quality
    # warnings.  The kernel emits it when post-Correction fallback ownership
    # is required; assemble-time Critical/primary checks use the same code so
    # confidence deduction remains idempotent at one MAJOR (-20) penalty.
    "OWNERSHIP_CRITICALITY",
    # The aggregation normalizer removes references that are absent from the
    # frozen Criterion evidence catalog and persists a service-warning note.
    # The repaired report remains consumable, but loses one bounded MAJOR
    # confidence penalty so the data-quality issue stays visible.
    "FINDING_EVIDENCE_UNKNOWN",
    # A policy-derived NOT_VERIFIABLE result remains protocol-valid when the
    # service copies the policy-basis reason into missing_evidence. Preserve a
    # bounded confidence deduction so the omitted model field stays visible.
    "NV_MISSING_EVIDENCE_RECOVERED",
})

# These errors still receive the single bounded model Correction turn.  If
# they remain afterwards, the document is structurally consumable and may be
# published with its normal confidence-layer deduction instead of entering
# CORRECTION_INVALID_TERMINAL.
POST_CORRECTION_WARNING_CODES = frozenset({
    "MAPPING_CLAIM_UNMAPPED",
    # A Criterion referencing evidence outside its allowlist is a bounded
    # data-quality gap that the model cannot always repair without semantic
    # re-evaluation. The report remains consumable with reduced confidence.
    "CRITERION_EVIDENCE_UNKNOWN",
    # A Criterion carrying evidence of the wrong type is a bounded data-quality
    # gap the model cannot fabricate without violating the evidence allowlist.
    # The kernel classifies it as a non-blocking MAJOR confidence deduction.
    "EVIDENCE_TYPE_MISSING",
})


def is_non_blocking_warning(error: TypedError) -> bool:
    """Return whether *error* is an accepted report-quality warning."""
    return error.code in NON_BLOCKING_WARNING_CODES


def is_post_correction_warning(error: TypedError) -> bool:
    """Return whether *error* may be downgraded after model Correction."""
    return error.code in POST_CORRECTION_WARNING_CODES


def confidence_layer_of(code: str) -> str:
    """Return the confidence layer for an error code (default MINOR)."""
    return CONFIDENCE_LAYERS.get(code, LAYER_MINOR)


def compute_confidence(errors: list[TypedError]) -> dict[str, Any]:
    """Compute a confidence result from a list of typed validation errors.

    Returns a dict suitable for writing as ``confidence-result.json``.
    """
    hard: list[dict[str, Any]] = []
    major: list[dict[str, Any]] = []
    minor: list[dict[str, Any]] = []
    total_deduction = 0
    bounded_warning_codes: set[str] = set()

    for error in errors:
        if error.repairability == SERVICE_NORMALIZATION:
            continue
        if is_non_blocking_warning(error):
            if error.code in bounded_warning_codes:
                continue
            bounded_warning_codes.add(error.code)
        layer = confidence_layer_of(error.code)
        deduction = _LAYER_DEDUCTION.get(layer, 5)
        entry = {
            "layer": layer,
            "code": error.code,
            "criterion_id": error.entity_id if error.entity_type == "criterion" else "",
            "deduction": deduction,
            "message": f"{error.expected}" if error.expected else error.code,
            "path": error.path,
        }
        if layer == LAYER_HARD:
            hard.append(entry)
        elif layer == LAYER_MAJOR:
            major.append(entry)
            total_deduction += deduction
        else:
            minor.append(entry)
            total_deduction += deduction

    score = max(0, 100 - total_deduction)
    if score >= 80:
        level = "HIGH"
    elif score >= 50:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "confidence_score": score,
        "confidence_level": level,
        "hard_errors": hard,
        "major_violations": major,
        "minor_violations": minor,
        "total_checks_failed": len(hard) + len(major) + len(minor),
        "deduction_total": total_deduction,
    }


def has_hard_errors(errors: list[TypedError]) -> bool:
    """Return True if any error is in the HARD confidence layer."""
    return any(
        confidence_layer_of(e.code) == LAYER_HARD
        for e in errors
        if e.repairability != SERVICE_NORMALIZATION
    )
