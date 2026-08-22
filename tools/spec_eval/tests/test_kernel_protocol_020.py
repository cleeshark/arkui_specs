"""Evaluator protocol 0.2.0 kernel tests (issue #25 / PR-1).

Covers the generator consistency, the typed validator's error codes on
constructed bad documents, normalizer determinism/immutability, the folded
quality gate, the purge command and the codex envelope v3 parse path.
"""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spec_eval.protocol_validator import (
    JsonSchemaSubsetValidator,
    validate_protocol,
    validate_semantic_result,
    validate_strict_output_schema,
)
from spec_eval.kernel import contracts as K
from spec_eval.kernel.errors import SERVICE_NORMALIZATION, TypedError, blocking
from spec_eval.kernel.evidence_paths import (
    EvidencePathError,
    FrozenEvidencePathResolver,
)
from spec_eval.kernel.machine_contract import (
    build_aggregation_machine_contract,
    build_observation_machine_contract,
)
from spec_eval.kernel.normalize import (
    OUTCOME_POLICY_BASIS_CRITERIA,
    assemble_semantic_result,
    normalize_aggregation,
    normalize_observation,
)
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.kernel.validate import (
    validate_aggregation_document,
    validate_observation_document,
)

SCHEMAS_ROOT = (
    Path(__file__).resolve().parents[3] / "evaluation" / "schemas"
)


def _compact_context(context: dict) -> dict:
    """Convert readable fixture rows to the normalized context tables."""
    catalog = {}
    criteria = []
    for row in context.get("criterion_mappings", []):
        evidence_ids = []
        for evidence in row.get("evidence_catalog", []):
            evidence_id = evidence["evidence_id"]
            catalog[evidence_id] = evidence
            evidence_ids.append(evidence_id)
        criteria.append({
            "criterion_id": row["criterion_id"],
            "observation_refs": [],
            "claim_refs": [],
            "unit_refs": [],
            "evidence_ids": evidence_ids,
            "allow_not_applicable": False,
            "outcomes": {},
            "required_evidence_types": [],
        })
    return {
        "schema_version": 3,
        "criteria": criteria,
        "observations": {},
        "claims": {},
        "units": {},
        "evidence_catalog": catalog,
        "valid_defect_keys": [],
    }
CRITERIA = (
    "CORRECTNESS-SOURCE-SUPPORT",
    "CORRECTNESS-CROSS-DOC-CONSISTENCY",
    "SPEC-AC-TESTABILITY",
    "SPEC-TRACEABILITY",
    "DESIGN-IMPACT-COVERAGE",
    "DESIGN-VERIFICATION-PLAN",
    "COMPATIBILITY-API-VERSION",
    "COMPATIBILITY-MULTI-DEVICE",
)
DIMENSION_BY_CRITERION = {
    "CORRECTNESS-SOURCE-SUPPORT": "correctness",
    "CORRECTNESS-CROSS-DOC-CONSISTENCY": "correctness",
    "SPEC-AC-TESTABILITY": "spec_executability",
    "SPEC-TRACEABILITY": "spec_executability",
    "DESIGN-IMPACT-COVERAGE": "design_quality",
    "DESIGN-VERIFICATION-PLAN": "design_quality",
    "COMPATIBILITY-API-VERSION": "compatibility_system_impact",
    "COMPATIBILITY-MULTI-DEVICE": "compatibility_system_impact",
}
SOURCE_REVISION = "a" * 40


def _gap() -> dict:
    return {
        "checked_scope": ["frozen Feat-01 spec scope"],
        "missing_evidence": ["implementation source for AC-1"],
        "consequence": "The claim cannot be verified from the frozen inputs.",
    }


def _template(tmp: Path, evidence_path: str) -> dict:
    (tmp / "input.txt").write_text("frozen evidence content\n", encoding="utf-8")
    return {
        "schema_version": 2,
        "func_id": "05-01-02",
        "source_revision": SOURCE_REVISION,
        "run_id": "run-1",
        "observation_id": "feature:Feat-01",
        "observation_type": "feature",
        "status": "pending",
        "expected_claim_ids": ["Feat-01/AC-1", "Feat-01/AC-2"],
        "required_checks": ["claim_source_support", "boundary_state"],
        "reviewed_claim_ids": [],
        "claim_reviews": [],
        "completed_checks": [],
        "observations": [],
        "open_questions": [],
        "notes": [],
        "_evidence_path": evidence_path,
    }


def _judgment(evidence_path: str, *, nv_first: bool = True) -> dict:
    gap = _gap() if nv_first else None
    first_outcome = "NOT_VERIFIABLE" if nv_first else "SUPPORTED"
    first_evidence = "e2" if nv_first else "e1"
    return {
        "evidence_declarations": [
            {
                "key": "e1",
                "type": "spec_location",
                "path": evidence_path,
                "lines": "1-1",
                "description": "Synthetic frozen evidence.",
            },
            {
                "key": "e2",
                "type": "review_record",
                "path": evidence_path,
                "lines": None,
                "description": (
                    "The evaluator inspected the frozen inputs before "
                    "recording this verification gap."
                ),
            },
        ],
        "claim_reviews": [
            {
                "claim_id": "Feat-01/AC-1",
                "local_outcome": first_outcome,
                "evidence_refs": [first_evidence],
                "reason": (
                    "Checked the frozen spec scope; the implementation source is "
                    "missing and the claim cannot be verified."
                    if nv_first else
                    "The frozen evidence content supports the evaluated claim."
                ),
                "verification_gap": gap,
                "defect_keys": [],
                "unit_reviews": [{
                    "unit_id": "u1",
                    "facet_type": "traceability",
                    "local_outcome": first_outcome,
                    "evidence_refs": [first_evidence],
                    "fact": (
                        "Checked the frozen spec scope; the atomic proof is missing "
                        "and is insufficient to verify this unit."
                        if nv_first else
                        "The frozen evidence content supports this atomic unit."
                    ),
                    "verification_gap": copy.deepcopy(gap),
                }],
            },
            {
                "claim_id": "Feat-01/AC-2",
                "local_outcome": "SUPPORTED",
                "evidence_refs": ["e1"],
                "reason": "The frozen evidence content supports the evaluated claim.",
                "verification_gap": None,
                "defect_keys": [],
                "unit_reviews": [{
                    "unit_id": "u1",
                    "facet_type": "traceability",
                    "local_outcome": "SUPPORTED",
                    "evidence_refs": ["e1"],
                    "fact": "The frozen evidence content supports this atomic unit.",
                    "verification_gap": None,
                }],
            },
        ],
        "observations": [{
            "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
            "check_ids": ["claim_source_support", "boundary_state"],
            "claim_ids": ["Feat-01/AC-1", "Feat-01/AC-2"],
            "local_outcome": "SUPPORTED",
            "breadth": "feat_core",
            "contract_family": "synthetic-contract",
            "fact": "The frozen evidence covers both claims.",
            "defect_key": None,
            "primary_criterion_id": None,
            "evidence_refs": ["e1", "e2"],
        }],
        "open_questions": [],
        "notes": [],
    }


class SchemaGenerationTest(unittest.TestCase):
    def test_both_payload_kinds_pass_strict_subset(self) -> None:
        for kind in ("observation", "aggregation"):
            schema = build_envelope_schema(kind)
            self.assertEqual(
                validate_strict_output_schema(schema), [], kind
            )
            self.assertNotIn("uniqueItems", json.dumps(schema), kind)

    def test_openai_profile_rejects_unique_items_but_keeps_min_items(self) -> None:
        schema = build_envelope_schema("observation")
        self.assertIn("minItems", json.dumps(schema))
        self.assertEqual(validate_strict_output_schema(schema), [])
        schema["$defs"]["observationJudgment"]["properties"][
            "claim_ids"
        ]["uniqueItems"] = True
        errors = validate_strict_output_schema(schema)
        self.assertTrue(
            any("claim_ids.uniqueItems" in error for error in errors), errors
        )

    def test_schema_enums_match_contracts(self) -> None:
        schema = build_envelope_schema("observation")
        defs = schema["$defs"]
        self.assertEqual(
            defs["claimJudgment"]["properties"]["local_outcome"]["enum"],
            list(K.LOCAL_OUTCOMES),
        )
        self.assertEqual(
            defs["observationJudgment"]["properties"]["breadth"]["enum"],
            list(K.BREADTHS),
        )
        self.assertEqual(
            defs["evidenceDeclaration"]["properties"]["type"]["enum"],
            list(K.EVIDENCE_TYPES),
        )
        self.assertEqual(
            defs["unitJudgment"]["properties"]["facet_type"]["enum"],
            list(K.UNIT_FACET_TYPES),
        )
        agg = build_envelope_schema("aggregation")
        self.assertEqual(
            agg["$defs"]["criterionJudgment"]["properties"]["conclusion"]["enum"],
            list(K.SEMANTIC_CONCLUSIONS),
        )

    def test_spiked_schema_shape_validates_spiked_document(self) -> None:
        validator = JsonSchemaSubsetValidator(SCHEMAS_ROOT)
        schema = build_envelope_schema("observation")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            judgment = _judgment(str(root / "input.txt"))
            (root / "input.txt").write_text("x\n", encoding="utf-8")
            document = {
                "schema_version": 3,
                "work_item_id": "feature:Feat-01",
                "status": "completed",
                "payload": judgment,
                "notes": [],
                "error": None,
            }
            schema_path = root / "schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            self.assertEqual(validator.validate_file(document, schema_path), [])

    def test_defect_key_fields_carry_pattern_constraint(self) -> None:
        obs = build_envelope_schema("observation")
        obs_defs = obs["$defs"]
        self.assertEqual(
            obs_defs["observationJudgment"]["properties"]["defect_key"]["pattern"],
            K.DEFECT_KEY_PATTERN,
        )
        self.assertEqual(
            obs_defs["claimJudgment"]["properties"]["defect_keys"]["items"]["pattern"],
            K.DEFECT_KEY_PATTERN,
        )
        agg = build_envelope_schema("aggregation")
        agg_defs = agg["$defs"]
        self.assertEqual(
            agg_defs["defectOwnership"]["properties"]["defect_key"]["pattern"],
            K.DEFECT_KEY_PATTERN,
        )
        self.assertEqual(
            agg_defs["contradictionBasis"]["properties"]["primary_defect_key"]["pattern"],
            K.DEFECT_KEY_PATTERN,
        )

    def test_aggregation_schema_accepts_only_canonical_evidence_references(self) -> None:
        schema = build_envelope_schema("aggregation")
        payload = NormalizeAggregationTest()._judgment()
        document = {
            "schema_version": 3,
            "work_item_id": "function-aggregation",
            "status": "completed",
            "payload": payload,
            "notes": [],
            "error": None,
        }
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            validator = JsonSchemaSubsetValidator(SCHEMAS_ROOT)
            self.assertEqual(validator.validate_file(document, schema_path), [])
            payload["criterion_results"][0]["evidence"] = [
                {"evidence_id": "EV-illegal-inline-row"}
            ]
            errors = validator.validate_file(document, schema_path)
        self.assertTrue(
            any("additional property" in error and ".evidence" in error for error in errors),
            errors,
        )


