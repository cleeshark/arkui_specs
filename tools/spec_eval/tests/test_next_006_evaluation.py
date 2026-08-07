from __future__ import annotations

import copy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from spec_eval.config import EvaluationConfig
from spec_eval.evaluation_validator import (
    build_evaluation_template,
    calculate_semantic_scores,
    function_input_snapshot,
    refresh_draft_evaluations,
    validate_evaluation_manifest,
    validate_function_evaluation,
)
from spec_eval.protocol_validator import validate_protocol
from spec_eval.tests.test_infra_001_003 import TemporaryRepository


class Next006FunctionEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.golden_root = cls.evaluation_root / "golden"
        cls.reviews_root = cls.evaluation_root / "reviews"
        cls.schemas_root = cls.evaluation_root / "schemas"
        cls.manifest = yaml.safe_load(
            (cls.golden_root / "manifest.yaml").read_text(encoding="utf-8")
        )
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)
        cls.config = EvaluationConfig.discover()

    def _confirmed_evaluation(self, func_id: str = "05-01-02") -> dict:
        evaluation = build_evaluation_template(
            self.manifest,
            self.config,
            self.rubric,
            self.complexity,
            func_id,
            "evaluator-a",
        )
        source_revision = evaluation["source_revision"]
        criteria = {
            criterion["id"]: criterion
            for dimension in self.rubric["dimensions"]
            for criterion in dimension["criteria"]
        }
        for index, result in enumerate(evaluation["semantic_result"]["criterion_results"]):
            criterion = criteria[result["criterion_id"]]
            result["conclusion"] = "SUPPORTED"
            result["reason"] = "冻结输入中的文档与证据支持该结论"
            result.pop("missing_evidence", None)
            result["evidence"] = [
                {
                    "evidence_id": f"EV-{index:02d}",
                    "type": criterion["required_evidence_types"][0],
                    "path": "specs/evaluation/rubric.yaml",
                    "source_revision": source_revision,
                    "content_hash": "sha256:" + "0" * 64,
                    "description": "测试用冻结证据",
                }
            ]
        semantic = evaluation["semantic_result"]
        semantic["coverage"]["not_verifiable_criteria"] = 0
        semantic["execution"]["semantic_complete"] = True
        dimensions, raw_score, _ = calculate_semantic_scores(semantic, self.rubric)
        evaluation["scores"] = {
            "dimensions": {key: float(value) for key, value in dimensions.items()},
            "raw_score": float(raw_score),
            "published_score": float(raw_score),
            "confidence": 0.9,
            "admission": "HIGH_QUALITY",
        }
        evaluation["status"] = "confirmed"
        evaluation["evaluator"]["evaluated_at"] = "2026-08-04T15:30:00+08:00"
        evaluation["confirmation"] = {
            "confirmed_by": "confirmer-a",
            "confirmed_at": "2026-08-04T16:00:00+08:00",
            "conclusion": "accepted",
            "notes": [],
        }
        return evaluation

    def test_pilot_manifest_is_reproducible_and_has_single_confirmation(self) -> None:
        self.assertEqual(self.protocol_errors, [])
        errors = validate_evaluation_manifest(
            self.manifest,
            self.config,
            self.complexity,
            self.schemas_root,
            check_revisions=False,
        )
        self.assertEqual(errors, [])
        pilot = self.manifest["pilot_functions"]
        self.assertEqual(len(pilot), 12)
        self.assertGreaterEqual(len({item["l1"]["id"] for item in pilot}), 6)
        self.assertEqual(
            {item["complexity"] for item in pilot},
            {"simple", "standard", "complex", "critical"},
        )
        self.assertEqual(self.manifest["status"], "ready")
        self.assertEqual(self.manifest["confirmation"]["confirmed_by"], "sunfei2021")
        self.assertNotIn("approval", self.manifest)

    def test_repository_has_one_review_file_for_each_pilot_function(self) -> None:
        evaluations = sorted(self.reviews_root.glob("*.yaml"))
        expected = sorted(
            f"{item['func_id']}.yaml" for item in self.manifest["pilot_functions"]
        )
        self.assertEqual([path.name for path in evaluations], expected)

    def test_draft_template_covers_all_rubric_criteria(self) -> None:
        evaluation = build_evaluation_template(
            self.manifest,
            self.config,
            self.rubric,
            self.complexity,
            "03-07-01",
            "evaluator-a",
        )
        self.assertEqual(
            validate_function_evaluation(
                evaluation,
                self.manifest,
                self.rubric,
                self.complexity,
                self.schemas_root,
            ),
            [],
        )
        self.assertEqual(evaluation["status"], "draft")
        self.assertEqual(len(evaluation["semantic_result"]["criterion_results"]), 20)
        self.assertEqual(evaluation["semantic_result"]["coverage"]["not_verifiable_criteria"], 20)
        self.assertIsNone(evaluation["scores"]["raw_score"])

    def test_refresh_drafts_upgrades_only_unconfirmed_reviews(self) -> None:
        manifest = copy.deepcopy(self.manifest)
        manifest["pilot_functions"] = [
            item for item in manifest["pilot_functions"] if item["func_id"] == "03-07-01"
        ]
        with TemporaryDirectory() as temporary:
            reviews_root = Path(temporary)
            path = reviews_root / "03-07-01.yaml"
            evaluation = build_evaluation_template(
                manifest,
                self.config,
                self.rubric,
                self.complexity,
                "03-07-01",
                "sunfei2021",
            )
            evaluation["semantic_result"]["rubric_version"] = "0.1.0"
            path.write_text(
                yaml.safe_dump(evaluation, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            refreshed, skipped = refresh_draft_evaluations(
                reviews_root, manifest, self.config, self.rubric, self.complexity
            )
            migrated = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(refreshed, ["03-07-01"])
            self.assertEqual(skipped, [])
            self.assertEqual(migrated["semantic_result"]["rubric_version"], "0.3.0")
            self.assertEqual(len(migrated["semantic_result"]["criterion_results"]), 20)

            migrated["status"] = "confirmed"
            migrated["notes"].append("must remain untouched")
            path.write_text(
                yaml.safe_dump(migrated, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            refreshed, skipped = refresh_draft_evaluations(
                reviews_root, manifest, self.config, self.rubric, self.complexity
            )
            preserved = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertEqual(refreshed, [])
            self.assertEqual(skipped, ["03-07-01: status=confirmed"])
            self.assertIn("must remain untouched", preserved["notes"])

    def test_stale_review_protocol_requires_regeneration_or_reevaluation(self) -> None:
        evaluation = build_evaluation_template(
            self.manifest,
            self.config,
            self.rubric,
            self.complexity,
            "03-07-01",
            "sunfei2021",
        )
        evaluation["semantic_result"]["rubric_version"] = "0.1.0"
        errors = validate_function_evaluation(
            evaluation,
            self.manifest,
            self.rubric,
            self.complexity,
            self.schemas_root,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("review protocol is stale", errors[0])
        self.assertIn("re-evaluate confirmed reviews", errors[0])

    def test_confirmed_evaluation_is_single_file_and_score_deterministic(self) -> None:
        evaluation = self._confirmed_evaluation()
        self.assertEqual(
            validate_function_evaluation(
                evaluation,
                self.manifest,
                self.rubric,
                self.complexity,
                self.schemas_root,
            ),
            [],
        )
        evaluation["scores"]["dimensions"]["correctness"] = 29
        errors = validate_function_evaluation(
            evaluation,
            self.manifest,
            self.rubric,
            self.complexity,
            self.schemas_root,
        )
        self.assertTrue(any("dimensions.correctness" in item for item in errors))

    def test_confirmed_evaluation_requires_real_judgments_and_confirmation(self) -> None:
        evaluation = build_evaluation_template(
            self.manifest,
            self.config,
            self.rubric,
            self.complexity,
            "05-01-02",
            "evaluator-a",
        )
        evaluation["status"] = "confirmed"
        errors = validate_function_evaluation(
            evaluation,
            self.manifest,
            self.rubric,
            self.complexity,
            self.schemas_root,
        )
        self.assertTrue(any("execution complete" in item for item in errors))
        self.assertTrue(any("every Criterion NOT_VERIFIABLE" in item for item in errors))
        self.assertTrue(any("confirmation.conclusion=accepted" in item for item in errors))

    def test_function_input_fingerprint_changes_with_document_content(self) -> None:
        fixture = TemporaryRepository()
        try:
            before = function_input_snapshot(fixture.config, "05-01-01")["input_fingerprint"]
            fixture.spec_path.write_text(
                fixture.spec_path.read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            after = function_input_snapshot(fixture.config, "05-01-01")["input_fingerprint"]
            self.assertNotEqual(before, after)
        finally:
            fixture.cleanup()

    def test_revision_or_fingerprint_drift_requires_reconfirmation(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["revisions"]["ace_engine"] = "0000000"
        invalid["pilot_functions"][0]["input_fingerprint"] = "sha256:" + "0" * 64
        errors = validate_evaluation_manifest(
            invalid,
            self.config,
            self.complexity,
            self.schemas_root,
            check_revisions=True,
        )
        self.assertTrue(any("input fingerprint changed" in item for item in errors))
        self.assertTrue(any("revision mismatch for ace_engine" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
