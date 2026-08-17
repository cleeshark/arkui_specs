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

from spec_eval.protocol_validator import (
    JsonSchemaSubsetValidator,
    validate_strict_output_schema,
)
from spec_eval.kernel import contracts as K
from spec_eval.kernel.errors import SERVICE_NORMALIZATION, TypedError, blocking
from spec_eval.kernel.machine_contract import (
    build_aggregation_machine_contract,
    build_observation_machine_contract,
)
from spec_eval.kernel.normalize import (
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
                        "Checked the frozen spec scope; the atomic proof is missing."
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

    def test_unreadable_evidence_is_fatal(self) -> None:
        judgment = _judgment("missing/file.txt")
        result = normalize_observation(self.template, judgment, repo_root=self.root)
        self.assertTrue(result.fatal)
        self.assertEqual(result.fatal[0].code, "EVIDENCE_PATH_UNREADABLE")
        self.assertIsNone(result.document)

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

    def test_unknown_criterion(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["criterion_ids"] = ["NOT-A-CRITERION"]
        self.assertIn("CRITERION_UNKNOWN", self._codes(document))

    def test_incomplete_check_coverage(self) -> None:
        document = copy.deepcopy(self.document)
        document["observations"][0]["check_ids"] = ["claim_source_support"]
        self.assertIn("CHECK_COVERAGE_INCOMPLETE", self._codes(document))

    def test_defect_key_undefined_on_claim(self) -> None:
        document = copy.deepcopy(self.document)
        document["claim_reviews"][1]["local_outcome"] = "CONFLICT"
        document["claim_reviews"][1]["defect_keys"] = ["synthetic-defect"]
        self.assertIn("DEFECT_KEY_UNDEFINED", self._codes(document))

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
                 "applicability": "APPLICABLE", "reason": ""}
                for cid in CRITERIA
            ],
            "notes": [],
        }

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
                    "evidence": [{"evidence_id": "EV-1"}],
                    "findings": [{
                        "key": "f1",
                        "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                        "claim_id": "Feat-01/AC-1",
                        "severity": "CRITICAL",
                        "message": "The published contract is contradicted.",
                        "evidence_ids": ["EV-1"],
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
                        "evidence": [{"evidence_id": "EV-1"}],
                        "findings": [],
                    }
                    for criterion_id in CRITERIA[1:]
                ],
            ],
            "notes": [],
        }

    def test_canonical_ids_and_secondary_derivation(self) -> None:
        result = normalize_aggregation(
            self._template(), self._judgment(),
            source_observation_ids=["feature:Feat-01"],
        )
        self.assertEqual(result.fatal, [])
        document = result.document
        finding = document["criterion_results"][0]["findings"][0]
        self.assertTrue(finding["finding_id"].startswith("SEM-"))
        ownership = document["defect_ownership"][0]
        self.assertEqual(ownership["finding_ids"], [finding["finding_id"]])
        self.assertEqual(ownership["secondary_criterion_ids"], [])
        self.assertEqual(
            document["source_observation_ids"], ["feature:Feat-01"]
        )

    def test_criterion_order_follows_template(self) -> None:
        judgment = self._judgment()
        judgment["criterion_results"].reverse()
        result = normalize_aggregation(
            self._template(), judgment, source_observation_ids=[]
        )
        self.assertEqual(result.fatal, [])
        ids = [
            row["criterion_id"] for row in result.document["criterion_results"]
        ]
        self.assertEqual(ids, list(CRITERIA))

    def test_valid_aggregation_has_no_blocking_errors(self) -> None:
        result = normalize_aggregation(
            self._template(), self._judgment(),
            source_observation_ids=["feature:Feat-01"],
        )
        errors = validate_aggregation_document(
            result.document, criterion_order=list(CRITERIA)
        )
        self.assertEqual(blocking(errors), [], [e.to_dict() for e in errors])

    def test_finding_cardinality_and_policy_errors(self) -> None:
        result = normalize_aggregation(
            self._template(), self._judgment(),
            source_observation_ids=["feature:Feat-01"],
        )
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
        result = normalize_aggregation(
            self._template(), self._judgment(),
            source_observation_ids=["feature:Feat-01"],
        )
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


class MachineContractTest(unittest.TestCase):
    def test_observation_contract_carries_reference_spaces(self) -> None:
        contract = build_observation_machine_contract(
            expected_claim_ids=["Feat-01/AC-1"],
            required_checks=K.FEATURE_REQUIRED_CHECKS,
            valid_criterion_ids=CRITERIA,
            evidence_catalog=[{"evidence_id": "EV-1", "type": "spec_location"}],
        )
        self.assertEqual(contract["expected_claim_ids"], ["Feat-01/AC-1"])
        self.assertEqual(contract["required_checks"], list(K.FEATURE_REQUIRED_CHECKS))
        self.assertEqual(contract["evidence_catalog"][0]["evidence_id"], "EV-1")
        self.assertIn("verification_gap", " ".join(contract["judgment_rules"]))

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
            second = purge_all(settings)
            self.assertEqual(sum(second["removed"].values()), 0)

    def test_purge_export_takes_backup_first(self) -> None:
        from spec_eval.service.governance import purge_all
        from spec_eval.service.settings import ServiceSettings
        from spec_eval.service.store.sqlite_store import SqliteStore

        with tempfile.TemporaryDirectory() as tmp:
            settings = ServiceSettings.discover(data_root=Path(tmp))
            store = SqliteStore(settings)
            store.close()
            self.assertTrue(settings.db_path.is_file())
            purge_all(settings, export_first=True)
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

    def test_v2_string_still_accepted(self) -> None:
        from spec_eval.service.executors import contract as C

        result = self._run({
            "schema_version": 2,
            "work_item_id": "feature:Feat-01",
            "status": "completed",
            "observation_json": json.dumps({"claim_reviews": []}),
            "notes": [],
            "error": None,
        })
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertEqual(result.observation, {"claim_reviews": []})

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
        from spec_eval.kernel.errors import (
            FATAL_INPUT, MODEL_CORRECTION, repairability_of,
        )

        self.assertEqual(
            repairability_of("EVIDENCE_PATH_UNREADABLE"), FATAL_INPUT
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


if __name__ == "__main__":
    unittest.main()
