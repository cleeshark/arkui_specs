"""Host unit + integration tests for the Phase 2 pipeline (TASK-011-03/04).

The semantic loop is driven with a FakeExecutor and a FakeScriptRunner so the
loop mechanics (executor dispatch, observation write, validate, checkpoint,
status transitions, awaiting/failed/cancelled) are covered without burning
Codex quota or producing a fully valid observation. One integration test runs
the REAL staged scripts against a real cached evidence package to confirm the
wrappers invoke them correctly.

    python3 -m unittest spec_eval.tests.test_next_011_pipeline -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline.context import RunContext
from spec_eval.service.pipeline.evidence_stage import EvidenceStageError, prepare_evidence
from spec_eval.service.pipeline.report_stage import ReportStageError, run_report
from spec_eval.service.pipeline.semantic_stage import run_job_pipeline, run_semantic
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore
from spec_eval.service.workspace.models import EvaluationWorkspace

EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.1.15"
JOB_ID = "c" * 40


# --- fakes ------------------------------------------------------------------

class FakeExecutor:
    """Writes a minimal valid executor-result; configurable to fail/await."""

    def __init__(self, *, fail_on: set[str] | None = None, awaiting: bool = False) -> None:
        self.fail_on = fail_on or set()
        self.awaiting = awaiting
        self.calls: list[str] = []

    def is_available(self) -> bool:
        return not self.awaiting

    def describe(self) -> dict:
        return {"type": "fake"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.calls.append(work.work_item_id)
        emit(C.ExecutionEvent(kind="command", message="fake-executor"))
        if self.awaiting:
            return C.ExecutionResult(status=C.STATUS_AWAITING, error="no executor")
        if work.work_item_id in self.fail_on:
            return C.ExecutionResult(status=C.STATUS_FAILED, error="injected failure")
        payload = (
            {
                "cross_feat_contracts_reviewed": True,
                "contradiction_bases": [],
                "defect_ownership": [],
                "outcome_policy_bases": [],
                "criterion_results": [],
                "notes": [],
            }
            if work.work_item_id == "aggregation:final"
            else {
                "claim_reviews": [],
                "observations": [],
                "open_questions": [],
                "notes": [],
            }
        )
        doc = {
            "schema_version": 2,
            "work_item_id": work.work_item_id,
            "status": "completed",
            "observation_json": json.dumps(payload),
            "notes": [],
            "error": None,
        }
        Path(work.executor_result_path).parent.mkdir(parents=True, exist_ok=True)
        Path(work.executor_result_path).write_text(json.dumps(doc), encoding="utf-8")
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED,
            exit_code=0,
            executor_result_path=work.executor_result_path,
            observation=payload,
            elapsed_seconds=0.5,
            token_usage={
                "input_tokens": 8,
                "cached_input_tokens": 2,
                "cache_write_input_tokens": 0,
                "output_tokens": 3,
                "reasoning_output_tokens": 1,
                "total_tokens": 11,
            },
            usage_reported=True,
        )


class FakeScriptRunner:
    """Simulates the staged-run skill scripts from their argv."""

    def __init__(self, work_items: list[dict]) -> None:
        self.work_items = list(work_items)
        self.calls: list[list[str]] = []

    def __call__(self, argv, *, cwd, timeout):
        self.calls.append(list(argv))
        joined = " ".join(argv)
        if "initialize_staged_run.py" in joined:
            return subprocess.CompletedProcess(argv, 0, "", "")
        if "show_next_work_item.py" in joined:
            if self.work_items:
                item = self.work_items.pop(0)
                return subprocess.CompletedProcess(
                    argv, 0, json.dumps({"current_phase": "semantic", "work_item": item}), ""
                )
            return subprocess.CompletedProcess(
                argv, 0, json.dumps({"current_phase": "aggregation", "next_action": "done"}), ""
            )
        if "validate_staged_run.py" in joined:
            return subprocess.CompletedProcess(argv, 0, "", "")
        if "assemble_semantic_result.py" in joined:
            run_dir = next((a for i, a in enumerate(argv) if i and argv[i - 1] == "--run-dir"), None)
            if run_dir:
                Path(run_dir, "semantic-result.json").write_text("{}", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "", "")
        # spec_eval score/stability/report: write dummy outputs to the */write paths
        for flag in ("--write", "--analysis-write", "--json-write", "--markdown-write"):
            for i, a in enumerate(argv):
                if a == flag and i + 1 < len(argv):
                    Path(argv[i + 1]).parent.mkdir(parents=True, exist_ok=True)
                    content = b"{}\n" if argv[i + 1].endswith(".json") else b"# report\n"
                    Path(argv[i + 1]).write_bytes(content)
        return subprocess.CompletedProcess(argv, 0, "", "")


# --- fixtures ---------------------------------------------------------------

class _PipelineTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.attempts = AttemptRepository(self.store)
        self.events = EventRepository(self.store)
        self.artifacts = ArtifactRepository(self.store)
        self.snapshots = DependencySnapshotRepository(self.store)
        self.statistics = JobStatisticsRepository(self.store)
        job = self.jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev-abc", run_count=1, job_id=JOB_ID),
            evaluator_version=EVALUATOR_VERSION,
        )
        self.ctx = RunContext.for_run(
            self.settings,
            job_id=job.job_id,
            func_id=job.func_id,
            source_revision=job.source_revision,
            run_id="run-1",
            evaluator_version=job.evaluator_version,
        )
        self.obs_dir = self.ctx.run_dir.parent / "obs"
        self.obs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _items(self, ids: list[str]) -> list[dict]:
        items: list[dict] = []
        for wid in ids:
            item_type = "feature" if wid.startswith("feature:") else "function_global"
            output_path = self.obs_dir / f"{wid.replace(':', '_')}.json"
            item = {
                "id": wid,
                "type": item_type,
                "feat_id": wid.split(":")[-1] if item_type == "feature" else None,
                "input_paths": [],
                "output_path": str(output_path),
                "expected_claim_ids": [],
                "required_checks": [],
            }
            output_path.write_text(
                json.dumps({
                    "schema_version": 2,
                    "evaluator_version": EVALUATOR_VERSION,
                    "func_id": self.ctx.func_id,
                    "source_revision": self.ctx.source_revision,
                    "run_id": self.ctx.run_id,
                    "observation_id": wid,
                    "observation_type": item_type,
                    "status": "pending",
                    "input_paths": [],
                    "expected_claim_ids": [],
                    "reviewed_claim_ids": [],
                    "claim_reviews": [],
                    "completed_checks": [],
                    "observations": [],
                    "open_questions": [],
                    "notes": [],
                }),
                encoding="utf-8",
            )
            items.append(item)
        self.ctx.run_dir.mkdir(parents=True, exist_ok=True)
        (self.ctx.run_dir / "work-items.json").write_text(
            json.dumps({"items": items}), encoding="utf-8"
        )
        (self.ctx.run_dir / "aggregation.json").write_text(
            json.dumps({
                "schema_version": 2,
                "evaluator_version": EVALUATOR_VERSION,
                "func_id": self.ctx.func_id,
                "source_revision": self.ctx.source_revision,
                "run_id": self.ctx.run_id,
                "status": "pending",
                "source_observation_ids": [],
                "cross_feat_contracts_reviewed": False,
                "contradiction_bases": [],
                "defect_ownership": [],
                "outcome_policy_bases": [],
                "criterion_results": [],
                "notes": [],
            }),
            encoding="utf-8",
        )
        return items

    def _to_semantic(self) -> None:
        """Advance the fresh job to SEMANTIC via the legal transition chain."""
        self.jobs.transition_status(JOB_ID, S.PREPARING, event_type="enter_preparing")
        self.jobs.transition_status(JOB_ID, S.EVIDENCE, event_type="enter_evidence")
        self.jobs.transition_status(JOB_ID, S.SEMANTIC, event_type="enter_semantic")

    def _write_evidence(self, package: Path | None = None, *, revision: str | None = None) -> Path:
        package = package or self.ctx.input_dir
        package.mkdir(parents=True, exist_ok=True)
        body = {"func_id": self.ctx.func_id, "source_revision": revision or self.ctx.source_revision}
        for name in ("function-context.json", "static-result.json", "evidence-manifest.json"):
            (package / name).write_text(json.dumps(body), encoding="utf-8")
        return package

    def _workspace(self, job) -> EvaluationWorkspace:
        return EvaluationWorkspace.control_checkout(self.settings, job.source_revision)


# --- run_semantic loop tests ------------------------------------------------

class RunSemanticTest(_PipelineTestBase):
    def test_completes_all_items_and_records_checkpoints(self) -> None:
        self._to_semantic()
        executor = FakeExecutor()
        runner = FakeScriptRunner(self._items(["feature:Feat-01", "function:global"]))
        result = run_semantic(
            self.ctx, executor, jobs=self.jobs, attempts=self.attempts,
            events=self.events, statistics=self.statistics, runner=runner,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED)
        self.assertEqual(result.completed_items, 2)
        self.assertEqual(executor.calls, ["feature:Feat-01", "function:global"])
        # one completed checkpoint per work item, all in the semantic stage
        ckpts = self.attempts.list_for_job(JOB_ID, stage=S.STAGE_SEMANTIC)
        self.assertEqual(len(ckpts), 2)
        for ckpt in ckpts:
            self.assertEqual(ckpt.status, S.ATTEMPT_COMPLETED)
        # observation files were written
        self.assertTrue((self.obs_dir / "feature_Feat-01.json").is_file())
        # observations_complete event recorded
        types = [e.event_type for e in self.events.list_for_job(JOB_ID)]
        self.assertIn("observations_complete", types)
        statistics = self.statistics.get(JOB_ID)
        self.assertEqual(statistics.executor_invocations, 2)
        self.assertEqual(statistics.executor_elapsed_ms, 1000)
        self.assertEqual(statistics.total_tokens, 22)

    def test_awaiting_executor_pauses_job(self) -> None:
        self._to_semantic()
        executor = FakeExecutor(awaiting=True)
        runner = FakeScriptRunner(self._items(["feature:Feat-01"]))
        result = run_semantic(
            self.ctx, executor, jobs=self.jobs, attempts=self.attempts, events=self.events, runner=runner
        )
        self.assertEqual(result.outcome, C.STATUS_AWAITING)
        self.assertEqual(self.jobs.get_job(JOB_ID).status, S.AWAITING_EXECUTOR)
        # no checkpoint completed while awaiting
        self.assertEqual(len(self.attempts.list_for_job(JOB_ID)), 0)

    def test_executor_failure_fails_job(self) -> None:
        self._to_semantic()
        executor = FakeExecutor(fail_on={"feature:Feat-01"})
        runner = FakeScriptRunner(self._items(["feature:Feat-01"]))
        result = run_semantic(
            self.ctx, executor, jobs=self.jobs, attempts=self.attempts, events=self.events, runner=runner
        )
        self.assertEqual(result.outcome, C.STATUS_FAILED)
        self.assertEqual(self.jobs.get_job(JOB_ID).status, S.FAILED)

    def test_pre_set_cancel_returns_cancelled(self) -> None:
        self._to_semantic()
        cancel = threading.Event()
        cancel.set()
        runner = FakeScriptRunner(self._items(["feature:Feat-01"]))
        result = run_semantic(
            self.ctx, FakeExecutor(),
            jobs=self.jobs, attempts=self.attempts, events=self.events,
            cancel=cancel, runner=runner,
        )
        self.assertEqual(result.outcome, C.STATUS_CANCELLED)

    def test_resume_skips_init_when_run_state_exists(self) -> None:
        # simulate a previously-initialized run
        self.ctx.run_dir.mkdir(parents=True, exist_ok=True)
        (self.ctx.run_dir / "run-state.json").write_text("{}", encoding="utf-8")
        runner = FakeScriptRunner([])  # no items -> completes immediately
        run_semantic(
            self.ctx, FakeExecutor(),
            jobs=self.jobs, attempts=self.attempts, events=self.events, runner=runner,
        )
        # initialize_staged_run.py must NOT have been called
        self.assertFalse(
            any("initialize_staged_run.py" in " ".join(c) for c in runner.calls)
        )


# --- run_job_pipeline driver test ------------------------------------------

class RunJobPipelineTest(_PipelineTestBase):
    def test_fresh_job_runs_to_completion(self) -> None:
        # pre-seed the evidence input-dir so the real evidence build is skipped
        self._write_evidence()
        executor = FakeExecutor()
        runner = FakeScriptRunner(self._items(["feature:Feat-01"]))
        result = run_job_pipeline(
            JOB_ID,
            settings=self.settings, jobs=self.jobs, attempts=self.attempts,
            events=self.events, artifacts=self.artifacts, snapshots=self.snapshots,
            executor=executor, workspace_provider=self._workspace, runner=runner,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED)
        job = self.jobs.get_job(JOB_ID)
        # full legal path queued -> preparing -> evidence -> semantic -> aggregation
        # -> archive -> site_history -> completed
        self.assertEqual(job.status, S.COMPLETED)
        types = [e.event_type for e in self.events.list_for_job(JOB_ID)]
        for stage in ("enter_preparing", "enter_evidence", "enter_semantic",
                      "enter_aggregation", "enter_archive", "enter_site_history",
                      "job_completed"):
            self.assertIn(stage, types)
        # dependency snapshot frozen for at least the ace_engine repo
        snaps = self.snapshots.list_for_job(JOB_ID)
        self.assertTrue(any(s.repo_name == "ace_engine" and s.status == "frozen" for s in snaps))
        # automated archive produced
        archive_dir = self.settings.archives_root / job.source_revision / job.func_id / job.job_id
        self.assertTrue((archive_dir / "archive-manifest.json").is_file())


# --- gate-fail exit codes ----------------------------------------------------

class GateFailExitCodeTest(_PipelineTestBase):
    """The spec_eval CLI exits 1 when a *gate* is "fail" (static gate for
    ``evidence``, effective gate for ``score``/``report``) even though all
    outputs are written. Findings producing a fail gate are the normal input
    for semantic evaluation, so the pipeline must keep running; only rc >= 2
    (SpecEvalError / gate "error") is a stage failure."""

    def _evidence_runner(self, rc: int):
        def runner(argv, *, cwd, timeout):
            self._write_evidence()
            return subprocess.CompletedProcess(argv, rc, "", "")
        return runner

    def test_evidence_static_gate_fail_is_not_an_error(self) -> None:
        package = prepare_evidence(self.ctx, runner=self._evidence_runner(1))
        self.assertTrue((package / "static-result.json").is_file())

    def test_evidence_spec_eval_error_still_raises(self) -> None:
        with self.assertRaises(EvidenceStageError):
            prepare_evidence(self.ctx, runner=self._evidence_runner(2))

    def _report_runner(self, rc: int, *, write_outputs: bool = True):
        def runner(argv, *, cwd, timeout):
            if write_outputs:
                for flag in ("--write", "--analysis-write", "--json-write", "--markdown-write"):
                    for i, arg in enumerate(argv):
                        if arg == flag and i + 1 < len(argv):
                            Path(argv[i + 1]).parent.mkdir(parents=True, exist_ok=True)
                            content = "{}\n" if argv[i + 1].endswith(".json") else "# report\n"
                            Path(argv[i + 1]).write_text(content, encoding="utf-8")
            return subprocess.CompletedProcess(argv, rc, "", "")
        return runner

    def _semantic_results(self) -> dict[str, Path]:
        sr = self.ctx.run_dir / "semantic-result.json"
        sr.parent.mkdir(parents=True, exist_ok=True)
        sr.write_text("{}", encoding="utf-8")
        return {"run-1": sr}

    def test_report_effective_gate_fail_is_not_an_error(self) -> None:
        outputs = run_report(
            self.ctx, semantic_results=self._semantic_results(), selected_run_id="run-1",
            runner=self._report_runner(1),
        )
        self.assertTrue(all(p.is_file() for p in outputs.values()))

    def test_report_spec_eval_error_still_raises(self) -> None:
        with self.assertRaises(ReportStageError):
            run_report(
                self.ctx, semantic_results=self._semantic_results(), selected_run_id="run-1",
                runner=self._report_runner(2),
            )

    def test_report_missing_output_after_gate_fail_raises(self) -> None:
        # rc 1 accepted only when the outputs were actually written
        with self.assertRaises(ReportStageError):
            run_report(
                self.ctx, semantic_results=self._semantic_results(), selected_run_id="run-1",
                runner=self._report_runner(1, write_outputs=False),
            )


# --- evidence package layout (issue #9) ---------------------------------------

class EvidenceLayoutTest(_PipelineTestBase):
    """Evidence is accepted only from the Job's exact frozen revision path."""

    def _package(self, rev: str) -> Path:
        package = self.ctx.evidence_output_root / rev / self.ctx.func_id
        return self._write_evidence(package, revision=rev)

    def _runner(self, rc: int = 0):
        def runner(argv, *, cwd, timeout):
            self._package(self.ctx.source_revision)
            return subprocess.CompletedProcess(argv, rc, "", "")
        return runner

    def test_prepare_uses_exact_revision_dir(self) -> None:
        package = prepare_evidence(self.ctx, runner=self._runner())
        self.assertEqual(package, self.ctx.input_dir)

    def test_ctx_input_dir_does_not_follow_another_revision(self) -> None:
        self._package("7" * 40)
        ctx = RunContext.for_run(
            self.settings, job_id=JOB_ID, func_id=self.ctx.func_id,
            source_revision="rev-abc", run_id="run-2",
        )
        self.assertEqual(ctx.input_dir, self.ctx.evidence_output_root / "rev-abc" / self.ctx.func_id)

    def test_retry_does_not_select_newer_wrong_revision(self) -> None:
        self._package("9" * 40)
        with self.assertRaises(EvidenceStageError):
            prepare_evidence(
                self.ctx,
                runner=lambda argv, *, cwd, timeout: subprocess.CompletedProcess(argv, 0, "", ""),
            )

    def test_revision_mismatch_inside_exact_dir_raises(self) -> None:
        def runner(argv, *, cwd, timeout):
            self._write_evidence(revision="wrong-revision")
            return subprocess.CompletedProcess(argv, 0, "", "")
        with self.assertRaisesRegex(EvidenceStageError, "source revision mismatch"):
            prepare_evidence(self.ctx, runner=runner)

    def test_no_package_written_raises(self) -> None:
        def runner(argv, *, cwd, timeout):
            return subprocess.CompletedProcess(argv, 0, "", "")
        with self.assertRaises(EvidenceStageError):
            prepare_evidence(self.ctx, runner=runner)


