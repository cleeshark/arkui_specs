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
from .result_payload import (
    claim_evidence_repair_prompt_contract,
    load_template,
    merge_observation_payload,
    observation_evidence_repair_prompt_contract,
    observation_prompt_contract,
    repair_prompt_contract,
)
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


_REPAIRABLE_VALIDATION_ERROR_MARKERS = (
    ".evidence_id: invalid evidence ID",
    ".content_hash: expected sha256:<64 lowercase hex digits>",
    ".criterion_ids: unknown criteria",
    ".defect_keys: only conflict or missing claims may own defects",
)
_MISSING_OBSERVATION_EVIDENCE = re.compile(
    r"\.observations\[(\d+)\]\.evidence: evidence is required for this local outcome$"
)
_CLAIM_REVIEW_REPAIR_ERROR = re.compile(
    r"\.claim_reviews\[(\d+)\](?:"
    r"(?:\.unit_reviews\[\d+\])?\.evidence_ids: unknown evidence|"
    r"\.reason: expected an evidence-specific explanation|"
    r"\.unit_reviews\[\d+\]\.fact: expected an evidence-specific atomic fact"
    r")"
)


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
    statistics: JobStatisticsRepository | None = None,
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

        try:
            output_path = Path(str(item["output_path"]))
            initialized = load_template(output_path)
        except (KeyError, ValueError) as exc:
            jobs.transition_status(
                ctx.job_id, S.FAILED,
                event_type="semantic_failed",
                payload={"work_item_id": item.get("id"), "error": f"template preflight: {exc}"},
            )
            return SemanticStageResult(C.STATUS_FAILED, completed, f"template preflight: {exc}")

        work = _build_work_input(ctx, item)
        events.append(ctx.job_id, "work_item_started", {"work_item_id": work.work_item_id})
        result = executor.execute(work, emit, cancel)
        _record_executor_statistics(statistics, ctx.job_id, result)

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

        candidate_path = output_path.with_name(f".{output_path.name}.candidate")
        try:
            candidate = merge_observation_payload(initialized, result.observation)
            _write_candidate(candidate_path, candidate)
            verdict = staged_stage.validate_work_item_candidate(
                ctx, work.work_item_id, candidate_path, runner=runner
            )
            repair_modes_attempted: set[str] = set()
            has_machine_contract = bool(
                work.prompt_extras.get("machine_contract", {}).get("payload")
            )
            while not verdict.ok and has_machine_contract:
                mechanical_errors = _mechanical_validation_errors(verdict.errors)
                target_indexes = _evidence_completion_indexes(verdict.errors)
                target_claim_indexes = _claim_review_repair_indexes(verdict.errors)

                if mechanical_errors and "mechanical" not in repair_modes_attempted:
                    repair_modes_attempted.add("mechanical")
                    events.append(
                        ctx.job_id,
                        "candidate_validation_failed",
                        {
                            "work_item_id": work.work_item_id,
                            "repairable": True,
                            "repair_mode": "repair_candidate",
                            "errors": list(verdict.errors),
                            "repair_errors": list(mechanical_errors),
                        },
                    )
                    repair_work = _build_repair_work_input(
                        work, candidate_path, mechanical_errors
                    )
                    events.append(
                        ctx.job_id,
                        "candidate_repair_started",
                        {"work_item_id": work.work_item_id, "repair_attempt": 1},
                    )
                    repair_result = executor.execute(repair_work, emit, cancel)
                    _record_executor_statistics(statistics, ctx.job_id, repair_result)
                    if repair_result.status == C.STATUS_CANCELLED or (
                        cancel is not None and cancel.is_set()
                    ):
                        return SemanticStageResult(
                            C.STATUS_CANCELLED, completed, "cancelled during candidate repair"
                        )
                    if not repair_result.succeeded:
                        error = repair_result.error or f"repair executor {repair_result.status}"
                        events.append(
                            ctx.job_id,
                            "candidate_repair_failed",
                            {
                                "work_item_id": work.work_item_id,
                                "repair_attempt": 1,
                                "error": error,
                            },
                        )
                        jobs.transition_status(
                            ctx.job_id,
                            S.FAILED,
                            event_type="semantic_failed",
                            payload={"work_item_id": work.work_item_id, "error": error},
                        )
                        return SemanticStageResult(C.STATUS_FAILED, completed, error)
                    candidate = merge_observation_payload(
                        initialized, repair_result.observation
                    )
                    _write_candidate(candidate_path, candidate)
                    verdict = staged_stage.validate_work_item_candidate(
                        ctx, work.work_item_id, candidate_path, runner=runner
                    )
                    mechanical_resolved = not _mechanical_validation_errors(verdict.errors)
                    events.append(
                        ctx.job_id,
                        (
                            "candidate_repair_completed"
                            if mechanical_resolved
                            else "candidate_repair_failed"
                        ),
                        {
                            "work_item_id": work.work_item_id,
                            "repair_attempt": 1,
                            "errors": list(verdict.errors),
                        },
                    )
                    continue

                if target_indexes and "observation_evidence" not in repair_modes_attempted:
                    repair_modes_attempted.add("observation_evidence")
                    evidence_errors = _observation_evidence_errors(verdict.errors)
                    events.append(
                        ctx.job_id,
                        "candidate_validation_failed",
                        {
                            "work_item_id": work.work_item_id,
                            "repairable": True,
                            "repair_mode": "complete_observation_evidence",
                            "errors": list(verdict.errors),
                            "repair_errors": list(evidence_errors),
                        },
                    )
                    repair_work = _build_evidence_repair_work_input(
                        work, candidate_path, evidence_errors, target_indexes
                    )
                    events.append(
                        ctx.job_id,
                        "candidate_evidence_repair_started",
                        {
                            "work_item_id": work.work_item_id,
                            "repair_attempt": 1,
                            "target_observation_indexes": list(target_indexes),
                        },
                    )
                    repair_result = executor.execute(repair_work, emit, cancel)
                    _record_executor_statistics(statistics, ctx.job_id, repair_result)
                    if repair_result.status == C.STATUS_CANCELLED or (
                        cancel is not None and cancel.is_set()
                    ):
                        return SemanticStageResult(
                            C.STATUS_CANCELLED,
                            completed,
                            "cancelled during observation evidence repair",
                        )
                    if not repair_result.succeeded:
                        error = repair_result.error or (
                            f"evidence repair executor {repair_result.status}"
                        )
                        events.append(
                            ctx.job_id,
                            "candidate_evidence_repair_failed",
                            {
                                "work_item_id": work.work_item_id,
                                "repair_attempt": 1,
                                "error": error,
                            },
                        )
                        jobs.transition_status(
                            ctx.job_id,
                            S.FAILED,
                            event_type="semantic_failed",
                            payload={"work_item_id": work.work_item_id, "error": error},
                        )
                        return SemanticStageResult(C.STATUS_FAILED, completed, error)
                    repaired_candidate = merge_observation_payload(
                        initialized, repair_result.observation
                    )
                    if not _evidence_repair_preserves_semantics(
                        candidate, repaired_candidate, target_indexes
                    ):
                        error = (
                            "observation evidence repair changed fields outside target evidence"
                        )
                        events.append(
                            ctx.job_id,
                            "candidate_evidence_repair_failed",
                            {
                                "work_item_id": work.work_item_id,
                                "repair_attempt": 1,
                                "error": error,
                            },
                        )
                        jobs.transition_status(
                            ctx.job_id,
                            S.FAILED,
                            event_type="semantic_failed",
                            payload={"work_item_id": work.work_item_id, "error": error},
                        )
                        return SemanticStageResult(C.STATUS_FAILED, completed, error)
                    candidate = repaired_candidate
                    _write_candidate(candidate_path, candidate)
                    verdict = staged_stage.validate_work_item_candidate(
                        ctx, work.work_item_id, candidate_path, runner=runner
                    )
                    evidence_resolved = not _evidence_completion_indexes(verdict.errors)
                    events.append(
                        ctx.job_id,
                        (
                            "candidate_evidence_repair_completed"
                            if evidence_resolved
                            else "candidate_evidence_repair_failed"
                        ),
                        {
                            "work_item_id": work.work_item_id,
                            "repair_attempt": 1,
                            "errors": list(verdict.errors),
                        },
                    )
                    continue

                if target_claim_indexes and "claim_evidence" not in repair_modes_attempted:
                    repair_modes_attempted.add("claim_evidence")
                    claim_errors = _claim_review_repair_errors(verdict.errors)
                    target_claim_ids = _claim_ids_for_indexes(
                        candidate, target_claim_indexes
                    )
                    available_evidence_ids = _available_evidence_ids(candidate)
                    events.append(
                        ctx.job_id,
                        "candidate_validation_failed",
                        {
                            "work_item_id": work.work_item_id,
                            "repairable": True,
                            "repair_mode": "repair_claim_evidence_references",
                            "errors": list(verdict.errors),
                            "repair_errors": list(claim_errors),
                        },
                    )
                    repair_work = _build_claim_evidence_repair_work_input(
                        work,
                        candidate_path,
                        claim_errors,
                        target_claim_ids,
                        available_evidence_ids,
                    )
                    events.append(
                        ctx.job_id,
                        "candidate_claim_evidence_repair_started",
                        {
                            "work_item_id": work.work_item_id,
                            "repair_attempt": 1,
                            "target_claim_ids": list(target_claim_ids),
                        },
                    )
                    repair_result = executor.execute(repair_work, emit, cancel)
                    _record_executor_statistics(statistics, ctx.job_id, repair_result)
                    if repair_result.status == C.STATUS_CANCELLED or (
                        cancel is not None and cancel.is_set()
                    ):
                        return SemanticStageResult(
                            C.STATUS_CANCELLED,
                            completed,
                            "cancelled during Claim evidence repair",
                        )
                    if not repair_result.succeeded:
                        error = repair_result.error or (
                            f"Claim evidence repair executor {repair_result.status}"
                        )
                        events.append(
                            ctx.job_id,
                            "candidate_claim_evidence_repair_failed",
                            {
                                "work_item_id": work.work_item_id,
                                "repair_attempt": 1,
                                "error": error,
                            },
                        )
                        jobs.transition_status(
                            ctx.job_id,
                            S.FAILED,
                            event_type="semantic_failed",
                            payload={"work_item_id": work.work_item_id, "error": error},
                        )
                        return SemanticStageResult(C.STATUS_FAILED, completed, error)
                    repaired_candidate = merge_observation_payload(
                        initialized, repair_result.observation
                    )
                    if not _claim_evidence_repair_preserves_scope(
                        candidate, repaired_candidate, target_claim_ids
                    ):
                        error = (
                            "Claim evidence repair changed fields outside target Claim reviews"
                        )
                        events.append(
                            ctx.job_id,
                            "candidate_claim_evidence_repair_failed",
                            {
                                "work_item_id": work.work_item_id,
                                "repair_attempt": 1,
                                "error": error,
                            },
                        )
                        jobs.transition_status(
                            ctx.job_id,
                            S.FAILED,
                            event_type="semantic_failed",
                            payload={"work_item_id": work.work_item_id, "error": error},
                        )
                        return SemanticStageResult(C.STATUS_FAILED, completed, error)
                    candidate = repaired_candidate
                    _write_candidate(candidate_path, candidate)
                    verdict = staged_stage.validate_work_item_candidate(
                        ctx, work.work_item_id, candidate_path, runner=runner
                    )
                    claim_evidence_resolved = not _claim_review_repair_indexes(
                        verdict.errors
                    )
                    events.append(
                        ctx.job_id,
                        (
                            "candidate_claim_evidence_repair_completed"
                            if claim_evidence_resolved
                            else "candidate_claim_evidence_repair_failed"
                        ),
                        {
                            "work_item_id": work.work_item_id,
                            "repair_attempt": 1,
                            "errors": list(verdict.errors),
                        },
                    )
                    continue

                break
            if not verdict.ok:
                jobs.transition_status(
                    ctx.job_id, S.FAILED,
                    event_type="semantic_failed",
                    payload={"work_item_id": work.work_item_id, "errors": list(verdict.errors)},
                )
                return SemanticStageResult(
                    C.STATUS_FAILED, completed, "validator: " + "; ".join(verdict.errors)
                )
            candidate_path.replace(output_path)
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            jobs.transition_status(
                ctx.job_id, S.FAILED,
                event_type="semantic_failed", payload={
                    "work_item_id": work.work_item_id,
                    "error": f"observation candidate: {exc}",
                },
            )
            return SemanticStageResult(
                C.STATUS_FAILED, completed, f"observation candidate: {exc}"
            )
        finally:
            candidate_path.unlink(missing_ok=True)

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
    input_paths = [str(path) for path in item.get("input_paths", [])]
    input_paths.append(str(output_path))
    staged_contract = ctx.skill_scripts_dir.parent / "references" / "staged-run-contract.md"
    if staged_contract.is_file():
        input_paths.append(str(staged_contract))
    input_paths = list(dict.fromkeys(input_paths))
    return C.WorkItemInput(
        job_id=ctx.job_id,
        func_id=ctx.func_id,
        run_id=ctx.run_id,
        work_item_id=str(item["id"]),
        work_item=item,
        run_dir=str(ctx.run_dir),
        input_paths=tuple(input_paths),
        executor_result_path=str(executor_result_path),
        repo_root=str(ctx.repo_root),
        skill_version=ctx.evaluator_version,
        protocol_version=ctx.protocol_version,
        forbidden_paths=ctx.forbidden_paths,
        prompt_extras=observation_prompt_contract(
            output_path, ctx.run_dir / "output-contract.json"
        ),
    )


