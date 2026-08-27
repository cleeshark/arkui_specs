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
import re
import secrets
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable

from ..domain import states as S
from ..domain.models import Attempt, Job, default_progress, make_job_id
from ..domain.models import EvaluationReportRecord, ReportDelta
from ..executors import contract as C
from ..executors.base import SemanticExecutor
from ..settings import ServiceSettings
from ..store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
    RefreshTargetRepository,
)
from ..store.sqlite_store import utc_now
from ._subprocess import Runner, default_runner
from .context import RunContext
from .evidence_stage import prepare_evidence, validate_evidence_package
from .result_payload import load_template  # noqa: F401  (re-exported helper)
from .observation_quality import assess_observation_quality
from . import staged_stage
from ..freshness import DEPENDENCY_SNAPSHOT_CHANGED
from ..report_registry import ReportRegistry, fingerprint_named_documents
from ..report_delta import build_report_delta, load_archived_report
from ..store.repositories import (
    EvaluationReportRepository,
    FreshnessPolicyRepository,
    FunctionReportHeadRepository,
    ReportDeltaRepository,
)
from ..workspace.models import EvaluationWorkspace


# --- outcome ----------------------------------------------------------------

@dataclass(frozen=True)
class SemanticStageResult:
    outcome: str  # C.STATUS_COMPLETED | C.STATUS_AWAITING | C.STATUS_FAILED | C.STATUS_CANCELLED
    completed_items: int
    error: str | None = None


