from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from spec_eval.function_report import (
    FunctionReportInputError,
    build_function_report,
    write_function_report,
)
from spec_eval.protocol_validator import validate_protocol, validate_evaluation_report
from spec_eval.score import build_score_result


class Next008ReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.schemas_root = cls.evaluation_root / "schemas"
        cls.fixtures_root = Path(__file__).resolve().parent / "fixtures" / "protocol"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)

    def semantic(self) -> dict:
        return json.loads((self.fixtures_root / "semantic-result.json").read_text(encoding="utf-8"))

    @staticmethod
    def static_result() -> dict:
        return {
            "func_id": "05-01-01", "source_revision": "abc123", "tool_version": "0.5.0",
            "rule_version": "0.2.16", "gate": "pass", "findings": [], "metrics": {},
        }

    @staticmethod
    def evidence_manifest() -> dict:
        return {"func_id": "05-01-01", "source_revision": "abc123", "metrics": {
            "claim_count": 0, "resolved_claim_count": 0, "evidence_coverage": 0,
        }, "shards": []}

    def inputs(self) -> tuple[dict, dict, dict, dict, dict]:
        semantic = self.semantic()
        score = build_score_result(
            static_result=self.static_result(), evidence_manifest=self.evidence_manifest(),
            semantic_result=semantic, rubric=self.rubric, complexity_rules=self.complexity,
            schemas_root=self.schemas_root,
        )
        analysis = {
            "schema_version": 1, "analysis_version": "spec-eval-function-analysis@0.1.0",
            "func_id": "05-01-01", "source_revision": "abc123",
            "versions": {
                "static_tool_version": "0.5.0", "static_rule_version": "0.2.16",
                "evaluator_protocol_version": semantic["evaluator_protocol_version"],
                "evaluator_version": semantic["evaluator_version"],
                "rubric_version": semantic["rubric_version"],
                "complexity_rules_version": semantic["complexity_rules_version"],
                "aggregator_protocol_version": score["aggregator_protocol_version"],
                "aggregator_version": score["aggregator_version"],
            },
            "score_summary": {
                "raw_score": score["raw_score"], "published_score": score["published_score"],
                "confidence": score["confidence"]["score"], "gate": score["gate"]["effective"],
                "admission": score["admission"]["status"],
            },
            "top_remediations": [{
                "rank": 1, "priority": "P1", "severity": "Major",
                "recommendation": "Close the traceability gap.", "feat_ids": ["Feat-01"],
                "finding_ids": ["SEM-111111111111111111111111"],
            }],
            "feat_risks": [{
                "feat_id": "Feat-01", "risk_level": "Major",
                "finding_counts": {"Critical": 0, "Major": 1, "Minor": 0, "Info": 0},
                "claims": {"support_rate": 0.5}, "traceability": {"closure_rate": 0.25},
            }],
            "function_shared_risk": {"risk_level": "None", "finding_count": 0},
        }
        stability = {
            "schema_version": 1, "stability_version": "spec-eval-stability@0.1.1",
            "status": "complete",
            "func_id": "05-01-01", "source_revision": "abc123",
            "selected_run": {"run_id": semantic["run_id"]},
            "runs": [{"run_id": semantic["run_id"], "raw_score": score["raw_score"]}],
            "score_statistics": {"count": 3, "range": 2, "population_stddev": 0.82},
            "consensus_summary": {"consensus_count": 20, "criterion_count": 20},
            "outlier_run_ids": [],
        }
        return self.static_result(), semantic, score, analysis, stability

    def test_builds_schema_valid_json_and_deterministic_markdown(self) -> None:
        values = self.inputs()
        first = build_function_report(
            static_result=values[0], semantic_result=values[1], score_result=values[2],
            analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
            complexity_rules=self.complexity, schemas_root=self.schemas_root,
        )
        second = build_function_report(
            static_result=values[0], semantic_result=values[1], score_result=values[2],
            analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
            complexity_rules=self.complexity, schemas_root=self.schemas_root,
        )
        self.assertEqual(first, second)
        self.assertEqual(validate_evaluation_report(first[0], self.rubric, self.complexity, self.schemas_root), [])
        self.assertIn("Top remediation items", first[1])
        self.assertIn("Feat-01", first[1])
        self.assertIn("Stability", first[1])

    def test_rejects_selected_run_mismatch(self) -> None:
        values = list(self.inputs())
        values[4] = copy.deepcopy(values[4])
        values[4]["selected_run"]["run_id"] = "other-run"
        with self.assertRaisesRegex(FunctionReportInputError, "selected semantic run"):
            build_function_report(
                static_result=values[0], semantic_result=values[1], score_result=values[2],
                analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
                complexity_rules=self.complexity, schemas_root=self.schemas_root,
            )

    def test_insufficient_runs_render_as_na_instead_of_zero_statistics(self) -> None:
        values = list(self.inputs())
        values[4] = {
            "schema_version": 1,
            "stability_version": "spec-eval-stability@0.1.1",
            "status": "insufficient_runs",
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "provided_run_count": 1,
            "required_run_count": 3,
            "selected_run": {"run_id": values[1]["run_id"]},
            "score_statistics": {"status": "not_computed", "count": 1},
            "consensus_summary": {"status": "not_computed"},
            "criterion_consensus": [],
            "outlier_run_ids": [],
        }
        _, markdown = build_function_report(
            static_result=values[0], semantic_result=values[1], score_result=values[2],
            analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
            complexity_rules=self.complexity, schemas_root=self.schemas_root,
        )
        self.assertIn("Status: **N/A — insufficient runs**", markdown)
        self.assertIn("Runs provided: 1", markdown)
        self.assertIn("Criterion consensus: N/A", markdown)
        self.assertNotIn("Criterion consensus: 0/0", markdown)

    def test_writes_json_and_markdown(self) -> None:
        values = self.inputs()
        report, markdown = build_function_report(
            static_result=values[0], semantic_result=values[1], score_result=values[2],
            analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
            complexity_rules=self.complexity, schemas_root=self.schemas_root,
        )
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            json_path, md_path = root / "evaluation-report.json", root / "function-report.md"
            write_function_report(json_path=json_path, markdown_path=md_path, report=report, markdown=markdown)
            self.assertEqual(json.loads(json_path.read_text(encoding="utf-8")), report)
            self.assertEqual(md_path.read_text(encoding="utf-8"), markdown)

    def test_kernel_confidence_renders_reliability_and_defects(self) -> None:
        values = self.inputs()
        kernel_confidence = {
            "confidence_score": 75,
            "confidence_level": "MEDIUM",
            "deduction_total": 25,
            "total_checks_failed": 2,
            "hard_errors": [],
            "major_violations": [{
                "layer": "MAJOR", "code": "FINDING_MULTI_OWNED",
                "criterion_id": "CORRECTNESS-SOURCE-SUPPORT", "deduction": 20,
                "message": "finding owned by multiple criteria", "path": "aggregation.notes",
            }],
            "minor_violations": [{
                "layer": "MINOR", "code": "NOTE_FORMAT",
                "criterion_id": "", "deduction": 5, "message": "note not prefixed", "path": "x",
            }],
        }
        report, markdown = build_function_report(
            static_result=values[0], semantic_result=values[1], score_result=values[2],
            analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
            complexity_rules=self.complexity, schemas_root=self.schemas_root,
            confidence_result=kernel_confidence,
        )
        # Kernel confidence is a Markdown-only companion; it never enters the
        # frozen evaluation-report.json schema.
        self.assertEqual(validate_evaluation_report(report, self.rubric, self.complexity, self.schemas_root), [])
        self.assertNotIn("kernel", json.dumps(report).lower())
        self.assertIn("Kernel confidence: **75 / 100** (MEDIUM)", markdown)
        self.assertIn("## Kernel confidence (report reliability)", markdown)
        self.assertIn("Report defects (validation deductions)", markdown)
        self.assertIn("FINDING_MULTI_OWNED", markdown)
        self.assertIn("Evidence confidence:", markdown)

    def test_kernel_confidence_absent_is_backward_compatible(self) -> None:
        values = self.inputs()
        _, markdown = build_function_report(
            static_result=values[0], semantic_result=values[1], score_result=values[2],
            analysis_result=values[3], stability_result=values[4], rubric=self.rubric,
            complexity_rules=self.complexity, schemas_root=self.schemas_root,
        )
        self.assertNotIn("Kernel confidence", markdown)
        self.assertNotIn("Report defects", markdown)


if __name__ == "__main__":
    unittest.main()
