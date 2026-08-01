from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from spec_eval.checks import (
    DesignStructureChecker,
    HygieneChecker,
    RegistryChecker,
    SpecStructureChecker,
    TraceabilityChecker,
)
from spec_eval.config import EvaluationConfig
from spec_eval.discovery import FunctionLocator
from spec_eval.parser import MarkdownParser


class CheckFixture:
    def __init__(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp.name) / "foundation" / "arkui" / "ace_engine"
        self.specs_root = self.repo_root / "specs"
        registry_root = self.specs_root / "registry"
        self.function_root = self.specs_root / "04-common-capability" / "01-test" / "01-sample"
        registry_root.mkdir(parents=True)
        self.function_root.mkdir(parents=True)
        self.spec_path = self.function_root / "Feat-01-sample-spec.md"
        self.design_path = self.function_root / "design.md"
        functions = {
            "functions": [
                {
                    "id": "04-01-01",
                    "path": "04-common-capability/01-test/01-sample/",
                    "design": "04-common-capability/01-test/01-sample/design.md",
                    "status": "active",
                }
            ]
        }
        features = {
            "features": [
                {
                    "func_id": "04-01-01",
                    "id": "Feat-01",
                    "title": "sample",
                    "spec": "04-common-capability/01-test/01-sample/Feat-01-sample-spec.md",
                    "status": "Baselined",
                }
            ]
        }
        (registry_root / "functions.yaml").write_text(yaml.safe_dump(functions, allow_unicode=True), encoding="utf-8")
        (registry_root / "features.yaml").write_text(yaml.safe_dump(features, allow_unicode=True), encoding="utf-8")
        self.spec_path.write_text(
            """# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | sample |
| 特性编号 | Func-04-01-01-Feat-01 |
| 优先级 | P1 |
| 目标版本 | API 1 |
| 状态 | Baselined |
| 复杂度 | 标准 |
## 用户故事
### US-1: sample
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN x THEN y | 正常 |
| AC-1.2 | WHEN a THEN b | 正常 |
## 验收追溯
| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-1.2 | R-1-R-2 | TASK-04-01-01-F1 | test | N/A |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | x | y | none | AC-1.1 |
| R-2 | 行为 | a | b | none | AC-1.2 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 | test | x |
## Spec 自审清单
- [ ] TODO later
[missing](missing.md)
`/home/user/source.cpp:10`
## context-references
""",
            encoding="utf-8",
        )
        self.design_path.write_text(
            """# 架构设计
## 设计元数据
| 字段 | 内容 |
|---|---|
| Design ID | DESIGN-Func-04-01-01 |
| 目标 Feature | Feat-01 sample |
| 状态 | Baselined |
## 关键设计决策
| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---|---|---|---|---|---|
| ADR-1 | x | y | z | r | i |
""",
            encoding="utf-8",
        )
        self.config = EvaluationConfig(
            repo_root=self.repo_root,
            specs_root=self.specs_root,
            oh_root=self.repo_root.parents[2],
            functions_registry=registry_root / "functions.yaml",
            features_registry=registry_root / "features.yaml",
            rules_root=self.specs_root / "evaluation",
            schemas_root=self.specs_root / "evaluation" / "schemas",
            output_root=self.repo_root / "out",
        )
        self.context = FunctionLocator(self.config).locate("04-01-01")
        parser = MarkdownParser(self.config)
        self.documents = [parser.parse(path) for path in self.context.all_documents() if path.is_file()]

    def cleanup(self) -> None:
        self.temp.cleanup()


