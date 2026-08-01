"""Citation, claim and evidence models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Citation:
    raw: str
    path: str
    line_ranges: tuple[tuple[int, int], ...]
    source_path: str | None = None
    content: str | None = None
    content_hash: str | None = None
    resolved: bool = False
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["line_ranges"] = [list(item) for item in self.line_ranges]
        return {key: value for key, value in result.items() if value not in (None, "", [], ())}


@dataclass
class Claim:
    claim_id: str
    claim_type: str
    text: str
    path: str
    line: int
    feat_id: str | None = None
    citations: list[Citation] = field(default_factory=list)
    sdk_declarations: list[dict[str, Any]] = field(default_factory=list)
    static_finding_ids: list[str] = field(default_factory=list)
    evidence_status: str = "NO_EVIDENCE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_type": self.claim_type,
            "text": self.text,
            "path": self.path,
            "line": self.line,
            "feat_id": self.feat_id,
            "citations": [item.to_dict() for item in self.citations],
            "sdk_declarations": self.sdk_declarations,
            "static_finding_ids": self.static_finding_ids,
            "evidence_status": self.evidence_status,
        }


@dataclass
class EvidenceBundle:
    func_id: str
    source_revision: str
    claims: list[Claim]
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "func_id": self.func_id,
            "source_revision": self.source_revision,
            "claims": [claim.to_dict() for claim in self.claims],
            "metrics": self.metrics,
        }

