from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / "skills" / "ohos-design-arkui-spec-evaluator" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from assemble_semantic_result import (  # noqa: E402
    main as assemble_semantic_main,
    record_finding_evidence_warning,
    record_mapping_warning,
    record_ownership_warning,
    record_contradiction_basis_warning,
    split_aggregation_warnings,
)
from aggregation_warning_policy import (  # noqa: E402
    record_evidence_type_warning,
    split_final_candidate_warnings,
)
from staged_run_support import (  # noqa: E402
    repair_missing_finding_evidence,
)
from validate_staged_run import main as validate_staged_main  # noqa: E402


class AssembleSemanticResultWarningTest(unittest.TestCase):
    def test_assemble_repairs_aggregation_before_validation(self) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            aggregation = {
                "func_id": "01-01-01",
                "defect_ownership": [],
                "criterion_results": [],
            }
            repaired = dict(aggregation)
            candidate = {"func_id": "01-01-01", "criterion_results": []}

            def load(path: Path) -> dict:
                if path.name == "semantic-template.json":
                    return {"criterion_results": []}
                return aggregation

            with (
                patch("assemble_semantic_result.load_object", side_effect=load),
                patch(
                    "assemble_semantic_result.repair_aggregation_contract",
                    return_value=(repaired, ["ownership repaired"]),
                ) as repair,
                patch(
                    "assemble_semantic_result.validate_stage",
                    return_value=([], {}, {}),
                ) as validate_stage,
                patch(
                    "assemble_semantic_result.build_final_candidate",
                    return_value=candidate,
                ),
                patch(
                    "assemble_semantic_result.validate_final_candidate",
                    return_value=[],
                ),
                patch("assemble_semantic_result.write_object") as write_object,
                patch("assemble_semantic_result.update_progress"),
            ):
                result = assemble_semantic_main(["--run-dir", str(run_dir)])

        self.assertEqual(result, 0)
        repair.assert_called_once_with(aggregation)
        self.assertEqual(
            write_object.call_args_list[0].args,
            (run_dir / "aggregation.json", repaired),
        )
        validate_stage.assert_called_once_with(run_dir, "aggregation")

    def test_only_non_structural_ownership_errors_are_warnings(self) -> None:
        blocking, warnings = split_aggregation_warnings([
            "aggregation.defect_ownership[1]: one defect may produce at most one Critical Finding",
            "aggregation.defect_ownership[2]: a Critical Finding must belong to the primary Criterion",
            (
                "aggregation.defect_ownership[3].primary_criterion_id: expected one of "
                "observation owners ['SPEC-RULE-COMPLETENESS']"
            ),
            "aggregation.defect_ownership[3].finding_ids: unknown Finding SEM-x",
            "aggregation.defect_ownership[4].defect_key: not defined by a validated observation",
            (
                "aggregation.criterion_results[CORRECTNESS-SDK-CONTRACT].claim_ids: "
                "not mapped to Criterion: ['design/ADR-1']"
            ),
            (
                "aggregation.notes: service-warning:"
                "FINDING_EVIDENCE_UNKNOWN:{\"findings\":[]}"
            ),
        ])
        self.assertEqual(len(warnings), 5)
        self.assertEqual(len(blocking), 2)

    def test_contradiction_basis_coverage_is_a_warning(self) -> None:
        blocking, warnings = split_aggregation_warnings([
            (
                "aggregation.contradiction_bases: basis defects must cover every "
                "CONTRADICTED Criterion through owned Findings; expected ['C1'], got []"
            ),
            "aggregation.finding_id: required",
        ])
        self.assertEqual(len(blocking), 1)
        self.assertEqual(len(warnings), 1)

    def test_post_correction_ownership_and_duplicate_basis_are_warnings(self) -> None:
        blocking, warnings = split_aggregation_warnings([
            (
                "aggregation.defect_ownership[1].primary_criterion_id: "
                "must own one mapped Finding"
            ),
            (
                "aggregation.contradiction_bases[1].primary_defect_key: "
                "duplicate contradiction basis"
            ),
            (
                "aggregation.contradiction_bases[0].primary_defect_key: "
                "unknown defect 'global.invalid'"
            ),
            (
                "aggregation.contradiction_bases[2].primary_defect_key: "
                "defect does not affect any CONTRADICTED Criterion"
            ),
            "aggregation.finding_id: required",
        ])
        self.assertEqual(blocking, ["aggregation.finding_id: required"])
        self.assertEqual(len(warnings), 4)

    def test_contradiction_basis_warning_deducts_minor_confidence_once(self) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            record_contradiction_basis_warning(run_dir, ["warning-1"])
            record_contradiction_basis_warning(run_dir, ["warning-2"])
            result = json.loads(
                (run_dir / "confidence-result.json").read_text(encoding="utf-8")
            )
        self.assertEqual(result["confidence_score"], 95)
        self.assertEqual(result["deduction_total"], 5)
        self.assertEqual(len(result["minor_violations"]), 1)
        self.assertEqual(
            result["minor_violations"][0]["code"],
            "CONTRADICTION_BASIS_INVALID",
        )

    def test_ownership_warning_deducts_confidence_once(self) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "confidence-result.json").write_text(
                json.dumps({
                    "confidence_score": 100,
                    "confidence_level": "HIGH",
                    "hard_errors": [],
                    "major_violations": [],
                    "minor_violations": [],
                    "total_checks_failed": 0,
                    "deduction_total": 0,
                }),
                encoding="utf-8",
            )
            record_ownership_warning(run_dir, ["warning-1", "warning-2"])
            record_ownership_warning(run_dir, ["warning-3"])
            result = json.loads((run_dir / "confidence-result.json").read_text())
        self.assertEqual(result["confidence_score"], 80)
        self.assertEqual(result["deduction_total"], 20)
        self.assertEqual(len(result["major_violations"]), 1)
        self.assertEqual(result["major_violations"][0]["code"], "OWNERSHIP_CRITICALITY")

    def test_mapping_warning_deducts_minor_confidence_once(self) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "confidence-result.json").write_text(
                json.dumps({
                    "confidence_score": 100,
                    "confidence_level": "HIGH",
                    "hard_errors": [],
                    "major_violations": [],
                    "minor_violations": [],
                    "total_checks_failed": 0,
                    "deduction_total": 0,
                }),
                encoding="utf-8",
            )
            record_mapping_warning(run_dir, ["warning-1"])
            record_mapping_warning(run_dir, ["warning-2"])
            result = json.loads((run_dir / "confidence-result.json").read_text())
        self.assertEqual(result["confidence_score"], 95)
        self.assertEqual(result["deduction_total"], 5)
        self.assertEqual(len(result["minor_violations"]), 1)
        self.assertEqual(
            result["minor_violations"][0]["code"],
            "MAPPING_CLAIM_UNMAPPED",
        )

    def test_finding_evidence_recovery_deducts_major_confidence_once(
        self,
    ) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            record_finding_evidence_warning(run_dir, ["warning-1"])
            record_finding_evidence_warning(run_dir, ["warning-2"])
            result = json.loads(
                (run_dir / "confidence-result.json").read_text(
                    encoding="utf-8"
                )
            )
        self.assertEqual(result["confidence_score"], 80)
        self.assertEqual(result["deduction_total"], 20)
        self.assertEqual(len(result["major_violations"]), 1)
        self.assertEqual(
            result["major_violations"][0]["code"],
            "FINDING_EVIDENCE_UNKNOWN",
        )

    def test_final_validation_downgrades_all_confidence_warnings(self) -> None:
        ownership = (
            "aggregation.defect_ownership[1].primary_criterion_id: expected "
            "one of observation owners ['SPEC-AC-TESTABILITY']"
        )
        mapping = (
            "aggregation.criterion_results[C].claim_ids: not mapped to "
            "Criterion: ['claim-1']"
        )
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            with (
                patch(
                    "validate_staged_run.validate_stage",
                    return_value=([ownership, mapping], {}, {}),
                ),
                patch("validate_staged_run.update_progress") as update_progress,
            ):
                result = validate_staged_main([
                    "--run-dir", str(run_dir),
                    "--stage", "final",
                    "--update-state",
                ])
            confidence = json.loads(
                (run_dir / "confidence-result.json").read_text(encoding="utf-8")
            )
        self.assertEqual(result, 0)
        update_progress.assert_called_once()
        self.assertEqual(confidence["confidence_score"], 75)
        self.assertEqual(confidence["deduction_total"], 25)
        self.assertEqual(
            {item["code"] for item in confidence["major_violations"]},
            {"OWNERSHIP_CRITICALITY"},
        )
        self.assertEqual(
            {item["code"] for item in confidence["minor_violations"]},
            {"MAPPING_CLAIM_UNMAPPED"},
        )

    def test_final_validation_keeps_structural_errors_blocking(self) -> None:
        with TemporaryDirectory() as temporary:
            with patch(
                "validate_staged_run.validate_stage",
                return_value=(["aggregation.finding_id: required"], {}, {}),
            ):
                result = validate_staged_main([
                    "--run-dir", temporary,
                    "--stage", "final",
                ])
        self.assertEqual(result, 1)

    def test_evidence_type_missing_is_a_final_warning(self) -> None:
        # A Criterion whose evidence is present but of the wrong required type is
        # a bounded data-quality gap: the model cannot fabricate a compliant type
        # and the kernel treats it as a non-blocking confidence deduction.
        blocking, warnings = split_final_candidate_warnings([
            (
                "CORRECTNESS-SDK-CONTRACT: evidence must include one of "
                "['sdk_declaration', 'source_citation'], got ['design_location']"
            ),
            "SEM-x: unresolved evidence IDs ['EV-1']",
        ])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(blocking, ["SEM-x: unresolved evidence IDs ['EV-1']"])

    def test_final_validation_downgrades_evidence_type_missing(self) -> None:
        # End-to-end at the final gate: an EVIDENCE_TYPE_MISSING error publishes
        # (result 0) with an EVIDENCE_TYPE_MISSING confidence deduction instead
        # of blocking.
        error = (
            "CORRECTNESS-SDK-CONTRACT: evidence must include one of "
            "['sdk_declaration', 'source_citation'], got ['design_location']"
        )
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            with (
                patch(
                    "validate_staged_run.validate_stage",
                    return_value=([error], {}, {}),
                ),
                patch("validate_staged_run.update_progress"),
            ):
                result = validate_staged_main([
                    "--run-dir", str(run_dir),
                    "--stage", "final",
                    "--update-state",
                ])
            confidence = json.loads(
                (run_dir / "confidence-result.json").read_text(encoding="utf-8")
            )
        self.assertEqual(result, 0)
        self.assertIn(
            "EVIDENCE_TYPE_MISSING",
            {item["code"] for item in confidence["major_violations"]},
        )

    def test_evidence_type_warning_deducts_confidence_once(self) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            record_evidence_type_warning(run_dir, ["warning-1"])
            record_evidence_type_warning(run_dir, ["warning-2"])
            confidence = json.loads(
                (run_dir / "confidence-result.json").read_text(encoding="utf-8")
            )
        self.assertEqual(confidence["confidence_score"], 80)
        self.assertEqual(confidence["deduction_total"], 20)
        self.assertEqual(
            [item["code"] for item in confidence["major_violations"]],
            ["EVIDENCE_TYPE_MISSING"],
        )