@dataclass(frozen=True)
class _RepairRejectionFallback:
    """Outcome of the one complete re-evaluation after a repair was rejected.

    ``terminal`` is non-None when the caller must return it (cancelled,
    awaiting executor or failed); otherwise ``candidate``/``verdict`` restart
    the bounded repair loop with the rebuilt full evaluation.
    """

    terminal: SemanticStageResult | None
    candidate: dict[str, Any]
    verdict: Any


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
    statistics: JobStatisticsRepository | None = None,
    invocations=None,
    cancel: Any = None,
    runner: Runner = default_runner,
) -> SemanticStageResult:
    """Run the staged observation loop for one run (protocol 0.2.0).

    Resume-safe: validated work items are skipped; a stored invalid candidate
    resumes at the single correction turn instead of regenerating.
    """
    from spec_eval.kernel import staged_state as SS
    from spec_eval.kernel.normalize import (
        normalize_observation,
        project_observation_derived_fields,
    )
    from spec_eval.kernel.validate import validate_observation_document
    from spec_eval.service.pipeline.judgment_flow import (
        JudgmentFlow, input_fingerprint,
    )
    from .result_payload import observe_observation_prompt_contract

    emit = _DBEmitter(events, ctx.job_id)

    run_state = ctx.run_dir / "run-state.json"
    if (
        not run_state.is_file()
        and not (ctx.run_dir / "work-items.json").is_file()
    ):
        staged_stage.init_staged_run(ctx, runner=runner)

    if not run_state.is_file():
        # work-items.json exists but run-state.json does not (interrupted init
        # or synthetic fixtures): synthesize the initial state document
        run_state.write_text(json.dumps({
            "validated_work_items": [],
            "aggregation_validated": False,
            "semantic_validated": False,
            "current_phase": "feature_observations",
        }), encoding="utf-8")
    output_contract_path = ctx.run_dir / "output-contract.json"
    output_contract = (
        json.loads(output_contract_path.read_text(encoding="utf-8"))
        if output_contract_path.is_file() else {}
    )
    valid_criterion_ids = tuple(output_contract.get("valid_criterion_ids", []))

    completed = 0
    while True:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, completed, "cancelled")
        item = staged_stage.next_work_item(ctx, runner=runner)
        if item is None:
            break
        output_path = Path(str(item["output_path"]))
        work = _build_work_input(ctx, item, valid_criterion_ids)
        template = load_template(output_path)
        fingerprint = input_fingerprint(
            evaluator_version=ctx.evaluator_version,
            protocol_version=ctx.protocol_version,
            input_paths=list(work.input_paths),
            template_bytes=output_path.read_bytes(),
            input_resources=work.work_item.get("input_resources", []),
        )

        flow = JudgmentFlow(
            ctx=ctx, executor=executor, jobs=jobs, events=events,
            statistics=statistics, invocations=invocations, emit=emit,
            cancel=cancel,
        )
        events.append(ctx.job_id, "work_item_started", {
            "work_item_id": work.work_item_id,
        })

        def _publish(document: dict[str, Any], _item=item) -> None:
            run_state_doc2 = json.loads(run_state.read_text(encoding="utf-8"))
            work_items_doc2 = json.loads(
                (ctx.run_dir / "work-items.json").read_text(encoding="utf-8")
            )
            SS.update_progress(
                ctx.run_dir, run_state_doc2, work_items_doc2,
                stage="observations", work_item_id=str(_item["id"]),
            )
            attempts.record_checkpoint(
                Attempt(
                    attempt_id=make_job_id(),
                    job_id=ctx.job_id,
                    run_id=ctx.run_id,
                    feat_id=_item.get("feat_id"),
                    stage=S.ATTEMPT_STAGE_OBSERVATION,
                    status=S.ATTEMPT_COMPLETED,
                    started_at=utc_now(),
                    finished_at=utc_now(),
                    exit_code=0,
                    artifact_dir=str(ctx.run_dir),
                )
            )

        required_evidence_paths = tuple(
            str(resource["canonical_path"])
            for resource in item.get("input_resources", [])
            if isinstance(resource, dict)
            and resource.get("citable") is True
            and resource.get("canonical_path")
        )
        evidence_resolver = ctx.evidence_resolver(
            required_paths=required_evidence_paths
        )
        outcome = flow.run(
            work=work,
            output_path=output_path,
            template=template,
            normalize=lambda payload, _t=template, _r=evidence_resolver: normalize_observation(
                _t, payload, repo_root=ctx.repo_root,
                evidence_resolver=_r,
            ),
            validate=lambda document: validate_observation_document(
                document,
                valid_criterion_ids=valid_criterion_ids,
                required_checks=item.get("required_checks"),
            ),
            base_contract=work.prompt_extras,
            on_publish=_publish,
            fingerprint=fingerprint,
            stage_event="work_item_completed",
            reproject=project_observation_derived_fields,
        )
        if outcome.status != C.STATUS_COMPLETED:
            return SemanticStageResult(
                outcome.status, completed, outcome.error
            )
        completed += 1
    events.append(ctx.job_id, "observations_complete", {
        "completed_items": completed,
    })
    return SemanticStageResult(C.STATUS_COMPLETED, completed)


