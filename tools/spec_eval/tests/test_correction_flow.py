"""Tests for bounded Observation Correction."""

from __future__ import annotations

import json
import unittest

from spec_eval.kernel.errors import TypedError
from spec_eval.kernel.machine_contract import build_correction_machine_contract
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.service.pipeline.correction import (
    apply_deterministic_correction,
    apply_json_patch,
    is_deterministic_error,
    is_model_correction_error,
    typed_error_json_path,
    validate_patch_scope,
)


class CorrectionFlowTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