class RepairMissingFindingEvidenceTest(unittest.TestCase):
    def _criterion(self, conclusion, evidence_ids, severity="Major"):
        return {
            "func_id": "03-01-02",
            "source_revision": "e429c14fdb8edf3d9d8ea1de59e4fa8492f2205d",
            "criterion_results": [{
                "criterion_id": "DESIGN-FEAT-RUNTIME-COVERAGE",
                "conclusion": conclusion,
                "evidence": [],
                "findings": [{
                    "finding_id": "SEM-" + "a" * 24,
                    "criterion_id": "DESIGN-FEAT-RUNTIME-COVERAGE",
                    "conclusion": conclusion,
                    "severity": severity,
                    "evidence_ids": list(evidence_ids),
                }],
            }],
        }

    def test_empty_evidence_finding_gets_placeholder(self) -> None:
        doc = self._criterion("MISSING", [])
        repaired, changes = repair_missing_finding_evidence(doc)
        self.assertTrue(changes)
        cr = repaired["criterion_results"][0]
        # A placeholder evidence item is inserted and referenced.
        self.assertEqual(len(cr["evidence"]), 1)
        gap = cr["evidence"][0]
        self.assertTrue(gap["evidence_id"].startswith("EV-gap-"))
        self.assertEqual(gap["source_revision"], doc["source_revision"])
        self.assertRegex(gap["content_hash"], r"^sha256:[0-9a-f]{64}$")
        # The placeholder type is one the Criterion accepts.
        self.assertIn(
            gap["type"],
            {"design_location", "spec_location", "source_citation", "registry_entry"},
        )
        self.assertEqual(cr["findings"][0]["evidence_ids"], [gap["evidence_id"]])

    def test_conclusion_and_severity_are_unchanged(self) -> None:
        doc = self._criterion("MISSING", [], severity="Major")
        repaired, _ = repair_missing_finding_evidence(doc)
        cr = repaired["criterion_results"][0]
        self.assertEqual(cr["conclusion"], "MISSING")
        self.assertEqual(cr["findings"][0]["severity"], "Major")

    def test_finding_with_evidence_is_untouched(self) -> None:
        doc = self._criterion("MISSING", ["EV-real"])
        doc["criterion_results"][0]["evidence"] = [{
            "evidence_id": "EV-real", "type": "design_location", "path": "x",
            "source_revision": doc["source_revision"],
            "content_hash": "sha256:" + "0" * 64, "description": "real",
        }]
        repaired, changes = repair_missing_finding_evidence(doc)
        self.assertEqual(changes, [])
        self.assertEqual(
            repaired["criterion_results"][0]["findings"][0]["evidence_ids"],
            ["EV-real"],
        )

    def test_supported_conclusion_is_not_touched(self) -> None:
        # SUPPORTED is not an evidence-required-finding conclusion for this path.
        doc = self._criterion("SUPPORTED", [])
        doc["criterion_results"][0]["findings"] = []
        repaired, changes = repair_missing_finding_evidence(doc)
        self.assertEqual(changes, [])

    def test_repair_is_idempotent(self) -> None:
        doc = self._criterion("MISSING", [])
        once, _ = repair_missing_finding_evidence(doc)
        twice, changes = repair_missing_finding_evidence(once)
        self.assertEqual(changes, [])
        self.assertEqual(
            len(twice["criterion_results"][0]["evidence"]), 1,
        )


if __name__ == "__main__":
    unittest.main()
