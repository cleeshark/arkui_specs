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
    "FINDING_ID_COLLISION": FATAL_INPUT,
    "DUPLICATE_DEFECT_OWNER": FATAL_INPUT,
    # --- coverage / mapping (model-owned) ----------------------------------
    "CLAIM_SET_MISMATCH": MODEL_CORRECTION,
    "CLAIM_ROW_DUPLICATED": MODEL_CORRECTION,
    "CLAIM_OUTCOME_INVALID": MODEL_CORRECTION,
    "UNIT_ROW_INVALID": MODEL_CORRECTION,
    "UNIT_CLAIM_OUTCOME_CONFLICT": MODEL_CORRECTION,
    "CHECK_COVERAGE_INCOMPLETE": MODEL_CORRECTION,
    "CRITERION_UNKNOWN": MODEL_CORRECTION,
    "OBSERVATION_CLAIM_UNEXPECTED": MODEL_CORRECTION,
    "OBSERVATION_CLAIM_IDS_EMPTY": MODEL_CORRECTION,
    "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE": MODEL_CORRECTION,
    "OBSERVATION_FIELD_INVALID": MODEL_CORRECTION,
    # --- evidence semantics (model-owned) ----------------------------------
    "EVIDENCE_DECLARATION_INVALID": MODEL_CORRECTION,
    "EVIDENCE_KEY_DUPLICATED": MODEL_CORRECTION,
    "EVIDENCE_PATH_NOT_ALLOWED": MODEL_CORRECTION,
    "EVIDENCE_PATH_NOT_FOUND": MODEL_CORRECTION,
    "EVIDENCE_KEY_UNKNOWN": MODEL_CORRECTION,
    "EVIDENCE_CARDINALITY_VIOLATED": MODEL_CORRECTION,
    "NV_INSPECTION_EVIDENCE_MISSING": MODEL_CORRECTION,
    "GAP_MISSING_FOR_NV": MODEL_CORRECTION,
    "GAP_UNEXPECTED_FOR_NON_NV": SERVICE_NORMALIZATION,
    "GAP_FIELD_INSUFFICIENT": MODEL_CORRECTION,
    # --- prose quality (model-owned) ---------------------------------------
    "REASON_PLACEHOLDER": MODEL_CORRECTION,
    "REASON_LOW_INFORMATION": MODEL_CORRECTION,
    # --- defect semantics (model-owned) -------------------------------------
    "DEFECT_KEYS_INVALID": MODEL_CORRECTION,
    "DEFECT_KEY_UNDEFINED": MODEL_CORRECTION,
    # --- aggregation contract (model-owned) ---------------------------------
    "CRITERION_SET_MISMATCH": MODEL_CORRECTION,
    "CRITERION_EVIDENCE_UNKNOWN": MODEL_CORRECTION,
    "FINDING_CARDINALITY_VIOLATED": MODEL_CORRECTION,
    "FINDING_EVIDENCE_UNKNOWN": MODEL_CORRECTION,
    "FINDING_OWNER_UNKNOWN": MODEL_CORRECTION,
    "FINDING_MULTI_OWNED": MODEL_CORRECTION,
    "CRITICAL_NOT_PRIMARY": MODEL_CORRECTION,
    "MAPPING_CLAIM_UNMAPPED": MODEL_CORRECTION,
    "MAPPING_CONCLUSION_FORBIDDEN": MODEL_CORRECTION,
    "MAPPING_NV_REQUIRED": MODEL_CORRECTION,
    "POLICY_BASIS_INVALID": MODEL_CORRECTION,
    "CONTRADICTION_BASIS_INVALID": MODEL_CORRECTION,
    "CROSS_FEAT_NOT_REVIEWED": MODEL_CORRECTION,
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
    # MAJOR: core invariants
    "MAPPING_CONCLUSION_FORBIDDEN": LAYER_MAJOR,
    "MAPPING_NV_REQUIRED": LAYER_MAJOR,
    "POLICY_BASIS_INVALID": LAYER_MAJOR,
    "FINDING_CARDINALITY_VIOLATED": LAYER_MAJOR,
    "FINDING_MULTI_OWNED": LAYER_MAJOR,
    "FINDING_OWNER_UNKNOWN": LAYER_MAJOR,
    "FINDING_EVIDENCE_UNKNOWN": LAYER_MAJOR,
    "DEFECT_KEYS_INVALID": LAYER_MAJOR,
    "DEFECT_KEY_UNDEFINED": LAYER_MAJOR,
    "DUPLICATE_DEFECT_OWNER": LAYER_MAJOR,
    "CRITICAL_NOT_PRIMARY": LAYER_MAJOR,
    "CROSS_FEAT_NOT_REVIEWED": LAYER_MAJOR,
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
}


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

    for error in errors:
        if error.repairability == SERVICE_NORMALIZATION:
            continue
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
