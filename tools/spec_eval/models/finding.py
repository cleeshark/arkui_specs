"""Finding and severity models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any


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

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["severity"] = self.severity.label()
        return {key: value for key, value in result.items() if value not in (None, {}, [])}