def _build_repair_work_input(
    work: C.WorkItemInput,
    candidate_path: Path,
    validation_errors: tuple[str, ...],
) -> C.WorkItemInput:
    template_path = Path(str(work.prompt_extras["template_path"]))
    output_contract_path = Path(str(work.prompt_extras["output_contract_path"]))
    result_path = Path(work.executor_result_path)
    repair_result_path = result_path.with_name(
        f"{result_path.stem}.repair-1{result_path.suffix}"
    )
    return replace(
        work,
        input_paths=(
            str(candidate_path),
            str(template_path),
            str(output_contract_path),
        ),
        executor_result_path=str(repair_result_path),
        prompt_extras=repair_prompt_contract(
            work.prompt_extras,
            candidate_path=candidate_path,
            validation_errors=validation_errors,
        ),
    )


def _build_evidence_repair_work_input(
    work: C.WorkItemInput,
    candidate_path: Path,
    validation_errors: tuple[str, ...],
    target_observation_indexes: tuple[int, ...],
) -> C.WorkItemInput:
    template_path = Path(str(work.prompt_extras["template_path"]))
    output_contract_path = Path(str(work.prompt_extras["output_contract_path"]))
    result_path = Path(work.executor_result_path)
    repair_result_path = result_path.with_name(
        f"{result_path.stem}.evidence-repair-1{result_path.suffix}"
    )
    input_paths = list(dict.fromkeys((
        str(candidate_path),
        str(template_path),
        str(output_contract_path),
        *work.input_paths,
    )))
    return replace(
        work,
        input_paths=tuple(input_paths),
        executor_result_path=str(repair_result_path),
        prompt_extras=observation_evidence_repair_prompt_contract(
            work.prompt_extras,
            candidate_path=candidate_path,
            validation_errors=validation_errors,
            target_observation_indexes=target_observation_indexes,
        ),
    )


