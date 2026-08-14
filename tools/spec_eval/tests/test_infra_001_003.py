from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from spec_eval.config import EvaluationConfig
from spec_eval.discovery.changed_function_resolver import ChangedFunctionResolver
from spec_eval.discovery.function_locator import FunctionLocator
from spec_eval.discovery.registry_loader import RegistryLoader
from spec_eval.models.finding import Finding, Severity
from spec_eval.parser.citation_parser import CitationParser
from spec_eval.parser.id_parser import IdParser
from spec_eval.parser.markdown_parser import MarkdownParser
from spec_eval.parser.table_parser import split_table_row


class TemporaryRepository:
    def __init__(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp.name) / "foundation" / "arkui" / "ace_engine"
        self.specs_root = self.repo_root / "specs"
        self.registry_root = self.specs_root / "registry"
        self.function_root = self.specs_root / "05-ui-components" / "01-test" / "01-sample"
        self.registry_root.mkdir(parents=True)
        self.function_root.mkdir(parents=True)
        self.spec_path = self.function_root / "Feat-01-sample-spec.md"
        self.design_path = self.function_root / "design.md"
        functions = {
            "functions": [
                {
                    "id": "05-01-01",
                    "path": "05-ui-components/01-test/01-sample/",
                    "design": "05-ui-components/01-test/01-sample/design.md",
                    "status": "active",
                }
            ]
        }
        features = {
            "features": [
                {
                    "func_id": "05-01-01",
                    "id": "Feat-01",
                    "title": "sample",
                    "spec": "05-ui-components/01-test/01-sample/Feat-01-sample-spec.md",
                    "status": "Baselined",
                }
            ]
        }
        (self.registry_root / "functions.yaml").write_text(yaml.safe_dump(functions, allow_unicode=True), encoding="utf-8")
        (self.registry_root / "features.yaml").write_text(yaml.safe_dump(features, allow_unicode=True), encoding="utf-8")
        self.spec_path.write_text(
            """# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性编号 | Func-05-01-01-Feat-01 |
| 状态 | Baselined |
## 用户故事
### US-1: sample
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN x THEN y | 正常 |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | x | y | `a|b` | AC-1.1 |
## Spec 自审清单
- [x] sample
[design](design.md)
```cpp
int value = 1;
```
""",
            encoding="utf-8",
        )
        self.design_path.write_text("# 架构设计\n## 设计元数据\n", encoding="utf-8")
        self.config = EvaluationConfig(
            repo_root=self.repo_root,
            specs_root=self.specs_root,
            oh_root=self.repo_root.parents[2],
            functions_registry=self.registry_root / "functions.yaml",
            features_registry=self.registry_root / "features.yaml",
            rules_root=self.specs_root / "evaluation",
            schemas_root=self.specs_root / "evaluation" / "schemas",
            output_root=self.repo_root / "out",
        )

    def cleanup(self) -> None:
        self.temp.cleanup()


class Infra001ContractTest(unittest.TestCase):
    def test_finding_serialization_uses_stable_severity(self) -> None:
        finding = Finding("TEST-001", Severity.MAJOR, "problem", "specs/test.md", line=2)
        self.assertEqual(finding.to_dict()["severity"], "Major")
        self.assertEqual(Severity.from_text("warning"), Severity.MINOR)

    def test_all_declared_schemas_are_valid_json_with_required_fields(self) -> None:
        schemas = Path(__file__).resolve().parents[3] / "evaluation" / "schemas"
        expected = {
            "function-context.schema.json",
            "static-result.schema.json",
            "evidence.schema.json",
            "semantic-result.schema.json",
            "score-result.schema.json",
            "evaluation-report.schema.json",
            "baseline.schema.json",
            "ci-summary.schema.json",
            "performance-summary.schema.json",
            "golden-manifest.schema.json",
            "function-evaluation.schema.json",
            "site-evaluation-report.schema.json",
            "site-evaluation-history.schema.json",
            "semantic-service-job.schema.json",
            "executor-result.schema.json",
            "automated-function-index.schema.json",
            "automated-function-history.schema.json",
        }
        self.assertEqual({path.name for path in schemas.glob("*.json")}, expected)
        for path in schemas.glob("*.json"):
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(document["type"], "object")
            self.assertTrue(document["required"])