class Infra004To008Test(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = CheckFixture()

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_registry_consistency_is_clean_for_registered_files(self) -> None:
        findings = RegistryChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)
        self.assertEqual(findings, [])

    def test_spec_and_design_missing_sections_are_reported(self) -> None:
        spec_rules = {item.rule_id for item in SpecStructureChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)}
        design_rules = {item.rule_id for item in DesignStructureChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)}
        self.assertIn("SPEC-STRUCT-H2-MISSING-001", spec_rules)
        self.assertIn("DESIGN-STRUCT-H2-MISSING-001", design_rules)

    def test_backticked_design_id_remains_invalid_and_reports_formatting_issue(self) -> None:
        original = self.fixture.design_path.read_text(encoding="utf-8")
        self.fixture.design_path.write_text(
            original.replace(
                "| Design ID | DESIGN-Func-04-01-01 |",
                "| Design ID | `DESIGN-Func-04-01-01` |",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]

        registry_finding = next(
            item
            for item in RegistryChecker(self.fixture.config).run(self.fixture.context, documents)
            if item.rule_id == "REG-DESIGN-METADATA-ID-001"
        )
        structure_finding = next(
            item
            for item in DesignStructureChecker(self.fixture.config).run(self.fixture.context, documents)
            if item.rule_id == "DESIGN-STRUCT-ID-001"
        )
        for finding in (registry_finding, structure_finding):
            self.assertIn("formatting error", finding.message)
            self.assertIn("without Markdown backticks", finding.message)
            self.assertEqual(finding.details["formatting_issue"], "markdown_inline_code")
            self.assertEqual(finding.details["actual_id"], "`DESIGN-Func-04-01-01`")
            self.assertEqual(finding.details["expected_id"], "DESIGN-Func-04-01-01")

    def test_trace_table_alias_reports_field_error_instead_of_missing_table(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |",
                "| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        findings = SpecStructureChecker(self.fixture.config).run(self.fixture.context, documents)
        field_finding = next(item for item in findings if item.rule_id == "SPEC-STRUCT-TABLE-FIELD-001")
        self.assertEqual(field_finding.details["section"], "验收追溯")
        self.assertEqual(field_finding.details["missing_fields"], ["AC编号"])
        self.assertEqual(field_finding.details["unexpected_fields"], ["AC"])
        self.assertIn("missing fields: `AC编号`", field_finding.message)
        self.assertIn("unexpected fields: `AC`", field_finding.message)
        self.assertFalse(
            any(
                item.rule_id == "SPEC-STRUCT-TABLE-001" and item.details.get("section") == "验收追溯"
                for item in findings
            )
        )

    def test_table_field_order_error_reports_expected_and_actual_order(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |",
                "| 关联规则 | AC编号 | 关联 Task | 验证方式 | 证据 |",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        findings = SpecStructureChecker(self.fixture.config).run(self.fixture.context, documents)
        finding = next(item for item in findings if item.rule_id == "SPEC-STRUCT-TABLE-FIELD-001")
        self.assertTrue(finding.details["field_order_mismatch"])
        self.assertIn("field order mismatch: expected `AC编号` -> `关联规则`", finding.message)
        self.assertIn("actual `关联规则` -> `AC编号`", finding.message)

    def test_user_story_requires_role_goal_and_value_in_order(self) -> None:
        checker = SpecStructureChecker(self.fixture.config)
        findings = checker.run(self.fixture.context, self.fixture.documents)
        user_story_findings = [item for item in findings if item.rule_id == "SPEC-STRUCT-USER-STORY-001"]
        self.assertEqual(len(user_story_findings), 1)
        self.assertEqual(user_story_findings[0].details["user_story"], "US-1: sample")
        self.assertIn("missing_作为", user_story_findings[0].details["issues"])

        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "### US-1: sample\n",
                "### US-1: sample\n\n"
                "**作为** 应用开发者\n"
                "**我想要** 使用示例能力\n"
                "**以便** 完成可验证的业务目标\n\n",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        valid_rules = {item.rule_id for item in checker.run(self.fixture.context, documents)}
        self.assertNotIn("SPEC-STRUCT-USER-STORY-001", valid_rules)

    def test_user_story_rejects_wrong_order_and_empty_value(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace(
                "### US-1: sample\n",
                "### US-1: sample\n\n"
                "**我想要** 使用示例能力\n"
                "**作为** 应用开发者\n"
                "**以便** ，\n\n",
                1,
            ),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        findings = SpecStructureChecker(self.fixture.config).run(self.fixture.context, documents)
        finding = next(item for item in findings if item.rule_id == "SPEC-STRUCT-USER-STORY-001")
        self.assertIn("empty_以便", finding.details["issues"])
        self.assertIn("invalid_field_order", finding.details["issues"])

    def test_user_story_section_requires_us_heading(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace("### US-1: sample\n", "", 1),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        findings = SpecStructureChecker(self.fixture.config).run(self.fixture.context, documents)
        finding = next(item for item in findings if item.rule_id == "SPEC-STRUCT-USER-STORY-001")
        self.assertEqual(finding.details["issues"], ["missing_user_story_heading"])

    def test_hygiene_reports_placeholder_absolute_path_link_and_checkbox(self) -> None:
        rules = {item.rule_id for item in HygieneChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)}
        self.assertIn("HYGIENE-PLACEHOLDER-001", rules)
        self.assertIn("HYGIENE-ABSOLUTE-PATH-001", rules)
        self.assertIn("HYGIENE-UNCHECKED-AUDIT-001", rules)
        self.assertIn("LINK-DEAD-001", rules)

    def test_hygiene_accepts_links_relative_to_specs_root(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original
            + "\n[specs-root](04-common-capability/01-test/01-sample/design.md)\n"
            + "[repo-root](specs/04-common-capability/01-test/01-sample/design.md)\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        findings = HygieneChecker(self.fixture.config).run(self.fixture.context, documents)
        dead_targets = {item.message for item in findings if item.rule_id == "LINK-DEAD-001"}

        self.assertIn("Markdown link target does not exist: `missing.md`", dead_targets)
        self.assertNotIn(
            "Markdown link target does not exist: `04-common-capability/01-test/01-sample/design.md`",
            dead_targets,
        )
        self.assertNotIn(
            "Markdown link target does not exist: `specs/04-common-capability/01-test/01-sample/design.md`",
            dead_targets,
        )

    def test_hygiene_accepts_links_relative_to_repo_root(self) -> None:
        repo_document = self.fixture.repo_root / "docs" / "architecture" / "sample.md"
        repo_document.parent.mkdir(parents=True)
        repo_document.write_text("# sample\n", encoding="utf-8")
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original + "\n[ace-engine-root](docs/architecture/sample.md)\n",
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        findings = HygieneChecker(self.fixture.config).run(self.fixture.context, documents)
        dead_targets = {item.message for item in findings if item.rule_id == "LINK-DEAD-001"}

        self.assertIn("Markdown link target does not exist: `missing.md`", dead_targets)
        self.assertNotIn(
            "Markdown link target does not exist: `docs/architecture/sample.md`",
            dead_targets,
        )

    def test_traceability_is_function_scoped_and_reports_range_and_gap(self) -> None:
        result = TraceabilityChecker(self.fixture.config).run(self.fixture.context, self.fixture.documents)
        rules = {item.rule_id for item in result.findings}
        self.assertIn("TRACE-RANGE-ID-001", rules)
        self.assertIn("TRACE-AC-NO-VM-001", rules)
        self.assertIn("Feat-01/AC-1.1", result.graph.nodes)
        self.assertIn("Feat-01/R-1", result.graph.nodes)
        self.assertEqual(result.metrics["ac_count"], 2)
        self.assertEqual(result.metrics["per_feat"]["Feat-01"]["closure_rate"], 0.5)

    def test_tilde_range_reports_and_suppresses_no_vm_cascade(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        self.fixture.spec_path.write_text(
            original.replace("| VM-1 | AC-1.1 | test | x |", "| VM-1 | AC-1.1~1.2 | test | x |", 1),
            encoding="utf-8",
        )
        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = TraceabilityChecker(self.fixture.config).run(self.fixture.context, documents)
        ranges = [item for item in result.findings if item.rule_id == "TRACE-RANGE-ID-001"]
        self.assertTrue(any("AC-1.1~1.2" in item.message for item in ranges))
        self.assertFalse(any(item.rule_id == "TRACE-AC-NO-VM-001" for item in result.findings))
        self.assertFalse(result.graph.outgoing("Feat-01/AC-1.1", "verified_by"))
        self.assertFalse(result.graph.outgoing("Feat-01/AC-1.2", "verified_by"))

    def test_tilde_ranges_suppress_no_rule_and_rule_orphan_cascades(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        updated = original.replace(
            "| AC-1.1-AC-1.2 | R-1-R-2 | TASK-04-01-01-F1 | test | N/A |",
            "| AC-1.1~1.2 | R-1~2 | TASK-04-01-01-F1 | test | N/A |",
            1,
        )
        updated = updated.replace("| R-1 | 行为 | x | y | none | AC-1.1 |", "| R-1 | 行为 | x | y | none | AC-1.1~1.2 |", 1)
        updated = updated.replace("| R-2 | 行为 | a | b | none | AC-1.2 |", "| R-2 | 行为 | a | b | none | AC-1.1~1.2 |", 1)
        self.fixture.spec_path.write_text(updated, encoding="utf-8")

        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = TraceabilityChecker(self.fixture.config).run(self.fixture.context, documents)

        range_messages = [item.message for item in result.findings if item.rule_id == "TRACE-RANGE-ID-001"]
        self.assertTrue(any("AC-1.1~1.2" in message for message in range_messages))
        self.assertTrue(any("R-1~2" in message for message in range_messages))
        self.assertFalse(any(item.rule_id == "TRACE-AC-NO-RULE-001" for item in result.findings))
        self.assertFalse(any(item.rule_id == "TRACE-RULE-ORPHAN-001" for item in result.findings))
        self.assertFalse(result.graph.outgoing("Feat-01/AC-1.1", "specified_by"))
        self.assertFalse(result.graph.outgoing("Feat-01/AC-1.2", "specified_by"))

    def test_full_id_tilde_ranges_report_and_suppress_all_trace_cascades(self) -> None:
        original = self.fixture.spec_path.read_text(encoding="utf-8")
        updated = original.replace(
            "| AC-1.1-AC-1.2 | R-1-R-2 | TASK-04-01-01-F1 | test | N/A |",
            "| AC-1.1 ~ AC-1.2 | R-1, R-2 | TASK-04-01-01-F1 | test | N/A |",
            1,
        )
        updated = updated.replace("| R-1 | 行为 | x | y | none | AC-1.1 |", "| R-1 | 行为 | x | y | none | AC-1.1~AC-1.2 |", 1)
        updated = updated.replace("| R-2 | 行为 | a | b | none | AC-1.2 |", "| R-2 | 行为 | a | b | none | AC-1.1~AC-1.2 |", 1)
        updated = updated.replace("| VM-1 | AC-1.1 | test | x |", "| VM-1 | AC-1.1 ~ AC-1.2 | test | x |", 1)
        self.fixture.spec_path.write_text(updated, encoding="utf-8")

        parser = MarkdownParser(self.fixture.config)
        documents = [parser.parse(path) for path in self.fixture.context.all_documents() if path.is_file()]
        result = TraceabilityChecker(self.fixture.config).run(self.fixture.context, documents)

        range_messages = [item.message for item in result.findings if item.rule_id == "TRACE-RANGE-ID-001"]
        self.assertTrue(any("AC-1.1 ~ AC-1.2" in message for message in range_messages))
        self.assertFalse(any(item.rule_id == "TRACE-AC-NO-VM-001" for item in result.findings))
        self.assertFalse(any(item.rule_id == "TRACE-AC-NO-RULE-001" for item in result.findings))
        self.assertFalse(any(item.rule_id == "TRACE-RULE-ORPHAN-001" for item in result.findings))
        self.assertFalse(result.graph.outgoing("Feat-01/AC-1.1", "verified_by"))
        self.assertFalse(result.graph.outgoing("Feat-01/AC-1.2", "verified_by"))
        self.assertEqual(
            TraceabilityChecker(self.fixture.config)._qualified_range_members(
                "AC-1.4 ~ AC-2.1", "ac", "Feat-01"
            ),
            {"Feat-01/AC-1.4", "Feat-01/AC-2.1"},
        )


if __name__ == "__main__":
    unittest.main()
