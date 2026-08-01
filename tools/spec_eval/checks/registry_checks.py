"""Function Registry and disk consistency checks."""

from __future__ import annotations

import re
from pathlib import Path

from spec_eval.checks.base import document_map, make_finding, registry_line
from spec_eval.config import EvaluationConfig
from spec_eval.models import DocumentModel, Finding, FunctionContext, Severity


class RegistryChecker:
    FUNC_ID_RE = re.compile(r"^\d{2}-\d{2}-\d{2}$")
    FEAT_ID_RE = re.compile(r"^Feat-(\d{2})$")

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> list[Finding]:
        findings: list[Finding] = []
        docs = document_map(documents)
        function_line = registry_line(self.config.functions_registry, f"id: {context.func_id}")
        if not self.FUNC_ID_RE.fullmatch(context.func_id):
            findings.append(
                make_finding(
                    self.config,
                    context,
                    "REG-FUNC-ID-001",
                    Severity.MAJOR,
                    f"invalid FuncID `{context.func_id}`",
                    self.config.functions_registry,
                    function_line,
                )
            )
        if not context.function_path.is_dir():
            findings.append(
                make_finding(
                    self.config,
                    context,
                    "REG-FUNC-PATH-001",
                    Severity.MAJOR,
                    "registered Function directory does not exist",
                    self.config.functions_registry,
                    function_line,
                    expected_path=self.config.repo_relative(context.function_path),
                )
            )

        registered_design = context.function_registry_entry.get("design")
        disk_design = context.function_path / "design.md"
        if registered_design and not (self.config.specs_root / str(registered_design)).is_file():
            findings.append(
                make_finding(
                    self.config,
                    context,
                    "REG-DESIGN-MISSING-001",
                    Severity.MAJOR,
                    "registered design file does not exist",
                    self.config.functions_registry,
                    function_line,
                    expected_path=str(registered_design),
                )
            )
        if disk_design.is_file() and not registered_design:
            findings.append(
                make_finding(
                    self.config,
                    context,
                    "REG-DESIGN-UNREGISTERED-001",
                    Severity.MAJOR,
                    "design.md exists on disk but is not registered",
                    disk_design,
                    1,
                )
            )

        registered_by_id = {str(entry.get("id")): entry for entry in context.feature_registry_entries}
        disk_by_id: dict[str, Path] = {}
        for path in context.function_path.glob("Feat-*-spec.md") if context.function_path.is_dir() else []:
            match = re.match(r"^(Feat-\d{2})-", path.name)
            if match:
                disk_by_id[match.group(1)] = path.resolve()

        numbers: list[int] = []
        for feat_id, entry in registered_by_id.items():
            match = self.FEAT_ID_RE.fullmatch(feat_id)
            feature_line = registry_line(self.config.features_registry, f"id: {feat_id}")
            if not match:
                findings.append(
                    make_finding(
                        self.config,
                        context,
                        "REG-FEAT-ID-001",
                        Severity.MAJOR,
                        f"invalid FeatID `{feat_id}`",
                        self.config.features_registry,
                        feature_line,
                        feat_id=feat_id,
                    )
                )
                continue
            numbers.append(int(match.group(1)))
            spec_value = entry.get("spec")
            if not spec_value:
                if str(entry.get("status")) != "Draft":
                    findings.append(
                        make_finding(
                            self.config,
                            context,
                            "REG-SPEC-PATH-EMPTY-001",
                            Severity.MAJOR,
                            "non-Draft Feature has no registered spec path",
                            self.config.features_registry,
                            feature_line,
                            feat_id=feat_id,
                        )
                    )
                continue
            registered_path = (self.config.specs_root / str(spec_value)).resolve()
            if not registered_path.is_file():
                findings.append(
                    make_finding(
                        self.config,
                        context,
                        "REG-SPEC-MISSING-001",
                        Severity.MAJOR,
                        "registered Feature spec does not exist",
                        self.config.features_registry,
                        feature_line,
                        feat_id=feat_id,
                        expected_path=str(spec_value),
                    )
                )
            disk_path = disk_by_id.get(feat_id)
            if disk_path is not None and disk_path != registered_path:
                findings.append(
                    make_finding(
                        self.config,
                        context,
                        "REG-SPEC-PATH-MISMATCH-001",
                        Severity.MAJOR,
                        "registered spec path does not match the Feat file on disk",
                        self.config.features_registry,
                        feature_line,
                        feat_id=feat_id,
                        registered=self.config.repo_relative(registered_path),
                        disk=self.config.repo_relative(disk_path),
                    )
                )

        if numbers:
            expected = list(range(1, max(numbers) + 1))
            if sorted(numbers) != expected:
                findings.append(
                    make_finding(
                        self.config,
                        context,
                        "REG-FEAT-CONTIGUOUS-001",
                        Severity.MAJOR,
                        "FeatIDs are not contiguous from Feat-01",
                        self.config.features_registry,
                        function_line,
                        actual=sorted(numbers),
                        expected=expected,
                    )
                )

        for feat_id, path in disk_by_id.items():
            if feat_id not in registered_by_id:
                findings.append(
                    make_finding(
                        self.config,
                        context,
                        "REG-SPEC-UNREGISTERED-001",
                        Severity.MAJOR,
                        "Feature spec exists on disk but is not registered",
                        path,
                        1,
                        feat_id=feat_id,
                    )
                )

        for path, document in docs.items():
            metadata = document.metadata()
            if document.kind == "spec" and document.feat_id:
                expected_id = f"Func-{context.func_id}-Feat-{document.feat_id.split('-')[1]}"
                actual_id = metadata.get("特性编号", "")
                if actual_id and actual_id != expected_id:
                    findings.append(
                        make_finding(
                            self.config,
                            context,
                            "REG-SPEC-METADATA-ID-001",
                            Severity.MAJOR,
                            f"spec metadata ID `{actual_id}` does not match `{expected_id}`",
                            path,
                            self._metadata_line(document, "特性编号"),
                            feat_id=document.feat_id,
                        )
                    )
            elif document.kind == "design":
                expected_design = f"DESIGN-Func-{context.func_id}"
                actual_design = metadata.get("Design ID", "")
                if actual_design and actual_design != expected_design:
                    if actual_design.strip("`") == expected_design:
                        message = (
                            f"design metadata ID has a formatting error: use plain text `{expected_design}` "
                            "without Markdown backticks"
                        )
                        details = {"formatting_issue": "markdown_inline_code"}
                    else:
                        message = f"design metadata ID `{actual_design}` does not match `{expected_design}`"
                        details = {}
                    findings.append(
                        make_finding(
                            self.config,
                            context,
                            "REG-DESIGN-METADATA-ID-001",
                            Severity.MAJOR,
                            message,
                            path,
                            self._metadata_line(document, "Design ID"),
                            actual_id=actual_design,
                            expected_id=expected_design,
                            **details,
                        )
                    )
        return findings

    @staticmethod
    def _metadata_line(document: DocumentModel, key: str) -> int | None:
        for table in document.tables:
            for row in table.rows:
                if row.cells and row.cells[0].strip() == key:
                    return row.line
        return None