class Infra002DiscoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = TemporaryRepository()

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_func_id_path_and_changed_file_resolve_same_function(self) -> None:
        registry = RegistryLoader(self.fixture.config).load()
        locator = FunctionLocator(self.fixture.config, registry)
        by_id = locator.locate("05-01-01")
        by_path = locator.locate_by_path(self.fixture.spec_path)
        changed = ChangedFunctionResolver(locator).resolve([self.fixture.spec_path])
        self.assertEqual(by_id.func_id, "05-01-01")
        self.assertEqual(by_path.func_id, by_id.func_id)
        self.assertEqual([item.func_id for item in changed], [by_id.func_id])
        self.assertEqual(by_id.feature_specs, (self.fixture.spec_path.resolve(),))
        self.assertEqual(by_id.design_path, self.fixture.design_path.resolve())

    def test_registry_change_resolves_all_functions(self) -> None:
        locator = FunctionLocator(self.fixture.config)
        changed = ChangedFunctionResolver(locator).resolve([self.fixture.config.features_registry])
        self.assertEqual([item.func_id for item in changed], ["05-01-01"])

    def test_rule_configuration_and_checker_changes_resolve_all_functions(self) -> None:
        locator = FunctionLocator(self.fixture.config)
        resolver = ChangedFunctionResolver(locator)
        rule_change = resolver.resolve([self.fixture.config.rules_root / "gate_rules.yaml"])
        checker_change = resolver.resolve(
            [self.fixture.config.specs_root / "tools" / "spec_eval" / "checks" / "traceability_checks.py"]
        )
        self.assertEqual([item.func_id for item in rule_change], ["05-01-01"])
        self.assertEqual([item.func_id for item in checker_change], ["05-01-01"])


class Infra003ParserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = TemporaryRepository()

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_markdown_parser_preserves_structure_and_lines(self) -> None:
        document = MarkdownParser(self.fixture.config).parse(self.fixture.spec_path)
        self.assertEqual(document.kind, "spec")
        self.assertEqual(document.feat_id, "Feat-01")
        self.assertIn("概述", document.h2_titles())
        self.assertEqual(len(document.code_blocks), 1)
        self.assertEqual(document.links[0].target, "design.md")
        self.assertTrue(document.checkboxes[0].checked)
        self.assertIn(("AC-1.1", 11), document.ids["ac"])
        rule_table = next(table for table in document.tables if "规则ID" in table.headers)
        self.assertEqual(rule_table.rows[0].as_mapping(rule_table.headers)["边界/约束"], "`a|b`")

    def test_table_parser_handles_inline_code_pipe(self) -> None:
        self.assertEqual(split_table_row("| A | `x|y` | C |"), ("A", "`x|y`", "C"))

    def test_id_and_citation_parsers(self) -> None:
        parser = IdParser()
        ids = parser.extract_line("AC-1.1 maps R-1 and VM-2")
        self.assertEqual(ids["ac"], ("AC-1.1",))
        self.assertEqual(ids["rule"], ("R-1",))
        self.assertEqual(
            parser.find_ranges("AC-1.1~1.12 maps R-1~12 and AC-2.1 ~ AC-2.3 with R-3~R-5"),
            ("AC-1.1~1.12", "R-1~12", "AC-2.1 ~ AC-2.3", "R-3~R-5"),
        )
        self.assertEqual(parser.expand_range("AC-1.1~1.3"), ("AC-1.1", "AC-1.2", "AC-1.3"))
        self.assertEqual(parser.expand_range("R-2~4"), ("R-2", "R-3", "R-4"))
        self.assertEqual(parser.expand_range("AC-1.1-AC-1.2"), ("AC-1.1", "AC-1.2"))
        self.assertEqual(parser.expand_range("AC-2.1 ~ AC-2.3"), ("AC-2.1", "AC-2.2", "AC-2.3"))
        self.assertEqual(parser.expand_range("R-3~R-5"), ("R-3", "R-4", "R-5"))
        citation = CitationParser().parse("frameworks/core/test.cpp:10-12,20")[0]
        self.assertEqual(citation.path, "frameworks/core/test.cpp")
        self.assertEqual(citation.line_ranges, ((10, 12), (20, 20)))


if __name__ == "__main__":
    unittest.main()
