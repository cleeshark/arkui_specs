"""Shared helpers for deterministic checks."""

from __future__ import annotations

from pathlib import Path

from spec_eval.config import EvaluationConfig
from spec_eval.models import DocumentModel, Finding, FunctionContext, Severity


def document_map(documents: list[DocumentModel]) -> dict[Path, DocumentModel]:
    return {document.path.resolve(): document for document in documents}


def registry_line(path: Path, needle: str) -> int | None:
    if not path.is_file():
        return None
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if needle in line:
            return line_no
    return None


def make_finding(
    config: EvaluationConfig,
    context: FunctionContext,
    rule_id: str,
    severity: Severity,
    message: str,
    path: Path,
    line: int | None = None,
    feat_id: str | None = None,
    recommendation: str | None = None,
    **details: object,
) -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=severity,
        message=message,
        path=config.repo_relative(path),
        line=line,
        func_id=context.func_id,
        feat_id=feat_id,
        recommendation=recommendation,
        details=details,
    )


def status_of(document: DocumentModel) -> str:
    return document.metadata().get("状态", "").strip()

