from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import yaml

from spec_eval.protocol_validator import (
    aggregate_function_complexity,
    validate_complexity_rules,
    validate_design_completeness_rules,
    validate_evaluation_report,
    validate_protocol,
    validate_rubric,
    validate_score_result,
    validate_semantic_result,
)


class Next005ProtocolTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.schemas_root = cls.evaluation_root / "schemas"
        cls.fixtures_root = Path(__file__).resolve().parent / "fixtures" / "protocol"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)
        cls.design_completeness = yaml.safe_load(
            (cls.evaluation_root / "design_completeness_rules.yaml").read_text(encoding="utf-8")
        )

    def load_fixture(self, name: str) -> dict:
        return json.loads((self.fixtures_root / name).read_text(encoding="utf-8"))

    def build_evaluation_report(self) -> dict:
        semantic = self.load_fixture("semantic-result.json")
        score = self.load_fixture("score-result.json")
        return {
            "schema_version": 1,
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "protocol": {
                "rubric_version": "0.3.0",
                "complexity_rules_version": "0.2.0",
                "evaluator_protocol_version": "0.3.0",
                "aggregator_protocol_version": "0.1.0",
            },
            "static": {
                "func_id": "05-01-01",
                "source_revision": "abc123",
                "tool_version": "0.5.0",
                "rule_version": "0.2.16",
                "gate": "pass",
                "findings": [],
                "metrics": {},
            },
            "semantic": semantic,
            "score": score,
            "summary": {
                "gate": "pass",
                "raw_score": 100,
                "published_score": 100,
                "confidence": 0.93,
                "admission_status": "HIGH_QUALITY",
            },
        }

    def test_protocol_and_valid_examples_close_the_contract(self) -> None:
        self.assertEqual(self.protocol_errors, [])
        self.assertEqual(self.rubric["status"], "frozen")
        self.assertEqual(self.rubric["approval"]["freeze_state"], "frozen")
        self.assertEqual(self.rubric["approval"]["confirmed_by"], "sunfei2021")
        semantic = self.load_fixture("semantic-result.json")
        score = self.load_fixture("score-result.json")
        self.assertEqual(
            validate_semantic_result(semantic, self.rubric, self.complexity, self.schemas_root),
            [],
        )
        self.assertEqual(validate_score_result(score, self.rubric, self.schemas_root), [])
        self.assertEqual(
            validate_evaluation_report(
                self.build_evaluation_report(), self.rubric, self.complexity, self.schemas_root
            ),
            [],
        )

    def test_rubric_freeze_requires_a_single_confirmation(self) -> None:
        invalid = copy.deepcopy(self.rubric)
        invalid["status"] = "candidate"
        invalid["approval"]["freeze_state"] = "pilot_single_confirmation"
        invalid["approval"]["confirmed_by"] = None
        errors = validate_rubric(invalid)
        self.assertTrue(any("must be frozen" in item for item in errors))
        self.assertTrue(any("requires confirmed_by" in item for item in errors))

    def test_rubric_rejects_weight_drift_and_duplicate_criterion_ids(self) -> None:
        invalid = copy.deepcopy(self.rubric)
        invalid["dimensions"][0]["weight"] = 31
        invalid["dimensions"][1]["criteria"][0]["id"] = invalid["dimensions"][0]["criteria"][0]["id"]
        errors = validate_rubric(invalid)
        self.assertTrue(any("sum to 100" in item for item in errors))
        self.assertTrue(any("duplicate criterion ID" in item for item in errors))

    def test_design_rubric_has_six_complete_criteria_and_twenty_total(self) -> None:
        criteria = [
            criterion
            for dimension in self.rubric["dimensions"]
            for criterion in dimension["criteria"]
        ]
        design = next(
            dimension for dimension in self.rubric["dimensions"]
            if dimension["id"] == "design_quality"
        )
        self.assertEqual(len(criteria), 20)
        self.assertEqual(len(design["criteria"]), 6)
        self.assertEqual(sum(item["max_score"] for item in design["criteria"]), 25)
        self.assertEqual(
            [item["id"] for item in design["criteria"]],
            [
                "DESIGN-IMPLEMENTATION-PATH",
                "DESIGN-FEAT-RUNTIME-COVERAGE",
                "DESIGN-ALGORITHM-DATA-STATE",
                "DESIGN-DECISION-QUALITY",
                "DESIGN-IMPACT-COVERAGE",
                "DESIGN-VERIFICATION-PLAN",
            ],
        )

    def test_design_completeness_rules_reject_missing_runtime_check(self) -> None:
        invalid = copy.deepcopy(self.design_completeness)
        invalid["criteria"]["DESIGN-FEAT-RUNTIME-COVERAGE"]["checks"].pop()
        errors = validate_design_completeness_rules(invalid, self.rubric)
        self.assertTrue(any("check IDs do not match" in item for item in errors))

    def test_design_completeness_does_not_reward_document_shape(self) -> None:
        forbidden = set(self.design_completeness["coverage_policy"]["forbidden_positive_factors"])
        self.assertEqual(
            forbidden,
            {
                "heading_presence_only",
                "table_presence_only",
                "diagram_presence_only",
                "document_length",
                "checked_self_audit_boxes",
            },
        )
        invalid = copy.deepcopy(self.design_completeness)
        invalid["coverage_policy"]["forbidden_positive_factors"].pop()
        errors = validate_design_completeness_rules(invalid, self.rubric)
        self.assertTrue(any("forbidden positive factors" in item for item in errors))

    def test_hybrid_design_check_requires_a_script_signal(self) -> None:
        invalid = copy.deepcopy(self.design_completeness)
        invalid["criteria"]["DESIGN-IMPLEMENTATION-PATH"]["checks"][0].pop("script_signal")
        errors = validate_design_completeness_rules(invalid, self.rubric)
        self.assertTrue(any("requires script_signal" in item for item in errors))

    def test_protocol_rejects_version_mismatch(self) -> None:
        invalid = copy.deepcopy(self.complexity)
        invalid["rubric_version"] = "9.9.0"
        errors = validate_complexity_rules(invalid, self.rubric)
        self.assertTrue(any("rubric_version" in item for item in errors))

    def test_critical_complexity_cannot_skip_design_completeness(self) -> None:
        invalid = copy.deepcopy(self.complexity)
        invalid["review_depth"]["critical"]["require_per_feature_runtime_coverage"] = False
        errors = validate_complexity_rules(invalid, self.rubric)
        self.assertTrue(any("require_per_feature_runtime_coverage" in item for item in errors))

    def test_complexity_normalization_handles_existing_free_form_values(self) -> None:
        result = aggregate_function_complexity(
            {
                "Feat-01": "简单（L1）",
                "Feat-02": "标准（多查询 API + 双路径）",
                "Feat-03": "较高（多重载双栈）",
                "Feat-04": "L3（关键）",
            },
            self.complexity,
        )
        self.assertEqual(
            result["normalized_feature_levels"],
            {
                "Feat-01": "simple",
                "Feat-02": "standard",
                "Feat-03": "complex",
                "Feat-04": "critical",
            },
        )
        self.assertEqual(result["function_level"], "critical")
        self.assertEqual(result["normalization_findings"], [])

    def test_unknown_complexity_defaults_but_emits_finding(self) -> None:
        result = aggregate_function_complexity({"Feat-01": "超大型"}, self.complexity)
        self.assertEqual(result["function_level"], "standard")
        self.assertEqual(result["normalization_findings"][0]["state"], "unknown")
        self.assertEqual(
            result["normalization_findings"][0]["finding"]["rule_id"],
            "SEM-COMPLEXITY-UNKNOWN-001",
        )

    def test_major_semantic_finding_requires_reproducible_evidence(self) -> None:
        invalid = self.load_fixture("semantic-result.json")
        result = invalid["criterion_results"][0]
        result["conclusion"] = "PARTIALLY_SUPPORTED"
        result["evidence"] = []
        result["findings"] = [
            {
                "finding_id": "SEM-aaaaaaaaaaaaaaaaaaaaaaaa",
                "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                "severity": "Major",
                "conclusion": "PARTIALLY_SUPPORTED",
                "message": "Only part of the claim is supported.",
                "recommendation": "Split the claim and add source evidence.",
                "evidence_ids": [],
            }
        ]
        errors = validate_semantic_result(invalid, self.rubric, self.complexity, self.schemas_root)
        self.assertTrue(any("requires reproducible evidence" in item for item in errors))
        self.assertTrue(any("Critical/Major finding requires evidence" in item for item in errors))

    def test_invalid_na_and_excessive_na_are_rejected(self) -> None:
        invalid = self.load_fixture("semantic-result.json")
        correctness = invalid["criterion_results"][0]
        correctness["applicability"] = "NOT_APPLICABLE"
        correctness["conclusion"] = "NOT_APPLICABLE"
        correctness["applicability_reason"] = "Incorrect attempt to skip factual review."
        errors = validate_semantic_result(invalid, self.rubric, self.complexity, self.schemas_root)
        self.assertTrue(any("CORRECTNESS-SOURCE-SUPPORT: N/A is not allowed" in item for item in errors))

        excessive = self.load_fixture("semantic-result.json")
        for criterion_id in ("COMPATIBILITY-API-VERSION", "COMPATIBILITY-SYSTEM-IMPACT"):
            result = next(
                item for item in excessive["criterion_results"] if item["criterion_id"] == criterion_id
            )
            result["applicability"] = "NOT_APPLICABLE"
            result["conclusion"] = "NOT_APPLICABLE"
            result["applicability_reason"] = "Explicit evidence-backed non-impact statement."
        excessive["coverage"].update(
            {"applicable_criteria": 15, "not_applicable_criteria": 3}
        )
        errors = validate_semantic_result(excessive, self.rubric, self.complexity, self.schemas_root)
        self.assertTrue(any("applicable criterion ratio" in item for item in errors))

    def test_score_rejects_wrong_cap_and_static_gate_downgrade(self) -> None:
        invalid = self.load_fixture("score-result.json")
        invalid["caps"]["active_severities"] = ["Major"]
        invalid["gate"] = {"static": "fail", "semantic": "pass", "effective": "pass"}
        errors = validate_score_result(invalid, self.rubric, self.schemas_root)
        self.assertTrue(any("applied cap must be Major/59" in item for item in errors))
        self.assertTrue(any("published_score must be" in item for item in errors))
        self.assertTrue(any("stricter static/semantic gate" in item for item in errors))

    def test_incomplete_tool_execution_cannot_be_publishable(self) -> None:
        invalid = self.load_fixture("score-result.json")
        invalid["execution"]["semantic"] = False
        errors = validate_score_result(invalid, self.rubric, self.schemas_root)
        self.assertTrue(any("tool_execution_completeness must be 0.75" in item for item in errors))
        self.assertTrue(any("publishable must equal all required stages complete" in item for item in errors))
        self.assertTrue(any("admission.status must be NOT_READY" in item for item in errors))

    def test_report_summary_and_versions_must_match_children(self) -> None:
        invalid = self.build_evaluation_report()
        invalid["protocol"]["rubric_version"] = "9.9.0"
        invalid["summary"]["published_score"] = 99
        errors = validate_evaluation_report(invalid, self.rubric, self.complexity, self.schemas_root)
        self.assertTrue(any("rubric version mismatch" in item for item in errors))
        self.assertTrue(any("summary must exactly mirror" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
