"""Finding and severity models."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from pathlib import PurePosixPath
from typing import Any


FINDING_IDENTITY_VERSION = 1

_STABLE_DETAIL_FIELDS = (
    "node_id",
    "section",
    "expected_path",
    "expected_id",
    "source_path",
    "raw",
    "api",
    "raw_api",
    "user_story",
    "target",
    "checkbox_text",
    "placeholder",
    "mermaid_header",
)
_LINE_SUFFIX_RE = re.compile(r"(?::|#L)(?:L)?\d+(?:[-:]\d+)?(?=$|[\s),;])")
_LINE_WORD_RE = re.compile(r"(?i)\b(?:lines?|line number)\s*[:=#]?\s*\d+(?:[-:]\d+)?")
_COUNT_RE = re.compile(
    r"(?i)\b(?:count|total|candidate count|candidates found)\s*[:=]?\s*\d+\b"
    r"|(?:共|数量(?:为|[:：])?|候选(?:数|数量)?[:：]?)\s*\d+\s*(?:个|条|项|处)?"
)
_USER_STORY_ID_RE = re.compile(r"\bUS-\d+(?:\.\d+)?\b", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


class Severity(IntEnum):
    INFO = 0
    MINOR = 1
    MAJOR = 2
    CRITICAL = 3

    @classmethod
    def from_text(cls, value: str) -> "Severity":
        normalized = value.strip().upper()
        aliases = {"WARN": "MINOR", "WARNING": "MINOR", "ERROR": "MAJOR"}
        return cls[aliases.get(normalized, normalized)]

    def label(self) -> str:
        return self.name.title()


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: str
    line: int | None = None
    func_id: str | None = None
    feat_id: str | None = None
    claim_id: str | None = None
    recommendation: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def problem_key(self) -> str:
        return finding_problem_key(
            self.rule_id,
            self.message,
            self.details,
        )

    @property
    def finding_id(self) -> str:
        return build_finding_id(
            rule_id=self.rule_id,
            func_id=self.func_id,
            feat_id=self.feat_id,
            claim_id=self.claim_id,
            path=self.path,
            problem_key=self.problem_key,
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["severity"] = self.severity.label()
        result["identity_version"] = FINDING_IDENTITY_VERSION
        result["problem_key"] = self.problem_key
        result["finding_id"] = self.finding_id
        return {key: value for key, value in result.items() if value not in (None, {}, [])}


def normalize_finding_path(value: str | None) -> str:
    """Normalize separators and harmless relative prefixes without resolving the path."""

    text = str(value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return PurePosixPath(text).as_posix() if text else ""


def normalize_finding_message(value: str | None) -> str:
    """Normalize presentation-only differences used by delta classification."""

    text = _WHITESPACE_RE.sub(" ", str(value or "").strip())
    text = _LINE_SUFFIX_RE.sub(":<line>", text)
    text = _LINE_WORD_RE.sub("line <line>", text)
    return _COUNT_RE.sub("<count>", text)


def finding_problem_key(rule_id: str, message: str, details: dict[str, Any] | None = None) -> str:
    """Return a semantic problem key that is stable across document line movement."""

    values = details if isinstance(details, dict) else {}
    stable: dict[str, Any] = {}
    for name in _STABLE_DETAIL_FIELDS:
        value = values.get(name)
        if value in (None, "", [], {}):
            continue
        if name in {"source_path", "raw", "expected_path"}:
            value = _LINE_SUFFIX_RE.sub(":<line>", normalize_finding_path(str(value)))
        if name == "user_story":
            match = _USER_STORY_ID_RE.search(str(value))
            value = match.group(0).upper() if match else value
        stable[name] = _normalize_identity_value(value)

    if rule_id in {"HYGIENE-ABSOLUTE-PATH-001", "REF-ABSOLUTE-PATH-001"}:
        stable = {"kind": "absolute-path"}

    # Table field defects belong to the table itself. Header changes are a
    # reclassification of that defect, not a resolved+added pair.
    if rule_id == "SPEC-STRUCT-TABLE-FIELD-001" and "section" in stable:
        stable = {"section": stable["section"]}

    if stable:
        return json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return normalize_finding_message(message)


def build_finding_id(
    *,
    rule_id: str,
    func_id: str | None,
    feat_id: str | None,
    claim_id: str | None,
    path: str | None,
    problem_key: str,
) -> str:
    identity = {
        "identity_version": FINDING_IDENTITY_VERSION,
        "rule_id": str(rule_id),
        "func_id": str(func_id or ""),
        "feat_id": str(feat_id or ""),
        "claim_id": str(claim_id or ""),
        "path": normalize_finding_path(path),
        "problem_key": problem_key,
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"FND-{hashlib.sha256(encoded).hexdigest()[:24]}"


def enrich_finding_identity(value: dict[str, Any], *, default_func_id: str | None = None) -> dict[str, Any]:
    """Add current identity fields to findings from older result archives."""

    result = dict(value)
    details = result.get("details") if isinstance(result.get("details"), dict) else {}
    problem_key = finding_problem_key(str(result.get("rule_id", "UNKNOWN")), str(result.get("message", "")), details)
    result["identity_version"] = FINDING_IDENTITY_VERSION
    result["problem_key"] = problem_key
    result["finding_id"] = build_finding_id(
        rule_id=str(result.get("rule_id", "UNKNOWN")),
        func_id=str(result.get("func_id") or default_func_id or ""),
        feat_id=str(result.get("feat_id") or ""),
        claim_id=str(result.get("claim_id") or ""),
        path=str(result.get("path") or ""),
        problem_key=problem_key,
    )
    return result


def _normalize_identity_value(value: Any) -> Any:
    if isinstance(value, str):
        return _WHITESPACE_RE.sub(" ", value.strip())
    if isinstance(value, dict):
        return {str(key): _normalize_identity_value(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [_normalize_identity_value(item) for item in value]
    return value
