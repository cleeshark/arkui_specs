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

EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.2.0"
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
    ) -> None:
        self.break_first = break_first
        self.break_all = break_all
        self.calls: list[tuple[str, str]] = []
        self.prompts: list[C.WorkItemInput] = []

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
            # claim set mismatch + low-information prose: guaranteed typed errors
            claims = claims[: max(0, len(claims) - 1)]
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
                            "fact": "ok",
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
        emit(C.ExecutionEvent(kind="command", message="fake"))
        broken = (self.break_first and mode == "observe" and is_first_call) or (
            self.break_all
        )
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED,
            exit_code=0,
            executor_result_path=work.executor_result_path,
            observation=self._payload(work, broken=broken),
            elapsed_seconds=0.25,
            token_usage={
                "input_tokens": 10, "cached_input_tokens": 0,
                "cache_write_input_tokens": 0, "output_tokens": 5,
                "reasoning_output_tokens": 0, "total_tokens": 15,
            },
            usage_reported=True,
        )


def _first_input(work: C.WorkItemInput) -> str:
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
        typed = correct_prompt.prompt_extras["typed_errors"]
        # the missing claim surfaces as a pending placeholder row whose NV
        # obligations are unmet: accurate typed errors either way
        self.assertTrue(any(e["code"] in {
            "CLAIM_SET_MISMATCH", "REASON_PLACEHOLDER",
            "REASON_LOW_INFORMATION", "GAP_MISSING_FOR_NV",
        } for e in typed), typed)
        event_types = [
            event.event_type for event in self.events.list_for_job(self.job.job_id)
        ]
        self.assertIn("candidate_invalid", event_types)
        calls = self.invocations.list_for_job(self.job.job_id)
        self.assertEqual(
            [call["attempt_type"] for call in calls], ["observe", "correct", "observe"]
        )

    def test_correction_still_invalid_is_terminal(self) -> None:
        executor = _JudgmentExecutor(break_all=True)
        result = run_semantic(
            self.ctx, executor,
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            statistics=self.statistics, invocations=self.invocations,
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertIn("still invalid", result.error or "")
        modes = [mode for _, mode in executor.calls]
        self.assertEqual(modes, ["observe", "correct"])  # exactly one correction
        work_items = json.loads(
            (self.ctx.run_dir / "work-items.json").read_text(encoding="utf-8")
        )
        feat = next(
            item for item in work_items["items"] if item["id"] == "feature:Feat-01"
        )
        self.assertEqual(feat["execution_state"], "CORRECTION_INVALID_TERMINAL")
        # candidate + typed errors stay on disk as the failure artifact
        candidate = self.ctx.run_dir / "observations" / ".Feat-01.json.candidate"
        errors = self.ctx.run_dir / "observations" / ".Feat-01.json.typed-errors.json"
        self.assertTrue(candidate.is_file())
        self.assertTrue(errors.is_file())

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
