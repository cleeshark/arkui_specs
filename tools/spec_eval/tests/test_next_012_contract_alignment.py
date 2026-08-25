"""Protocol 0.2.0 observation flow tests (issue #26 / PR-2).

Replaces the 0.1.x repair-chain contract tests: the staged observation loop is
now observe -> normalize -> typed validate -> (one) correct, driven by the
kernel, with the work item state machine and per-call invocations.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline import staged_stage
from spec_eval.service.pipeline.semantic_stage import run_semantic
from spec_eval.service.store.repositories import (
    AttemptRepository,
    EventRepository,
    ExecutorCallRepository,
    JobRepository,
    JobStatisticsRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore

SKILL_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "skills"
    / "ohos-design-arkui-spec-evaluator"
    / "scripts"
)
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.3.0"
SOURCE_REVISION = "a" * 40


def _gap(claim_id: str) -> dict:
    return {
        "checked_scope": ["frozen Feat-01 spec scope"],
        "missing_evidence": [f"implementation proof for {claim_id}"],
        "consequence": f"{claim_id} cannot be verified from the frozen inputs.",
    }


class _JudgmentExecutor:
    """Produces 0.2.0 observation judgments; can be scripted to fail."""

    def __init__(
        self,
        *,
        break_first: bool = False,
        break_all: bool = False,
        invalid_global_path_once: bool = False,
        empty_observation_claims_once: bool = False,
        json_patch_correction: bool = False,
        json_patch_evidence_correction: bool = False,
        correction_primary_mismatch: bool = False,
        invalid_criterion_once: bool = False,
    ) -> None:
        self.break_first = break_first
        self.break_all = break_all
        self.invalid_global_path_once = invalid_global_path_once
        self.empty_observation_claims_once = empty_observation_claims_once
        self.json_patch_correction = json_patch_correction
        self.json_patch_evidence_correction = json_patch_evidence_correction
        self.correction_primary_mismatch = correction_primary_mismatch
        self.invalid_criterion_once = invalid_criterion_once
        self._invalid_global_path_emitted = False
        self._empty_observation_claims_emitted = False
        self._invalid_criterion_emitted = False
        self.calls: list[tuple[str, str]] = []
        self.prompts: list[C.WorkItemInput] = []
        self.correction_candidates: list[dict] = []

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "judgment-fake"}

    def _payload(self, work: C.WorkItemInput, *, broken: bool) -> dict:
        claims = list(work.work_item.get("expected_claim_ids", []))
        checks = list(work.work_item.get("required_checks", []))
        declarations = [
            {
                "key": "e1",
                "type": "spec_location",
                "path": _first_input(work),
                "lines": "1-20",
                "description": "Frozen Feat-01 spec evidence.",
            },
            {
                "key": "e2",
                "type": "review_record",
                "path": _first_input(work),
                "lines": None,
                "description": "The evaluator inspected the frozen inputs.",
            },
        ]
        if broken and claims:
            # Keep structure/mappings valid and introduce only a semantic
            # low-information defect.  This must still enter the model
            # correction turn under the evidence/semantic-only routing rule.
            return {
                "evidence_declarations": declarations,
                "claim_reviews": [
                    {
                        "claim_id": claim_id,
                        "local_outcome": "SUPPORTED",
                        "evidence_refs": ["e1"],
                        "reason": "supported",
                        "verification_gap": None,
                        "defect_keys": [],
                        "unit_reviews": [{
                            "unit_id": "u1",
                            "facet_type": "traceability",
                            "local_outcome": "SUPPORTED",
                            "evidence_refs": ["e1"],
                            "fact": "The inspected unit is supported by the frozen evidence.",
                            "verification_gap": None,
                        }],
                    }
                    for claim_id in claims
                ],
                "observations": [{
                    "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                    "check_ids": checks,
                    "claim_ids": claims,
                    "local_outcome": "SUPPORTED",
                    "breadth": "feat_core",
                    "contract_family": "synthetic-contract",
                    "fact": "The frozen evidence supports the synthetic claims.",
                    "defect_key": None,
                    "primary_criterion_id": None,
                    "evidence_refs": ["e1"],
                }],
                "open_questions": [],
                "notes": [],
            }
        return {
            "evidence_declarations": declarations,
            "claim_reviews": [
                {
                    "claim_id": claim_id,
                    "local_outcome": "SUPPORTED",
                    "evidence_refs": ["e1"],
                    "reason": (
                        "The frozen Feat-01 spec evidence supports the evaluated "
                        f"claim {claim_id}."
                    ),
                    "verification_gap": None,
                    "defect_keys": [],
                    "unit_reviews": [{
                        "unit_id": "u1",
                        "facet_type": "traceability",
                        "local_outcome": "SUPPORTED",
                        "evidence_refs": ["e1"],
                        "fact": (
                            "The frozen evidence supports this atomic unit of "
                            f"{claim_id}."
                        ),
                        "verification_gap": None,
                    }],
                }
                for claim_id in claims
            ],
            "observations": [{
                "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                "check_ids": checks,
                "claim_ids": claims,
                "local_outcome": "SUPPORTED",
                "breadth": "feat_core",
                "contract_family": "synthetic-contract",
                "fact": "The frozen evidence supports the synthetic claims.",
                "defect_key": None,
                "primary_criterion_id": None,
                "evidence_refs": ["e1"],
            }],
            "open_questions": [],
            "notes": [],
        }

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        mode = work.prompt_extras.get("mode", "observe")
        is_first_call = not self.calls
        self.calls.append((work.work_item_id, mode))
        self.prompts.append(work)
        if mode == "correct":
            candidate_path = Path(str(work.prompt_extras["candidate_path"]))
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            self.correction_candidates.append(candidate)
            if self.json_patch_evidence_correction:
                valid_path = _first_input(work)
                return C.ExecutionResult(
                    status=C.STATUS_COMPLETED,
                    exit_code=0,
                    executor_result_path=work.executor_result_path,
                    observation={
                        "patches": [{
                            "op": "replace",
                            "path": "/evidence_declarations/0/path",
                            "value": valid_path,
                        }, {
                            "op": "replace",
                            "path": "/evidence_declarations/1/path",
                            "value": valid_path,
                        }],
                        "notes": ["evidence paths corrected"],
                    },
                )
            if self.invalid_criterion_once:
                return C.ExecutionResult(
                    status=C.STATUS_COMPLETED,
                    exit_code=0,
                    executor_result_path=work.executor_result_path,
                    observation={
                        "patches": [{
                            "op": "replace",
                            "path": "/observations/0/criterion_ids",
                            "value": json.dumps([
                                "CORRECTNESS-SOURCE-SUPPORT"
                            ]),
                        }, {
                            "op": "replace",
                            "path": "/claim_reviews/0/evidence_ids",
                            "value": json.dumps(["EV-1"]),
                        }, {
                            "op": "replace",
                            "path": "/claim_reviews/0/unit_reviews/0/evidence_ids",
                            "value": json.dumps(["EV-1"]),
                        }],
                        "notes": [
                            "unknown Criterion and Evidence references corrected"
                        ],
                    },
                )
            if self.json_patch_correction:
                return C.ExecutionResult(
                    status=C.STATUS_COMPLETED,
                    exit_code=0,
                    executor_result_path=work.executor_result_path,
                    observation={
                        "patches": [{
                            "op": "replace",
                            "path": "/claim_reviews/0/reason",
                            "value": json.dumps(
                                "The frozen evidence supports this claim after source verification.",
                            ),
                        }],
                        "notes": ["semantic reason corrected"],
                    },
                )
        emit(C.ExecutionEvent(kind="command", message="fake"))
        broken = (self.break_first and mode == "observe" and is_first_call) or (
            self.break_all
        )
        payload = self._payload(work, broken=broken)
        if mode == "correct" and self.correction_primary_mismatch:
            observation = payload["observations"][0]
            observation["local_outcome"] = "MISSING"
            observation["defect_key"] = "missing.primary_criterion_route"
            observation["primary_criterion_id"] = "SPEC-TRACEABILITY"
        if (
            self.empty_observation_claims_once
            and not self._empty_observation_claims_emitted
            and work.work_item_id == "feature:Feat-01"
            and mode == "observe"
        ):
            self._empty_observation_claims_emitted = True
            payload["observations"][0]["claim_ids"] = []
        if (
            self.invalid_criterion_once
            and not self._invalid_criterion_emitted
            and work.work_item_id == "feature:Feat-01"
            and mode == "observe"
        ):
            self._invalid_criterion_emitted = True
            payload["observations"][0]["criterion_ids"] = [
                "SPEC-CROSS-DOC-CONSISTENCY"
            ]
            payload["claim_reviews"][0]["evidence_refs"] = ["e35"]
            payload["claim_reviews"][0]["unit_reviews"][0][
                "evidence_refs"
            ] = ["e35"]
        if (
            self.invalid_global_path_once
            and not self._invalid_global_path_emitted
            and work.work_item_id == "function-global"
            and mode == "observe"
        ):
            self._invalid_global_path_emitted = True
            for declaration in payload["evidence_declarations"]:
                declaration["path"] = "runs/run-1/staged/output-contract.json"
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED,
            exit_code=0,
            executor_result_path=work.executor_result_path,
            observation=payload,
            elapsed_seconds=0.25,
            token_usage={
                "input_tokens": 10, "cached_input_tokens": 0,
                "cache_write_input_tokens": 0, "output_tokens": 5,
                "reasoning_output_tokens": 0, "total_tokens": 15,
            },
            usage_reported=True,
        )


def _first_input(work: C.WorkItemInput) -> str:
    for resource in work.work_item.get("input_resources", []):
        if resource.get("citable") is True and resource.get("canonical_path"):
            return str(resource["canonical_path"])
    for path in work.input_paths:
        if path.endswith(".md") or path.endswith(".json"):
            candidate = Path(path)
            if candidate.is_file():
                return str(candidate)
    return next(iter(work.input_paths), "specs/missing.txt")


class _StagedRunIntegrationTest(unittest.TestCase):
    """Shared one-run staged fixture with a real initialize."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        from spec_eval.service.settings import ServiceSettings
        from spec_eval.service.pipeline.context import RunContext

        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.attempts = AttemptRepository(self.store)
        self.events = EventRepository(self.store)
        self.statistics = JobStatisticsRepository(self.store)
        self.invocations = ExecutorCallRepository(self.store)
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
        self.jobs.transition_status(self.job.job_id, S.RUNNING, stage=S.STAGE_PREPARING, event_type="test")
        self.jobs.transition_status(self.job.job_id, S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="test")
        self.jobs.transition_status(self.job.job_id, S.RUNNING, stage=S.STAGE_OBSERVATION, event_type="test")

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
            "design_path": (
                "specs/01-architecture/01-architecture-design/01-build-system/"
                "design.md"
            ),
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


