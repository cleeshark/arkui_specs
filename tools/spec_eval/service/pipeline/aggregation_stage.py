"""Aggregation stage (TASK-011-07): produce a validated ``semantic-result.json``.

After all observation work items are validated, this stage asks the executor to
complete ``aggregation.json`` (the function-global model judgment: criterion
conclusions, defect ownership, contradiction bases, outcome policies), then runs
``assemble_semantic_result.py`` to freeze ``semantic-result.json`` and validates
the ``final`` stage. The executor's structured result carries the aggregation
document in its ``observation`` field; the stage writes it to
``aggregation.json`` exactly as returned.

Anti-fake-completion: a missing/invalid aggregation body, an assemble failure,
or a failed final validator all fail the job — ``semantic-result.json`` is never
written by a failed path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..domain import states as S
from ..domain.models import Attempt, make_job_id
from ..executors import contract as C
from ..executors.base import SemanticExecutor
from ..store.repositories import AttemptRepository, EventRepository, JobRepository
from ..store.sqlite_store import utc_now
from ._subprocess import Runner, default_runner
from .context import RunContext
from .semantic_stage import _DBEmitter
from . import staged_stage


def run_aggregation(
    ctx: RunContext,
    executor: SemanticExecutor,
    *,
    jobs: JobRepository,
    attempts: AttemptRepository,
    events: EventRepository,
    cancel: Any = None,
    runner: Runner = default_runner,
) -> tuple[str, Path | None]:
    """Complete aggregation + assemble + validate-final.

    Returns ``(outcome, semantic_result_path)``. ``outcome`` is one of the
    ``C.STATUS_*`` tokens; ``semantic_result_path`` is set only on success.
    """
    emit = _DBEmitter(events, ctx.job_id)
    work = _build_aggregation_input(ctx)
    events.append(ctx.job_id, "aggregation_started", {"work_item_id": work.work_item_id})

    result = executor.execute(work, emit, cancel)

    if result.status == C.STATUS_CANCELLED or (cancel is not None and cancel.is_set()):
        return C.STATUS_CANCELLED, None
    if result.status == C.STATUS_AWAITING:
        # The frozen matrix only allows AGGREGATION -> {ARCHIVE, FAILED} (no
        # awaiting_executor edge), so an unavailable executor during aggregation
        # fails the job; an explicit retry re-runs semantic + aggregation.
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"work_item_id": work.work_item_id, "error": f"executor unavailable: {result.error}"},
        )
        return C.STATUS_FAILED, None
    if not result.succeeded:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"work_item_id": work.work_item_id, "status": result.status, "error": result.error},
        )
        return C.STATUS_FAILED, None

    aggregation_path = ctx.run_dir / "aggregation.json"
    try:
        document = json.loads(Path(result.executor_result_path).read_text(encoding="utf-8"))
        body = document.get("observation")
        if not isinstance(body, dict):
            raise ValueError("executor result has no aggregation object")
        aggregation_path.write_text(
            json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"error": f"aggregation write: {exc}"},
        )
        return C.STATUS_FAILED, None

    try:
        semantic_result = staged_stage.assemble_semantic(ctx, runner=runner)
    except staged_stage.StagedStageError as exc:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"error": f"assemble: {exc}"},
        )
        return C.STATUS_FAILED, None

    verdict = staged_stage.validate_final(ctx, runner=runner)
    if not verdict.ok:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"errors": list(verdict.errors)},
        )
        return C.STATUS_FAILED, None

    attempts.record_checkpoint(
        Attempt(
            attempt_id=make_job_id(),
            job_id=ctx.job_id,
            run_id=ctx.run_id,
            feat_id=None,
            stage=S.STAGE_AGGREGATION,
            status=S.ATTEMPT_COMPLETED,
            started_at=utc_now(),
            finished_at=utc_now(),
            exit_code=0,
            artifact_dir=str(ctx.run_dir),
        )
    )
    events.append(
        ctx.job_id, "aggregation_completed", {"semantic_result": str(semantic_result)}
    )
    return C.STATUS_COMPLETED, semantic_result


def _build_aggregation_input(ctx: RunContext) -> C.WorkItemInput:
    observations_dir = ctx.run_dir / "observations"
    input_paths: list[str] = []
    if observations_dir.is_dir():
        for obs in sorted(observations_dir.glob("*.json")):
            input_paths.append(str(obs))
    template = ctx.run_dir / "semantic-template.json"
    if template.is_file():
        input_paths.append(str(template))
    rubric = ctx.specs_root / "evaluation" / "rubric.yaml"
    if rubric.is_file():
        input_paths.append(str(rubric))
    aggregation_path = ctx.run_dir / "aggregation.json"
    return C.WorkItemInput(
        job_id=ctx.job_id,
        func_id=ctx.func_id,
        run_id=ctx.run_id,
        work_item_id="aggregation:final",
        work_item={
            "id": "aggregation:final",
            "observation_type": "aggregation",
            "input_paths": input_paths,
            "output_path": str(aggregation_path),
        },
        run_dir=str(ctx.run_dir),
        input_paths=tuple(input_paths),
        executor_result_path=str(ctx.run_dir / "aggregation.executor-result.json"),
        repo_root=str(ctx.repo_root),
        skill_version=ctx.evaluator_version,
        protocol_version=ctx.protocol_version,
        forbidden_paths=ctx.forbidden_paths,
    )