def _build_claim_evidence_repair_work_input(
    work: C.WorkItemInput,
    candidate_path: Path,
    validation_errors: tuple[str, ...],
    target_claim_ids: tuple[str, ...],
    available_evidence_ids: tuple[str, ...],
) -> C.WorkItemInput:
    template_path = Path(str(work.prompt_extras["template_path"]))
    output_contract_path = Path(str(work.prompt_extras["output_contract_path"]))
    result_path = Path(work.executor_result_path)
    repair_result_path = result_path.with_name(
        f"{result_path.stem}.claim-evidence-repair-1{result_path.suffix}"
    )
    input_paths = list(dict.fromkeys((
        str(candidate_path),
        str(template_path),
        str(output_contract_path),
        *work.input_paths,
    )))
    return replace(
        work,
        input_paths=tuple(input_paths),
        executor_result_path=str(repair_result_path),
        prompt_extras=claim_evidence_repair_prompt_contract(
            work.prompt_extras,
            candidate_path=candidate_path,
            validation_errors=validation_errors,
            target_claim_ids=target_claim_ids,
            available_evidence_ids=available_evidence_ids,
        ),
    )


def _mechanical_validation_errors(errors: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        error
        for error in errors
        if (".evidence[" in error and ".type:" in error)
        or any(marker in error for marker in _REPAIRABLE_VALIDATION_ERROR_MARKERS)
    )


