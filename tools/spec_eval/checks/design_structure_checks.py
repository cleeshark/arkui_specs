"""Deterministic shared design structure checks."""

from __future__ import annotations

import re

from spec_eval.checks.base import make_finding
from spec_eval.config import EvaluationConfig
from spec_eval.models import DocumentModel, Finding, FunctionContext, Severity


class DesignStructureChecker:
    REQUIRED_H2 = (
        "设计元数据",
        "需求基线",
        "上下文和现状",
        "不涉及项承接",
        "关键设计决策",
        "设计骨架",
        "后续 Task 拆分",
        "API 签名、Kit 与权限",
        "构建系统影响",
        "可选设计扩展",
        "详细设计",
        "风险和开放问题",
        "设计审批",
    )
    BASE_ADR_RE = re.compile(r"^ADR-\d+$")
    FEATURE_ADR_RE = re.compile(r"^ADR-F(\d+)-\d+$")

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> list[Finding]:
        designs = [document for document in documents if document.kind == "design"]
        if not designs:
            return [
                make_finding(
                    self.config,
                    context,
                    "DESIGN-STRUCT-MISSING-001",
                    Severity.MAJOR,
                    "Function has no design.md",
                    context.function_path,
                    1,
                )
            ]
        findings: list[Finding] = []
        document = designs[0]
        h1 = next((heading for heading in document.headings if heading.level == 1), None)
        if h1 is None or h1.title != "架构设计":
            findings.append(self._finding(context, document, "DESIGN-STRUCT-H1-001", "design H1 must be `架构设计`", 1))
        h2 = document.h2_titles()
        for title in self.REQUIRED_H2:
            if title not in h2:
                findings.append(self._finding(context, document, "DESIGN-STRUCT-H2-MISSING-001", f"missing design section `{title}`", 1, section=title))
        present = [title for title in h2 if title in self.REQUIRED_H2]
        expected = [title for title in self.REQUIRED_H2 if title in h2]
        if present != expected:
            findings.append(self._finding(context, document, "DESIGN-STRUCT-H2-ORDER-001", "design sections are not in the standard order", 1))
        for heading in document.headings:
            if heading.level == 2 and heading.title.startswith("Feat-"):
                findings.append(
                    self._finding(
                        context,
                        document,
                        "DESIGN-STRUCT-FEAT-H2-001",
                        "Feature content must be merged into shared design sections, not a standalone H2",
                        heading.line,
                    )
                )

        metadata = document.metadata()
        expected_id = f"DESIGN-Func-{context.func_id}"
        actual_id = metadata.get("Design ID", "")
        if actual_id != expected_id:
            if actual_id.strip("`") == expected_id:
                findings.append(
                    self._finding(
                        context,
                        document,
                        "DESIGN-STRUCT-ID-001",
                        f"Design ID has a formatting error: use plain text `{expected_id}` without Markdown backticks",
                        1,
                        actual_id=actual_id,
                        expected_id=expected_id,
                        formatting_issue="markdown_inline_code",
                    )
                )
            else:
                findings.append(
                    self._finding(
                        context,
                        document,
                        "DESIGN-STRUCT-ID-001",
                        f"Design ID must be `{expected_id}`",
                        1,
                        actual_id=actual_id,
                        expected_id=expected_id,
                    )
                )
        targets = metadata.get("目标 Feature", "")
        for feat_id in context.feature_ids():
            if feat_id not in targets:
                findings.append(
                    self._finding(
                        context,
                        document,
                        "DESIGN-STRUCT-TARGET-FEAT-001",
                        f"design metadata does not include `{feat_id}`",
                        1,
                        feat_id=feat_id,
                    )
                )

        adr_tables = [table for table in document.tables if "决策 ID" in table.headers]
        for table in adr_tables:
            for row in table.rows:
                adr = row.as_mapping(table.headers).get("决策 ID", "").strip(" `")
                if not adr:
                    continue
                if self.BASE_ADR_RE.fullmatch(adr):
                    continue
                match = self.FEATURE_ADR_RE.fullmatch(adr)
                if not match:
                    findings.append(self._finding(context, document, "DESIGN-STRUCT-ADR-ID-001", f"invalid ADR ID `{adr}`", row.line))
                    continue
                feat_id = f"Feat-{int(match.group(1)):02d}"
                if feat_id not in context.feature_ids():
                    findings.append(
                        self._finding(
                            context,
                            document,
                            "DESIGN-STRUCT-ADR-FEAT-001",
                            f"ADR `{adr}` references unregistered `{feat_id}`",
                            row.line,
                            feat_id=feat_id,
                        )
                    )
        return findings

    def _finding(self, context: FunctionContext, document: DocumentModel, rule: str, message: str, line: int, **details) -> Finding:
        feat_id = details.pop("feat_id", None)
        return make_finding(
            self.config,
            context,
            rule,
            Severity.MAJOR,
            message,
            document.path,
            line,
            feat_id=feat_id,
            **details,
        )