def _build_work_input(
    ctx: RunContext,
    item: dict[str, Any],
    valid_criterion_ids: tuple[str, ...] = (),
) -> C.WorkItemInput:
    from spec_eval.kernel.machine_contract import (
        build_observation_machine_contract,
    )
    from .result_payload import observe_observation_prompt_contract

    output_path = Path(str(item["output_path"]))
    executor_result_path = (
        output_path.parent / f"{output_path.stem}.executor-result.json"
    )
    work_item = dict(item)
    input_paths = [str(path) for path in item.get("input_paths", [])]
    input_resources = [
        dict(resource) for resource in item.get("input_resources", [])
        if isinstance(resource, dict)
    ]
    if not input_resources:
        input_resources = [
            {"path": path, "role": "semantic_input", "citable": False}
            for path in input_paths
        ]
    phase_references: list[dict[str, str]] = []
    observation_profile = str(item.get("observation_profile") or "").strip()
    if observation_profile not in {"feature", "function_global"}:
        observation_profile = (
            "function_global" if item.get("type") == "function_global" else "feature"
        )
    for name, filename, role in (
        ("observation-contract", "observation-contract.md", "executor_contract"),
        ("observation-guide", "observation-guide.md", "executor_guide"),
    ):
        reference = ctx.skill_scripts_dir.parent / "references" / filename
        if not reference.is_file():
            continue
        content = reference.read_text(encoding="utf-8")
        input_paths.append(str(reference))
        input_resources.append({
            "path": str(reference),
            "role": role,
            "citable": False,
            "embedded": True,
        })
        phase_references.append({
            "name": name,
            "path": str(reference),
            "content_hash": "sha256:" + hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest(),
            "content": content,
        })
    input_paths = list(dict.fromkeys(input_paths))
    work_item["input_resources"] = input_resources
    machine_contract = build_observation_machine_contract(
        expected_claim_ids=item.get("expected_claim_ids", []),
        required_checks=item.get("required_checks", []),
        valid_criterion_ids=valid_criterion_ids,
        observation_profile=observation_profile,
        citable_input_paths=(
            str(resource["canonical_path"])
            for resource in input_resources
            if resource.get("citable") is True and resource.get("canonical_path")
        ),
    )
    prompt_contract = observe_observation_prompt_contract(
        template_path=output_path,
        schema_dir=ctx.run_dir,
        machine_contract=machine_contract,
    )
    prompt_contract["phase_references"] = phase_references
    prompt_contract["observation_profile"] = observation_profile
    return C.WorkItemInput(
        job_id=ctx.job_id,
        func_id=ctx.func_id,
        run_id=ctx.run_id,
        work_item_id=str(item["id"]),
        work_item=work_item,
        run_dir=str(ctx.run_dir),
        input_paths=tuple(input_paths),
        executor_result_path=str(executor_result_path),
        repo_root=str(ctx.repo_root),
        skill_version=ctx.evaluator_version,
        protocol_version=ctx.protocol_version,
        forbidden_paths=ctx.forbidden_paths,
        prompt_extras=prompt_contract,
    )

