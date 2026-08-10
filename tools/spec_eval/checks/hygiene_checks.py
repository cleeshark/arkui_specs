"""Document hygiene, portability, links and basic diagram checks."""

from __future__ import annotations

import re
from pathlib import Path

from spec_eval.checks.base import make_finding, status_of
from spec_eval.config import EvaluationConfig
from spec_eval.models.document import DocumentModel
from spec_eval.models.finding import Finding, Severity
from spec_eval.models.function import FunctionContext


class HygieneChecker:
    PLACEHOLDER_RE = re.compile(r"TODO|TBD|待定|待补充", re.IGNORECASE)
    ABSOLUTE_PATH_RE = re.compile(r"(?:/home/[^\s`|，。、)]+|[A-Za-z]:\\\\Users\\\\[^\s`|，。、)]+|file://[^\s)]+)")
    ASCII_DIAGRAM_RE = re.compile(r"[+┌┐└┘├┤┬┴┼][-─]{2,}[+┌┐└┘├┤┬┴┼]")

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> list[Finding]:
        findings: list[Finding] = []
        for document in documents:
            status = status_of(document)
            for line_no, line in enumerate(document.lines, 1):
                if status.startswith("Baselined") and self.PLACEHOLDER_RE.search(line) and not self._placeholder_audit(line):
                    findings.append(
                        self._finding(context, document, "HYGIENE-PLACEHOLDER-001", Severity.MAJOR, "Baselined document contains placeholder text", line_no)
                    )
                for match in self.ABSOLUTE_PATH_RE.finditer(line):
                    findings.append(
                        self._finding(
                            context,
                            document,
                            "HYGIENE-ABSOLUTE-PATH-001",
                            Severity.MINOR,
                            "document contains a non-portable absolute path",
                            line_no,
                            raw=match.group(0),
                        )
                    )
                if self.ASCII_DIAGRAM_RE.search(line):
                    findings.append(
                        self._finding(context, document, "DIAGRAM-ASCII-001", Severity.MINOR, "use Mermaid instead of ASCII box diagrams", line_no)
                    )
            if status.startswith("Baselined"):
                for checkbox in document.checkboxes:
                    if not checkbox.checked:
                        findings.append(
                            self._finding(
                                context,
                                document,
                                "HYGIENE-UNCHECKED-AUDIT-001",
                                Severity.MINOR,
                                "Baselined document contains an unchecked audit item",
                                checkbox.line,
                            )
                        )
            findings.extend(self._check_links(context, document))
            findings.extend(self._check_mermaid(context, document))
        return findings

    def _check_links(self, context: FunctionContext, document: DocumentModel) -> list[Finding]:
        findings: list[Finding] = []
        for link in document.links:
            target = link.target.strip()
            if not target or target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            candidates = self._link_candidates(document, target_path)
            if not any(candidate.exists() for candidate in candidates):
                findings.append(
                    self._finding(
                        context,
                        document,
                        "LINK-DEAD-001",
                        Severity.MINOR,
                        f"Markdown link target does not exist: `{target}`",
                        link.line,
                    )
                )
        return findings

    def _link_candidates(self, document: DocumentModel, target_path: str) -> list[Path]:
        """Return supported filesystem interpretations for a local Markdown link."""
        target = Path(target_path)
        if target.is_absolute():
            return [target]

        return [
            document.path.parent / target,
            self.config.specs_root / target,
            self.config.repo_root / target,
        ]

    def _check_mermaid(self, context: FunctionContext, document: DocumentModel) -> list[Finding]:
        findings: list[Finding] = []
        allowed_starts = ("graph ", "flowchart ", "sequenceDiagram", "stateDiagram", "classDiagram", "erDiagram", "journey", "gantt", "pie")
        for block in document.code_blocks:
            if block.language.lower() != "mermaid":
                continue
            first = next((line.strip() for line in block.content.splitlines() if line.strip()), "")
            if not first.startswith(allowed_starts):
                findings.append(
                    self._finding(
                        context,
                        document,
                        "DIAGRAM-MERMAID-HEADER-001",
                        Severity.MINOR,
                        "Mermaid block does not start with a supported diagram directive",
                        block.start_line,
                    )
                )
        return findings

    def _finding(
        self,
        context: FunctionContext,
        document: DocumentModel,
        rule: str,
        severity: Severity,
        message: str,
        line: int,
        **details,
    ) -> Finding:
        return make_finding(
            self.config,
            context,
            rule,
            severity,
            message,
            document.path,
            line,
            feat_id=document.feat_id,
            **details,
        )

    @staticmethod
    def _placeholder_audit(line: str) -> bool:
        return ("无" in line and "占位" in line) or "不允许存在" in line or "placeholder" in line.lower()
