"""Aggregation stage (TASK-011-07): produce a validated ``semantic-result.json``.

After all observation work items are validated, this stage asks the executor to
complete ``aggregation.json`` (the function-global model judgment: criterion
conclusions, defect ownership, contradiction bases, outcome policies), then runs
``assemble_semantic_result.py`` to freeze ``semantic-result.json`` and validates
the ``final`` stage. The executor returns only mutable aggregation fields; the
service merges them into the initialized flat template and retains identity.

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
from .result_payload import (
    aggregation_prompt_contract,
    load_template,
    merge_aggregation_payload,
)
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
    aggregation_path = ctx.run_dir / "aggregation.json"
    candidate_path = ctx.run_dir / ".aggregation.json.candidate"
    try:
        initialized = load_template(aggregation_path)
        source_observation_ids = _source_observation_ids(ctx.run_dir / "work-items.json")
    except ValueError as exc:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"error": f"template preflight: {exc}"},
        )
        return C.STATUS_FAILED, None

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

    try:
        candidate = merge_aggregation_payload(
            initialized,
            result.observation,
            source_observation_ids=source_observation_ids,
        )
        candidate_path.write_text(
            json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        verdict = staged_stage.validate_aggregation_candidate(ctx, candidate_path, runner=runner)
        if not verdict.ok:
            jobs.transition_status(
                ctx.job_id, S.FAILED,
                event_type="aggregation_failed",
                payload={"errors": list(verdict.errors)},
            )
            return C.STATUS_FAILED, None
        candidate_path.replace(aggregation_path)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"error": f"aggregation write: {exc}"},
        )
        return C.STATUS_FAILED, None
    finally:
        candidate_path.unlink(missing_ok=True)

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
    for contract_input in (
        aggregation_path,
        ctx.run_dir / "work-items.json",
        ctx.skill_scripts_dir.parent / "references" / "staged-run-contract.md",
    ):
        if contract_input.is_file():
            input_paths.append(str(contract_input))
    input_paths = list(dict.fromkeys(input_paths))
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
        prompt_extras=aggregation_prompt_contract(aggregation_path),
    )


def _source_observation_ids(work_items_path: Path) -> list[str]:
    try:
        document = json.loads(work_items_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load work items {work_items_path}: {exc}") from exc
    items = document.get("items") if isinstance(document, dict) else None
    if not isinstance(items, list):
        raise ValueError(f"work items document has no items list: {work_items_path}")
    result: list[str] = []
    for item in items:
        item_id = item.get("id") if isinstance(item, dict) else None
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"work items contain an invalid id: {work_items_path}")
        result.append(item_id)
    return result