def _observation_evidence_errors(errors: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(error for error in errors if _MISSING_OBSERVATION_EVIDENCE.search(error))


def _evidence_completion_indexes(errors: tuple[str, ...]) -> tuple[int, ...]:
    indexes: set[int] = set()
    for error in errors:
        match = _MISSING_OBSERVATION_EVIDENCE.search(error)
        if match is not None:
            indexes.add(int(match.group(1)))
    return tuple(sorted(indexes))


def _claim_review_repair_errors(errors: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(error for error in errors if _CLAIM_REVIEW_REPAIR_ERROR.search(error))


def _claim_review_repair_indexes(errors: tuple[str, ...]) -> tuple[int, ...]:
    indexes: set[int] = set()
    for error in errors:
        match = _CLAIM_REVIEW_REPAIR_ERROR.search(error)
        if match is not None:
            indexes.add(int(match.group(1)))
    return tuple(sorted(indexes))


def _claim_ids_for_indexes(
    candidate: dict[str, Any], target_indexes: tuple[int, ...]
) -> tuple[str, ...]:
    claim_reviews = candidate.get("claim_reviews")
    if not isinstance(claim_reviews, list):
        raise ValueError("Claim evidence repair requires claim_reviews")
    claim_ids: list[str] = []
    for index in target_indexes:
        if index >= len(claim_reviews) or not isinstance(claim_reviews[index], dict):
            raise ValueError(f"Claim evidence repair target index is invalid: {index}")
        claim_id = claim_reviews[index].get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            raise ValueError(f"Claim evidence repair target has no Claim ID: {index}")
        claim_ids.append(claim_id)
    return tuple(claim_ids)


def _available_evidence_ids(candidate: dict[str, Any]) -> tuple[str, ...]:
    evidence_ids: set[str] = set()
    observations = candidate.get("observations")
    if not isinstance(observations, list):
        return ()
    for observation in observations:
        if not isinstance(observation, dict) or not isinstance(observation.get("evidence"), list):
            continue
        for evidence in observation["evidence"]:
            if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str):
                evidence_ids.add(evidence["evidence_id"])
    return tuple(sorted(evidence_ids))


def _evidence_repair_preserves_semantics(
    candidate: dict[str, Any],
    repaired: dict[str, Any],
    target_observation_indexes: tuple[int, ...],
) -> bool:
    before = json.loads(json.dumps(candidate))
    after = json.loads(json.dumps(repaired))
    before_observations = before.get("observations")
    after_observations = after.get("observations")
    if not isinstance(before_observations, list) or not isinstance(after_observations, list):
        return False
    if len(before_observations) != len(after_observations):
        return False
    for index in target_observation_indexes:
        if index >= len(before_observations):
            return False
        before_observation = before_observations[index]
        after_observation = after_observations[index]
        if not isinstance(before_observation, dict) or not isinstance(after_observation, dict):
            return False
        if before_observation.get("evidence"):
            return False
        if not after_observation.get("evidence"):
            return False
        before_observation["evidence"] = []
        after_observation["evidence"] = []
    return before == after


def _claim_evidence_repair_preserves_scope(
    candidate: dict[str, Any],
    repaired: dict[str, Any],
    target_claim_ids: tuple[str, ...],
) -> bool:
    before = json.loads(json.dumps(candidate))
    after = json.loads(json.dumps(repaired))
    before_reviews = before.get("claim_reviews")
    after_reviews = after.get("claim_reviews")
    if not isinstance(before_reviews, list) or not isinstance(after_reviews, list):
        return False
    if len(before_reviews) != len(after_reviews):
        return False
    before["claim_reviews"] = []
    after["claim_reviews"] = []
    if before != after:
        return False

    target_ids = set(target_claim_ids)
    seen_targets: set[str] = set()
    available_evidence_ids = set(_available_evidence_ids(candidate))
    for before_review, after_review in zip(before_reviews, after_reviews):
        if not isinstance(before_review, dict) or not isinstance(after_review, dict):
            return False
        claim_id = before_review.get("claim_id")
        if claim_id != after_review.get("claim_id") or not isinstance(claim_id, str):
            return False
        if claim_id not in target_ids:
            if before_review != after_review:
                return False
            continue
        seen_targets.add(claim_id)
        if _claim_review_scope(before_review) != _claim_review_scope(after_review):
            return False
        if not _bounded_outcome_change(
            before_review.get("local_outcome"), after_review.get("local_outcome")
        ):
            return False
        after_evidence = after_review.get("evidence_ids")
        if (
            not isinstance(after_evidence, list)
            or not all(isinstance(item, str) for item in after_evidence)
            or not set(after_evidence) <= available_evidence_ids
        ):
            return False
        before_defects = before_review.get("defect_keys")
        after_defects = after_review.get("defect_keys")
        if (
            not isinstance(before_defects, list)
            or not isinstance(after_defects, list)
            or not all(isinstance(item, str) for item in before_defects)
            or not all(isinstance(item, str) for item in after_defects)
        ):
            return False
        if not set(after_defects) <= set(before_defects):
            return False
        if after_review.get("local_outcome") == "NOT_VERIFIABLE":
            if after_evidence or after_defects:
                return False

        before_units = before_review.get("unit_reviews")
        after_units = after_review.get("unit_reviews")
        if not isinstance(before_units, list) or not isinstance(after_units, list):
            return False
        if len(before_units) != len(after_units):
            return False
        for before_unit, after_unit in zip(before_units, after_units):
            if not isinstance(before_unit, dict) or not isinstance(after_unit, dict):
                return False
            if not _bounded_outcome_change(
                before_unit.get("local_outcome"), after_unit.get("local_outcome")
            ):
                return False
            unit_evidence = after_unit.get("evidence_ids")
            if (
                not isinstance(unit_evidence, list)
                or not all(isinstance(item, str) for item in unit_evidence)
                or not set(unit_evidence) <= available_evidence_ids
            ):
                return False
            if after_unit.get("local_outcome") == "NOT_VERIFIABLE" and unit_evidence:
                return False
    return seen_targets == target_ids


def _claim_review_scope(review: dict[str, Any]) -> dict[str, Any]:
    scope = json.loads(json.dumps(review))
    for field in ("local_outcome", "evidence_ids", "reason", "defect_keys"):
        scope.pop(field, None)
    units = scope.get("unit_reviews")
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict):
                continue
            for field in ("local_outcome", "evidence_ids", "fact"):
                unit.pop(field, None)
    return scope