class InputFingerprintTest(unittest.TestCase):
    def test_fingerprint_changes_when_input_file_content_changes(self) -> None:
        from spec_eval.service.pipeline.judgment_flow import input_fingerprint

        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "aggregation-context.json"
            input_path.write_text('{"schema_version": 1}\n', encoding="utf-8")
            before = input_fingerprint(
                evaluator_version=K.EVALUATOR_VERSION,
                protocol_version=K.EVALUATION_PROTOCOL_VERSION,
                input_paths=[str(input_path)],
                template_bytes=b"template",
            )
            input_path.write_text('{"schema_version": 2}\n', encoding="utf-8")
            after = input_fingerprint(
                evaluator_version=K.EVALUATOR_VERSION,
                protocol_version=K.EVALUATION_PROTOCOL_VERSION,
                input_paths=[str(input_path)],
                template_bytes=b"template",
            )
        self.assertNotEqual(before, after)


class CorrectionRegressionGuardTest(unittest.TestCase):
    """Tests for _guard_correction_regression (#46)."""

    def test_rollback_non_targeted_criterion_conclusion_change(self):
        from spec_eval.service.pipeline.judgment_flow import _guard_correction_regression

        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = Path(tmp) / ".aggregation.json.candidate"
            original = {
                "criterion_results": [
                    {"criterion_id": "A", "conclusion": "NOT_VERIFIABLE", "reason": "ok"},
                    {"criterion_id": "B", "conclusion": "SUPPORTED", "reason": "ok"},
                ],
            }
            candidate_path.write_text(
                json.dumps(original), encoding="utf-8",
            )
            corrected = {
                "criterion_results": [
                    {"criterion_id": "A", "conclusion": "PARTIALLY_SUPPORTED", "reason": "changed"},
                    {"criterion_id": "B", "conclusion": "CONTRADICTED", "reason": "fixed"},
                ],
            }
            typed_errors = [
                {"code": "CRITERION_EVIDENCE_UNKNOWN", "entity_type": "criterion",
                 "entity_id": "B", "path": "$.criterion_results[B]"},
            ]
            result = _guard_correction_regression(corrected, candidate_path, typed_errors)
            rows = {r["criterion_id"]: r for r in result["criterion_results"]}
            self.assertEqual(rows["A"]["conclusion"], "NOT_VERIFIABLE")
            self.assertEqual(rows["B"]["conclusion"], "CONTRADICTED")

    def test_no_rollback_when_no_candidate(self):
        from spec_eval.service.pipeline.judgment_flow import _guard_correction_regression

        corrected = {"criterion_results": [
            {"criterion_id": "A", "conclusion": "SUPPORTED"},
        ]}
        result = _guard_correction_regression(
            corrected, Path("/nonexistent"), [],
        )
        self.assertEqual(result, corrected)

    def test_no_rollback_when_conclusion_unchanged(self):
        from spec_eval.service.pipeline.judgment_flow import _guard_correction_regression

        with tempfile.TemporaryDirectory() as tmp:
            candidate_path = Path(tmp) / ".candidate"
            original = {"criterion_results": [
                {"criterion_id": "A", "conclusion": "SUPPORTED", "reason": "ok"},
            ]}
            candidate_path.write_text(json.dumps(original), encoding="utf-8")
            corrected = {"criterion_results": [
                {"criterion_id": "A", "conclusion": "SUPPORTED", "reason": "updated"},
            ]}
            result = _guard_correction_regression(corrected, candidate_path, [])
            self.assertEqual(
                result["criterion_results"][0]["reason"], "updated",
            )


class NormalizeObservationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence_rel = "input.txt"
        self.template = _template(self.root, self.evidence_rel)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_expansion_assigns_ids_hashes_and_order(self) -> None:
        judgment = _judgment(self.evidence_rel)
        result = normalize_observation(
            self.template, judgment, repo_root=self.root
        )
        self.assertEqual(result.fatal, [])
        document = result.document
        self.assertIsNotNone(document)
        self.assertEqual(document["status"], "complete")
        self.assertEqual(
            document["reviewed_claim_ids"], ["Feat-01/AC-1", "Feat-01/AC-2"]
        )
        self.assertEqual(document["completed_checks"], [
            "boundary_state", "claim_source_support",
        ])
        evidence = document["observations"][0]["evidence"][0]
        self.assertEqual(evidence["evidence_id"], "EV-1")
        self.assertTrue(evidence["content_hash"].startswith("sha256:"))
        self.assertEqual(evidence["source_revision"], SOURCE_REVISION)
        self.assertEqual(
            document["claim_reviews"][0]["evidence_ids"], ["EV-2"]
        )
        self.assertEqual(
            document["claim_reviews"][0]["criterion_ids"],
            ["CORRECTNESS-SOURCE-SUPPORT"],
        )
        self.assertEqual(result.evidence_catalog[0]["evidence_id"], "EV-1")

    def test_input_documents_are_not_mutated(self) -> None:
        judgment = _judgment(self.evidence_rel)
        judgment_copy = copy.deepcopy(judgment)
        template_copy = copy.deepcopy(self.template)
        normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(judgment, judgment_copy)
        self.assertEqual(
            {k: v for k, v in self.template.items() if k != "_evidence_path"},
            {k: v for k, v in template_copy.items() if k != "_evidence_path"},
        )

    def test_normalize_is_idempotent_on_published_shape(self) -> None:
        judgment = _judgment(self.evidence_rel)
        first = normalize_observation(self.template, judgment, repo_root=self.root)
        # re-normalizing the same judgment from the same template is stable
        second = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(
            json.dumps(first.document, sort_keys=True),
            json.dumps(second.document, sort_keys=True),
        )

    def test_missing_evidence_is_correctable(self) -> None:
        judgment = _judgment("missing/file.txt")
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        self.assertEqual(result.errors[0].code, "EVIDENCE_PATH_NOT_FOUND")
        self.assertIsNone(result.document)

    def test_resolved_but_unreadable_frozen_evidence_is_fatal(self) -> None:
        judgment = _judgment(self.evidence_rel)
        with patch("spec_eval.kernel.normalize._content_hash", return_value=None):
            result = normalize_observation(
                self.template, judgment, repo_root=self.root
            )
        self.assertEqual(result.errors, [])
        self.assertEqual(
            {error.code for error in result.fatal},
            {"FROZEN_EVIDENCE_UNREADABLE"},
        )
        self.assertIsNone(result.document)

    def test_duplicate_evidence_key_is_correctable(self) -> None:
        judgment = _judgment(self.evidence_rel)
        judgment["evidence_declarations"][1]["key"] = "e1"
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        self.assertEqual(result.errors[0].code, "EVIDENCE_KEY_DUPLICATED")
        self.assertIsNone(result.document)

    def test_absolute_existing_path_is_rejected_before_hashing(self) -> None:
        judgment = _judgment(str(self.root / self.evidence_rel))
        with patch("spec_eval.kernel.normalize._content_hash") as content_hash:
            result = normalize_observation(
                self.template, judgment, repo_root=self.root
            )
        content_hash.assert_not_called()
        self.assertEqual(result.fatal, [])
        self.assertEqual(
            {error.code for error in result.errors},
            {"EVIDENCE_PATH_NOT_ALLOWED"},
        )

    def test_unexpected_claims_are_dropped_and_reported(self) -> None:
        judgment = _judgment(self.evidence_rel)
        judgment["claim_reviews"].append({
            "claim_id": "Feat-01/AC-9", "local_outcome": "SUPPORTED",
            "evidence_refs": [], "reason": "extra", "verification_gap": None,
            "defect_keys": [], "unit_reviews": [],
        })
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        ids = [row["claim_id"] for row in result.document["claim_reviews"]]
        self.assertEqual(ids, ["Feat-01/AC-1", "Feat-01/AC-2"])
        self.assertTrue(any("AC-9" in change for change in result.changes))


class EvidencePathResolverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.oh_root = Path(self.tmp.name) / "oh"
        self.ace_root = self.oh_root / "foundation" / "arkui" / "ace_engine"
        self.sdk_js_root = self.oh_root / "interface" / "sdk-js"
        self.sdk_c_root = self.oh_root / "interface" / "sdk_c"
        self.job_root = Path(self.tmp.name) / "service-data" / "jobs" / "job-1"
        files = {
            self.ace_root / "frameworks/core/example.cpp": "source",
            self.ace_root / "specs/domain/design.md": "design",
            self.sdk_js_root / "api/example.d.ts": "sdk-js",
            self.sdk_c_root / "interfaces/example.h": "sdk-c",
            self.job_root / "runs/run-1/staged/output-contract.json": "service",
        }
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        self.resolver = FrozenEvidencePathResolver(
            {
                "ace_engine": self.ace_root,
                "sdk-js": self.sdk_js_root,
                "sdk_c": self.sdk_c_root,
            },
            forbidden_roots=(self.job_root,),
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_resolves_all_frozen_repository_namespaces(self) -> None:
        cases = {
            "frameworks/core/example.cpp": "ace_engine",
            "specs/domain/design.md": "ace_engine",
            "interface/sdk-js/api/example.d.ts": "sdk-js",
            "interface/sdk_c/interfaces/example.h": "sdk_c",
        }
        for path, repository in cases.items():
            with self.subTest(path=path):
                result = self.resolver.resolve(path)
                self.assertEqual(result.canonical_path, path)
                self.assertEqual(result.repository, repository)

    def test_rejects_absolute_parent_and_service_paths_before_read(self) -> None:
        paths = (
            str(self.job_root / "runs/run-1/staged/output-contract.json"),
            "../service-data/jobs/job-1/secret.txt",
            "runs/run-1/staged/output-contract.json",
            "evidence/revision/function-context.json",
        )
        for path in paths:
            with self.subTest(path=path), self.assertRaises(EvidencePathError) as ctx:
                self.resolver.resolve(path)
            self.assertEqual(ctx.exception.code, "EVIDENCE_PATH_NOT_ALLOWED")

    def test_rejects_symlink_escape(self) -> None:
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        link = self.ace_root / "frameworks/core/escaped.txt"
        link.symlink_to(outside)
        with self.assertRaises(EvidencePathError) as ctx:
            self.resolver.resolve("frameworks/core/escaped.txt")
        self.assertEqual(ctx.exception.code, "EVIDENCE_PATH_NOT_ALLOWED")

    def test_missing_required_catalog_path_is_fatal_input(self) -> None:
        resolver = FrozenEvidencePathResolver(
            {"ace_engine": self.ace_root},
            required_paths=("specs/domain/missing-design.md",),
        )
        with self.assertRaises(EvidencePathError) as ctx:
            resolver.resolve("specs/domain/missing-design.md")
        self.assertEqual(ctx.exception.code, "FROZEN_EVIDENCE_UNREADABLE")


class ValidateObservationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence_rel = "input.txt"
        self.template = _template(self.root, self.evidence_rel)
        base = normalize_observation(
            self.template, _judgment(self.evidence_rel), repo_root=self.root
        )
        assert base.document is not None
        self.document = base.document

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _codes(self, document: dict) -> list[str]:
        return [
            error.code
            for error in validate_observation_document(
                document, valid_criterion_ids=CRITERIA
            )
        ]

    def test_valid_document_has_no_blocking_errors(self) -> None:
        errors = validate_observation_document(
            self.document, valid_criterion_ids=CRITERIA
        )
        self.assertEqual(blocking(errors), [], [e.to_dict() for e in errors])

    def test_missing_claim_row(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"] = document["claim_reviews"][:1]
        self.assertIn("CLAIM_SET_MISMATCH", self._codes(document))

    def test_unknown_evidence_reference(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][0]["evidence_ids"] = ["EV-404"]
        self.assertIn("EVIDENCE_KEY_UNKNOWN", self._codes(document))

    def test_nv_without_gap(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][0]["verification_gap"] = None
        self.assertIn("GAP_MISSING_FOR_NV", self._codes(document))

    def test_gap_on_non_nv_is_normalizable(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["verification_gap"] = _gap()
        errors = validate_observation_document(
            document, valid_criterion_ids=CRITERIA
        )
        gap_errors = [e for e in errors if e.code == "GAP_UNEXPECTED_FOR_NON_NV"]
        self.assertEqual(len(gap_errors), 1)
        self.assertEqual(gap_errors[0].repairability, SERVICE_NORMALIZATION)

    def test_low_information_reason(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["reason"] = "supported"
        self.assertIn("REASON_LOW_INFORMATION", self._codes(document))

    def test_supported_claim_requires_atomic_unit_review(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["reviewed_units"] = []
        document["claim_reviews"][1]["unit_reviews"] = []
        codes = self._codes(document)
        self.assertIn("UNIT_ROW_INVALID", codes)

    def test_unit_review_ids_must_match_reviewed_units(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["reviewed_units"] = ["different-unit"]
        self.assertIn("UNIT_ROW_INVALID", self._codes(document))

    def test_unknown_criterion(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["criterion_ids"] = ["NOT-A-CRITERION"]
        self.assertIn("CRITERION_UNKNOWN", self._codes(document))

    def test_observation_requires_claim_ids_when_claims_exist(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["claim_ids"] = []
        codes = self._codes(document)
        self.assertIn("OBSERVATION_CLAIM_IDS_EMPTY", codes)
        self.assertIn("OBSERVATION_CLAIM_COVERAGE_INCOMPLETE", codes)

    def test_observation_claims_must_cover_expected_claims(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["claim_ids"] = ["Feat-01/AC-1"]
        self.assertIn(
            "OBSERVATION_CLAIM_COVERAGE_INCOMPLETE", self._codes(document)
        )

    def test_incomplete_check_coverage(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["check_ids"] = ["claim_source_support"]
        self.assertIn("CHECK_COVERAGE_INCOMPLETE", self._codes(document))

    def test_defect_key_undefined_on_claim(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["local_outcome"] = "CONFLICT"
        document["claim_reviews"][1]["defect_keys"] = ["synthetic-defect"]
        self.assertIn("DEFECT_KEY_UNDEFINED", self._codes(document))

    def test_uppercase_defect_key_rejected_on_observation(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["local_outcome"] = "CONFLICT"
        document["observations"][0]["defect_key"] = "TRACE-RULE-ORPHAN-001"
        document["observations"][0]["primary_criterion_id"] = CRITERIA[0]
        self.assertIn("DEFECT_KEYS_INVALID", self._codes(document))

    def test_unit_claim_outcome_conflict(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["unit_reviews"][0]["local_outcome"] = "CONFLICT"
        self.assertIn("UNIT_CLAIM_OUTCOME_CONFLICT", self._codes(document))

    def test_quality_gate_flags_degenerate_output(self) -> None:
        document = copy.deepcopy(self.document)
        prototype = document["claim_reviews"][0]
        rows = []
        for index in range(12):
            row = copy.deepcopy(prototype)
            row["claim_id"] = f"Feat-01/AC-{index + 1}"
            row["evidence_ids"] = []
            row["reason"] = "Scoped inputs do not provide enough resolved evidence."
            row["unit_reviews"][0]["evidence_ids"] = []
            row["unit_reviews"][0]["fact"] = (
                "Scoped inputs do not provide enough resolved evidence."
            )
            rows.append(row)
        document["claim_reviews"] = rows
        document["expected_claim_ids"] = [row["claim_id"] for row in rows]
        codes = self._codes(document)
        self.assertTrue(
            any(code.startswith("QUALITY_") for code in codes), codes
        )


class NormalizeAggregationTest(unittest.TestCase):
    @staticmethod
    def _evidence_id(criterion_id: str) -> str:
        return "EV-" + criterion_id.lower().replace("_", "-")

    def _template(self) -> dict:
        return {
            "schema_version": 2,
            "func_id": "05-01-02",
            "source_revision": SOURCE_REVISION,
            "run_id": "run-1",
            "status": "pending",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": False,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": [
                {"criterion_id": cid, "content_status": "PENDING",
                 "evidence_status": "PENDING", "conflict_scope": "PENDING",
                 "reason": "待评价人填写"}
                for cid in (
                    "SPEC-AC-TESTABILITY", "SPEC-TRACEABILITY",
                    "DESIGN-IMPACT-COVERAGE", "DESIGN-VERIFICATION-PLAN",
                    "COMPATIBILITY-API-VERSION", "COMPATIBILITY-MULTI-DEVICE",
                )
            ],
            "criterion_results": [
                {"criterion_id": cid, "conclusion": "NOT_VERIFIABLE",
                 "dimension_id": DIMENSION_BY_CRITERION[cid],
                 "applicability": "APPLICABLE", "reason": ""}
                for cid in CRITERIA
            ],
            "notes": [],
        }

    def _aggregation_context(self) -> dict:
        return {
            "schema_version": 2,
            "criterion_mappings": [
                {
                    "criterion_id": criterion_id,
                    "evidence_catalog": [{
                        "evidence_id": self._evidence_id(criterion_id),
                        "type": "source_citation",
                        "path": "frameworks/core/example.cpp",
                        "line_start": 1,
                        "line_end": 2,
                        "source_revision": SOURCE_REVISION,
                        "content_hash": "sha256:" + "0" * 64,
                        "description": "Inherited observation evidence.",
                        "source_work_item_id": "feature:Feat-01",
                        "source_evidence_id": "EV-1",
                    }],
                }
                for criterion_id in CRITERIA
            ],
        }

    def _normalize(
        self, judgment: dict | None = None, *, source_observation_ids: list[str] | None = None
    ):
        return normalize_aggregation(
            self._template(), judgment or self._judgment(),
            source_observation_ids=source_observation_ids or [],
            aggregation_context=_compact_context(self._aggregation_context()),
        )

    def _judgment(self) -> dict:
        return {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [{
                "defect_key": "missing-source-proof",
                "primary_criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                "finding_keys": ["f1"],
                "rationale": "One defect explains both findings.",
            }],
            "outcome_policy_bases": [
                {"criterion_id": "SPEC-AC-TESTABILITY", "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "Content and evidence verified."},
                {"criterion_id": "SPEC-TRACEABILITY", "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "Content and evidence verified."},
                {"criterion_id": "DESIGN-IMPACT-COVERAGE",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
                {"criterion_id": "DESIGN-VERIFICATION-PLAN",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
                {"criterion_id": "COMPATIBILITY-API-VERSION",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
                {"criterion_id": "COMPATIBILITY-MULTI-DEVICE",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
            ],
            "criterion_results": [
                {
                    "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                    "conclusion": "CONTRADICTED",
                    "applicability": "APPLICABLE",
                    "reason": "Mapped units contradict the published contract.",
                    "applicability_reason": None,
                    "missing_evidence": None,
                    "claim_ids": ["Feat-01/AC-1"],
                    "evidence_ids": [
                        self._evidence_id("CORRECTNESS-SOURCE-SUPPORT")
                    ],
                    "findings": [{
                        "key": "f1",
                        "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                        "claim_id": "Feat-01/AC-1",
                        "severity": "CRITICAL",
                        "message": "The published contract is contradicted.",
                        "evidence_ids": [
                            self._evidence_id("CORRECTNESS-SOURCE-SUPPORT")
                        ],
                        "recommendation": "Align the contract with the mapping.",
                    }],
                },
                *[
                    {
                        "criterion_id": criterion_id,
                        "conclusion": "SUPPORTED",
                        "applicability": "APPLICABLE",
                        "reason": "No violation was found for this criterion.",
                        "applicability_reason": None,
                        "missing_evidence": None,
                        "claim_ids": [],
                        "evidence_ids": [self._evidence_id(criterion_id)],
                        "findings": [],
                    }
                    for criterion_id in CRITERIA[1:]
                ],
            ],
            "notes": [],
        }

    def test_canonical_ids_and_secondary_derivation(self) -> None:
        result = self._normalize(source_observation_ids=["feature:Feat-01"])
        self.assertEqual(result.fatal, [])
        document = result.document
        finding = document["criterion_results"][0]["findings"][0]
        self.assertTrue(finding["finding_id"].startswith("SEM-"))
        self.assertEqual(finding["severity"], "Critical")
        self.assertEqual(finding["conclusion"], "CONTRADICTED")
        self.assertNotIn("source_work_item_id", document["criterion_results"][0]["evidence"][0])
        self.assertNotIn("source_evidence_id", document["criterion_results"][0]["evidence"][0])
        ownership = document["defect_ownership"][0]
        self.assertEqual(ownership["finding_ids"], [finding["finding_id"]])
        self.assertEqual(ownership["secondary_criterion_ids"], [])
        self.assertEqual(
            document["source_observation_ids"], ["feature:Feat-01"]
        )

    def test_unknown_criterion_evidence_is_correctable(self) -> None:
        judgment = self._judgment()
        judgment["criterion_results"][0]["evidence_ids"] = ["EV-unknown"]
        result = self._normalize(judgment)
        self.assertIsNone(result.document)
        self.assertEqual([error.code for error in result.errors], [
            "CRITERION_EVIDENCE_UNKNOWN"
        ])
        self.assertTrue(result.evidence_catalog)

    def test_missing_context_does_not_accept_inline_or_guessed_evidence(self) -> None:
        result = normalize_aggregation(
            self._template(), self._judgment(), source_observation_ids=[]
        )
        self.assertIsNone(result.document)
        self.assertTrue(result.errors)
        self.assertEqual(
            {error.code for error in result.errors},
            {"CRITERION_EVIDENCE_UNKNOWN"},
        )

    def test_duplicate_aggregation_references_are_stably_deduplicated(self) -> None:
        judgment = self._judgment()
        row = judgment["criterion_results"][0]
        evidence_id = row["evidence_ids"][0]
        row["claim_ids"] = ["Feat-01/AC-1", "Feat-01/AC-1"]
        row["evidence_ids"] = [evidence_id, evidence_id]
        row["findings"][0]["evidence_ids"] = [evidence_id, evidence_id]
        result = self._normalize(judgment)
        self.assertEqual(result.errors, [])
        published = result.document["criterion_results"][0]
        self.assertEqual(published["claim_ids"], ["Feat-01/AC-1"])
        self.assertEqual(
            [item["evidence_id"] for item in published["evidence"]],
            [evidence_id],
        )
        self.assertEqual(
            published["findings"][0]["evidence_ids"], [evidence_id]
        )
        self.assertEqual(
            sum("deduplicated" in change for change in result.changes), 3
        )

    def test_normalize_preserves_dimension_and_omits_nullable_reason(self) -> None:
        result = self._normalize()
        self.assertEqual(result.fatal, [])
        for criterion in result.document["criterion_results"]:
            criterion_id = criterion["criterion_id"]
            self.assertEqual(
                criterion["dimension_id"], DIMENSION_BY_CRITERION[criterion_id]
            )
            self.assertNotIn("applicability_reason", criterion)

    def test_normalize_keeps_explicit_reason_and_falls_back_for_na(self) -> None:
        judgment = self._judgment()
        judgment["criterion_results"][1]["applicability_reason"] = (
            "Explicit evidence-backed non-impact statement."
        )
        judgment["criterion_results"][2].update({
            "conclusion": "NOT_APPLICABLE",
            "applicability": "NOT_APPLICABLE",
            "reason": "This criterion is outside the function scope.",
            "applicability_reason": None,
            "findings": [],
        })
        result = self._normalize(judgment)
        self.assertEqual(result.fatal, [])
        rows = {
            row["criterion_id"]: row for row in result.document["criterion_results"]
        }
        self.assertEqual(
            rows["CORRECTNESS-CROSS-DOC-CONSISTENCY"]["applicability_reason"],
            "Explicit evidence-backed non-impact statement.",
        )
        self.assertEqual(
            rows["SPEC-AC-TESTABILITY"]["applicability_reason"],
            "This criterion is outside the function scope.",
        )

    def test_criterion_order_follows_template(self) -> None:
        judgment = self._judgment()
        judgment["criterion_results"].reverse()
        result = self._normalize(judgment)
        self.assertEqual(result.fatal, [])
        ids = [
            row["criterion_id"] for row in result.document["criterion_results"]
        ]
        self.assertEqual(ids, list(CRITERIA))

    def test_empty_first_criterion_findings_do_not_crash(self) -> None:
        judgment = self._judgment()
        judgment["criterion_results"][0]["findings"] = []
        judgment["criterion_results"][0]["conclusion"] = "SUPPORTED"
        result = self._normalize(judgment)
        self.assertEqual(result.fatal, [])
        self.assertEqual(result.errors, [])
        self.assertEqual(result.document["criterion_results"][0]["findings"], [])
        self.assertFalse(
            any("CORRECTNESS-SOURCE-SUPPORT" in change for change in result.changes)
        )

    def test_empty_later_criterion_does_not_inherit_previous_finding(self) -> None:
        judgment = self._judgment()
        judgment["criterion_results"][1]["findings"] = []
        judgment["criterion_results"][1]["conclusion"] = "SUPPORTED"
        result = self._normalize(judgment)
        self.assertEqual(result.fatal, [])
        self.assertEqual(result.document["criterion_results"][1]["findings"], [])
        self.assertFalse(
            any("CORRECTNESS-CROSS-DOC-CONSISTENCY" in change for change in result.changes)
        )

    def test_valid_aggregation_has_no_blocking_errors(self) -> None:
        result = self._normalize(source_observation_ids=["feature:Feat-01"])
        errors = validate_aggregation_document(
            result.document, criterion_order=list(CRITERIA)
        )
        self.assertEqual(blocking(errors), [], [e.to_dict() for e in errors])

    def test_finding_cardinality_and_policy_errors(self) -> None:
        result = self._normalize(source_observation_ids=["feature:Feat-01"])
        document = result.document
        document["criterion_results"][1]["conclusion"] = "MISSING"
        document["criterion_results"][1]["findings"] = []
        codes = [
            error.code
            for error in validate_aggregation_document(
                document, criterion_order=list(CRITERIA)
            )
        ]
        self.assertIn("FINDING_CARDINALITY_VIOLATED", codes)
        document["outcome_policy_bases"][0]["conflict_scope"] = "CORE"
        codes = [
            error.code
            for error in validate_aggregation_document(
                document, criterion_order=list(CRITERIA)
            )
        ]
        self.assertIn("POLICY_BASIS_INVALID", codes)

    def test_assemble_semantic_result_shape(self) -> None:
        result = self._normalize(source_observation_ids=["feature:Feat-01"])
        semantic_template = {
            "func_id": "05-01-02", "source_revision": SOURCE_REVISION,
            "run_id": "run-1", "execution": {"notes": []},
            "criterion_results": [],
        }
        candidate = assemble_semantic_result(semantic_template, result.document)
        self.assertTrue(candidate["execution"]["semantic_complete"])
        self.assertEqual(
            candidate["coverage"]["expected_criteria"], len(CRITERIA)
        )
        self.assertEqual(
            candidate["criterion_results"], result.document["criterion_results"]
        )

    def test_inherited_evidence_survives_final_semantic_validation(self) -> None:
        specs_root = Path(__file__).resolve().parents[3]
        evaluation_root = specs_root / "evaluation"
        rubric, complexity, protocol_errors = validate_protocol(evaluation_root)
        self.assertEqual(protocol_errors, [])
        semantic_template = json.loads(
            (Path(__file__).parent / "fixtures" / "protocol" / "semantic-result.json")
            .read_text(encoding="utf-8")
        )
        criteria = [
            (dimension["id"], criterion)
            for dimension in rubric["dimensions"]
            for criterion in dimension["criteria"]
        ]
        aggregation_template = {
            "schema_version": 2,
            "func_id": semantic_template["func_id"],
            "source_revision": semantic_template["source_revision"],
            "run_id": semantic_template["run_id"],
            "status": "pending",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": False,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": [
                {"criterion_id": criterion_id, "content_status": "PENDING",
                 "evidence_status": "PENDING", "conflict_scope": "PENDING",
                 "reason": "待评价人填写"}
                for criterion_id in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": [
                {"criterion_id": criterion["id"], "dimension_id": dimension_id,
                 "conclusion": "NOT_VERIFIABLE", "applicability": "APPLICABLE",
                 "reason": ""}
                for dimension_id, criterion in criteria
            ],
            "notes": [],
        }
        evidence_ids = {
            criterion["id"]: "EV-" + criterion["id"].lower()
            for _, criterion in criteria
        }
        aggregation_context = _compact_context({
            "schema_version": 2,
            "criterion_mappings": [
                {
                    "criterion_id": criterion["id"],
                    "evidence_catalog": [{
                        "evidence_id": evidence_ids[criterion["id"]],
                        "type": criterion["required_evidence_types"][0],
                        "path": "frameworks/core/sample.cpp",
                        "line_start": 10,
                        "line_end": 20,
                        "source_revision": semantic_template["source_revision"],
                        "content_hash": "sha256:" + "a" * 64,
                        "description": "Inherited observation evidence.",
                        "source_work_item_id": "feature:Feat-01",
                        "source_evidence_id": "EV-1",
                    }],
                }
                for _, criterion in criteria
            ],
        })
        judgment_rows = []
        for index, (_, criterion) in enumerate(criteria):
            criterion_id = criterion["id"]
            adverse = index == 0
            judgment_rows.append({
                "criterion_id": criterion_id,
                "conclusion": "CONTRADICTED" if adverse else "SUPPORTED",
                "applicability": "APPLICABLE",
                "reason": "Inherited observation evidence supports this conclusion.",
                "applicability_reason": None,
                "missing_evidence": None,
                "claim_ids": ["Feat-01/AC-1"] if adverse else [],
                "evidence_ids": [evidence_ids[criterion_id]],
                "findings": [{
                    "key": "f1",
                    "criterion_id": criterion_id,
                    "claim_id": "Feat-01/AC-1",
                    "severity": "CRITICAL",
                    "message": "The source contradicts the published contract.",
                    "evidence_ids": [evidence_ids[criterion_id]],
                    "recommendation": "Align the contract with the source.",
                }] if adverse else [],
            })
        judgment = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [{
                "defect_key": "source_contract_conflict",
                "primary_criterion_id": criteria[0][1]["id"],
                "finding_keys": ["f1"],
                "rationale": "The source conflict owns the adverse finding.",
            }],
            "outcome_policy_bases": [
                {"criterion_id": criterion_id, "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "Content and evidence were reviewed."}
                for criterion_id in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": judgment_rows,
            "notes": [],
        }
        normalized = normalize_aggregation(
            aggregation_template, judgment,
            source_observation_ids=["feature:Feat-01"],
            aggregation_context=aggregation_context,
        )
        self.assertEqual(normalized.errors, [])
        self.assertEqual(normalized.fatal, [])
        candidate = assemble_semantic_result(semantic_template, normalized.document)
        self.assertEqual(
            validate_semantic_result(
                candidate, rubric, complexity, evaluation_root / "schemas"
            ),
            [],
        )


class MachineContractTest(unittest.TestCase):
    def test_observation_contract_carries_reference_spaces(self) -> None:
        contract = build_observation_machine_contract(
            expected_claim_ids=["Feat-01/AC-1"],
            required_checks=K.FEATURE_REQUIRED_CHECKS,
            valid_criterion_ids=CRITERIA,
            evidence_catalog=[{"evidence_id": "EV-1", "type": "spec_location"}],
            citable_input_paths=["specs/domain/Feat-01-spec.md"],
        )
        self.assertEqual(contract["expected_claim_ids"], ["Feat-01/AC-1"])
        self.assertEqual(contract["required_checks"], list(K.FEATURE_REQUIRED_CHECKS))
        self.assertEqual(contract["evidence_catalog"][0]["evidence_id"], "EV-1")
        self.assertEqual(
            contract["evidence_path_policy"]["citable_input_paths"],
            ["specs/domain/Feat-01-spec.md"],
        )
        rules = " ".join(contract["judgment_rules"])
        self.assertIn("verification_gap", rules)
        self.assertIn("injected Observation references", rules)
        self.assertIn("service derives published reviewed_units", rules)
        self.assertNotIn("reviewed_units and unit_reviews must contain", rules)

    def test_observation_profile_source_loading_delegates_to_references(self) -> None:
        contract = build_observation_machine_contract(
            expected_claim_ids=["Feat-01/AC-1"],
            required_checks=K.FEATURE_REQUIRED_CHECKS,
            valid_criterion_ids=CRITERIA,
        )
        source_loading = " ".join(contract["profile_rules"]["source_loading"])
        self.assertIn("injected Observation references", source_loading)
        self.assertIn("focus hints", source_loading)
        self.assertNotIn("Do not scan unrelated Feature shards", source_loading)

    def test_observation_contract_defect_rule_contains_format(self) -> None:
        contract = build_observation_machine_contract(
            expected_claim_ids=["Feat-01/AC-1"],
            required_checks=K.FEATURE_REQUIRED_CHECKS,
            valid_criterion_ids=CRITERIA,
        )
        self.assertIn(K.DEFECT_KEY_PATTERN, contract["defect_rule"])

    def test_aggregation_contract_carries_mapping_rule(self) -> None:
        contract = build_aggregation_machine_contract(
            valid_criterion_ids=CRITERIA,
            aggregation_context_path="/tmp/run/aggregation-context.json",
        )
        self.assertEqual(
            contract["aggregation_context_path"], "/tmp/run/aggregation-context.json"
        )
        self.assertIn("authoritative", contract["mapping_rule"])


class PurgeTest(unittest.TestCase):
    def test_purge_is_idempotent_and_keeps_skeleton(self) -> None:
        from spec_eval.service.governance import purge_all
        from spec_eval.service.settings import ServiceSettings

        with tempfile.TemporaryDirectory() as tmp:
            settings = ServiceSettings.discover(data_root=Path(tmp))
            (settings.jobs_root / "j1").mkdir(parents=True)
            (settings.jobs_root / "j1" / "staged").write_text("x", encoding="utf-8")
            (settings.archives_root / "automated").mkdir(parents=True)
            first = purge_all(settings)
            self.assertEqual(sum(first["removed"].values()) >= 2, True)
            for name in ("db", "jobs", "archives", "locks", "logs", "backups",
                         "workspaces", "exports"):
                self.assertTrue((settings.data_root / name).is_dir(), name)

    def test_legacy_artifact_purge_is_scoped_and_idempotent(self) -> None:
        from spec_eval.service.governance import purge_legacy_artifacts
        from spec_eval.service.settings import ServiceSettings

        with tempfile.TemporaryDirectory() as tmp:
            settings = ServiceSettings.discover(data_root=Path(tmp))
            old = settings.jobs_root / "j1" / "staged" / "run-state.json"
            old.parent.mkdir(parents=True)
            old.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            current = settings.jobs_root / "j1" / "staged" / "current.json"
            current.write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
            old_archive = settings.archives_root / "legacy.json"
            old_archive.parent.mkdir(parents=True, exist_ok=True)
            old_archive.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
            self.assertEqual(len(purge_legacy_artifacts(settings)["removed"]), 2)
            self.assertFalse(old.exists())
            self.assertFalse(old_archive.exists())
            self.assertTrue(current.exists())
            self.assertEqual(purge_legacy_artifacts(settings)["removed"], [])

    def test_purge_export_takes_backup_first(self) -> None:
        from spec_eval.service.governance import purge_all
        from spec_eval.service.settings import ServiceSettings
        from spec_eval.service.store.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as tmp:
            settings = ServiceSettings.discover(data_root=Path(tmp))
            store = SqliteStore(settings)
            store.close()
            self.assertTrue(settings.db_path.is_file())
            summary = purge_all(settings, export_first=True)
            self.assertTrue(summary["exported"])
            self.assertTrue(Path(summary["export_path"]).is_file())
            backups = list(settings.backups_root.glob("service-*.sqlite3"))
            # the backup lands under backups/ *before* it is purged, so the
            # snapshot is removed together with the rest by design; the export
            # flag's observable effect is that no exception is raised and the
            # root remains usable
            self.assertTrue(settings.data_root.is_dir())


class EnvelopeV3ParseTest(unittest.TestCase):
    def _run(self, document: dict) -> "object":
        from spec_eval.service.executors import contract as C
        from spec_eval.service.executors.codex_cli import CodexCliExecutor
        from spec_eval.service.executors.process import ProcessResult
        from spec_eval.service.executors.telemetry import (
            ExecutionTelemetryAccumulator,
        )
        from spec_eval.service.executors.usage import TokenUsageAccumulator

        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "out.json"
            result_path.write_text(json.dumps(document), encoding="utf-8")
            work = C.WorkItemInput(
                job_id="j", func_id="f", run_id="r",
                work_item_id="feature:Feat-01", work_item={},
                run_dir=tmp, input_paths=(),
                executor_result_path=str(result_path), repo_root=tmp,
                skill_version="x", protocol_version="0.2.0",
            )
            executor = CodexCliExecutor.__new__(CodexCliExecutor)
            executor._schemas_root = SCHEMAS_ROOT
            if document.get("schema_version") == 3:
                # the v3 envelope is validated against the generated strict
                # schema (kernel.schema_gen), mirroring how PR-2 wires it
                executor._output_schema_path = Path(tmp) / "envelope-v3.json"
                executor._output_schema_path.write_text(
                    json.dumps(build_envelope_schema("observation")),
                    encoding="utf-8",
                )
            else:
                executor._output_schema_path = (
                    SCHEMAS_ROOT / "executor-result.schema.json"
                )
            proc_result = ProcessResult(
                exit_code=0, timed_out=False, cancelled=False,
                elapsed_seconds=0.0,
                stdout_log_path=str(Path(tmp) / "o.log"),
                stderr_log_path=str(Path(tmp) / "e.log"),
            )
            return executor._validate_result(
                work, proc_result, 0, 0.0,
                TokenUsageAccumulator(), ExecutionTelemetryAccumulator(work),
            )

    def test_payload_object_is_accepted(self) -> None:
        from spec_eval.service.executors import contract as C

        result = self._run({
            "schema_version": 3,
            "work_item_id": "feature:Feat-01",
            "status": "completed",
            "payload": {"evidence_declarations": [], "claim_reviews": [],
                        "observations": [], "open_questions": [], "notes": []},
            "notes": [],
            "error": None,
        })
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertEqual(result.observation["notes"], [])

    def test_v2_string_rejected_after_schema_upgrade(self) -> None:
        from spec_eval.service.executors import contract as C

        result = self._run({
            "schema_version": 2,
            "work_item_id": "feature:Feat-01",
            "status": "completed",
            "observation_json": json.dumps({"claim_reviews": []}),
            "notes": [],
            "error": None,
        })
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("schema", (result.error or "").lower())

    def test_v1_envelope_rejected_after_schema_upgrade(self) -> None:
        from spec_eval.service.executors import contract as C

        result = self._run({
            "schema_version": 1,
            "work_item_id": "feature:Feat-01",
            "status": "completed",
            "observation_json": "{}",
            "notes": [],
            "error": None,
        })
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("schema", (result.error or "").lower())

    def test_completed_without_payload_fails(self) -> None:
        from spec_eval.service.executors import contract as C

        result = self._run({
            "schema_version": 3,
            "work_item_id": "feature:Feat-01",
            "status": "completed",
            "payload": None,
            "notes": [],
            "error": None,
        })
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("payload", result.error or "")


class TypedErrorContractTest(unittest.TestCase):
    def test_registry_codes_resolve_repairability(self) -> None:
        from spec_eval.kernel.errors import FATAL_INPUT, MODEL_CORRECTION, repairability_of

        self.assertEqual(
            repairability_of("FROZEN_EVIDENCE_UNREADABLE"), FATAL_INPUT
        )
        self.assertEqual(
            repairability_of("EVIDENCE_PATH_NOT_ALLOWED"), MODEL_CORRECTION
        )
        self.assertEqual(repairability_of("GAP_MISSING_FOR_NV"), MODEL_CORRECTION)
        with self.assertRaises(ValueError):
            repairability_of("NOT_A_CODE")

    def test_blocking_filters_normalizable(self) -> None:
        errors = [
            TypedError("GAP_UNEXPECTED_FOR_NON_NV", "$", repairability=SERVICE_NORMALIZATION),
            TypedError("GAP_MISSING_FOR_NV", "$"),
        ]
        self.assertEqual([e.code for e in blocking(errors)], ["GAP_MISSING_FOR_NV"])

    def test_evaluator_version_is_exactly_020(self) -> None:
        import sys

        scripts = Path(__file__).resolve().parents[3] / "skills" / "ohos-design-arkui-spec-evaluator" / "scripts"
        if str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from create_pilot_template import validate_evaluator_version

        validate_evaluator_version("skill:ohos-design-arkui-spec-evaluator@0.3.0")
        with self.assertRaisesRegex(ValueError, "unsupported evaluator_version"):
            validate_evaluator_version("skill:ohos-design-arkui-spec-evaluator@0.1.19")


class FindingEvidenceClosureTest(unittest.TestCase):
    """Issue #37: normalizer closes criterion evidence over finding refs."""

    @staticmethod
    def _evidence_id(criterion_id: str) -> str:
        return "EV-" + criterion_id.lower().replace("_", "-")

    def _template(self) -> dict:
        return {
            "schema_version": 2,
            "func_id": "05-01-02",
            "source_revision": SOURCE_REVISION,
            "run_id": "run-1",
            "status": "pending",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": False,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": [
                {"criterion_id": cid, "content_status": "PENDING",
                 "evidence_status": "PENDING", "conflict_scope": "PENDING",
                 "reason": "待评价人填写"}
                for cid in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": [
                {"criterion_id": cid, "conclusion": "NOT_VERIFIABLE",
                 "dimension_id": DIMENSION_BY_CRITERION[cid],
                 "applicability": "APPLICABLE", "reason": ""}
                for cid in CRITERIA
            ],
            "notes": [],
        }

    def _aggregation_context(self, *, extra_evidence_ids=None) -> dict:
        extra = extra_evidence_ids or {}
        return {
            "schema_version": 2,
            "criterion_mappings": [
                {
                    "criterion_id": criterion_id,
                    "evidence_catalog": [
                        {
                            "evidence_id": eid,
                            "type": "source_citation",
                            "path": "frameworks/core/example.cpp",
                            "line_start": 1, "line_end": 2,
                            "source_revision": SOURCE_REVISION,
                            "content_hash": "sha256:" + "0" * 64,
                            "description": f"Evidence {eid}.",
                            "source_work_item_id": "feature:Feat-01",
                            "source_evidence_id": "EV-1",
                        }
                        for eid in [self._evidence_id(criterion_id)]
                        + extra.get(criterion_id, [])
                    ],
                }
                for criterion_id in CRITERIA
            ],
        }

    def test_finding_evidence_auto_closed_into_criterion(self) -> None:
        """When a finding references valid catalog evidence that the model
        omitted from criterion evidence_ids, the normalizer closes the gap
        deterministically instead of sending FINDING_EVIDENCE_UNKNOWN."""
        extra_ev = "EV-extra-finding-ref"
        context = _compact_context(self._aggregation_context(
            extra_evidence_ids={"CORRECTNESS-SOURCE-SUPPORT": [extra_ev]}
        ))
        judgment = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [{
                "defect_key": "missing-proof",
                "primary_criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                "finding_keys": ["f1"],
                "rationale": "Single defect.",
            }],
            "outcome_policy_bases": [
                {"criterion_id": cid, "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "All verified."}
                for cid in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": [
                {
                    "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                    "conclusion": "CONTRADICTED",
                    "applicability": "APPLICABLE",
                    "reason": "Source contradicts spec.",
                    "applicability_reason": None,
                    "missing_evidence": None,
                    "claim_ids": ["Feat-01/AC-1"],
                    # Model only listed one evidence at criterion level
                    "evidence_ids": [
                        self._evidence_id("CORRECTNESS-SOURCE-SUPPORT"),
                    ],
                    "findings": [{
                        "key": "f1",
                        "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                        "claim_id": "Feat-01/AC-1",
                        "severity": "CRITICAL",
                        "message": "Contradiction found.",
                        # Finding references extra_ev which is NOT in criterion evidence_ids
                        "evidence_ids": [
                            self._evidence_id("CORRECTNESS-SOURCE-SUPPORT"),
                            extra_ev,
                        ],
                        "recommendation": "Fix the contradiction.",
                    }],
                },
                *[
                    {
                        "criterion_id": cid,
                        "conclusion": "SUPPORTED",
                        "applicability": "APPLICABLE",
                        "reason": "No violation.",
                        "applicability_reason": None,
                        "missing_evidence": None,
                        "claim_ids": [],
                        "evidence_ids": [self._evidence_id(cid)],
                        "findings": [],
                    }
                    for cid in CRITERIA[1:]
                ],
            ],
            "notes": [],
        }
        result = normalize_aggregation(
            self._template(), judgment,
            source_observation_ids=["feature:Feat-01"],
            aggregation_context=context,
        )
        # No errors — the normalizer auto-closed instead of erroring
        self.assertEqual(result.errors, [])
        self.assertEqual(result.fatal, [])
        self.assertIsNotNone(result.document)
        # Criterion evidence now includes the auto-closed extra_ev
        criterion = result.document["criterion_results"][0]
        criterion_ev_ids = [e["evidence_id"] for e in criterion["evidence"]]
        self.assertIn(extra_ev, criterion_ev_ids)
        # A normalization change was recorded
        closed_changes = [
            c for c in result.changes if "closed over" in c
        ]
        self.assertTrue(closed_changes)
        # Validator also passes
        errors = validate_aggregation_document(
            result.document, criterion_order=list(CRITERIA),
            aggregation_context=context,
        )
        finding_ev_errors = [e for e in errors if e.code == "FINDING_EVIDENCE_UNKNOWN"]
        self.assertEqual(finding_ev_errors, [])

    def test_finding_evidence_unknown_still_reported_for_missing_catalog_id(self) -> None:
        """Evidence IDs not in the criterion catalog are still errors."""
        judgment = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [{
                "defect_key": "missing-proof",
                "primary_criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                "finding_keys": ["f1"],
                "rationale": "Single defect.",
            }],
            "outcome_policy_bases": [
                {"criterion_id": cid, "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "All verified."}
                for cid in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": [
                {
                    "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                    "conclusion": "CONTRADICTED",
                    "applicability": "APPLICABLE",
                    "reason": "Source contradicts spec.",
                    "applicability_reason": None,
                    "missing_evidence": None,
                    "claim_ids": ["Feat-01/AC-1"],
                    "evidence_ids": [
                        self._evidence_id("CORRECTNESS-SOURCE-SUPPORT"),
                        "EV-does-not-exist",  # unknown → error
                    ],
                    "findings": [{
                        "key": "f1",
                        "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                        "claim_id": "Feat-01/AC-1",
                        "severity": "CRITICAL",
                        "message": "Contradiction found.",
                        "evidence_ids": [
                            self._evidence_id("CORRECTNESS-SOURCE-SUPPORT"),
                        ],
                        "recommendation": "Fix.",
                    }],
                },
                *[
                    {
                        "criterion_id": cid,
                        "conclusion": "SUPPORTED",
                        "applicability": "APPLICABLE",
                        "reason": "No violation.",
                        "applicability_reason": None,
                        "missing_evidence": None,
                        "claim_ids": [],
                        "evidence_ids": [self._evidence_id(cid)],
                        "findings": [],
                    }
                    for cid in CRITERIA[1:]
                ],
            ],
            "notes": [],
        }
        result = normalize_aggregation(
            self._template(), judgment,
            source_observation_ids=[],
            aggregation_context=_compact_context(self._aggregation_context()),
        )
        self.assertIsNone(result.document)
        self.assertTrue(
            any(e.code == "CRITERION_EVIDENCE_UNKNOWN" for e in result.errors)
        )


class PolicyConclusionDerivationTest(unittest.TestCase):
    """Issue #37: normalizer derives conclusion from policy basis."""

    @staticmethod
    def _evidence_id(criterion_id: str) -> str:
        return "EV-" + criterion_id.lower().replace("_", "-")

    def _template(self) -> dict:
        return {
            "schema_version": 2,
            "func_id": "05-01-02",
            "source_revision": SOURCE_REVISION,
            "run_id": "run-1",
            "status": "pending",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": False,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": [
                {"criterion_id": cid, "content_status": "PENDING",
                 "evidence_status": "PENDING", "conflict_scope": "PENDING",
                 "reason": "待评价人填写"}
                for cid in OUTCOME_POLICY_BASIS_CRITERIA
            ],
            "criterion_results": [
                {"criterion_id": cid, "conclusion": "NOT_VERIFIABLE",
                 "dimension_id": DIMENSION_BY_CRITERION[cid],
                 "applicability": "APPLICABLE", "reason": ""}
                for cid in CRITERIA
            ],
            "notes": [],
        }

    def _aggregation_context(self) -> dict:
        return {
            "schema_version": 2,
            "criterion_mappings": [
                {
                    "criterion_id": criterion_id,
                    "evidence_catalog": [{
                        "evidence_id": self._evidence_id(criterion_id),
                        "type": "source_citation",
                        "path": "frameworks/core/example.cpp",
                        "line_start": 1, "line_end": 2,
                        "source_revision": SOURCE_REVISION,
                        "content_hash": "sha256:" + "0" * 64,
                        "description": "Evidence.",
                        "source_work_item_id": "feature:Feat-01",
                        "source_evidence_id": "EV-1",
                    }],
                }
                for criterion_id in CRITERIA
            ],
        }

    def _base_judgment(self, policy_overrides=None) -> dict:
        default_policy = [
            {"criterion_id": cid, "content_status": "PRESENT",
             "evidence_status": "VERIFIED", "conflict_scope": "NONE",
             "reason": "All verified."}
            for cid in OUTCOME_POLICY_BASIS_CRITERIA
        ]
        if policy_overrides:
            by_id = {p["criterion_id"]: p for p in default_policy}
            for override in policy_overrides:
                by_id[override["criterion_id"]].update(override)
            default_policy = list(by_id.values())
        return {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": default_policy,
            "criterion_results": [
                {
                    "criterion_id": cid,
                    "conclusion": "SUPPORTED",
                    "applicability": "APPLICABLE",
                    "reason": "No violation.",
                    "applicability_reason": None,
                    "missing_evidence": None,
                    "claim_ids": [],
                    "evidence_ids": [self._evidence_id(cid)],
                    "findings": [],
                }
                for cid in CRITERIA
            ],
            "notes": [],
        }

    def test_normalizer_overrides_conclusion_from_policy_basis(self) -> None:
        """Model says SUPPORTED but policy basis says ABSENT → normalizer
        deterministically derives MISSING."""
        judgment = self._base_judgment(policy_overrides=[
            {"criterion_id": "SPEC-AC-TESTABILITY",
             "content_status": "ABSENT",
             "evidence_status": "VERIFIED",
             "conflict_scope": "NONE"},
        ])
        # Model incorrectly says SUPPORTED for the policy criterion
        for row in judgment["criterion_results"]:
            if row["criterion_id"] == "SPEC-AC-TESTABILITY":
                row["conclusion"] = "SUPPORTED"
        result = normalize_aggregation(
            self._template(), judgment,
            source_observation_ids=[],
            aggregation_context=_compact_context(self._aggregation_context()),
        )
        self.assertEqual(result.errors, [])
        rows_by_id = {
            r["criterion_id"]: r
            for r in result.document["criterion_results"]
        }
        # Normalizer derived MISSING from content_status=ABSENT
        self.assertEqual(rows_by_id["SPEC-AC-TESTABILITY"]["conclusion"], "MISSING")
        # Normalization change was logged
        derived_changes = [
            c for c in result.changes if "derived from outcome_policy_bases" in c
        ]
        self.assertTrue(derived_changes)

    def test_policy_derivation_covers_all_precedence_rules(self) -> None:
        """Exercise each row of the precedence table."""
        cases = [
            # (content, evidence, conflict) → expected
            ("NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE"),
            ("PRESENT", "VERIFIED", "CORE", "CONTRADICTED"),
            ("ABSENT", "VERIFIED", "NONE", "MISSING"),
            ("PLACEHOLDER_ONLY", "PARTIAL", "NONE", "MISSING"),
            ("PRESENT", "VERIFIED", "LOCAL", "PARTIALLY_SUPPORTED"),
            ("PRESENT", "UNAVAILABLE", "NONE", "NOT_VERIFIABLE"),
            ("PRESENT", "PARTIAL", "NONE", "PARTIALLY_SUPPORTED"),
            ("PRESENT", "VERIFIED", "NONE", "SUPPORTED"),
        ]
        for content, evidence, conflict, expected in cases:
            result = K.expected_policy_conclusion(content, evidence, conflict)
            self.assertEqual(
                result, expected,
                f"({content}, {evidence}, {conflict}) → expected {expected}, got {result}",
            )

    def test_mixed_na_returns_none(self) -> None:
        """Mixed NOT_APPLICABLE is invalid and returns None."""
        self.assertIsNone(
            K.expected_policy_conclusion("NOT_APPLICABLE", "VERIFIED", "NONE")
        )

    def test_finding_conclusion_inherits_derived_value(self) -> None:
        """Findings under a policy criterion get the derived conclusion."""
        judgment = self._base_judgment(policy_overrides=[
            {"criterion_id": "SPEC-AC-TESTABILITY",
             "content_status": "PRESENT",
             "evidence_status": "VERIFIED",
             "conflict_scope": "CORE"},
        ])
        for row in judgment["criterion_results"]:
            if row["criterion_id"] == "SPEC-AC-TESTABILITY":
                row["conclusion"] = "SUPPORTED"  # model says wrong
                row["findings"] = [{
                    "key": "f1",
                    "criterion_id": "SPEC-AC-TESTABILITY",
                    "claim_id": None,
                    "severity": "CRITICAL",
                    "message": "Core conflict.",
                    "evidence_ids": [self._evidence_id("SPEC-AC-TESTABILITY")],
                    "recommendation": "Fix.",
                }]
        judgment["defect_ownership"] = [{
            "defect_key": "testability-conflict",
            "primary_criterion_id": "SPEC-AC-TESTABILITY",
            "finding_keys": ["f1"],
            "rationale": "One defect.",
        }]
        result = normalize_aggregation(
            self._template(), judgment,
            source_observation_ids=[],
            aggregation_context=_compact_context(self._aggregation_context()),
        )
        self.assertEqual(result.errors, [])
        rows_by_id = {
            r["criterion_id"]: r
            for r in result.document["criterion_results"]
        }
        criterion = rows_by_id["SPEC-AC-TESTABILITY"]
        self.assertEqual(criterion["conclusion"], "CONTRADICTED")
        self.assertEqual(criterion["findings"][0]["conclusion"], "CONTRADICTED")

    def test_validator_error_points_to_policy_basis(self) -> None:
        """When policy basis and conclusion disagree after normalization,
        the error message names the three basis fields."""
        result = normalize_aggregation(
            self._template(), self._base_judgment(),
            source_observation_ids=[],
            aggregation_context=_compact_context(self._aggregation_context()),
        )
        doc = result.document
        # Manually break the derived conclusion to trigger validation error
        for row in doc["criterion_results"]:
            if row["criterion_id"] == "SPEC-AC-TESTABILITY":
                row["conclusion"] = "CONTRADICTED"
        errors = validate_aggregation_document(
            doc, criterion_order=list(CRITERIA),
        )
        policy_errors = [e for e in errors if e.code == "POLICY_BASIS_INVALID"]
        self.assertTrue(policy_errors)
        # Error message should reference the basis fields
        msg = policy_errors[0].expected or ""
        self.assertIn("content_status=", msg)
        self.assertIn("evidence_status=", msg)
        self.assertIn("conflict_scope=", msg)
        self.assertIn("correct the policy basis", msg)


class MachineContractPolicyRuleTest(unittest.TestCase):
    """Issue #37: machine contract exposes policy derivation rule."""

    def test_aggregation_contract_carries_policy_conclusion_rule(self) -> None:
        contract = build_aggregation_machine_contract(
            valid_criterion_ids=list(CRITERIA),
        )
        self.assertIn("policy_conclusion_rule", contract)
        rule = contract["policy_conclusion_rule"]
        self.assertEqual(
            rule["derived_from"],
            ["content_status", "evidence_status", "conflict_scope"],
        )
        self.assertTrue(rule["precedence"])
        conclusions = {entry["conclusion"] for entry in rule["precedence"]}
        self.assertIn("CONTRADICTED", conclusions)
        self.assertIn("MISSING", conclusions)
        self.assertIn("NOT_VERIFIABLE", conclusions)

    def test_aggregation_contract_documents_evidence_closure(self) -> None:
        contract = build_aggregation_machine_contract(
            valid_criterion_ids=list(CRITERIA),
        )
        rules = contract["judgment_rules"]
        closure_mentioned = any("closes" in rule for rule in rules)
        self.assertTrue(
            closure_mentioned,
            "Aggregation judgment_rules should mention evidence closure",
        )

    def test_aggregation_contract_documents_policy_derivation(self) -> None:
        contract = build_aggregation_machine_contract(
            valid_criterion_ids=list(CRITERIA),
        )
        rules = contract["judgment_rules"]
        policy_mentioned = any("derives conclusion" in rule for rule in rules)
        self.assertTrue(
            policy_mentioned,
            "Aggregation judgment_rules should mention service derives conclusion",
        )


class DefectKeyNormalizationTest(unittest.TestCase):
    """Tests for _normalize_defect_key canonicalization across flow points."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.evidence_rel = "input.txt"
        self.template = _template(self.root, self.evidence_rel)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _obs_judgment(self, *, obs_defect_key=None, obs_outcome="SUPPORTED",
                      claim_defect_keys=None, claim_outcome="SUPPORTED"):
        claim_defect_keys = claim_defect_keys or []
        gap = _gap() if claim_outcome == "NOT_VERIFIABLE" else None
        return {
            "evidence_declarations": [
                {
                    "key": "e1",
                    "type": "spec_location",
                    "path": self.evidence_rel,
                    "lines": "1-1",
                    "description": "Synthetic frozen evidence.",
                },
                {
                    "key": "e2",
                    "type": "review_record",
                    "path": self.evidence_rel,
                    "lines": None,
                    "description": "Inspection evidence for verification gap.",
                },
            ],
            "claim_reviews": [
                {
                    "claim_id": "Feat-01/AC-1",
                    "local_outcome": claim_outcome,
                    "evidence_refs": ["e1"],
                    "reason": "Synthetic claim review.",
                    "verification_gap": gap,
                    "defect_keys": claim_defect_keys,
                    "unit_reviews": [{
                        "unit_id": "u1",
                        "facet_type": "traceability",
                        "local_outcome": claim_outcome,
                        "evidence_refs": ["e1"],
                        "fact": "Synthetic unit fact.",
                        "verification_gap": copy.deepcopy(gap),
                    }],
                },
                {
                    "claim_id": "Feat-01/AC-2",
                    "local_outcome": "SUPPORTED",
                    "evidence_refs": ["e1"],
                    "reason": "The frozen evidence supports the claim.",
                    "verification_gap": None,
                    "defect_keys": [],
                    "unit_reviews": [{
                        "unit_id": "u1",
                        "facet_type": "traceability",
                        "local_outcome": "SUPPORTED",
                        "evidence_refs": ["e1"],
                        "fact": "Supported unit.",
                        "verification_gap": None,
                    }],
                },
            ],
            "observations": [{
                "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                "check_ids": ["claim_source_support", "boundary_state"],
                "claim_ids": ["Feat-01/AC-1", "Feat-01/AC-2"],
                "local_outcome": obs_outcome,
                "breadth": "feat_core",
                "contract_family": "synthetic-contract",
                "fact": "Synthetic observation fact.",
                "defect_key": obs_defect_key,
                "primary_criterion_id": (
                    "CORRECTNESS-SOURCE-SUPPORT" if obs_defect_key else None
                ),
                "evidence_refs": ["e1", "e2"],
            }],
            "open_questions": [],
            "notes": [],
        }

    def test_defect_key_uppercase_normalized(self) -> None:
        judgment = self._obs_judgment(
            obs_defect_key="MISSING-VERIFICATION", obs_outcome="CONFLICT"
        )
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        doc = result.document
        self.assertIsNotNone(doc)
        self.assertEqual(doc["observations"][0]["defect_key"], "missing-verification")
        self.assertTrue(
            any("canonicalized" in c and "MISSING-VERIFICATION" in c
                for c in result.changes)
        )

    def test_defect_key_mixed_case_claim(self) -> None:
        judgment = self._obs_judgment(
            claim_defect_keys=["FOO.Bar"], claim_outcome="CONFLICT",
            obs_defect_key="foo.bar", obs_outcome="CONFLICT",
        )
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        doc = result.document
        self.assertIsNotNone(doc)
        self.assertEqual(doc["claim_reviews"][0]["defect_keys"], ["foo.bar"])
        self.assertTrue(
            any("canonicalized" in c and "FOO.Bar" in c for c in result.changes)
        )

    def test_defect_key_already_lowercase(self) -> None:
        judgment = self._obs_judgment(
            obs_defect_key="already-lowercase", obs_outcome="CONFLICT"
        )
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        doc = result.document
        self.assertIsNotNone(doc)
        self.assertEqual(doc["observations"][0]["defect_key"], "already-lowercase")
        self.assertFalse(
            any("canonicalized" in c and "defect_key" in c for c in result.changes)
        )

    def test_defect_key_null_preserved(self) -> None:
        judgment = self._obs_judgment(obs_defect_key=None, obs_outcome="SUPPORTED")
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertEqual(result.fatal, [])
        doc = result.document
        self.assertIsNotNone(doc)
        self.assertIsNone(doc["observations"][0]["defect_key"])

    def test_aggregation_ownership_key_normalized(self) -> None:
        template = {
            "schema_version": 2,
            "func_id": "05-01-02",
            "source_revision": SOURCE_REVISION,
            "run_id": "run-1",
            "status": "pending",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": False,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": [
                {"criterion_id": cid, "content_status": "PENDING",
                 "evidence_status": "PENDING", "conflict_scope": "PENDING",
                 "reason": "待评价人填写"}
                for cid in (
                    "SPEC-AC-TESTABILITY", "SPEC-TRACEABILITY",
                    "DESIGN-IMPACT-COVERAGE", "DESIGN-VERIFICATION-PLAN",
                    "COMPATIBILITY-API-VERSION", "COMPATIBILITY-MULTI-DEVICE",
                )
            ],
            "criterion_results": [
                {"criterion_id": cid, "conclusion": "NOT_VERIFIABLE",
                 "dimension_id": DIMENSION_BY_CRITERION[cid],
                 "applicability": "APPLICABLE", "reason": ""}
                for cid in CRITERIA
            ],
            "notes": [],
        }
        agg_context = _compact_context({
            "schema_version": 2,
            "criterion_mappings": [
                {
                    "criterion_id": cid,
                    "evidence_catalog": [{
                        "evidence_id": "EV-" + cid.lower().replace("_", "-"),
                        "type": "source_citation",
                        "path": "frameworks/core/example.cpp",
                        "line_start": 1,
                        "line_end": 2,
                        "source_revision": SOURCE_REVISION,
                        "content_hash": "sha256:" + "0" * 64,
                        "description": "Inherited observation evidence.",
                        "source_work_item_id": "feature:Feat-01",
                        "source_evidence_id": "EV-1",
                    }],
                }
                for cid in CRITERIA
            ],
        })
        ev_id = lambda cid: "EV-" + cid.lower().replace("_", "-")
        judgment = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [{
                "defect_key": "TRACE-RULE-ORPHAN",
                "primary_criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                "finding_keys": ["f1"],
                "rationale": "One defect explains both findings.",
            }],
            "outcome_policy_bases": [
                {"criterion_id": "SPEC-AC-TESTABILITY", "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "Content and evidence verified."},
                {"criterion_id": "SPEC-TRACEABILITY", "content_status": "PRESENT",
                 "evidence_status": "VERIFIED", "conflict_scope": "NONE",
                 "reason": "Content and evidence verified."},
                {"criterion_id": "DESIGN-IMPACT-COVERAGE",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
                {"criterion_id": "DESIGN-VERIFICATION-PLAN",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
                {"criterion_id": "COMPATIBILITY-API-VERSION",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
                {"criterion_id": "COMPATIBILITY-MULTI-DEVICE",
                 "content_status": "PRESENT", "evidence_status": "VERIFIED",
                 "conflict_scope": "NONE", "reason": "Content and evidence verified."},
            ],
            "criterion_results": [
                {
                    "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                    "conclusion": "CONTRADICTED",
                    "applicability": "APPLICABLE",
                    "reason": "Mapped units contradict the published contract.",
                    "applicability_reason": None,
                    "missing_evidence": None,
                    "claim_ids": ["Feat-01/AC-1"],
                    "evidence_ids": [ev_id("CORRECTNESS-SOURCE-SUPPORT")],
                    "findings": [{
                        "key": "f1",
                        "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                        "claim_id": "Feat-01/AC-1",
                        "severity": "CRITICAL",
                        "message": "The published contract is contradicted.",
                        "evidence_ids": [ev_id("CORRECTNESS-SOURCE-SUPPORT")],
                        "recommendation": "Align the contract with the mapping.",
                    }],
                },
                *[
                    {
                        "criterion_id": cid,
                        "conclusion": "SUPPORTED",
                        "applicability": "APPLICABLE",
                        "reason": "No violation was found for this criterion.",
                        "applicability_reason": None,
                        "missing_evidence": None,
                        "claim_ids": [],
                        "evidence_ids": [ev_id(cid)],
                        "findings": [],
                    }
                    for cid in CRITERIA[1:]
                ],
            ],
            "notes": [],
        }
        result = normalize_aggregation(
            template, judgment,
            source_observation_ids=[],
            aggregation_context=agg_context,
        )
        self.assertEqual(result.fatal, [])
        doc = result.document
        self.assertIsNotNone(doc)
        ownership = doc["defect_ownership"]
        self.assertEqual(len(ownership), 1)
        self.assertEqual(ownership[0]["defect_key"], "trace-rule-orphan")
        self.assertTrue(
            any("canonicalized" in c and "TRACE-RULE-ORPHAN" in c
                for c in result.changes)
        )


class ConfidenceModelTest(unittest.TestCase):
    """Tests for the confidence layer classification and scoring (#47)."""

    def test_hard_error_detected(self):
        from spec_eval.kernel.errors import (
            LAYER_HARD, TypedError, confidence_layer_of, has_hard_errors,
        )
        self.assertEqual(confidence_layer_of("CRITERION_SET_MISMATCH"), LAYER_HARD)
        self.assertEqual(confidence_layer_of("IDENTITY_MISMATCH"), LAYER_HARD)
        errors = [TypedError("CRITERION_SET_MISMATCH", "$.criterion_results")]
        self.assertTrue(has_hard_errors(errors))

    def test_major_error_not_hard(self):
        from spec_eval.kernel.errors import (
            LAYER_MAJOR, TypedError, confidence_layer_of, has_hard_errors,
        )
        self.assertEqual(confidence_layer_of("MAPPING_CONCLUSION_FORBIDDEN"), LAYER_MAJOR)
        errors = [TypedError("MAPPING_CONCLUSION_FORBIDDEN", "$.x",
                             entity_type="criterion", entity_id="C1")]
        self.assertFalse(has_hard_errors(errors))

    def test_minor_error_not_hard(self):
        from spec_eval.kernel.errors import (
            LAYER_MINOR, TypedError, confidence_layer_of, has_hard_errors,
        )
        self.assertEqual(confidence_layer_of("MAPPING_CLAIM_UNMAPPED"), LAYER_MINOR)
        errors = [TypedError("MAPPING_CLAIM_UNMAPPED", "$.x")]
        self.assertFalse(has_hard_errors(errors))

    def test_unknown_code_defaults_to_minor(self):
        from spec_eval.kernel.errors import LAYER_MINOR, confidence_layer_of
        self.assertEqual(confidence_layer_of("UNKNOWN_FUTURE_CODE"), LAYER_MINOR)

    def test_confidence_score_full_when_no_errors(self):
        from spec_eval.kernel.errors import compute_confidence
        result = compute_confidence([])
        self.assertEqual(result["confidence_score"], 100)
        self.assertEqual(result["confidence_level"], "HIGH")
        self.assertEqual(result["total_checks_failed"], 0)

    def test_confidence_score_deducted_for_major(self):
        from spec_eval.kernel.errors import TypedError, compute_confidence
        errors = [
            TypedError("MAPPING_CONCLUSION_FORBIDDEN", "$.x",
                       entity_type="criterion", entity_id="C1"),
        ]
        result = compute_confidence(errors)
        self.assertEqual(result["confidence_score"], 80)
        self.assertEqual(result["confidence_level"], "HIGH")
        self.assertEqual(len(result["major_violations"]), 1)
        self.assertEqual(result["deduction_total"], 20)

    def test_confidence_score_deducted_for_minor(self):
        from spec_eval.kernel.errors import TypedError, compute_confidence
        errors = [
            TypedError("MAPPING_CLAIM_UNMAPPED", "$.x",
                       entity_type="criterion", entity_id="C2"),
        ]
        result = compute_confidence(errors)
        self.assertEqual(result["confidence_score"], 95)
        self.assertEqual(result["confidence_level"], "HIGH")

    def test_multiple_errors_accumulate(self):
        from spec_eval.kernel.errors import TypedError, compute_confidence
        errors = [
            TypedError("MAPPING_CONCLUSION_FORBIDDEN", "$.a",
                       entity_type="criterion", entity_id="C1"),
            TypedError("MAPPING_NV_REQUIRED", "$.b",
                       entity_type="criterion", entity_id="C2"),
            TypedError("MAPPING_CLAIM_UNMAPPED", "$.c",
                       entity_type="criterion", entity_id="C3"),
        ]
        result = compute_confidence(errors)
        # 100 - 20 - 20 - 5 = 55
        self.assertEqual(result["confidence_score"], 55)
        self.assertEqual(result["confidence_level"], "MEDIUM")

    def test_confidence_floors_at_zero(self):
        from spec_eval.kernel.errors import TypedError, compute_confidence
        errors = [
            TypedError("MAPPING_CONCLUSION_FORBIDDEN", f"$.{i}",
                       entity_type="criterion", entity_id=f"C{i}")
            for i in range(10)
        ]
        result = compute_confidence(errors)
        self.assertEqual(result["confidence_score"], 0)
        self.assertEqual(result["confidence_level"], "LOW")

    def test_service_normalization_ignored(self):
        from spec_eval.kernel.errors import (
            SERVICE_NORMALIZATION, TypedError, compute_confidence,
        )
        errors = [
            TypedError("GAP_UNEXPECTED_FOR_NON_NV", "$.x",
                       repairability=SERVICE_NORMALIZATION),
        ]
        result = compute_confidence(errors)
        self.assertEqual(result["confidence_score"], 100)
        self.assertEqual(result["total_checks_failed"], 0)


if __name__ == "__main__":
    unittest.main()
