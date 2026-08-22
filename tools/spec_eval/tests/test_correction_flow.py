"""Tests for bounded Observation Correction."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from spec_eval.kernel.errors import TypedError
from spec_eval.kernel.machine_contract import build_correction_machine_contract
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline.correction import (
    apply_deterministic_correction,
    apply_json_patch,
    is_deterministic_error,
    is_model_correction_error,
    resolve_typed_error_json_path,
    typed_error_json_path,
    validate_patch_scope,
)
from spec_eval.service.pipeline.judgment_flow import JudgmentFlow


class CorrectionFlowTest(unittest.TestCase):
    def test_primary_criterion_is_added_to_observation_criteria_without_model(self) -> None:
        document = {
            "observations": [{
                "local_outcome": "MISSING",
                "criterion_ids": ["DESIGN-IMPACT-COVERAGE"],
                "defect_key": "missing.build_config_entry",
                "primary_criterion_id": "SPEC-TRACEABILITY",
            }],
        }
        error = TypedError(
            "DEFECT_KEYS_INVALID",
            "observation.observations[0].primary_criterion_id",
            entity_type="defect",
            entity_id="missing.build_config_entry",
        )
        corrected, changes, unresolved = apply_deterministic_correction(
            document, [error]
        )
        self.assertFalse(unresolved)
        self.assertEqual(
            corrected["observations"][0]["criterion_ids"],
            ["DESIGN-IMPACT-COVERAGE", "SPEC-TRACEABILITY"],
        )
        self.assertTrue(changes)

    def test_defect_key_is_mapped_from_claim_owner_without_model(self) -> None:
        document = {
            "claim_reviews": [{
                "claim_id": "design/RISK-290",
                "local_outcome": "MISSING",
                "defect_keys": ["risk.cross-platform-mitigation-unbounded"],
            }],
            "observations": [{
                "claim_ids": ["design/RISK-290"],
                "local_outcome": "MISSING",
                "defect_key": "design.state-recovery-coverage-incomplete",
            }],
        }
        error = TypedError(
            "DEFECT_KEY_UNDEFINED",
            "observation.claim_reviews[0].defect_keys",
            entity_type="defect",
            entity_id="risk.cross-platform-mitigation-unbounded",
        )
        corrected, changes, unresolved = apply_deterministic_correction(
            document, [error]
        )
        self.assertFalse(unresolved)
        self.assertEqual(
            corrected["claim_reviews"][0]["defect_keys"],
            ["design.state-recovery-coverage-incomplete"],
        )
        self.assertTrue(changes)

    def test_json_patch_decodes_transport_values(self) -> None:
        result = apply_json_patch(
            {"claim_reviews": [{"defect_keys": []}]},
            [{
                "op": "replace",
                "path": "/claim_reviews/0/defect_keys",
                "value": json.dumps(["defect.one"]),
            }],
        )
        self.assertEqual(result["claim_reviews"][0]["defect_keys"], ["defect.one"])

    def test_patch_scope_blocks_identity_changes(self) -> None:
        violations = validate_patch_scope(
            [{"op": "replace", "path": "/func_id", "value": json.dumps("x")}],
            allowed_paths=["/claim_reviews/0/defect_keys"],
            immutable_paths=["/func_id"],
        )
        self.assertTrue(violations)

    def test_typed_error_path_becomes_json_pointer(self) -> None:
        self.assertEqual(
            typed_error_json_path("observation.claim_reviews[12].defect_keys"),
            "/claim_reviews/12/defect_keys",
        )
        self.assertEqual(
            typed_error_json_path("$.evidence_declarations[0].path"),
            "/evidence_declarations/0/path",
        )
        self.assertEqual(
            typed_error_json_path(
                "aggregation.criterion_results[FUNCTION-FEAT-COVERAGE].claim_ids"
            ),
            "/criterion_results/FUNCTION-FEAT-COVERAGE/claim_ids",
        )

    def test_named_criterion_path_resolves_and_applies_to_real_list(self) -> None:
        document = {
            "criterion_results": [
                {
                    "criterion_id": "OTHER",
                    "evidence_ids": ["EV-other"],
                },
                {
                    "criterion_id": "SPEC-SCOPE-BOUNDARY",
                    "evidence_ids": ["EV-old"],
                },
            ],
        }
        error = TypedError(
            "CRITERION_EVIDENCE_UNKNOWN",
            "aggregation.criterion_results[SPEC-SCOPE-BOUNDARY].evidence_ids",
            entity_type="criterion",
            entity_id="SPEC-SCOPE-BOUNDARY",
        )
        path = resolve_typed_error_json_path(document, error)
        self.assertEqual(path, "/criterion_results/1/evidence_ids")
        corrected = apply_json_patch(document, [{
            "op": "replace",
            "path": path,
            "value": json.dumps(["EV-new"]),
        }])
        self.assertEqual(
            corrected["criterion_results"][1]["evidence_ids"],
            ["EV-new"],
        )
        self.assertEqual(
            corrected["criterion_results"][0]["evidence_ids"],
            ["EV-other"],
        )

    def test_aggregation_correction_prompt_uses_resolved_numeric_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            candidate_path = run_dir / "aggregation.json.candidate"
            candidate_path.write_text(json.dumps({
                "criterion_results": [
                    {"criterion_id": "OTHER", "evidence_ids": []},
                    {
                        "criterion_id": "SPEC-SCOPE-BOUNDARY",
                        "evidence_ids": ["EV-unknown"],
                    },
                ],
            }), encoding="utf-8")
            work = C.WorkItemInput(
                job_id="job",
                func_id="01-01-01",
                run_id="run-1",
                work_item_id="aggregation",
                work_item={
                    "observation_type": "aggregation",
                    "input_resources": [],
                },
                run_dir=str(run_dir),
                input_paths=(),
                executor_result_path=str(run_dir / "aggregation.result.json"),
                repo_root=str(run_dir),
                skill_version="0.3.0",
                protocol_version="0.2.0",
                prompt_extras={"payload_kind": "aggregation"},
            )
            error = TypedError(
                "CRITERION_EVIDENCE_UNKNOWN",
                "aggregation.criterion_results[SPEC-SCOPE-BOUNDARY].evidence_ids",
                entity_type="criterion",
                entity_id="SPEC-SCOPE-BOUNDARY",
            ).to_dict()
            flow = JudgmentFlow(
                ctx=SimpleNamespace(run_dir=run_dir),
                executor=None,
                jobs=None,
                events=None,
            )
            correction_work = flow._correct_work_input(
                work, candidate_path, [error], {"evidence_catalog": []},
            )
            expected = ["/criterion_results/1/evidence_ids"]
            self.assertEqual(
                correction_work.prompt_extras["correction_contract"]["allowed_paths"],
                expected,
            )
            self.assertEqual(
                correction_work.prompt_extras["machine_contract"]["allowed_paths"],
                expected,
            )

    def test_finding_wildcard_resolves_from_typed_error_entity(self) -> None:
        document = {
            "criterion_results": [{
                "criterion_id": "DESIGN-FEAT-RUNTIME-COVERAGE",
                "findings": [
                    {"finding_id": "F-1", "key": "first", "severity": "Minor"},
                    {"finding_id": "F-2", "key": "second", "severity": "Minor"},
                ],
            }],
        }
        path = resolve_typed_error_json_path(document, TypedError(
            "SEVERITY_BELOW_FLOOR",
            "aggregation.criterion_results[DESIGN-FEAT-RUNTIME-COVERAGE].findings[].severity",
            entity_type="finding",
            entity_id="F-2",
        ))
        self.assertEqual(path, "/criterion_results/0/findings/1/severity")

    def test_named_selector_resolution_is_fail_closed(self) -> None:
        error = TypedError(
            "CRITERION_EVIDENCE_UNKNOWN",
            "aggregation.criterion_results[MISSING].evidence_ids",
            entity_type="criterion",
            entity_id="MISSING",
        )
        with self.assertRaisesRegex(ValueError, "matched 0 rows"):
            resolve_typed_error_json_path(
                {"criterion_results": [{"criterion_id": "OTHER"}]},
                error,
            )
        with self.assertRaisesRegex(ValueError, "matched 2 rows"):
            resolve_typed_error_json_path(
                {"criterion_results": [
                    {"criterion_id": "MISSING"},
                    {"criterion_id": "MISSING"},
                ]},
                error,
            )

    def test_evidence_error_is_model_correctable_but_mapping_is_not(self) -> None:
        self.assertTrue(is_model_correction_error({"code": "EVIDENCE_KEY_UNKNOWN"}))
        self.assertFalse(is_deterministic_error({"code": "EVIDENCE_KEY_UNKNOWN"}))
        self.assertTrue(is_deterministic_error({"code": "OBSERVATION_FIELD_INVALID"}))
        self.assertFalse(is_model_correction_error({"code": "OBSERVATION_FIELD_INVALID"}))
        # Unknown validator codes are fail-closed and never delegated to a
        # model until explicitly classified as semantic/evidence.
        self.assertTrue(is_deterministic_error({"code": "NEW_UNCLASSIFIED_CODE"}))

    def test_correction_schema_is_generated_and_compact(self) -> None:
        schema = build_envelope_schema("correction")
        payload = schema["$defs"]["correctionPayload"]
        self.assertEqual(payload["required"], ["patches", "notes"])
        self.assertEqual(
            schema["$defs"]["jsonPatch"]["properties"]["value"]["type"],
            "string",
        )

    def test_correction_machine_contract_does_not_expand_observation_contract(self) -> None:
        contract = build_correction_machine_contract(
            payload_kind="observation",
            typed_errors=[{"code": "DEFECT_KEY_UNDEFINED", "path": "/claim_reviews/0/defect_keys"}],
            allowed_paths=["/claim_reviews/0/defect_keys"],
        )
        self.assertEqual(contract["output_format"], "json_patch")
        self.assertNotIn("expected_claim_ids", contract)
        self.assertNotIn("required_checks", contract)

    def test_aggregation_correction_contract_is_scoped(self) -> None:
        contract = build_correction_machine_contract(
            payload_kind="aggregation",
            observation_profile="aggregation",
            typed_errors=[{
                "code": "CRITERION_EVIDENCE_UNKNOWN",
                "path": "aggregation.criterion_results[C].evidence_ids",
            }],
            allowed_paths=["/criterion_results/0/evidence_ids"],
        )
        self.assertIn(
            "Keep patches local to the named Aggregation Criterion/Policy/Finding paths.",
            contract["rules"],
        )
        self.assertIn(
            "Do not modify Observation source facts, non-target Criteria, or derived Finding IDs.",
            contract["rules"],
        )


if __name__ == "__main__":
    unittest.main()
