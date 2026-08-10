from __future__ import annotations

import unittest
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from spec_eval.checks.reference_checks import ReferenceChecker
from spec_eval.checks.sdk_contract_checks import SdkContractChecker
from spec_eval.checks.traceability_checks import TraceabilityChecker
from spec_eval.config import EvaluationConfig
from spec_eval.orchestrator import EvaluationOrchestrator
from spec_eval.parser.markdown_parser import MarkdownParser
from spec_eval.tests.test_infra_004_008 import CheckFixture


class RuleCalibrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[4]
        cls.matrix_path = cls.repo_root / "specs" / "evaluation" / "rule_applicability.yaml"
        cls.expectations_path = cls.repo_root / "specs" / "evaluation" / "golden" / "static_expectations.yaml"

    def test_rule_applicability_matrix_covers_34_active_rules(self) -> None:
        document = yaml.safe_load(self.matrix_path.read_text(encoding="utf-8"))
        rules = document["rules"]
        self.assertEqual(document["baseline"]["active_rule_count"], 34)
        self.assertEqual(len(rules), 34)
        self.assertEqual(len({item["rule_id"] for item in rules}), 34)
        required = {
            "rule_id",
            "checker",
            "calibration_class",
            "applies_to",
            "prerequisites",
            "suppress_when",
            "default_severity",
            "recommended_gate",
            "legacy_policy",
            "owner",
        }
        for entry in rules:
            with self.subTest(rule_id=entry["rule_id"]):
                self.assertTrue(required.issubset(entry))
                self.assertIn(entry["calibration_class"], {"stable_hard", "legacy_debt", "conditional"})
                self.assertEqual(entry["owner"], "spec-eval")

    def test_top_ten_expectations_have_three_cross_domain_samples_each(self) -> None:
        document = yaml.safe_load(self.expectations_path.read_text(encoding="utf-8"))
        samples = document["samples"]
        self.assertEqual(len(samples), 30)
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for sample in samples:
            grouped[str(sample["rule_id"])].append(sample)
            self.assertIn(sample["classification"], document["classifications"])
            self.assertGreaterEqual(sample["baseline_count"], 0)
            self.assertGreaterEqual(sample["expected_count"], 0)
        self.assertEqual(len(grouped), 10)
        for rule_id, entries in grouped.items():
            with self.subTest(rule_id=rule_id):
                self.assertEqual(len(entries), 3)
                self.assertEqual(len({str(item["func_id"]).split("-", 1)[0] for item in entries}), 3)

    def test_top_ten_real_function_counts_match_calibrated_expectations(self) -> None:
        document = yaml.safe_load(self.expectations_path.read_text(encoding="utf-8"))
        evaluator = EvaluationOrchestrator(EvaluationConfig.discover())
        counts_by_function: dict[str, Counter[str]] = {}
        for sample in document["samples"]:
            func_id = str(sample["func_id"])
            if func_id not in counts_by_function:
                run = evaluator.evaluate(func_id)
                counts_by_function[func_id] = Counter(item.rule_id for item in run.static_result.findings)
            with self.subTest(rule_id=sample["rule_id"], func_id=func_id):
                self.assertEqual(counts_by_function[func_id][sample["rule_id"]], sample["expected_count"])

    def test_nonstandard_trace_tables_report_structure_without_trace_cascade(self) -> None:
        fixture = CheckFixture()
        try:
            original = fixture.spec_path.read_text(encoding="utf-8")
            updated = original.replace(
                "| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |",
                "| AC编号 | 业务规则 | 关联 Task | 验证方式 | 证据 |",
                1,
            ).replace(
                "| 编号 | 对应规格项 | 验证方式 | 验证重点 |",
                "| VM编号 | AC编号 | 验证类型 | 位置/用例 |",
                1,
            )
            fixture.spec_path.write_text(updated, encoding="utf-8")
            parser = MarkdownParser(fixture.config)
            documents = [parser.parse(path) for path in fixture.context.all_documents() if path.is_file()]
            result = TraceabilityChecker(fixture.config).run(fixture.context, documents)
            rules = {item.rule_id for item in result.findings}
            self.assertNotIn("TRACE-AC-NO-RULE-001", rules)
            self.assertNotIn("TRACE-AC-NO-VM-001", rules)
            self.assertNotIn("TRACE-RULE-ORPHAN-001", rules)
            metrics = result.metrics["per_feat"]["Feat-01"]
            self.assertFalse(metrics["rule_trace_applicable"])
            self.assertFalse(metrics["vm_trace_applicable"])
        finally:
            fixture.cleanup()

    def test_partial_repo_suffix_resolves_and_ignored_basename_is_ambiguous(self) -> None:
        fixture = CheckFixture()
        try:
            unique = fixture.repo_root / "frameworks" / "bridge" / "sample" / "sdk" / "local_storage.ts"
            unique.parent.mkdir(parents=True)
            unique.write_text("export class LocalStorage {}\n", encoding="utf-8")
            for root in ("generated/one", "generated/two"):
                candidate = fixture.repo_root / root / "ArkUIGeneratedNativeModule.ets"
                candidate.parent.mkdir(parents=True)
                candidate.write_text("export class Generated {}\n", encoding="utf-8")
            fixture.spec_path.write_text(
                fixture.spec_path.read_text(encoding="utf-8")
                + "\n`sdk/local_storage.ts:1`\n"
                + "`ArkUIGeneratedNativeModule.ets:1`\n",
                encoding="utf-8",
            )
            parser = MarkdownParser(fixture.config)
            documents = [parser.parse(path) for path in fixture.context.all_documents() if path.is_file()]
            result = ReferenceChecker(fixture.config).run(fixture.context, documents)
            self.assertFalse(
                any(
                    item.rule_id == "REF-NOT-FOUND-001" and item.details.get("raw") == "sdk/local_storage.ts:1"
                    for item in result.findings
                )
            )
            self.assertTrue(
                any(
                    item.rule_id == "REF-AMBIGUOUS-001"
                    and item.details.get("raw") == "ArkUIGeneratedNativeModule.ets:1"
                    for item in result.findings
                )
            )
        finally:
            fixture.cleanup()

    def test_sdk_unique_suffix_resolves_but_wildcard_requires_concrete_api(self) -> None:
        fixture = CheckFixture()
        try:
            ndk = fixture.config.oh_root / "interface" / "sdk_c" / "arkui" / "native" / "sample.h"
            ndk.parent.mkdir(parents=True)
            ndk.write_text(
                "int32_t OH_ArkUI_CreateThing(void);\n"
                "int32_t OH_ArkUI_DestroyThing(void);\n"
                "int32_t OH_ArkUI_GetXByIndex(void);\n"
                "int32_t OH_ArkUI_GetYByIndex(void);\n",
                encoding="utf-8",
            )
            fixture.spec_path.write_text(
                fixture.spec_path.read_text(encoding="utf-8")
                + "\n### SDK calibration fixture\n"
                + "| API 名称 | 开放范围 | 功能描述 |\n"
                + "|---|---|---|\n"
                + "| `OH_ArkUI_CreateThing` / `DestroyThing` | Public(NDK) | unique suffix |\n"
                + "| `OH_ArkUI_*ByIndex` | Public(NDK) | wildcard |\n",
                encoding="utf-8",
            )
            parser = MarkdownParser(fixture.config)
            documents = [parser.parse(path) for path in fixture.context.all_documents() if path.is_file()]
            result = SdkContractChecker(fixture.config).run(fixture.context, documents)
            findings = [item for item in result.findings if item.rule_id == "SDK-API-NOT-FOUND-001"]
            self.assertFalse(any(item.details.get("api") == "DestroyThing" for item in findings))
            wildcard = next(item for item in findings if item.details.get("non_concrete_api_entry") is True)
            self.assertIn("enumerate each Public/System API explicitly", wildcard.message)
        finally:
            fixture.cleanup()


if __name__ == "__main__":
    unittest.main()
