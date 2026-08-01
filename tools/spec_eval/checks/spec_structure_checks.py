"""Deterministic Feature spec structure checks."""

from __future__ import annotations

import re

from spec_eval.checks.base import make_finding
from spec_eval.config import EvaluationConfig
from spec_eval.models import DocumentModel, Finding, FunctionContext, Severity


class SpecStructureChecker:
    USER_STORY_HEADING_RE = re.compile(r"^US-\d+\b", re.IGNORECASE)
    USER_STORY_LINE_RE = re.compile(r"^\s*\*\*(作为|我想要|以便)\*\*\s*(.*?)\s*$")
    USER_STORY_FIELDS = ("作为", "我想要", "以便")
    REQUIRED_H2 = (
        "概述",
        "本次变更范围（Delta）",
        "输入文档",
        "用户故事",
        "验收追溯",
        "规则定义",
        "验证映射",
        "API 变更分析",
        "接口规格",
        "兼容性声明",
        "架构约束",
        "非功能性需求",
        "多设备适配声明",
        "全局特性影响",
        "Spec 自审清单",
        "context-references",
    )
    REQUIRED_METADATA = ("特性名称", "特性编号", "优先级", "目标版本", "状态", "复杂度")
    TABLE_REQUIREMENTS = {
        "用户故事": ("AC编号", "验收标准", "类型"),
        "验收追溯": ("AC编号", "关联规则", "关联 Task", "验证方式", "证据"),
        "规则定义": ("规则ID", "类型", "触发条件", "预期行为", "边界/约束", "关联AC"),
        "验证映射": ("编号", "对应规格项", "验证方式", "验证重点"),
    }
    ALLOWED_STATUS = {"Draft", "Baselined", "Deprecated"}
    ALLOWED_PRIORITY = {"P0", "P1", "P2", "P3"}
    ALLOWED_AC_TYPE = {"正常", "异常", "边界", "恢复"}
    ALLOWED_RULE_TYPE = {"行为", "边界", "异常", "恢复"}

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> list[Finding]:
        findings: list[Finding] = []
        for document in documents:
            if document.kind != "spec":
                continue
            h1 = next((heading for heading in document.headings if heading.level == 1), None)
            if h1 is None or h1.title != "特性规格":
                findings.append(self._finding(context, document, "SPEC-STRUCT-H1-001", "spec H1 must be `特性规格`", 1))
            h2 = document.h2_titles()
            for title in self.REQUIRED_H2:
                if title not in h2:
                    findings.append(
                        self._finding(
                            context,
                            document,
                            "SPEC-STRUCT-H2-MISSING-001",
                            f"missing required section `{title}`",
                            1,
                            section=title,
                        )
                    )
            present_required = [title for title in h2 if title in self.REQUIRED_H2]
            expected_present = [title for title in self.REQUIRED_H2 if title in h2]
            if present_required != expected_present:
                findings.append(
                    self._finding(
                        context,
                        document,
                        "SPEC-STRUCT-H2-ORDER-001",
                        "required spec sections are not in the standard order",
                        1,
                    )
                )

            metadata = document.metadata()
            for field in self.REQUIRED_METADATA:
                if not metadata.get(field, "").strip():
                    findings.append(
                        self._finding(
                            context,
                            document,
                            "SPEC-STRUCT-METADATA-001",
                            f"missing metadata field `{field}`",
                            1,
                            field=field,
                        )
                    )
            status = metadata.get("状态", "").strip()
            if status and status not in self.ALLOWED_STATUS:
                findings.append(self._finding(context, document, "SPEC-STRUCT-STATUS-001", f"invalid status `{status}`", 1))
            priority = metadata.get("优先级", "").strip()
            if priority and priority not in self.ALLOWED_PRIORITY:
                findings.append(self._finding(context, document, "SPEC-STRUCT-PRIORITY-001", f"invalid priority `{priority}`", 1))

            findings.extend(self._check_user_stories(context, document))

            for section, required_headers in self.TABLE_REQUIREMENTS.items():
                tables = document.tables_in_section(section)
                if not tables:
                    findings.append(
                        self._finding(
                            context,
                            document,
                            "SPEC-STRUCT-TABLE-001",
                            f"section `{section}` does not contain the required table",
                            self._section_line(document, section),
                            section=section,
                        )
                    )
                    continue
                if any(table.headers == required_headers for table in tables):
                    continue
                candidate = max(
                    tables,
                    key=lambda table: sum(header in required_headers for header in table.headers),
                )
                missing_fields = [header for header in required_headers if header not in candidate.headers]
                unexpected_fields = [header for header in candidate.headers if header not in required_headers]
                field_order_mismatch = (
                    not missing_fields
                    and not unexpected_fields
                    and candidate.headers != required_headers
                )
                mismatch_details = []
                if missing_fields:
                    mismatch_details.append(
                        "missing fields: " + ", ".join(f"`{field}`" for field in missing_fields)
                    )
                if unexpected_fields:
                    mismatch_details.append(
                        "unexpected fields: " + ", ".join(f"`{field}`" for field in unexpected_fields)
                    )
                if field_order_mismatch:
                    mismatch_details.append(
                        "field order mismatch: expected "
                        + " -> ".join(f"`{field}`" for field in required_headers)
                        + "; actual "
                        + " -> ".join(f"`{field}`" for field in candidate.headers)
                    )
                findings.append(
                    self._finding(
                        context,
                        document,
                        "SPEC-STRUCT-TABLE-FIELD-001",
                        f"section `{section}` table fields do not match the standard header: "
                        + "; ".join(mismatch_details),
                        candidate.line,
                        section=section,
                        required_fields=list(required_headers),
                        actual_fields=list(candidate.headers),
                        missing_fields=missing_fields,
                        unexpected_fields=unexpected_fields,
                        field_order_mismatch=field_order_mismatch,
                    )
                )

            for table in document.tables:
                if "AC编号" in table.headers and "类型" in table.headers:
                    self._check_enum(context, document, table, "类型", self.ALLOWED_AC_TYPE, "SPEC-STRUCT-AC-TYPE-001", findings)
                if "规则ID" in table.headers and "类型" in table.headers:
                    self._check_enum(context, document, table, "类型", self.ALLOWED_RULE_TYPE, "SPEC-STRUCT-RULE-TYPE-001", findings)
        return findings

    def _check_user_stories(self, context: FunctionContext, document: DocumentModel) -> list[Finding]:
        section = next(
            (heading for heading in document.headings if heading.level == 2 and heading.title == "用户故事"),
            None,
        )
        if section is None:
            return []
        section_end = next(
            (heading.line for heading in document.headings if heading.level == 2 and heading.line > section.line),
            len(document.lines) + 1,
        )
        stories = [
            heading
            for heading in document.headings
            if heading.level == 3
            and section.line < heading.line < section_end
            and self.USER_STORY_HEADING_RE.match(heading.title)
        ]
        if not stories:
            return [
                self._finding(
                    context,
                    document,
                    "SPEC-STRUCT-USER-STORY-001",
                    "section `用户故事` must contain at least one `### US-N` structured user story",
                    section.line,
                    issues=["missing_user_story_heading"],
                )
            ]

        findings: list[Finding] = []
        for story in stories:
            block_end = next(
                (
                    heading.line
                    for heading in document.headings
                    if heading.line > story.line and heading.level <= 3
                ),
                section_end,
            )
            fields: list[tuple[str, str, int]] = []
            for line_no in range(story.line + 1, block_end):
                match = self.USER_STORY_LINE_RE.match(document.line_text(line_no))
                if match:
                    fields.append((match.group(1), match.group(2).strip(), line_no))

            issues: list[str] = []
            for field in self.USER_STORY_FIELDS:
                matches = [item for item in fields if item[0] == field]
                if not matches:
                    issues.append(f"missing_{field}")
                elif len(matches) > 1:
                    issues.append(f"duplicate_{field}")
                elif not self._has_user_story_value(matches[0][1]):
                    issues.append(f"empty_{field}")
            if [item[0] for item in fields] != list(self.USER_STORY_FIELDS):
                issues.append("invalid_field_order")
            if issues:
                findings.append(
                    self._finding(
                        context,
                        document,
                        "SPEC-STRUCT-USER-STORY-001",
                        f"user story `{story.title}` must contain non-empty `**作为**`, `**我想要**`, and `**以便**` lines in order",
                        story.line,
                        user_story=story.title,
                        issues=issues,
                    )
                )
        return findings

    @staticmethod
    def _has_user_story_value(value: str) -> bool:
        return bool(value.strip().strip("，,。.;；:："))

    def _check_enum(
        self,
        context: FunctionContext,
        document: DocumentModel,
        table,
        column: str,
        allowed: set[str],
        rule_id: str,
        findings: list[Finding],
    ) -> None:
        for row in table.rows:
            value = row.as_mapping(table.headers).get(column, "").strip()
            if value and value not in allowed:
                findings.append(self._finding(context, document, rule_id, f"invalid `{column}` value `{value}`", row.line))

    def _finding(self, context: FunctionContext, document: DocumentModel, rule: str, message: str, line: int, **details) -> Finding:
        return make_finding(
            self.config,
            context,
            rule,
            Severity.MAJOR,
            message,
            document.path,
            line,
            feat_id=document.feat_id,
            **details,
        )

    @staticmethod
    def _section_line(document: DocumentModel, title: str) -> int:
        heading = next((item for item in document.headings if item.level == 2 and item.title == title), None)
        return heading.line if heading else 1