def _bounded_outcome_change(before: Any, after: Any) -> bool:
    return after == before or after == "NOT_VERIFIABLE"


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

    # preparing (once): freeze dependency revisions
    if job.status == S.QUEUED:
        jobs.transition_status(job_id, S.PREPARING, event_type="enter_preparing")
        _freeze_snapshots(job_id, workspace, snapshots, events)

    # evidence (once): build the shared package unless already present
    job = jobs.get_job(job_id)
    if job.status == S.PREPARING:
        jobs.transition_status(job_id, S.EVIDENCE, event_type="enter_evidence")
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

    # semantic phase: observations for every run
    job = jobs.get_job(job_id)
    if job.status == S.EVIDENCE:
        jobs.transition_status(job_id, S.SEMANTIC, event_type="enter_semantic")
    for run_id in run_ids:
        if cancel is not None and cancel.is_set():
            return SemanticStageResult(C.STATUS_CANCELLED, 0, "cancelled")
        sem = run_semantic(
            ctx_for(run_id), executor, jobs=jobs, attempts=attempts, events=events,
            statistics=statistics, cancel=cancel, runner=runner,
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
            statistics=statistics, cancel=cancel, runner=runner,
        )
        if outcome != C.STATUS_COMPLETED:
            return SemanticStageResult(outcome, 0, None)
        semantic_results[run_id] = sr

    # deterministic report (score/stability/report) on the selected run
    job = jobs.get_job(job_id)
    if job.status == S.AGGREGATION:
        from . import report_stage, site_history_stage, archive_stage
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
        jobs.transition_status(job_id, S.ARCHIVE, event_type="enter_archive")
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
        if refresh_targets is not None:
            target = refresh_targets.get(job_id)
            if target is not None:
                _register_rolling_report(
                    settings=settings,
                    job=resolved_job,
                    target=target,
                    archive_dir=archive_dir,
                    aggregate_dir=report_ctx.aggregate_dir,
                    selected_run_id=selected_run_id,
                    refresh_targets=refresh_targets,
                    events=events,
                    pending_delta=pending_delta,
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
    )


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
