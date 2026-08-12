"""Semantic stage: the per-work-item loop and the single-job pipeline driver.

The loop drives one staged run: initialize (once), then repeatedly fetch the
next pending work item, ask the executor to complete it, write the observation,
validate the checkpoint, and record it. It resumes after interruption because
``show_next_work_item`` skips already-validated items and ``init`` is skipped
when a ``run-state.json`` already exists.

Phase 2 scope ends with all observation work items validated. Aggregation →
``semantic-result.json`` is Phase 4 (TASK-011-07); the job is therefore left in
the ``semantic`` state with an ``observations_complete`` marker rather than
advanced to ``aggregation``.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..domain import states as S
from ..domain.models import Attempt, default_progress, make_job_id
from ..executors import contract as C
from ..executors.base import SemanticExecutor
from ..settings import ServiceSettings
from ..store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EventRepository,
    JobRepository,
)
from ..store.sqlite_store import utc_now
from ._subprocess import Runner, default_runner
from .context import RunContext
from .evidence_stage import prepare_evidence
from . import staged_stage


# --- outcome ----------------------------------------------------------------

@dataclass(frozen=True)
class SemanticStageResult:
    outcome: str  # C.STATUS_COMPLETED | C.STATUS_AWAITING | C.STATUS_FAILED | C.STATUS_CANCELLED
    completed_items: int
    error: str | None = None


# --- executor event -> DB event bridge (capped) -----------------------------

class _DBEmitter:
    """Forward executor events to the events table, capping verbose JSONL."""

    def __init__(self, events: EventRepository, job_id: str, *, jsonl_cap: int = 20) -> None:
        self._events = events
        self._job_id = job_id
        self._jsonl_cap = jsonl_cap
        self._jsonl_seen = 0

    def __call__(self, ev: C.ExecutionEvent) -> None:
        if ev.kind == "jsonl":
            self._jsonl_seen += 1
            if self._jsonl_seen > self._jsonl_cap:
                return
        message = ev.message if len(ev.message) <= 800 else ev.message[:800] + "…"
        payload = {"kind": ev.kind, "message": message}
        payload.update(ev.data)
        self._events.append(self._job_id, f"executor_{ev.kind}", payload)


# --- the loop ---------------------------------------------------------------

def run_semantic(
    ctx: RunContext,
    executor: SemanticExecutor,
    *,
    jobs: JobRepository,
    attempts: AttemptRepository,
    events: EventRepository,
    cancel: Any = None,
    runner: Runner = default_runner,
) -> SemanticStageResult:
    """Run the staged semantic loop for one run. Resume-safe across interruptions."""
    emit = _DBEmitter(events, ctx.job_id)

    run_state = ctx.run_dir / "run-state.json"
    if not run_state.is_file():
        staged_stage.init_staged_run(ctx, runner=runner)

    completed = 0
    while True:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, completed, "cancelled")
        item = staged_stage.next_work_item(ctx, runner=runner)
        if item is None:
            break  # no more observation work items

        work = _build_work_input(ctx, item)
        events.append(ctx.job_id, "work_item_started", {"work_item_id": work.work_item_id})
        result = executor.execute(work, emit, cancel)

        if result.status == C.STATUS_CANCELLED or (cancel is not None and cancel.is_set()):
            return SemanticStageResult(C.STATUS_CANCELLED, completed, "cancelled during work item")
        if result.status == C.STATUS_AWAITING:
            jobs.transition_status(
                ctx.job_id, S.AWAITING_EXECUTOR,
                event_type="awaiting_executor",
                payload={"work_item_id": work.work_item_id, "error": result.error},
            )
            return SemanticStageResult(C.STATUS_AWAITING, completed, result.error)
        if not result.succeeded:
            jobs.transition_status(
                ctx.job_id, S.FAILED,
                event_type="semantic_failed",
                payload={"work_item_id": work.work_item_id, "status": result.status, "error": result.error},
            )
            return SemanticStageResult(C.STATUS_FAILED, completed, result.error or f"executor {result.status}")

        try:
            _write_observation(result.executor_result_path, str(item["output_path"]))
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            jobs.transition_status(
                ctx.job_id, S.FAILED,
                event_type="semantic_failed",
                payload={"work_item_id": work.work_item_id, "error": f"observation write: {exc}"},
            )
            return SemanticStageResult(C.STATUS_FAILED, completed, f"observation write: {exc}")

        verdict = staged_stage.validate_work_item(ctx, work.work_item_id, runner=runner)
        if not verdict.ok:
            jobs.transition_status(
                ctx.job_id, S.FAILED,
                event_type="semantic_failed",
                payload={"work_item_id": work.work_item_id, "errors": list(verdict.errors)},
            )
            return SemanticStageResult(
                C.STATUS_FAILED, completed, "validator: " + "; ".join(verdict.errors)
            )

        attempts.record_checkpoint(
            Attempt(
                attempt_id=make_job_id(),
                job_id=ctx.job_id,
                run_id=ctx.run_id,
                feat_id=item.get("feat_id"),
                stage=S.STAGE_SEMANTIC,
                status=S.ATTEMPT_COMPLETED,
                started_at=utc_now(),
                finished_at=utc_now(),
                exit_code=0,
                artifact_dir=str(ctx.run_dir),
            )
        )
        events.append(ctx.job_id, "work_item_completed", {"work_item_id": work.work_item_id})
        completed += 1

    events.append(ctx.job_id, "observations_complete", {"completed_items": completed})
    return SemanticStageResult(C.STATUS_COMPLETED, completed)


def _build_work_input(ctx: RunContext, item: dict[str, Any]) -> C.WorkItemInput:
    output_path = Path(str(item["output_path"]))
    executor_result_path = output_path.parent / f"{output_path.stem}.executor-result.json"
    return C.WorkItemInput(
        job_id=ctx.job_id,
        func_id=ctx.func_id,
        run_id=ctx.run_id,
        work_item_id=str(item["id"]),
        work_item=item,
        run_dir=str(ctx.run_dir),
        input_paths=tuple(str(p) for p in item.get("input_paths", [])),
        executor_result_path=str(executor_result_path),
        repo_root=str(ctx.repo_root),
        skill_version=ctx.evaluator_version,
        protocol_version=ctx.protocol_version,
        forbidden_paths=ctx.forbidden_paths,
    )


def _write_observation(executor_result_path: str | None, observation_output_path: str) -> None:
    """Extract the observation body from the executor result and write it."""
    if not executor_result_path:
        raise ValueError("executor produced no result path")
    document = json.loads(Path(executor_result_path).read_text(encoding="utf-8"))
    observation = document.get("observation")
    if not isinstance(observation, dict):
        raise ValueError("executor result has no observation object")
    out = Path(observation_output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(observation, ensure_ascii=False, indent=2), encoding="utf-8")


# --- single-job pipeline driver --------------------------------------------

def run_job_pipeline(
    job_id: str,
    *,
    settings: ServiceSettings,
    jobs: JobRepository,
    attempts: AttemptRepository,
    events: EventRepository,
    artifacts: ArtifactRepository,
    snapshots: DependencySnapshotRepository,
    executor: SemanticExecutor,
    cancel: Any = None,
    runner: Runner = default_runner,
) -> SemanticStageResult:
    """Drive one job to completion: prepare -> evidence -> semantic (all runs)
    -> aggregation (all runs) -> report -> site-history -> archive -> completed.

    Each status transition is guarded by the current status, so re-entering a
    partially progressed job skips already-done phases. Within semantic,
    :func:`run_semantic` resumes from the last validated checkpoint per run.
    """
    job = jobs.get_job(job_id)
    run_ids = _run_ids(job)
    selected_run_id = job.selected_run_ids[0] if job.selected_run_ids else run_ids[0]

    def ctx_for(run_id: str) -> RunContext:
        return RunContext.for_run(
            settings,
            job_id=job.job_id,
            func_id=job.func_id,
            source_revision=job.source_revision,
            run_id=run_id,
            evaluator_version=job.evaluator_version,
        )

    # preparing (once): freeze dependency revisions
    if job.status == S.QUEUED:
        jobs.transition_status(job_id, S.PREPARING, event_type="enter_preparing")
        _freeze_snapshots(ctx_for(run_ids[0]), snapshots, events)

    # evidence (once): build the shared package unless already present
    job = jobs.get_job(job_id)
    if job.status == S.PREPARING:
        jobs.transition_status(job_id, S.EVIDENCE, event_type="enter_evidence")
        first_ctx = ctx_for(run_ids[0])
        if not (first_ctx.input_dir / "function-context.json").is_file():
            prepare_evidence(first_ctx, runner=runner)
            _record_evidence_artifacts(first_ctx, job_id, artifacts)

    # semantic phase: observations for every run
    job = jobs.get_job(job_id)
    if job.status == S.EVIDENCE:
        jobs.transition_status(job_id, S.SEMANTIC, event_type="enter_semantic")
    for run_id in run_ids:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, 0, "cancelled")
        sem = run_semantic(
            ctx_for(run_id), executor, jobs=jobs, attempts=attempts, events=events,
            cancel=cancel, runner=runner,
        )
        if sem.outcome != C.STATUS_COMPLETED:
            return sem

    # aggregation phase: assemble a validated semantic-result for every run
    job = jobs.get_job(job_id)
    if job.status == S.SEMANTIC:
        jobs.transition_status(job_id, S.AGGREGATION, event_type="enter_aggregation")
    semantic_results: dict[str, Path] = {}
    for run_id in run_ids:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, 0, "cancelled")
        from . import aggregation_stage
        outcome, sr = aggregation_stage.run_aggregation(
            ctx_for(run_id), executor, jobs=jobs, attempts=attempts, events=events,
            cancel=cancel, runner=runner,
        )
        if outcome != C.STATUS_COMPLETED:
            return SemanticStageResult(outcome, 0, None)
        semantic_results[run_id] = sr

    # deterministic report (score/stability/report) on the selected run
    job = jobs.get_job(job_id)
    if job.status == S.AGGREGATION:
        from . import report_stage, site_history_stage, archive_stage
        report_ctx = ctx_for(selected_run_id)
        aggregate_outputs = report_stage.run_report(
            report_ctx, semantic_results=semantic_results,
            selected_run_id=selected_run_id, runner=runner,
        )
        snapshot_path = site_history_stage.write_site_history_snapshot(
            settings, job, report_ctx.aggregate_dir,
            selected_run_id=selected_run_id, run_ids=run_ids,
        )
        # archive (automated namespace) then advance to terminal
        jobs.transition_status(job_id, S.ARCHIVE, event_type="enter_archive")
        archive_dir = archive_stage.write_archive(
            settings, job,
            semantic_results=semantic_results,
            aggregate_outputs=aggregate_outputs,
            run_ids=run_ids,
            selected_run_id=selected_run_id,
            site_snapshot_path=snapshot_path,
        )
        events.append(job_id, "job_archived", {"archive_dir": str(archive_dir)})
        jobs.transition_status(job_id, S.SITE_HISTORY, event_type="enter_site_history")
        jobs.transition_status(job_id, S.COMPLETED, event_type="job_completed")
        progress = default_progress(S.COMPLETED)
        progress["completed_checkpoints"] = [f"{rid}:semantic+aggregation" for rid in run_ids]
        progress["note"] = f"archived at {archive_dir}"
        jobs.update_progress(job_id, progress)
        events.append(job_id, "job_completed", {"archive_dir": str(archive_dir)})

    return SemanticStageResult(C.STATUS_COMPLETED, len(semantic_results))


def _run_ids(job) -> list[str]:
    if job.selected_run_ids:
        return list(job.selected_run_ids)
    return [f"run-{i}" for i in range(1, max(1, job.run_count) + 1)]


def _freeze_snapshots(
    ctx: RunContext, snapshots: DependencySnapshotRepository, events: EventRepository
) -> None:
    """Record current git SHAs of the source/SDK repos (task-level freeze)."""
    oh_root = ctx.repo_root.parents[2]
    repos = [
        ("ace_engine", ctx.repo_root, "master"),
        ("specs", ctx.specs_root, "main"),
        ("sdk-js", oh_root / "interface" / "sdk-js", "master"),
        ("sdk_c", oh_root / "interface" / "sdk_c", "master"),
    ]
    now = utc_now()
    frozen = []
    for name, path, branch in repos:
        if not path.is_dir():
            continue
        sha = _git_sha(path)
        if sha is None:
            continue
        snapshots.freeze(_snapshot_dto(ctx.job_id, name, branch, sha, now))
        frozen.append({"name": name, "sha": sha})
    events.append(ctx.job_id, "dependency_snapshot_frozen", {"repos": frozen})


def _record_evidence_artifacts(
    ctx: RunContext, job_id: str, artifacts: ArtifactRepository
) -> None:
    for kind, name in (
        ("function_context", "function-context.json"),
        ("static_result", "static-result.json"),
        ("evidence_manifest", "evidence-manifest.json"),
    ):
        path = ctx.input_dir / name
        if not path.is_file():
            continue
        artifacts.record(_artifact_dto(job_id, kind, path))


# --- helpers ----------------------------------------------------------------

def _git_sha(path: Path) -> str | None:
    try:
        cp = subprocess.run(  # noqa: S603,S607
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if cp.returncode != 0:
        return None
    return cp.stdout.strip() or None


def _snapshot_dto(job_id: str, name: str, branch: str, sha: str, now: str):
    from ..domain.models import DependencySnapshot

    return DependencySnapshot(
        job_id=job_id,
        repo_name=name,
        branch=branch,
        sha=sha,
        status="frozen",
        created_at=now,
    )


def _artifact_dto(job_id: str, kind: str, path: Path):
    from ..domain.models import Artifact

    data = path.read_bytes()
    return Artifact(
        artifact_id=secrets.token_hex(12),
        job_id=job_id,
        kind=kind,
        path=str(path),
        sha256="sha256:" + hashlib.sha256(data).hexdigest(),
        size=len(data),
        created_at=utc_now(),
    )
