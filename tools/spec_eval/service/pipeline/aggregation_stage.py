"""Aggregation stage (protocol 0.2.0): produce a validated ``semantic-result.json``.

After all observation work items are validated, this stage asks the executor
for one aggregation judgment payload (envelope v3, strict schema), expands it
into the published ``aggregation.json`` through the kernel normalizer, typed-
validates it against the aggregation context, then runs
``assemble_semantic_result.py`` to freeze ``semantic-result.json`` and
validates the ``final`` stage. Evidence or semantic correction uses one bounded
JSON Patch turn; only unambiguous field/enum/ownership normalization remains
service-handled. Semantic Criterion/Claim mapping errors are delegated to the
model with the other correction errors.

Anti-fake-completion: a missing/invalid aggregation body, a structural assemble
failure, or a failed final validator all fail the job — ``semantic-result.json``
is never written by a failed path. The assemble script may downgrade bounded
cross-Criterion Critical and observation-primary ownership checks to confidence
warnings.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from spec_eval.kernel.errors import compute_confidence, has_hard_errors
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

    final_status: dict[str, Any] = {"ok": True, "errors": [], "confidence": None}

    def _publish(document: dict[str, Any]) -> None:
        typed_errors = _validate_existing(document)
        if has_hard_errors(typed_errors):
            final_status.update(
                ok=False,
                errors=[f"{e.code}: {e.expected or e.actual}" for e in typed_errors],
            )
            return
        final_status["errors"] = [
            f"{error.code}: {error.expected or error.actual}"
            for error in typed_errors
        ]
        confidence = compute_confidence(typed_errors)
        confidence_path = ctx.run_dir / "confidence-result.json"
        try:
            confidence_path.write_text(
                json.dumps(confidence, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
        final_status["confidence"] = confidence
        try:
            staged_stage.assemble_semantic(ctx, runner=runner)
        except staged_stage.StagedStageError as exc:
            final_status.update(ok=False, errors=[str(exc)])
            return
        try:
            verdict = staged_stage.validate_final(ctx, runner=runner)
        except staged_stage.StagedStageError as exc:
            verdict = staged_stage.ValidationResult(ok=False, errors=(str(exc),))
        if not verdict.ok:
            final_status["errors"] = list(verdict.errors)
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
        if existing.get("status") == "complete" and not has_hard_errors(
            _validate_existing(existing)
        ):
            _publish(existing)
            if final_status["ok"]:
                events.append(ctx.job_id, "aggregation_reused_document", {
                    "aggregation": str(aggregation_path),
                    "confidence": final_status.get("confidence"),
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
            template, payload,
            source_observation_ids=source_observation_ids,
            aggregation_context=aggregation_context,
        )

    def _normalize_after_correction(payload: dict[str, Any]) -> Any:
        return normalize_aggregation(
            template, payload,
            source_observation_ids=source_observation_ids,
            aggregation_context=aggregation_context,
            allow_ownership_fallback=True,
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
        input_paths=[
            *work.input_paths,
            str(work.prompt_extras["schema_path"]),
        ],
        input_resources=work.work_item.get("input_resources", []),
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
        normalize_after_correction=_normalize_after_correction,
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
    confidence = final_status.get("confidence")
    if confidence and final_status["errors"]:
        events.append(ctx.job_id, "aggregation_completed_with_warnings", {
            "confidence_score": confidence.get("confidence_score"),
            "confidence_level": confidence.get("confidence_level"),
            "warnings": final_status["errors"][:10],
        })
    return C.STATUS_COMPLETED, semantic_result_path


def _build_aggregation_input(
    ctx: RunContext,
    aggregation_context_path: Path | None,
    valid_criterion_ids: tuple[str, ...] = (),
) -> C.WorkItemInput:
    from spec_eval.kernel.machine_contract import (
        build_aggregation_machine_contract,
    )

    aggregation_path = ctx.run_dir / "aggregation.json"
    input_paths: list[str] = []
    input_resources: list[dict[str, Any]] = []
    if aggregation_context_path is not None and aggregation_context_path.is_file():
        input_paths.append(str(aggregation_context_path))
        input_resources.append({
            "path": str(aggregation_context_path),
            "role": "semantic_input",
            "citable": False,
        })
    phase_references: list[dict[str, str]] = []
    for name, filename, role in (
        ("aggregation-contract", "aggregation-contract.md", "executor_contract"),
        ("aggregation-guide", "aggregation-guide.md", "executor_guide"),
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
    machine_contract = build_aggregation_machine_contract(
        valid_criterion_ids=valid_criterion_ids,
        aggregation_context_path=(
            str(aggregation_context_path)
            if aggregation_context_path is not None else None
        ),
    )
    prompt_contract = observe_aggregation_prompt_contract(
        template_path=aggregation_path,
        schema_dir=ctx.run_dir,
        machine_contract=machine_contract,
    )
    prompt_contract["phase_references"] = phase_references
    prompt_contract["observation_profile"] = "aggregation"
    return C.WorkItemInput(
        job_id=ctx.job_id,
        func_id=ctx.func_id,
        run_id=ctx.run_id,
        work_item_id="aggregation:final",
        work_item={
            "id": "aggregation:final",
            "type": "aggregation",
            "observation_type": "aggregation",
            "observation_profile": "aggregation",
            "input_paths": input_paths,
            "input_resources": input_resources,
            "output_path": str(aggregation_path),
        },
        run_dir=str(ctx.run_dir),
        input_paths=tuple(input_paths),
        executor_result_path=str(ctx.run_dir / "aggregation.executor-result.json"),
        repo_root=str(ctx.repo_root),
        skill_version=ctx.evaluator_version,
        protocol_version=ctx.protocol_version,
        forbidden_paths=ctx.forbidden_paths,
        prompt_extras=prompt_contract,
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
