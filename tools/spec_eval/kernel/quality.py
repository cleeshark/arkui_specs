"""Semantic-quality predicates for evaluator protocol 0.2.0.

Keep the service-side predicate independent of the orchestrator so typed
validation can be exercised directly and reused by future staged validators.
"""

from __future__ import annotations

import re


_CHECKED_PATTERNS = (
    re.compile(
        r"\b(?:check(?:ed|ing)?|inspect(?:ed|ing|ion)?|review(?:ed|ing)?|"
        r"examin(?:e|ed|ing|ation)|search(?:ed|ing)?|scan(?:ned|ning)?)\b"
    ),
)
_MISSING_PATTERNS = (
    re.compile(r"\b(?:missing|absent|absence|unavailable|insufficient|lacks?|lacking)\b"),
    re.compile(r"\bnot\s+(?:present|found|available|included)\b"),
    re.compile(r"\bwithout(?:\s+the)?\b"),
    re.compile(r"\b(?:does|do|did)\s+not\s+(?:include|contain|provide|cover)\b"),
    re.compile(
        r"\bno\b[^.;:\n]{0,120}\b(?:evidence|proof|source|content|implementation|"
        r"record|test|coverage|artifact|file|path|data)\b"
    ),
)
_CONSEQUENCE_PATTERNS = (
    re.compile(
        r"\b(?:cannot|can\s+not|unable\s+to)\s+(?:\w+\s+){0,3}"
        r"verif(?:y|ied|iable)\b"
    ),
    re.compile(r"\bnot\s+verifiable\b"),
    re.compile(
        r"\b(?:cannot|can\s+not|unable\s+to)\s+(?:\w+\s+){0,3}"
        r"determin(?:e|ed)\b"
    ),
    re.compile(
        r"\bprevent(?:s|ed|ing)?\s+(?:\w+\s+){0,3}"
        r"(?:verif(?:y|ying|ication)|determin(?:e|ing|ation))\b"
    ),
    re.compile(r"\binsufficient\s+to\b"),
)


def _matches_any(value: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(value) is not None for pattern in patterns)


def has_unverifiable_gap_explanation(value: object) -> bool:
    """Return whether NV prose names scope, evidence gap, and consequence.

    The predicate intentionally mirrors the staged protocol's three-signal
    rule and accepts both English expression families and the documented
    Chinese terms.
    """
    if not isinstance(value, str) or len(value.strip()) < 24:
        return False
    normalized = re.sub(r"\s+", " ", value.casefold())
    checked = _matches_any(normalized, _CHECKED_PATTERNS) or any(
        term in normalized for term in ("检查", "审查")
    )
    missing = _matches_any(normalized, _MISSING_PATTERNS) or any(
        term in normalized for term in ("缺少", "缺失", "不足", "不可用")
    )
    consequence = _matches_any(normalized, _CONSEQUENCE_PATTERNS) or any(
        term in normalized for term in ("无法验证", "不能验证", "不足以", "无法判断")
    )
    return checked and missing and consequence