def _write_candidate(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")


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
    workspace_provider: Callable[[Job], EvaluationWorkspace],
    refresh_targets: RefreshTargetRepository | None = None,
    statistics: JobStatisticsRepository | None = None,
    invocations: Any = None,
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
    workspace = workspace_provider(job)
    resolved_job = replace(job, source_revision=workspace.revisions["ace_engine"])
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
            workspace=workspace,
        )

    # preparing (once): freeze dependency revisions. The persisted stage is
    # kept on the queued -> running transition so crash recovery resumes at
    # the interrupted stage instead of restarting the pipeline.
    if job.status == S.QUEUED:
        jobs.transition_status(job_id, S.RUNNING, event_type="enter_preparing")
        _freeze_snapshots(job_id, workspace, snapshots, events)

    # evidence (once): build the shared package unless already present
    job = jobs.get_job(job_id)
    if job.status == S.RUNNING and job.stage == S.STAGE_PREPARING:
        jobs.transition_status(
            job_id, S.RUNNING, stage=S.STAGE_EVIDENCE, event_type="enter_evidence"
        )
        first_ctx = ctx_for(run_ids[0])
        if not (first_ctx.input_dir / "function-context.json").is_file():
            prepare_evidence(first_ctx, runner=runner)
        validate_evidence_package(first_ctx)
        _record_evidence_artifacts(first_ctx, job_id, artifacts)
        if refresh_targets is not None:
            target = refresh_targets.get(job_id)
            if target is not None:
                input_fingerprint, evidence_fingerprint = _evaluation_input_fingerprints(first_ctx)
                target = refresh_targets.bind_fingerprints(
                    job_id,
                    input_fingerprint=input_fingerprint,
                    evidence_fingerprint=evidence_fingerprint,
                )
                FunctionReportHeadRepository(refresh_targets.store).bind_fingerprint(
                    job.func_id,
                    generation=target.generation,
                    job_id=job_id,
                    input_fingerprint=input_fingerprint,
                    stale_reasons=(DEPENDENCY_SNAPSHOT_CHANGED,),
                )

    # observation phase: judgments for every run
    job = jobs.get_job(job_id)
    if job.status == S.RUNNING and job.stage == S.STAGE_EVIDENCE:
        jobs.transition_status(
            job_id, S.RUNNING, stage=S.STAGE_OBSERVATION,
            event_type="enter_observation",
        )
    for run_id in run_ids:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, 0, "cancelled")
        sem = run_semantic(
            ctx_for(run_id), executor, jobs=jobs, attempts=attempts, events=events,
            statistics=statistics, invocations=invocations, cancel=cancel,
            runner=runner,
        )
        if sem.outcome != C.STATUS_COMPLETED:
            return sem

    # aggregation phase: assemble a validated semantic-result for every run
    job = jobs.get_job(job_id)
    if job.status == S.RUNNING and job.stage == S.STAGE_OBSERVATION:
        jobs.transition_status(
            job_id, S.RUNNING, stage=S.STAGE_AGGREGATION,
            event_type="enter_aggregation",
        )
    semantic_results: dict[str, Path] = {}
    for run_id in run_ids:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, 0, "cancelled")
        from . import aggregation_stage
        outcome, sr = aggregation_stage.run_aggregation(
            ctx_for(run_id), executor, jobs=jobs, attempts=attempts, events=events,
            statistics=statistics, invocations=invocations, cancel=cancel,
            runner=runner,
        )
        if outcome != C.STATUS_COMPLETED:
            return SemanticStageResult(outcome, 0, None)
        semantic_results[run_id] = sr

    # deterministic report (score/stability/report) on the selected run
    job = jobs.get_job(job_id)
    if job.status == S.RUNNING and job.stage in {S.STAGE_AGGREGATION, S.STAGE_REPORT}:
        from . import report_stage, site_history_stage, archive_stage, projector
        if job.stage == S.STAGE_AGGREGATION:
            jobs.transition_status(
                job_id, S.RUNNING, stage=S.STAGE_REPORT, event_type="enter_report"
            )
        # If already at STAGE_REPORT (e.g., retry after report failure), skip transition
        report_ctx = ctx_for(selected_run_id)
        try:
            aggregate_outputs = report_stage.run_report(
                report_ctx, semantic_results=semantic_results,
                selected_run_id=selected_run_id, runner=runner,
            )
        except report_stage.ReportStageError as exc:
            jobs.transition_status(
                job_id,
                S.FAILED,
                event_type="report_failed",
                payload={"error": str(exc)},
            )
            return SemanticStageResult(C.STATUS_FAILED, 0, str(exc))
        try:
            stability_result = json.loads(
                aggregate_outputs["stability"].read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            stability_result = {}
        if stability_result.get("status") == "insufficient_runs":
            events.append(
                job_id,
                "stability_insufficient_runs",
                {
                    "provided": stability_result.get("provided_run_count"),
                    "required": stability_result.get("required_run_count"),
                    "selected_run_id": selected_run_id,
                },
            )
        pending_delta = None
        if refresh_targets is not None and refresh_targets.get(job_id) is not None:
            existing_report = EvaluationReportRepository(refresh_targets.store).get_for_job(job_id)
            if existing_report is None:
                pending_delta = _prepare_report_delta(
                    refresh_targets.store,
                    resolved_job.func_id,
                    aggregate_outputs["report_json"],
                    report_ctx.aggregate_dir,
                )
                aggregate_outputs["delta"] = pending_delta[1]
            else:
                pending_delta = _load_archived_delta(existing_report.archive_path)
        snapshot_path = site_history_stage.write_site_history_snapshot(
            settings, resolved_job, report_ctx.aggregate_dir,
            selected_run_id=selected_run_id, run_ids=run_ids,
        )
        # archive (automated namespace) then advance to terminal
        jobs.transition_status(
            job_id, S.RUNNING, stage=S.STAGE_ARCHIVE, event_type="enter_archive"
        )
        archive_dir = archive_stage.write_archive(
            settings, resolved_job,
            semantic_results=semantic_results,
            aggregate_outputs=aggregate_outputs,
            run_ids=run_ids,
            selected_run_id=selected_run_id,
            site_snapshot_path=snapshot_path,
            aggregation_contexts={
                run_id: result_path.parent / "aggregation-context.json"
                for run_id, result_path in semantic_results.items()
                if (result_path.parent / "aggregation-context.json").is_file()
            },
        )
        events.append(job_id, "job_archived", {"archive_dir": str(archive_dir)})
        # design v3 R6/D2: the synchronous critical path ends at the archive.
        # The job is completed here; site-history projection and rolling-report
        # registration run asynchronously through the projection outbox and
        # can never regress the completed job to failed.
        jobs.transition_status(job_id, S.COMPLETED, event_type="job_completed")
        progress = default_progress(S.COMPLETED)
        progress["completed_checkpoints"] = [f"{rid}:semantic+aggregation" for rid in run_ids]
        progress["note"] = f"archived at {archive_dir}"
        jobs.update_progress(job_id, progress)
        events.append(job_id, "job_completed", {"archive_dir": str(archive_dir)})
        projector.enqueue_projection(
            settings,
            job=resolved_job,
            report_id=f"report-{job_id}",
            archive_dir=archive_dir,
            aggregate_dir=report_ctx.aggregate_dir,
            selected_run_id=selected_run_id,
            pending_delta=pending_delta,
            events=events,
        )
        projector.run_projection(settings, job=resolved_job, events=events, runner=runner)

    return SemanticStageResult(C.STATUS_COMPLETED, len(semantic_results))


def _run_ids(job) -> list[str]:
    if job.selected_run_ids:
        return list(job.selected_run_ids)
    return [f"run-{i}" for i in range(1, max(1, job.run_count) + 1)]


def _record_executor_statistics(
    statistics: JobStatisticsRepository | None,
    job_id: str,
    result: C.ExecutionResult,
) -> None:
    if statistics is None:
        return
    if result.status == C.STATUS_AWAITING and result.elapsed_seconds <= 0 and result.event_count == 0:
        return
    statistics.record_executor_result(
        job_id,
        elapsed_seconds=result.elapsed_seconds,
        token_usage=result.token_usage,
        usage_reported=result.usage_reported,
        telemetry=result.telemetry,
        telemetry_reported=result.telemetry_reported,
    )


def _executor_telemetry_payload(result: C.ExecutionResult) -> dict[str, Any]:
    return {
        "reported": result.telemetry_reported,
        **result.telemetry,
    }


def _freeze_snapshots(
    job_id: str,
    workspace: EvaluationWorkspace,
    snapshots: DependencySnapshotRepository,
    events: EventRepository,
) -> None:
    """Persist the already-isolated workspace envelope without overwriting it."""
    now = utc_now()
    frozen = []
    for name, sha in sorted(workspace.revisions.items()):
        snapshots.freeze(_snapshot_dto(job_id, name, "detached", sha, now))
        frozen.append({"name": name, "sha": sha})
    events.append(job_id, "dependency_snapshot_frozen", {"repos": frozen})


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


def _evaluation_input_fingerprints(ctx: RunContext) -> tuple[str, str]:
    evidence_docs: list[tuple[str, Path]] = [
        ("evidence-manifest.json", ctx.input_dir / "evidence-manifest.json"),
    ]
    evidence_root = ctx.input_dir / "evidence"
    if evidence_root.is_dir():
        evidence_docs.extend(
            (f"evidence/{path.relative_to(evidence_root).as_posix()}", path)
            for path in evidence_root.rglob("*") if path.is_file()
        )
    input_docs = [
        ("function-context.json", ctx.input_dir / "function-context.json"),
        ("static-result.json", ctx.input_dir / "static-result.json"),
        *evidence_docs,
    ]
    for name in ("rubric.yaml", "complexity_rules.yaml", "design_completeness_rules.yaml"):
        input_docs.append((f"evaluation/{name}", ctx.specs_root / "evaluation" / name))
    skill_root = ctx.specs_root / "skills" / "ohos-design-arkui-spec-evaluator"
    if skill_root.is_dir():
        input_docs.extend(
            (f"skill/{path.relative_to(skill_root).as_posix()}", path)
            for path in skill_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
    return (
        fingerprint_named_documents(input_docs, normalize_revision_fields=True),
        fingerprint_named_documents(evidence_docs, normalize_revision_fields=True),
    )


def _register_rolling_report(
    *,
    settings: ServiceSettings,
    job: Job,
    target,
    archive_dir: Path,
    aggregate_dir: Path,
    selected_run_id: str,
    refresh_targets: RefreshTargetRepository,
    events: EventRepository,
    pending_delta,
) -> None:
    if not target.input_fingerprint or not target.evidence_fingerprint:
        raise RuntimeError("refresh target has no frozen input/evidence fingerprint")
    manifest_path = archive_dir / "archive-manifest.json"
    report_path = aggregate_dir / "evaluation-report.json"
    report_document = json.loads(report_path.read_text(encoding="utf-8"))
    archive_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = report_document.get("summary", {}) if isinstance(report_document, dict) else {}
    protocol = report_document.get("protocol", {}) if isinstance(report_document, dict) else {}
    report = EvaluationReportRecord(
        report_id=f"report-{job.job_id}",
        job_id=job.job_id,
        func_id=job.func_id,
        source_revision=job.source_revision,
        revision_set={**target.revision_set, "evaluator_toolchain": job.evaluator_version},
        input_fingerprint=target.input_fingerprint,
        evidence_fingerprint=target.evidence_fingerprint,
        evaluator_version=job.evaluator_version,
        protocol_version=job.protocol_version,
        rubric_version=str(protocol.get("rubric_version", "0.3.0")),
        selected_run_id=selected_run_id,
        run_count=job.run_count,
        target_generation=target.generation,
        completed_at=str(archive_manifest.get("created_at") or utc_now()),
        archive_path=str(archive_dir),
        manifest_sha256="sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        summary=summary,
    )
    store = refresh_targets.store
    registry = ReportRegistry(
        settings,
        EvaluationReportRepository(store),
        FunctionReportHeadRepository(store),
        FreshnessPolicyRepository(store),
    )
    result = registry.register_and_promote(report)
    if result.promotion_status in {"PROMOTED", "ALREADY_CURRENT"} and pending_delta is not None:
        delta_document, _, expected_previous_id = pending_delta
        if (
            result.promotion_status == "PROMOTED"
            and result.previous_report_id != expected_previous_id
        ):
            raise RuntimeError(
                "current report changed while preparing delta: "
                f"expected {expected_previous_id}, got {result.previous_report_id}"
            )
        details_path = archive_dir / "aggregate-delta-report-delta.json"
        ReportDeltaRepository(store).insert(
            ReportDelta(
                report_id=report.report_id,
                previous_report_id=result.previous_report_id,
                summary=delta_document["summary"],
                details_path=str(details_path),
            )
        )
    refresh_targets.finish(job.job_id, status="COMPLETED")
    events.append(
        job.job_id,
        "rolling_report_registered",
        {"report_id": report.report_id, "promotion_status": result.promotion_status},
    )


def _prepare_report_delta(store, func_id: str, current_report_path: Path, aggregate_dir: Path):
    heads = FunctionReportHeadRepository(store)
    reports = EvaluationReportRepository(store)
    head = heads.ensure(func_id)
    previous = reports.get(head.current_report_id) if head.current_report_id else None
    previous_document = load_archived_report(previous.archive_path) if previous else None
    current_document = json.loads(current_report_path.read_text(encoding="utf-8"))
    delta = build_report_delta(previous_document, current_document)
    delta["previous_report_id"] = previous.report_id if previous else None
    path = aggregate_dir / "report-delta.json"
    path.write_text(
        json.dumps(delta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return delta, path, previous.report_id if previous else None


def _load_archived_delta(archive_path: str):
    path = Path(archive_path) / "aggregate-delta-report-delta.json"
    if not path.is_file():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(document, dict) or not isinstance(document.get("summary"), dict):
        return None
    return document, path, document.get("previous_report_id")


# --- helpers ----------------------------------------------------------------

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
