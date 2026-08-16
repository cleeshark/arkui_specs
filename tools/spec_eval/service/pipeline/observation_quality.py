"""Deterministic detection of degenerate staged observation output.

The gate intentionally combines several independent signals. A high
NOT_VERIFIABLE ratio alone is legitimate when frozen inputs are genuinely
incomplete; it becomes suspicious only when inspection evidence collapses and
the review also exhibits a second quality failure such as repeated prose or no
decisive outcome at all.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


MIN_CLAIMS = 10
HIGH_NV_RATIO = 0.60
EVIDENCE_COLLAPSE_RATIO = 0.80
MIN_INSPECTION_COVERAGE = 0.20
REPETITIVE_TEXT_RATIO = 0.50


@dataclass(frozen=True)
class ObservationQualityAssessment:
    suspected: bool
    reason_codes: tuple[str, ...]
    metrics: dict[str, int | float]

    def payload(self) -> dict[str, Any]:
        return {
            "suspected": self.suspected,
            "reason_codes": list(self.reason_codes),
            "metrics": dict(self.metrics),
        }


def assess_observation_quality(payload: dict[str, Any] | None) -> ObservationQualityAssessment:
    claims = _dict_rows(payload, "claim_reviews")
    observations = _dict_rows(payload, "observations")
    nv_claims = [row for row in claims if row.get("local_outcome") == "NOT_VERIFIABLE"]
    nv_units = [
        unit
        for claim in nv_claims
        for unit in _dict_rows(claim, "unit_reviews")
        if unit.get("local_outcome") == "NOT_VERIFIABLE"
    ]

    inspection_ids = {
        evidence.get("evidence_id")
        for observation in observations
        for evidence in _dict_rows(observation, "evidence")
        if evidence.get("type") == "review_record"
        and isinstance(evidence.get("evidence_id"), str)
    }
    empty_nv_claims = sum(not _string_list(row.get("evidence_ids")) for row in nv_claims)
    empty_nv_units = sum(not _string_list(row.get("evidence_ids")) for row in nv_units)
    inspected_nv_claims = sum(
        bool(set(_string_list(row.get("evidence_ids"))) & inspection_ids)
        for row in nv_claims
    )
    decisive_outcomes = sum(
        row.get("local_outcome") in {"SUPPORTED", "CONFLICT"}
        for row in claims
    )

    review_texts = [
        text
        for text in (
            *[row.get("reason") for row in nv_claims],
            *[row.get("fact") for row in nv_units],
        )
        if isinstance(text, str) and text.strip()
    ]
    repeated_ratio = _max_repetition_ratio(review_texts)
    claim_count = len(claims)
    nv_claim_count = len(nv_claims)
    nv_unit_count = len(nv_units)
    nv_ratio = _ratio(nv_claim_count, claim_count)
    empty_claim_ratio = _ratio(empty_nv_claims, nv_claim_count)
    empty_unit_ratio = _ratio(empty_nv_units, nv_unit_count)
    inspection_coverage = _ratio(inspected_nv_claims, nv_claim_count)
    low_observation_density = len(observations) <= max(5, claim_count // 10)

    conditions = {
        "HIGH_NOT_VERIFIABLE_RATIO": claim_count >= MIN_CLAIMS and nv_ratio >= HIGH_NV_RATIO,
        "EMPTY_NV_EVIDENCE": (
            empty_claim_ratio >= EVIDENCE_COLLAPSE_RATIO
            or (nv_unit_count > 0 and empty_unit_ratio >= EVIDENCE_COLLAPSE_RATIO)
        ),
        "MISSING_INSPECTION_EVIDENCE": (
            nv_claim_count > 0 and inspection_coverage < MIN_INSPECTION_COVERAGE
        ),
        "REPETITIVE_REVIEW_TEXT": repeated_ratio >= REPETITIVE_TEXT_RATIO,
        "NO_DECISIVE_OUTCOMES": claim_count > 0 and decisive_outcomes == 0,
        "LOW_OBSERVATION_DENSITY": claim_count >= MIN_CLAIMS and low_observation_density,
    }
    evidence_collapse = conditions["EMPTY_NV_EVIDENCE"] or conditions[
        "MISSING_INSPECTION_EVIDENCE"
    ]
    corroborating = any(
        conditions[code]
        for code in (
            "REPETITIVE_REVIEW_TEXT",
            "NO_DECISIVE_OUTCOMES",
            "LOW_OBSERVATION_DENSITY",
        )
    )
    suspected = conditions["HIGH_NOT_VERIFIABLE_RATIO"] and evidence_collapse and corroborating
    reason_codes = tuple(code for code, matched in conditions.items() if matched)
    metrics: dict[str, int | float] = {
        "claim_count": claim_count,
        "not_verifiable_claim_count": nv_claim_count,
        "not_verifiable_claim_ratio": round(nv_ratio, 4),
        "empty_nv_claim_evidence_ratio": round(empty_claim_ratio, 4),
        "not_verifiable_unit_count": nv_unit_count,
        "empty_nv_unit_evidence_ratio": round(empty_unit_ratio, 4),
        "nv_inspection_coverage_ratio": round(inspection_coverage, 4),
        "repeated_review_text_ratio": round(repeated_ratio, 4),
        "decisive_outcome_count": decisive_outcomes,
        "observation_count": len(observations),
    }
    return ObservationQualityAssessment(suspected, reason_codes, metrics)


def _dict_rows(value: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get(key), list):
        return []
    return [row for row in value[key] if isinstance(row, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _max_repetition_ratio(values: list[str]) -> float:
    normalized = [
        re.sub(r"[\W_]+", "", value, flags=re.UNICODE).casefold()
        for value in values
    ]
    normalized = [value for value in normalized if value]
    if not normalized:
        return 0.0
    return max(Counter(normalized).values()) / len(normalized)