# --- real staged-script integration on cached evidence ----------------------

class StagedScriptIntegrationTest(unittest.TestCase):
    """Runs the REAL initialize/show_next scripts against a cached evidence dir."""

    def setUp(self) -> None:
        # locate a real cached evidence package under specs/.evaluator/<rev>/<FuncID>/
        evaluator_root = (
            Path(__file__).resolve().parents[3] / ".evaluator"
        )
        self.func_id: str | None = None
        self.fixture: Path | None = None
        if evaluator_root.is_dir():
            for rev_dir in evaluator_root.iterdir():
                if not rev_dir.is_dir() or len(rev_dir.name) != 40:
                    continue
                for cand in sorted(rev_dir.iterdir()):
                    if (
                        cand.is_dir()
                        and (cand / "function-context.json").is_file()
                        and (cand / "static-result.json").is_file()
                        and (cand / "evidence-manifest.json").is_file()
                    ):
                        self.func_id = cand.name
                        self.fixture = cand
                        break
                if self.fixture:
                    break

    def test_real_init_and_show_next(self) -> None:
        if self.fixture is None:
            self.skipTest("no cached evidence package under specs/.evaluator; skipping integration test")
        tmp = tempfile.TemporaryDirectory()
        try:
            fixture_revision = json.loads(
                (self.fixture / "function-context.json").read_text(encoding="utf-8")
            )["source_revision"]
            settings = ServiceSettings.discover(data_root=Path(tmp.name))
            store = SqliteStore(settings)
            jobs = JobRepository(store)
            job = jobs.create_job(
                CreateJobCommand(
                    func_id=self.func_id,  # type: ignore[arg-type]
                    source_revision=fixture_revision,
                    run_count=1,
                    job_id="d" * 40,
                ),
                evaluator_version=EVALUATOR_VERSION,
            )
            ctx = RunContext.for_run(
                settings, job_id=job.job_id, func_id=job.func_id,
                source_revision=fixture_revision, run_id="run-1",
                evaluator_version=EVALUATOR_VERSION,
            )
            # copy the cached evidence package into place as the input-dir
            shutil.copytree(self.fixture, ctx.input_dir)  # type: ignore[arg-type]

            from spec_eval.service.pipeline import staged_stage

            staged_stage.init_staged_run(ctx)  # real subprocess
            self.assertTrue((ctx.run_dir / "run-state.json").is_file())
            self.assertTrue((ctx.run_dir / "work-items.json").is_file())
            item = staged_stage.next_work_item(ctx)  # real subprocess
            self.assertIsInstance(item, dict)
            self.assertIn("id", item)
            self.assertIn("output_path", item)
            store.close()
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
