"""Resolve source citations and validate paths and line ranges."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from spec_eval.checks.base import make_finding
from spec_eval.config import EvaluationConfig
from spec_eval.evidence.source_reader import SourceReader
from spec_eval.models.evidence import Citation
from spec_eval.models.document import DocumentModel
from spec_eval.models.finding import Finding, Severity
from spec_eval.models.function import FunctionContext
from spec_eval.parser.citation_parser import CitationParser


@dataclass
class ReferenceResult:
    findings: list[Finding]
    citations: list[Citation]
    by_location: dict[tuple[str, int], list[Citation]] = field(default_factory=dict)

    def citations_at(self, path: str, line: int) -> list[Citation]:
        return list(self.by_location.get((path, line), []))


class ReferenceChecker:
    def __init__(self, config: EvaluationConfig, reader: SourceReader | None = None) -> None:
        self.config = config
        self.parser = CitationParser()
        self.reader = reader or SourceReader(config)

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> ReferenceResult:
        findings: list[Finding] = []
        citations: list[Citation] = []
        by_location: dict[tuple[str, int], list[Citation]] = {}
        for document in documents:
            mermaid_lines = {
                line_no
                for block in document.code_blocks
                if block.language.lower() == "mermaid"
                for line_no in range(block.start_line, block.end_line + 1)
            }
            for line_no, line in enumerate(document.lines, 1):
                if line_no in mermaid_lines:
                    continue
                for citation in self.parser.parse(line, line_no):
                    resolved_path, resolution = self.reader.resolve(citation.path, document.path.parent)
                    if resolution == "absolute":
                        findings.append(
                            self._finding(
                                context,
                                document,
                                "REF-ABSOLUTE-PATH-001",
                                Severity.MAJOR,
                                "absolute personal paths cannot be used as reproducible evidence",
                                line_no,
                                raw=citation.raw,
                            )
                        )
                        resolved = citation
                    elif resolved_path is None:
                        if resolution == "ambiguous":
                            rule = "REF-AMBIGUOUS-001"
                            if self.reader.is_sdk_declaration_basename(citation.path):
                                message = (
                                    f"source citation is ambiguous: `{citation.path}`; use the complete "
                                    f"repository-relative path, for example `interface/sdk-js/.../{citation.path}` "
                                    f"for an SDK declaration or `frameworks/.../{citation.path}` for an "
                                    f"ace_engine source"
                                )
                                resolution_details = {
                                    "required_path_style": "complete repository-relative path",
                                    "searched_roots": ["ace_engine", "interface/sdk-js"],
                                }
                            else:
                                message = (
                                    f"source citation is ambiguous: `{citation.path}`; use the complete "
                                    f"repository-relative path from the ace_engine root, for example "
                                    f"`frameworks/.../{citation.path}`"
                                )
                                resolution_details = {
                                    "required_path_style": "complete repository-relative path from ace_engine root"
                                }
                        else:
                            rule = "REF-NOT-FOUND-001"
                            message = f"source citation cannot be resolved: `{citation.path}`"
                            resolution_details = {}
                        findings.append(
                            self._finding(
                                context,
                                document,
                                rule,
                                Severity.MAJOR,
                                message,
                                line_no,
                                raw=citation.raw,
                                **resolution_details,
                            )
                        )
                        resolved = citation
                    elif resolution == "directory":
                        resolved = replace(
                            citation,
                            source_path=self.config.repo_relative(resolved_path),
                            resolved=True,
                        )
                    else:
                        content, content_hash, invalid = self.reader.read_ranges(resolved_path, citation.line_ranges)
                        if invalid:
                            findings.append(
                                self._finding(
                                    context,
                                    document,
                                    "REF-LINE-RANGE-001",
                                    Severity.MAJOR,
                                    "source citation line range is outside the file",
                                    line_no,
                                    source_path=self.config.repo_relative(resolved_path),
                                    invalid_ranges=[list(item) for item in invalid],
                                )
                            )
                        if self.reader.is_disallowed(resolved_path):
                            findings.append(
                                self._finding(
                                    context,
                                    document,
                                    "REF-DISALLOWED-SOURCE-001",
                                    Severity.MAJOR,
                                    "generated/site copies cannot be used as authoritative evidence",
                                    line_no,
                                    source_path=self.config.repo_relative(resolved_path),
                                )
                            )
                        resolved = replace(
                            citation,
                            source_path=self.config.repo_relative(resolved_path),
                            content=content,
                            content_hash=content_hash,
                            resolved=not invalid,
                        )
                    citations.append(resolved)
                    by_location.setdefault((document.relative_path, line_no), []).append(resolved)
        return ReferenceResult(findings, citations, by_location)

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