class ObservationFlowTest(_StagedRunIntegrationTest):
    def test_observe_first_pass_publishes_without_correction(self) -> None:
        executor = _JudgmentExecutor()
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(result.completed_items, 2)
        modes = [mode for _, mode in executor.calls]
        self.assertEqual(modes, ["observe", "observe"])
        resources = executor.prompts[0].work_item["input_resources"]
        self.assertTrue(any(resource.get("citable") is True for resource in resources))
        self.assertTrue(any(resource.get("citable") is False for resource in resources))
        embedded = [resource for resource in resources if resource.get("embedded") is True]
        self.assertEqual(len(embedded), 2)
        references = executor.prompts[0].prompt_extras["phase_references"]
        self.assertEqual(
            [reference["name"] for reference in references],
            ["observation-contract", "observation-guide"],
        )
        self.assertTrue(all(reference["content"] for reference in references))
        self.assertTrue(all(
            reference["content_hash"].startswith("sha256:")
            for reference in references
        ))
        policy = executor.prompts[0].prompt_extras["machine_contract"][
            "evidence_path_policy"
        ]
        self.assertTrue(policy["citable_input_paths"])

        feature = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(feature["status"], "complete")
        self.assertEqual(feature["reviewed_claim_ids"], ["Feat-01/AC-1"])
        self.assertEqual(feature["claim_reviews"][0]["evidence_ids"], ["EV-1"])
        self.assertEqual(feature["completed_checks"] != [], True)

        state = json.loads(
            (self.ctx.run_dir / "run-state.json").read_text(encoding="utf-8")
        )
        # both observation work items validated; aggregation has not run yet
        self.assertEqual(state["current_phase"], "aggregation")
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("observations_complete", event_types)
        self.assertNotIn("candidate_invalid", event_types)

        calls = self.invocations.list_for_job(self.job.job_id)
        self.assertEqual(len(calls), 2)
        self.assertEqual({call["attempt_type"] for call in calls}, {"observe"})
        self.assertEqual(calls[0]["executor"], "judgment-fake")
        self.assertTrue(calls[0]["usage"]["usage_reported"])

    def test_one_correction_recovers_an_invalid_observe(self) -> None:
        executor = _JudgmentExecutor(break_first=True)
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        modes = [mode for _, mode in executor.calls]
        # Feat-01: observe(broken) -> correct(fixed); function-global: observe
        self.assertEqual(modes, ["observe", "correct", "observe"])
        correct_prompt = executor.prompts[1]
        self.assertEqual(correct_prompt.prompt_extras["mode"], "correct")
        self.assertEqual(correct_prompt.prompt_extras["payload_kind"], "correction")
        self.assertEqual(
            correct_prompt.prompt_extras["correction_contract"]["format"],
            "json_patch",
        )
        self.assertTrue(
            correct_prompt.prompt_extras["schema_path"].endswith(
                "envelope-correction.schema.json"
            )
        )
        self.assertEqual(correct_prompt.prompt_extras["phase_references"], [])
        self.assertFalse(any(
            str(path).endswith((
                "SKILL.md", "observation-contract.md", "observation-guide.md",
                "aggregation-contract.md", "aggregation-guide.md",
            ))
            for path in correct_prompt.input_paths
        ))
        typed = correct_prompt.prompt_extras["typed_errors"]
        self.assertTrue(any(
            e["code"] == "REASON_LOW_INFORMATION" for e in typed
        ), typed)
        self.assertFalse(
            (self.ctx.run_dir / "observations" / ".Feat-01.json.candidate").exists()
        )
        self.assertFalse(
            (self.ctx.run_dir / "observations" / ".Feat-01.json.typed-errors.json").exists()
        )
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("candidate_invalid", event_types)
        calls = self.invocations.list_for_job(self.job.job_id)
        self.assertEqual(
            [call["attempt_type"] for call in calls], ["observe", "correct", "observe"]
        )

    def test_json_patch_correction_is_merged_by_service(self) -> None:
        executor = _JudgmentExecutor(
            break_first=True,
            json_patch_correction=True,
        )
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(
            [mode for _, mode in executor.calls], ["observe", "correct", "observe"]
        )
        published = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("after source verification", published["claim_reviews"][0]["reason"])

    def test_unknown_criterion_uses_one_model_correction_and_reprojects(self) -> None:
        executor = _JudgmentExecutor(invalid_criterion_once=True)
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )

        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(
            [mode for _, mode in executor.calls],
            ["observe", "correct", "observe"],
        )
        correction = executor.prompts[1]
        self.assertEqual(
            {error["code"] for error in correction.prompt_extras["typed_errors"]},
            {"CRITERION_UNKNOWN", "EVIDENCE_KEY_UNKNOWN"},
        )
        valid_ids = correction.prompt_extras["machine_contract"][
            "valid_criterion_ids"
        ]
        self.assertIn("CORRECTNESS-SOURCE-SUPPORT", valid_ids)
        self.assertEqual(
            correction.prompt_extras["correction_contract"][
                "allowed_values_by_path"
            ]["/observations/0/criterion_ids"],
            list(valid_ids),
        )
        published = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            published["observations"][0]["criterion_ids"],
            ["CORRECTNESS-SOURCE-SUPPORT"],
        )
        self.assertEqual(
            published["claim_reviews"][0]["criterion_ids"],
            ["CORRECTNESS-SOURCE-SUPPORT"],
        )

    def test_service_repairs_primary_mapping_reintroduced_by_correction(self) -> None:
        executor = _JudgmentExecutor(
            break_first=True,
            correction_primary_mismatch=True,
        )
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        published = json.loads(
            (self.ctx.run_dir / "observations" / "Feat-01.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(
            "SPEC-TRACEABILITY",
            published["observations"][0]["criterion_ids"],
        )
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("correction_deterministic_repaired", event_types)

    def test_empty_observation_claim_ids_is_service_terminal_without_model(self) -> None:
        executor = _JudgmentExecutor(empty_observation_claims_once=True)
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertEqual([mode for _, mode in executor.calls], ["observe"])
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("candidate_invalid", event_types)

    def test_function_global_service_path_gets_one_correction(self) -> None:
        executor = _JudgmentExecutor(invalid_global_path_once=True)
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(
            [mode for _, mode in executor.calls],
            ["observe", "observe", "correct"],
        )
        correction = executor.prompts[-1]
        errors = correction.prompt_extras["typed_errors"]
        self.assertTrue(errors)
        self.assertEqual(
            {error["code"] for error in errors},
            {"EVIDENCE_PATH_NOT_ALLOWED"},
        )
        candidate = executor.correction_candidates[-1]
        self.assertEqual(
            candidate["evidence_declarations"][0]["path"],
            "runs/run-1/staged/output-contract.json",
        )

    def test_raw_payload_patch_is_normalized_before_validation(self) -> None:
        executor = _JudgmentExecutor(
            invalid_global_path_once=True,
            json_patch_evidence_correction=True,
        )
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )

        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        self.assertEqual(
            [mode for _, mode in executor.calls],
            ["observe", "observe", "correct"],
        )
        correction = executor.prompts[-1]
        self.assertEqual(
            correction.prompt_extras["correction_contract"]["base"],
            "raw_payload",
        )
        self.assertTrue(any(
            "normalize it again" in constraint
            for constraint in correction.prompt_extras["correction_constraints"]
        ))
        published = json.loads(
            (self.ctx.run_dir / "observations" / "function-global.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(published["status"], "complete")
        self.assertEqual(
            published["reviewed_claim_ids"],
            published["expected_claim_ids"],
        )
        self.assertFalse(
            (self.ctx.run_dir / "observations" / ".function-global.json.candidate").exists()
        )
        self.assertFalse(
            (self.ctx.run_dir / "observations" / ".function-global.json.typed-errors.json").exists()
        )

    def test_correction_still_model_invalid_is_warning(self) -> None:
        executor = _JudgmentExecutor(break_all=True)
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        modes = [mode for _, mode in executor.calls]
        self.assertEqual(
            modes, ["observe", "correct", "observe", "correct"]
        )  # exactly one semantic correction per work item
        work_items = json.loads(
            (self.ctx.run_dir / "work-items.json").read_text(encoding="utf-8")
        )
        feat = next(
            item for item in work_items["items"] if item["id"] == "feature:Feat-01"
        )
        self.assertEqual(feat["execution_state"], "VALIDATED")
        # The consumable candidate is published; unresolved model errors are
        # retained in the correction-completed warning event for confidence
        # deduction by the downstream publisher.
        candidate = self.ctx.run_dir / "observations" / ".Feat-01.json.candidate"
        errors = self.ctx.run_dir / "observations" / ".Feat-01.json.typed-errors.json"
        self.assertFalse(candidate.exists())
        self.assertFalse(errors.exists())
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("correction_completed_with_warnings", event_types)

    def test_interrupted_attempt_resumes_into_correction(self) -> None:
        executor = _JudgmentExecutor(break_first=True)
        # first run: observe invalid -> correction published... simulate an
        # interruption right after the observe by failing the correction call
        class _Interrupted(_JudgmentExecutor):
            def execute(self, work, emit, cancel=None):
                if work.prompt_extras.get("mode") == "correct":
                    self.calls.append((work.work_item_id, "correct"))
                    return C.ExecutionResult(
                        status=C.STATUS_AWAITING, error="interrupted"
                    )
                return super().execute(work, emit, cancel)

        interrupted = _Interrupted(break_first=True)
        result = run_semantic(
            self.ctx, interrupted,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_AWAITING)
        self.assertEqual(
            self.jobs.get_job(self.job.job_id).status, S.WAITING
        )
        # resume: the stored candidate skips the observe turn entirely
        resume = _JudgmentExecutor()
        result = run_semantic(
            self.ctx, resume,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED, result.error)
        modes = [mode for _, mode in resume.calls]
        self.assertEqual(modes, ["correct", "observe"])
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("candidate_resumed", event_types)


class ExecutorModeSurfaceTest(unittest.TestCase):
    def test_deleted_modes_are_gone(self) -> None:
        import inspect

        from spec_eval.service.pipeline import result_payload, semantic_stage

        source = inspect.getsource(result_payload) + inspect.getsource(semantic_stage)
        for banned in (
            "repair_claim_evidence_references",
            "retry_degenerate_observation",
            "retry_after_repair_rejection",
            "reconcile_aggregation_candidate",
            "complete_observation_evidence",
            "repair_candidate",
            "_EXECUTOR_QUALITY_EVALUATOR_VERSIONS",
        ):
            self.assertNotIn(banned, source, banned)


if __name__ == "__main__":
    unittest.main()
