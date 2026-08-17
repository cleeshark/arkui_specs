"""Typed validation errors for evaluator protocol 0.2.0.

Errors are data, not prose: every failure carries a stable code, a JSON path,
the entity it belongs to and a closed ``repairability`` classification. The
orchestrator routes on ``repairability`` only and never matches validator
message text.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

# Closed repairability classification. New error codes must bind to one of
# these three values at registration time.
SERVICE_NORMALIZATION = "SERVICE_NORMALIZATION"
MODEL_CORRECTION = "MODEL_CORRECTION"
FATAL_INPUT = "FATAL_INPUT"

_REPAIRABILITY = (SERVICE_NORMALIZATION, MODEL_CORRECTION, FATAL_INPUT)


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
