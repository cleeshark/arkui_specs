"""End-to-end contract alignment tests for issue #12."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline import aggregation_stage, staged_stage
from spec_eval.service.pipeline.context import RunContext
from spec_eval.service.pipeline.result_payload import merge_aggregation_payload
from spec_eval.service.pipeline.semantic_stage import run_semantic
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    AttemptRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore


EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.1.12"
SOURCE_REVISION = "a" * 40


class _PayloadExecutor:
    def __init__(self, *, nested: bool = False, invalid: bool = False) -> None:
        self.nested = nested
        self.invalid = invalid
        self.prompts: list[C.WorkItemInput] = []

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake-contract-executor"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.prompts.append(work)
        if self.nested:
            payload = {
                "identity": {"func_id": work.func_id, "run_id": work.run_id},
                "input": {"input_paths": list(work.input_paths)},
                "verdict": "complete",
            }
        else:
            expected_claims = list(work.work_item["expected_claim_ids"])
            required_checks = list(work.work_item["required_checks"])
            payload = {
                "claim_reviews": [
                    {
                        "claim_id": claim_id,
                        "status": "complete",
                        "local_outcome": "NOT_VERIFIABLE",
                        "reviewed_units": ["frozen-evidence"],
                        "unit_reviews": [{
                            "unit_id": "frozen-evidence",
                            "facet_type": "traceability",
                            "local_outcome": "NOT_VERIFIABLE",
                            "evidence_ids": [],
                            "fact": "The synthetic fixture deliberately provides no source proof.",
                        }],
                        "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                        "evidence_ids": [],
                        "defect_keys": [],
                        "reason": "The synthetic fixture is intentionally not verifiable.",
                    }
                    for claim_id in expected_claims
                ],
                "observations": [{
                    "observation_id": "OBS-" + work.work_item_id.replace(":", "-"),
                    "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                    "check_ids": required_checks,
                    "claim_ids": expected_claims,
                    "local_outcome": "NOT_VERIFIABLE",
                    "breadth": (
                        "feat_core" if work.work_item.get("type") == "feature" else "function_shared"
                    ),
                    "contract_family": "synthetic-contract",
                    "fact": "The staged payload was completed against the initialized flat contract.",
                    "evidence": [],
                }],
                "open_questions": [],
                "notes": [],
            }
            if self.invalid:
                payload["observations"] = []
        return C.ExecutionResult(status=C.STATUS_COMPLETED, exit_code=0, observation=payload)


class _AggregationPayloadExecutor:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake-aggregation-executor"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED, exit_code=0, observation=self.payload
        )


class _Issue13RepairExecutor(_PayloadExecutor):
    """First emit the real issue #13 shape, then mechanically repair it."""

    def __init__(self, *, repair_succeeds: bool = True) -> None:
        super().__init__()
        self.repair_succeeds = repair_succeeds

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        result = super().execute(work, emit, cancel)
        payload = result.observation
        assert payload is not None
        repair_mode = work.prompt_extras.get("mode") == "repair_candidate"
        if work.work_item_id != "feature:Feat-01":
            return result

        rubric_path = Path(work.repo_root) / "specs" / "evaluation" / "rubric.yaml"
        digest = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
        repaired = repair_mode and self.repair_succeeds
        evidence_id = "EV-E1" if repaired else "E1"
        evidence = {
            "evidence_id": evidence_id,
            "path": "specs/evaluation/rubric.yaml",
            "source_revision": SOURCE_REVISION,
            "content_hash": f"sha256:{digest}" if repaired else digest,
            "description": "Synthetic issue #13 contract evidence.",
        }
        if repaired:
            evidence["type"] = "spec_location"
        observation = payload["observations"][0]
        observation.update(
            local_outcome="SUPPORTED",
            criterion_ids=[
                "CORRECTNESS-SOURCE-SUPPORT"
                if repaired else "DESIGN-EXCEPTION-RECOVERY"
            ],
            evidence=[evidence],
        )
        review = payload["claim_reviews"][0]
        review.update(
            local_outcome="SUPPORTED",
            evidence_ids=[evidence_id],
            defect_keys=[] if repaired else ["misplaced-defect"],
        )
        review["unit_reviews"][0].update(
            local_outcome="SUPPORTED",
            evidence_ids=[evidence_id],
        )
        return result


class ContractAlignmentIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.attempts = AttemptRepository(self.store)
        self.events = EventRepository(self.store)
        self.statistics = JobStatisticsRepository(self.store)
        self.job = self.jobs.create_job(
            CreateJobCommand(
                func_id="01-01-01",
                source_revision=SOURCE_REVISION,
                run_count=1,
                job_id="e" * 40,
            ),
            evaluator_version=EVALUATOR_VERSION,
        )
        self.ctx = RunContext.for_run(
            self.settings,
            job_id=self.job.job_id,
            func_id=self.job.func_id,
            source_revision=self.job.source_revision,
            run_id="run-1",
            evaluator_version=EVALUATOR_VERSION,
        )
        self._write_input_fixture()
        staged_stage.init_staged_run(self.ctx)
        self.jobs.transition_status(self.job.job_id, S.PREPARING, event_type="test")
        self.jobs.transition_status(self.job.job_id, S.EVIDENCE, event_type="test")
        self.jobs.transition_status(self.job.job_id, S.SEMANTIC, event_type="test")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _write_input_fixture(self) -> None:
        input_dir = self.ctx.input_dir
        evidence_dir = input_dir / "evidence"
        evidence_dir.mkdir(parents=True)
        common = {"func_id": self.job.func_id, "source_revision": SOURCE_REVISION}
        context = {
            **common,
            "design_path": "specs/01-architecture/01-architecture-design/01-build-system/design.md",
            "feature_registry_entries": [{
                "id": "Feat-01",
                "status": "active",
                "spec": (
                    "01-architecture/01-architecture-design/01-build-system/"
                    "Feat-01-build-gn-structure-spec.md"
                ),
            }],
        }
        (input_dir / "function-context.json").write_text(
            json.dumps(context), encoding="utf-8"
        )
        (input_dir / "static-result.json").write_text(
            json.dumps({**common, "gate": "fail", "findings": []}), encoding="utf-8"
        )
        (input_dir / "evidence-manifest.json").write_text(
            json.dumps({
                **common,
                "shards": [
                    {"name": "Feat-01", "path": "Feat-01.json"},
                    {"name": "design", "path": "design.json"},
                ],
            }),
            encoding="utf-8",
        )
        (input_dir / "report.md").write_text("# synthetic evidence\n", encoding="utf-8")
        (evidence_dir / "Feat-01.json").write_text(
            json.dumps({"claims": [{"claim_id": "Feat-01/AC-1"}]}), encoding="utf-8"
        )
        (evidence_dir / "design.json").write_text(
            json.dumps({"claims": [{"claim_id": "DESIGN/R-1"}]}), encoding="utf-8"
        )

    def test_payload_passes_real_initializer_and_validator(self) -> None:
        executor = _PayloadExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        state = json.loads((self.ctx.run_dir / "run-state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["validated_work_items"], ["feature:Feat-01", "function-global"]
        )
        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        self.assertEqual(feature["schema_version"], 2)
        self.assertEqual(feature["source_revision"], SOURCE_REVISION)
        self.assertEqual(feature["status"], "complete")
        self.assertEqual(feature["reviewed_claim_ids"], ["Feat-01/AC-1"])
        self.assertNotIn("identity", feature)
        self.assertNotIn("input", feature)
        first_work = executor.prompts[0]
        self.assertIn(str(Path(first_work.work_item["output_path"])), first_work.input_paths)
        self.assertIn(str(self.ctx.run_dir / "output-contract.json"), first_work.input_paths)
        self.assertEqual(
            first_work.prompt_extras["result_kind"], "staged_observation_payload"
        )
        machine_contract = first_work.prompt_extras["machine_contract"]
        self.assertIn("source_citation", machine_contract["common"]["evidence"]["type_enum"])
        self.assertEqual(
            machine_contract["common"]["evidence"]["evidence_id_pattern"],
            "^EV-[A-Za-z0-9._-]+$",
        )
        self.assertIn(
            "CORRECTNESS-SOURCE-SUPPORT", machine_contract["valid_criterion_ids"]
        )

    def test_issue_13_contract_drift_is_repaired_once(self) -> None:
        executor = _Issue13RepairExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(len(executor.prompts), 3)
        repair_work = executor.prompts[1]
        self.assertEqual(repair_work.prompt_extras["mode"], "repair_candidate")
        self.assertTrue(repair_work.executor_result_path.endswith(".repair-1.json"))
        self.assertEqual(len(repair_work.input_paths), 3)
        self.assertTrue(any(path.endswith(".candidate") for path in repair_work.input_paths))

        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(encoding="utf-8")
        )
        evidence = feature["observations"][0]["evidence"][0]
        self.assertEqual(evidence["type"], "spec_location")
        self.assertEqual(evidence["evidence_id"], "EV-E1")
        self.assertTrue(evidence["content_hash"].startswith("sha256:"))
        self.assertEqual(feature["claim_reviews"][0]["defect_keys"], [])

        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("candidate_validation_failed", event_types)
        self.assertIn("candidate_repair_started", event_types)
        self.assertIn("candidate_repair_completed", event_types)
        self.assertEqual(self.statistics.get(self.job.job_id).executor_invocations, 3)

    def test_nested_issue_12_shape_is_rejected_without_overwriting_template(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        before = template_path.read_bytes()
        result = run_semantic(
            self.ctx,
            _PayloadExecutor(nested=True),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("payload fields", result.error or "")
        self.assertEqual(template_path.read_bytes(), before)

    def test_pre_012_run_without_machine_contract_remains_resumable(self) -> None:
        contract_path = self.ctx.run_dir / "output-contract.json"
        contract_path.unlink()
        state_path = self.ctx.run_dir / "run-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["input_artifacts"] = [
            item
            for item in state["input_artifacts"]
            if item.get("kind") != "staged_output_contract"
        ]
        state_path.write_text(json.dumps(state), encoding="utf-8")
        work_items_path = self.ctx.run_dir / "work-items.json"
        work_items = json.loads(work_items_path.read_text(encoding="utf-8"))
        for item in work_items["items"]:
            item["input_paths"] = [
                path for path in item["input_paths"] if path != str(contract_path)
            ]
        work_items_path.write_text(json.dumps(work_items), encoding="utf-8")

        executor = _PayloadExecutor()
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(executor.prompts[0].prompt_extras["machine_contract"], {
            "valid_criterion_ids": [], "common": {}, "payload": {}
        })

    def test_invalid_candidate_is_rejected_without_overwriting_template(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        before = template_path.read_bytes()
        executor = _PayloadExecutor(invalid=True)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("expected at least one evidence-backed observation", result.error or "")
        self.assertEqual(template_path.read_bytes(), before)
        self.assertEqual(len(executor.prompts), 1)

    def test_failed_repair_keeps_initialized_template_and_stops_after_one_round(self) -> None:
        template_path = self.ctx.run_dir / "observations" / "Feat-01.json"
        before = template_path.read_bytes()
        executor = _Issue13RepairExecutor(repair_succeeds=False)
        result = run_semantic(
            self.ctx,
            executor,
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
            statistics=self.statistics,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertEqual(len(executor.prompts), 2)
        self.assertEqual(template_path.read_bytes(), before)
        self.assertEqual(self.statistics.get(self.job.job_id).executor_invocations, 2)
        event_types = [event.event_type for event in self.events.list_for_job(self.job.job_id)]
        self.assertIn("candidate_repair_failed", event_types)

    def test_aggregation_merge_keeps_identity_and_derives_sources(self) -> None:
        initialized = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        payload = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": initialized["outcome_policy_bases"],
            "criterion_results": initialized["criterion_results"],
            "notes": [],
        }
        candidate = merge_aggregation_payload(
            initialized,
            payload,
            source_observation_ids=("feature:Feat-01", "function-global"),
        )
        self.assertEqual(candidate["source_revision"], SOURCE_REVISION)
        self.assertEqual(candidate["status"], "complete")
        self.assertEqual(
            candidate["source_observation_ids"], ["feature:Feat-01", "function-global"]
        )

    def test_aggregation_payload_passes_real_assemble_and_final_validator(self) -> None:
        semantic = run_semantic(
            self.ctx,
            _PayloadExecutor(),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(semantic.outcome, C.STATUS_COMPLETED, semantic.error)
        initialized = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        criterion_results = []
        for row in initialized["criterion_results"]:
            completed = dict(row)
            completed.update(
                conclusion="NOT_VERIFIABLE",
                reason="Synthetic evidence is intentionally unavailable.",
                evidence=[],
                findings=[],
            )
            criterion_results.append(completed)
        policy_bases = []
        for row in initialized["outcome_policy_bases"]:
            completed = dict(row)
            completed.update(
                content_status="PRESENT",
                evidence_status="UNAVAILABLE",
                conflict_scope="NONE",
                reason="Synthetic evidence is intentionally unavailable.",
            )
            policy_bases.append(completed)
        payload = {
            "cross_feat_contracts_reviewed": True,
            "contradiction_bases": [],
            "defect_ownership": [],
            "outcome_policy_bases": policy_bases,
            "criterion_results": criterion_results,
            "notes": [],
        }
        self.jobs.transition_status(self.job.job_id, S.AGGREGATION, event_type="test")
        outcome, semantic_result = aggregation_stage.run_aggregation(
            self.ctx,
            _AggregationPayloadExecutor(payload),
            jobs=self.jobs,
            attempts=self.attempts,
            events=self.events,
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(semantic_result is not None and semantic_result.is_file())
        aggregation = json.loads(
            (self.ctx.run_dir / "aggregation.json").read_text(encoding="utf-8")
        )
        self.assertEqual(aggregation["source_revision"], SOURCE_REVISION)
        self.assertEqual(aggregation["status"], "complete")


if __name__ == "__main__":
    unittest.main()
