"""Aggregation stage (protocol 0.2.0): produce a validated ``semantic-result.json``.

After all observation work items are validated, this stage asks the executor
for one aggregation judgment payload (envelope v3, strict schema), expands it
into the published ``aggregation.json`` through the kernel normalizer, typed-
validates it against the aggregation context, then runs
``assemble_semantic_result.py`` to freeze ``semantic-result.json`` and
validates the ``final`` stage. The single generic correction turn (design R3)
uses the single generic typed-correction mode; no legacy reconciliation path exists.

Anti-fake-completion: a missing/invalid aggregation body, an assemble failure,
or a failed final validator all fail the job — ``semantic-result.json`` is
never written by a failed path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from spec_eval.kernel.errors import blocking
from spec_eval.kernel.normalize import normalize_aggregation
from spec_eval.kernel.validate import validate_aggregation_document
from ..domain import states as S
from ..domain.models import Attempt, make_job_id
from ..executors import contract as C
from ..executors.base import SemanticExecutor
from ..store.repositories import (
    AttemptRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from ..store.sqlite_store import utc_now
from ._subprocess import Runner, default_runner
from .context import RunContext
from .judgment_flow import JudgmentFlow, input_fingerprint
from .result_payload import (
    load_template,
    observe_aggregation_prompt_contract,
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
    statistics: JobStatisticsRepository | None = None,
    invocations: Any = None,
    cancel: Any = None,
    runner: Runner = default_runner,
) -> tuple[str, Path | None]:
    """Complete aggregation + assemble + validate-final (0.2.0 flow).

    Returns ``(outcome, semantic_result_path)``.
    """
    emit = _DBEmitter(events, ctx.job_id)
    aggregation_path = ctx.run_dir / "aggregation.json"
    semantic_result_path = ctx.run_dir / "semantic-result.json"

    if semantic_result_path.is_file():
        try:
            reused_verdict = staged_stage.validate_final(ctx, runner=runner)
            reuse_errors = reused_verdict.errors
        except staged_stage.StagedStageError as exc:
            reused_verdict = None
            reuse_errors = (str(exc),)
        if reused_verdict is not None and reused_verdict.ok:
            events.append(
                ctx.job_id, "aggregation_reused",
                {"semantic_result": str(semantic_result_path)},
            )
            return C.STATUS_COMPLETED, semantic_result_path
        events.append(ctx.job_id, "aggregation_reuse_rejected", {
            "semantic_result": str(semantic_result_path),
            "errors": list(reuse_errors),
        })

    try:
        observation_preflight = staged_stage.validate_observation_checkpoints(
            ctx, runner=runner
        )
    except staged_stage.StagedStageError as exc:
        observation_preflight = staged_stage.ValidationResult(
            ok=False, errors=(str(exc),)
        )
    if not observation_preflight.ok:
        jobs.transition_status(
            ctx.job_id,
            S.FAILED,
            event_type="aggregation_preflight_rejected",
            payload={"errors": list(observation_preflight.errors)},
        )
        return C.STATUS_FAILED, None

    try:
        template = load_template(aggregation_path)
        source_observation_ids = _source_observation_ids(
            ctx.run_dir / "work-items.json"
        )
        output_contract = (
            load_template(ctx.run_dir / "output-contract.json")
            if (ctx.run_dir / "output-contract.json").is_file() else {}
        )
        mapping_required = bool(
            output_contract.get("aggregation_payload", {}).get("mapping_context")
        )
        aggregation_context_path = (
            staged_stage.build_aggregation_context(ctx, runner=runner)
            if mapping_required else None
        )
    except (ValueError, staged_stage.StagedStageError) as exc:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"error": f"template preflight: {exc}"},
        )
        return C.STATUS_FAILED, None

    aggregation_context = None
    if aggregation_context_path is not None and aggregation_context_path.is_file():
        aggregation_context = load_template(aggregation_context_path)
    criterion_order = _criterion_order(output_contract)
    valid_criterion_ids = tuple(output_contract.get("valid_criterion_ids", []))

    def _validate_existing(document: dict[str, Any]) -> list:
        return validate_aggregation_document(
            document,
            criterion_order=criterion_order,
            aggregation_context=aggregation_context,
        )

    final_status: dict[str, Any] = {"ok": True, "errors": []}

    def _publish(document: dict[str, Any]) -> None:
        try:
            staged_stage.assemble_semantic(ctx, runner=runner)
            verdict = staged_stage.validate_final(ctx, runner=runner)
        except staged_stage.StagedStageError as exc:
            final_status.update(ok=False, errors=[str(exc)])
            return
        if not verdict.ok:
            final_status.update(ok=False, errors=list(verdict.errors))
            return
        attempts.record_checkpoint(
            Attempt(
                attempt_id=make_job_id(),
                job_id=ctx.job_id,
                run_id=ctx.run_id,
                feat_id=None,
                stage=S.ATTEMPT_STAGE_AGGREGATION,
                status=S.ATTEMPT_COMPLETED,
                started_at=utc_now(),
                finished_at=utc_now(),
                exit_code=0,
                artifact_dir=str(ctx.run_dir),
            )
        )

    # design D2 artifact reuse: an already-validated aggregation document is
    # re-assembled without a new executor call (a stale semantic-result or a
    # stale executor-result cache never invalidates the published judgment)
    if aggregation_path.is_file():
        existing = load_template(aggregation_path)
        if existing.get("status") == "complete" and not blocking(
            _validate_existing(existing)
        ):
            _publish(existing)
            if final_status["ok"]:
                events.append(ctx.job_id, "aggregation_reused_document", {
                    "aggregation": str(aggregation_path),
                })
                return C.STATUS_COMPLETED, semantic_result_path
            final_status.update(ok=True, errors=[])
            events.append(ctx.job_id, "aggregation_reuse_rejected_document", {
                "errors": list(final_status["errors"]),
            })

    work = _build_aggregation_input(
        ctx, aggregation_context_path, valid_criterion_ids
    )

    def _normalize(payload: dict[str, Any]) -> Any:
        return normalize_aggregation(
            template, payload, source_observation_ids=source_observation_ids
        )

    def _validate(document: dict[str, Any]) -> list:
        return validate_aggregation_document(
            document,
            criterion_order=criterion_order,
            aggregation_context=aggregation_context,
        )


    flow = JudgmentFlow(
        ctx=ctx, executor=executor, jobs=jobs, events=events,
        statistics=statistics, invocations=invocations, emit=emit,
        cancel=cancel,
    )
    events.append(ctx.job_id, "work_item_started", {
        "work_item_id": work.work_item_id,
    })
    fingerprint = input_fingerprint(
        evaluator_version=ctx.evaluator_version,
        protocol_version=ctx.protocol_version,
        input_paths=list(work.input_paths),
        template_bytes=aggregation_path.read_bytes(),
    )
    outcome = flow.run(
        work=work,
        output_path=aggregation_path,
        template=template,
        normalize=_normalize,
        validate=_validate,
        base_contract=work.prompt_extras,
        on_publish=_publish,
        fingerprint=fingerprint,
        stage_event="aggregation_completed",
    )
    if outcome.status != C.STATUS_COMPLETED:
        return outcome.status, None
    if not final_status["ok"]:
        jobs.transition_status(
            ctx.job_id, S.FAILED,
            event_type="aggregation_failed",
            payload={"errors": final_status["errors"]},
        )
        return C.STATUS_FAILED, None
    return C.STATUS_COMPLETED, semantic_result_path


def _build_aggregation_input(
    ctx: RunContext,
    aggregation_context_path: Path | None,
    valid_criterion_ids: tuple[str, ...] = (),
) -> C.WorkItemInput:
    from spec_eval.kernel.machine_contract import (
        build_aggregation_machine_contract,
    )

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
        ctx.run_dir / "output-contract.json",
        aggregation_context_path,
        ctx.run_dir / "work-items.json",
        ctx.skill_scripts_dir.parent / "references" / "staged-run-contract.md",
    ):
        if contract_input is not None and contract_input.is_file():
            input_paths.append(str(contract_input))
    input_paths = list(dict.fromkeys(input_paths))
    machine_contract = build_aggregation_machine_contract(
        valid_criterion_ids=valid_criterion_ids,
        aggregation_context_path=(
            str(aggregation_context_path)
            if aggregation_context_path is not None else None
        ),
    )
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
        prompt_extras=observe_aggregation_prompt_contract(
            template_path=aggregation_path,
            schema_dir=ctx.run_dir,
            machine_contract=machine_contract,
        ),
    )


def _criterion_order(output_contract: dict[str, Any]) -> list[str]:
    order = output_contract.get("aggregation_payload", {}).get("criterion_order")
    if isinstance(order, list):
        return [str(item) for item in order]
    return [str(item) for item in output_contract.get("valid_criterion_ids", [])]


def _source_observation_ids(work_items_path: Path) -> list[str]:
    try:
        document = json.loads(work_items_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"cannot load work items {work_items_path}: {exc}"
        ) from exc
    items = document.get("items") if isinstance(document, dict) else None
    if not isinstance(items, list):
        raise ValueError(f"work items document has no items list: {work_items_path}")
    result: list[str] = []
    for item in items:
        item_id = item.get("id") if isinstance(item, dict) else None
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(
                f"work items contain an invalid id: {work_items_path}"
            )
        result.append(item_id)
    return result
