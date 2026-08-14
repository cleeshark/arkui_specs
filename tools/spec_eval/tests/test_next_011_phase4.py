"""Host unit tests for the Phase 4 stages (TASK-011-07 / TASK-011-08).

* report_stage: orchestration (argv + outputs + failure) via a fake runner; the
  real determinism of score/stability/report is already covered by the
  test_next_008_* suite.
* archive_stage: REAL atomic write + SHA-256 manifest + idempotency.
* site_history_stage: REAL snapshot + automated-namespace isolation (confirmed
  review/history bytes unchanged).
* aggregation_stage + driver: orchestration via FakeExecutor/FakeScriptRunner,
  ending in COMPLETED with an archive.

    python3 -m unittest spec_eval.tests.test_next_011_phase4 -v
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import Attempt, CreateJobCommand, Job, make_job_id, default_progress
from spec_eval.service.executors import contract as C
from spec_eval.service.pipeline import aggregation_stage, archive_stage, report_stage, site_history_stage
from spec_eval.service.pipeline.context import RunContext
from spec_eval.service.pipeline.semantic_stage import run_job_pipeline
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EvaluationReportRepository,
    EventRepository,
    FunctionReportHeadRepository,
    JobRepository,
    RefreshTargetRepository,
    ReportDeltaRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore, utc_now
from spec_eval.service.workspace.models import EvaluationWorkspace

EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.1.12"


# --- fakes ------------------------------------------------------------------

class _FakeExecutor:
    """Handles observation work items and the aggregation:final item."""

    def __init__(self, *, fail_aggregation: bool = False) -> None:
        self.fail_aggregation = fail_aggregation
        self.calls: list[str] = []

    def is_available(self) -> bool:
        return True

    def describe(self) -> dict:
        return {"type": "fake"}

    def execute(self, work: C.WorkItemInput, emit, cancel=None) -> C.ExecutionResult:
        self.calls.append(work.work_item_id)
        emit(C.ExecutionEvent(kind="command", message="fake"))
        if work.work_item_id == "aggregation:final" and self.fail_aggregation:
            return C.ExecutionResult(status=C.STATUS_FAILED, error="injected aggregation failure")
        body = (
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
        Path(work.executor_result_path).parent.mkdir(parents=True, exist_ok=True)
        Path(work.executor_result_path).write_text(
            json.dumps({
                "schema_version": 2,
                "work_item_id": work.work_item_id,
                "status": "completed",
                "observation_json": json.dumps(body),
                "notes": [],
                "error": None,
            }),
            encoding="utf-8",
        )
        return C.ExecutionResult(
            status=C.STATUS_COMPLETED,
            exit_code=0,
            executor_result_path=work.executor_result_path,
            observation=body,
        )


class _FakeScriptRunner:
    """Handles skill scripts AND spec_eval score/stability/report argv."""

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
                return subprocess.CompletedProcess(argv, 0, json.dumps({"work_item": item}), "")
            return subprocess.CompletedProcess(argv, 0, json.dumps({"next_action": "done"}), "")
        if "validate_staged_run.py" in joined:
            return subprocess.CompletedProcess(argv, 0, "", "")
        if "assemble_semantic_result.py" in joined:
            # write the semantic-result.json the assembler would produce
            run_dir = _argv_value(argv, "--run-dir")
            if run_dir:
                Path(run_dir, "semantic-result.json").write_text("{}", encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, "", "")
        # spec_eval score/stability/report: write dummy outputs to --*/write paths
        for flag in ("--write", "--analysis-write", "--json-write", "--markdown-write"):
            value = _argv_value(argv, flag)
            if value:
                Path(value).parent.mkdir(parents=True, exist_ok=True)
                content = b"{}\n" if value.endswith(".json") else b"# report\n"
                Path(value).write_bytes(content)
        return subprocess.CompletedProcess(argv, 0, "", "")


def _argv_value(argv: list[str], flag: str) -> str | None:
    for i, token in enumerate(argv):
        if token == flag and i + 1 < len(argv):
            return argv[i + 1]
    return None


def _make_job(job_id: str = "p" * 40, func_id: str = "04-01-01", run_count: int = 1) -> Job:
    now = utc_now()
    return Job(
        job_id=job_id, func_id=func_id, source_revision="rev-" + func_id,
        run_count=run_count, selected_run_ids=(), status=S.COMPLETED,
        progress=default_progress(S.COMPLETED), executor_config={},
        protocol_version="0.1.0", evaluator_version=EVALUATOR_VERSION,
        created_at=now, updated_at=now,
    )


# --- report_stage -----------------------------------------------------------

class ReportStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        job = JobRepository(self.store).create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=1, job_id="p" * 40),
            evaluator_version=EVALUATOR_VERSION,
        )
        self.ctx = RunContext.for_run(
            self.settings, job_id=job.job_id, func_id=job.func_id,
            source_revision=job.source_revision, run_id="run-1", evaluator_version=EVALUATOR_VERSION,
        )
        self.ctx.input_dir.mkdir(parents=True, exist_ok=True)
        (self.ctx.input_dir / "static-result.json").write_text("{}", encoding="utf-8")
        (self.ctx.input_dir / "evidence-manifest.json").write_text("{}", encoding="utf-8")
        self.semantic_result = self.ctx.run_dir / "semantic-result.json"
        self.semantic_result.parent.mkdir(parents=True, exist_ok=True)
        self.semantic_result.write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_orchestrates_score_stability_report(self) -> None:
        outputs = report_stage.run_report(
            self.ctx, semantic_results={"run-1": self.semantic_result},
            selected_run_id="run-1", runner=_FakeScriptRunner([]),
        )
        for key in ("score", "analysis", "stability", "report_json", "report_md"):
            self.assertTrue(outputs[key].is_file(), key)

    def test_unknown_selected_run_raises(self) -> None:
        with self.assertRaises(report_stage.ReportStageError):
            report_stage.run_report(
                self.ctx, semantic_results={"run-1": self.semantic_result},
                selected_run_id="run-9", runner=_FakeScriptRunner([]),
            )

    def test_command_failure_propagates(self) -> None:
        def failing_runner(argv, *, cwd, timeout):
            return subprocess.CompletedProcess(argv, 3, "", "boom")
        with self.assertRaises(report_stage.ReportStageError):
            report_stage.run_report(
                self.ctx, semantic_results={"run-1": self.semantic_result},
                selected_run_id="run-1", runner=failing_runner,
            )


# --- archive_stage (real) ---------------------------------------------------

class ArchiveStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _artifacts(self, job_root: Path) -> tuple[dict[str, Path], dict[str, Path], Path]:
        sr = job_root / "semantic-result-run-1.json"
        sr.write_text('{"semantic": true}', encoding="utf-8")
        agg = {
            "score": job_root / "score-result.json",
            "analysis": job_root / "function-analysis.json",
            "stability": job_root / "stability-result.json",
            "report_json": job_root / "evaluation-report.json",
            "report_md": job_root / "function-report.md",
        }
        for p in agg.values():
            p.write_text('{"x":1}', encoding="utf-8") if p.suffix == ".json" else p.write_text("# md", encoding="utf-8")
        snapshot = job_root / "site-history-snapshot.json"
        snapshot.write_text('{"ns":"automated"}', encoding="utf-8")
        return {"run-1": sr}, agg, snapshot

    def test_manifest_has_sha256_and_atomic_publish(self) -> None:
        job = _make_job()
        job_root = self.settings.jobs_root / job.job_id
        job_root.mkdir(parents=True)
        sr, agg, snap = self._artifacts(job_root)
        archive_dir = archive_stage.write_archive(
            self.settings, job, semantic_results=sr, aggregate_outputs=agg,
            run_ids=["run-1"], selected_run_id="run-1", site_snapshot_path=snap,
        )
        self.assertTrue(archive_dir.is_dir())
        manifest = json.loads((archive_dir / "archive-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["namespace"], "automated")
        self.assertEqual(manifest["func_id"], job.func_id)
        # every recorded file has a valid sha256 + matching size
        for entry in manifest["files"]:
            self.assertTrue(entry["sha256"].startswith("sha256:"))
            data = (archive_dir / entry["path"]).read_bytes()
            self.assertEqual(entry["sha256"], "sha256:" + hashlib.sha256(data).hexdigest())
            self.assertEqual(entry["size"], len(data))
        # no temp dir left behind
        self.assertFalse(any(p.name.startswith(archive_dir.name + ".tmp") for p in archive_dir.parent.iterdir()))

    def test_re_archive_is_idempotent(self) -> None:
        job = _make_job()
        job_root = self.settings.jobs_root / job.job_id
        job_root.mkdir(parents=True)
        sr, agg, snap = self._artifacts(job_root)
        kwargs = dict(semantic_results=sr, aggregate_outputs=agg, run_ids=["run-1"],
                      selected_run_id="run-1", site_snapshot_path=snap)
        first = archive_stage.write_archive(self.settings, job, **kwargs)
        before = (first / "aggregate-score-score-result.json").read_bytes()
        agg["score"].write_text('{"x":2}', encoding="utf-8")
        second = archive_stage.write_archive(self.settings, job, **kwargs)
        self.assertEqual(first, second)
        self.assertTrue((first / "archive-manifest.json").is_file())
        self.assertEqual((first / "aggregate-score-score-result.json").read_bytes(), before)

    def test_namespace_is_under_archives_automated(self) -> None:
        job = _make_job()
        d = archive_stage.archive_dir_for(self.settings, job)
        self.assertEqual(d, self.settings.archives_root / job.source_revision / job.func_id / job.job_id)


# --- site_history_stage (real, isolation) -----------------------------------

class SiteHistoryStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.confirmed_history = self.settings.specs_root / ".evaluator" / "site-evaluation-history.json"
        self.confirmed_hash_before = (
            hashlib.sha256(self.confirmed_history.read_bytes()).hexdigest()
            if self.confirmed_history.is_file() else None
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_snapshot_written_and_isolated(self) -> None:
        job = _make_job()
        aggregate_dir = self.settings.jobs_root / job.job_id / "aggregate"
        aggregate_dir.mkdir(parents=True)
        (aggregate_dir / "score-result.json").write_text('{"score": 80}', encoding="utf-8")
        (aggregate_dir / "evaluation-report.json").write_text(
            '{"findings": [{"finding_id": "SEM-x", "severity": "Major"}]}', encoding="utf-8"
        )
        snap = site_history_stage.write_site_history_snapshot(
            self.settings, job, aggregate_dir, selected_run_id="run-1", run_ids=["run-1"],
        )
        self.assertTrue(snap.is_file())
        doc = json.loads(snap.read_text(encoding="utf-8"))
        self.assertEqual(doc["namespace"], "automated")
        self.assertEqual(doc["finding_summary"]["total"], 1)
        # automated history log under data_root (never the confirmed path)
        auto_log = site_history_stage.automated_history_path(self.settings)
        self.assertTrue(auto_log.is_file())
        self.assertTrue(str(auto_log).startswith(str(self.settings.data_root)))
        # confirmed review/history file is byte-for-byte unchanged
        if self.confirmed_hash_before is not None:
            self.assertEqual(
                hashlib.sha256(self.confirmed_history.read_bytes()).hexdigest(),
                self.confirmed_hash_before,
            )


# --- aggregation_stage + driver (orchestration) -----------------------------

class _DriverTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.attempts = AttemptRepository(self.store)
        self.events = EventRepository(self.store)
        self.artifacts = ArtifactRepository(self.store)
        self.snapshots = DependencySnapshotRepository(self.store)
        self.job = self.jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=1, job_id="d" * 40),
            evaluator_version=EVALUATOR_VERSION,
        )
        self.ctx = RunContext.for_run(
            self.settings, job_id=self.job.job_id, func_id=self.job.func_id,
            source_revision=self.job.source_revision, run_id="run-1", evaluator_version=EVALUATOR_VERSION,
        )
        # pre-seed evidence so the real evidence build is skipped
        self.ctx.input_dir.mkdir(parents=True, exist_ok=True)
        evidence = {"func_id": self.job.func_id, "source_revision": self.job.source_revision}
        for name in ("function-context.json", "static-result.json", "evidence-manifest.json"):
            (self.ctx.input_dir / name).write_text(json.dumps(evidence), encoding="utf-8")
        self.ctx.run_dir.mkdir(parents=True, exist_ok=True)
        self._write_aggregation_template([])

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _work_items(self) -> list[dict]:
        obs = self.ctx.run_dir.parent / "obs"
        obs.mkdir(parents=True, exist_ok=True)
        output_path = obs / "feature_Feat-01.json"
        item = {
            "id": "feature:Feat-01", "type": "feature", "feat_id": "Feat-01",
            "input_paths": [], "output_path": str(output_path),
            "expected_claim_ids": [], "required_checks": [],
        }
        output_path.write_text(
            json.dumps({
                "schema_version": 2,
                "evaluator_version": EVALUATOR_VERSION,
                "func_id": self.ctx.func_id,
                "source_revision": self.ctx.source_revision,
                "run_id": self.ctx.run_id,
                "observation_id": item["id"],
                "observation_type": item["type"],
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
        self._write_aggregation_template([item])
        return [item]

    def _write_aggregation_template(self, items: list[dict]) -> None:
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


class AggregationStageTest(_DriverTestBase):
    def test_orchestration_produces_semantic_result(self) -> None:
        self.jobs.transition_status(self.job.job_id, S.PREPARING, event_type="x")
        self.jobs.transition_status(self.job.job_id, S.EVIDENCE, event_type="x")
        self.jobs.transition_status(self.job.job_id, S.SEMANTIC, event_type="x")
        outcome, sr = aggregation_stage.run_aggregation(
            self.ctx, _FakeExecutor(), jobs=self.jobs, attempts=self.attempts,
            events=self.events, runner=_FakeScriptRunner([]),
        )
        self.assertEqual(outcome, C.STATUS_COMPLETED)
        self.assertTrue(sr is not None and sr.is_file())
        # aggregation checkpoint recorded
        self.assertTrue(self.attempts.list_for_job(self.job.job_id, stage=S.STAGE_AGGREGATION))

    def test_aggregation_failure_fails_job(self) -> None:
        self.jobs.transition_status(self.job.job_id, S.PREPARING, event_type="x")
        self.jobs.transition_status(self.job.job_id, S.EVIDENCE, event_type="x")
        self.jobs.transition_status(self.job.job_id, S.SEMANTIC, event_type="x")
        outcome, sr = aggregation_stage.run_aggregation(
            self.ctx, _FakeExecutor(fail_aggregation=True), jobs=self.jobs, attempts=self.attempts,
            events=self.events, runner=_FakeScriptRunner([]),
        )
        self.assertEqual(outcome, C.STATUS_FAILED)
        self.assertEqual(self.jobs.get_job(self.job.job_id).status, S.FAILED)


class DriverCompletionTest(_DriverTestBase):
    def test_pipeline_runs_to_completed_with_archive(self) -> None:
        runner = _FakeScriptRunner(self._work_items())
        result = run_job_pipeline(
            self.job.job_id,
            settings=self.settings, jobs=self.jobs, attempts=self.attempts,
            events=self.events, artifacts=self.artifacts, snapshots=self.snapshots,
            executor=_FakeExecutor(),
            workspace_provider=lambda job: EvaluationWorkspace.control_checkout(
                self.settings, job.source_revision
            ),
            runner=runner,
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED)
        job = self.jobs.get_job(self.job.job_id)
        self.assertEqual(job.status, S.COMPLETED)
        # archive exists in the automated namespace
        archive_dir = self.settings.archives_root / job.source_revision / job.func_id / job.job_id
        self.assertTrue((archive_dir / "archive-manifest.json").is_file())
        types = [e.event_type for e in self.events.list_for_job(self.job.job_id)]
        self.assertIn("job_completed", types)

    def test_manual_refresh_pipeline_registers_and_promotes_report(self) -> None:
        targets = RefreshTargetRepository(self.store)
        _, created = targets.create_active(
            job_id=self.job.job_id,
            func_id=self.job.func_id,
            desired_revision=self.job.source_revision,
            revision_set={"ace_engine": self.job.source_revision, "specs": "s" * 40},
            provisional_fingerprint="sha256:" + "p" * 64,
            dedupe_key="sha256:" + "d" * 64,
            stale_reasons=("DEPENDENCY_SNAPSHOT_CHANGED",),
        )
        self.assertTrue(created)
        result = run_job_pipeline(
            self.job.job_id,
            settings=self.settings, jobs=self.jobs, attempts=self.attempts,
            events=self.events, artifacts=self.artifacts, snapshots=self.snapshots,
            executor=_FakeExecutor(),
            workspace_provider=lambda job: EvaluationWorkspace.control_checkout(
                self.settings, job.source_revision
            ),
            refresh_targets=targets,
            runner=_FakeScriptRunner(self._work_items()),
        )
        self.assertEqual(result.outcome, C.STATUS_COMPLETED)
        stored = targets.get(self.job.job_id)
        self.assertEqual(stored.status, "COMPLETED")  # type: ignore[union-attr]
        report = EvaluationReportRepository(self.store).get_for_job(self.job.job_id)
        self.assertIsNotNone(report)
        head = FunctionReportHeadRepository(self.store).get(self.job.func_id)
        self.assertEqual(head.current_report_id, report.report_id)  # type: ignore[union-attr]
        self.assertIsNotNone(ReportDeltaRepository(self.store).get(report.report_id))


if __name__ == "__main__":
    unittest.main()
