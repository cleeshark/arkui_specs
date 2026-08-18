"""Unified judgment flow for evaluator protocol 0.2.0.

Implements the work item state machine (design v3 R3) shared by the
observation and aggregation stages:

    GENERATE_PENDING
      -> GENERATED_INVALID   (observe completed, typed validation failed)
      -> VALIDATED           (observe first pass)
    GENERATED_INVALID
      -> CORRECTION_PENDING  (the single generic correction turn)
    CORRECTION_PENDING
      -> VALIDATED                     (correction output validates)
      -> CORRECTION_INVALID_TERMINAL   (correction completed but still invalid:
                                        terminal, requires a new generation)
      -> CORRECTION_PENDING            (process interrupted before a complete
                                        result: the retry resumes the same
                                        attempt from the stored candidate)

Every executor call is recorded as one invocation (attempt) with executor,
timing and usage. The 0.1.x repair modes, scope guards and fallbacks do not
exist here.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from spec_eval.kernel import staged_state as SS
from spec_eval.kernel.errors import TypedError, blocking
from spec_eval.kernel.normalize import NormalizationResult
from spec_eval.service.domain import states as S
from spec_eval.service.executors import contract as C
from spec_eval.service.executors.base import SemanticExecutor
from spec_eval.service.pipeline.context import RunContext
from spec_eval.service.pipeline.result_payload import (
    correct_prompt_contract,
)
from spec_eval.service.store.repositories import (
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)

Terminating = Callable[[str, str], None]
"""transition(job_id, event_type, payload) used for terminal failures."""


@dataclass(frozen=True)
class JudgmentOutcome:
    """One work item's terminal or checkpoint outcome."""

    status: str  # C.STATUS_* value
    error: str | None = None
    published: bool = False


def input_fingerprint(
    *, evaluator_version: str, protocol_version: str, input_paths: Sequence[str],
    template_bytes: bytes, input_resources: Sequence[dict[str, Any]] = (),
) -> str:
    """Layered fingerprint base for resume decisions (design v3 R4).

    Covers the evaluator/protocol identity, the frozen input path set and file
    contents, and the initialized template; callers extend it with executor
    identity where the executor varies per run.
    """
    digest = hashlib.sha256()
    digest.update(evaluator_version.encode("utf-8"))
    digest.update(b"\0")
    digest.update(protocol_version.encode("utf-8"))
    digest.update(b"\0")
    for path in input_paths:
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        input_path = Path(path)
        if input_path.is_file():
            with input_path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        digest.update(b"\n")
    digest.update(b"\0")
    digest.update(json.dumps(
        list(input_resources), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8"))
    digest.update(b"\0")
    digest.update(template_bytes)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


class JudgmentFlow:
    """Drives observe -> normalize -> typed validate -> (one) correct."""

    def __init__(
        self,
        *,
        ctx: RunContext,
        executor: SemanticExecutor,
        jobs: JobRepository,
        events: EventRepository,
        statistics: JobStatisticsRepository | None = None,
        invocations: Any = None,
        emit: Any = None,
        cancel: Any = None,
        runner: Any = None,
    ) -> None:
        self.ctx = ctx
        self.executor = executor
        self.jobs = jobs
        self.events = events
        self.statistics = statistics
        self.invocations = invocations
        self.emit = emit
        self.cancel = cancel

    # --- executor invocation ------------------------------------------------

    def _execute(
        self, work: C.WorkItemInput, attempt_type: str
    ) -> tuple[C.ExecutionResult | None, str | None]:
        started = time.monotonic()
        result = self.executor.execute(work, self.emit, self.cancel)
        self._record(work, attempt_type, result, started)
        if self.cancel is not None and self.cancel.is_set():
            return None, "cancelled"
        if result.status == C.STATUS_CANCELLED:
            return None, "cancelled"
        if result.status == C.STATUS_AWAITING:
            self.jobs.transition_status(
                self.ctx.job_id,
                S.WAITING,
                event_type="awaiting_executor",
                payload={
                    "work_item_id": work.work_item_id,
                    "attempt_type": attempt_type,
                    "error": result.error,
                },
            )
            return None, "awaiting"
        if not result.succeeded:
            error = result.error or f"executor {result.status}"
            self.events.append(self.ctx.job_id, "executor_call_failed", {
                "work_item_id": work.work_item_id,
                "attempt_type": attempt_type,
                "error": error,
            })
            return None, error
        return result, None

    def _record(
        self,
        work: C.WorkItemInput,
        attempt_type: str,
        result: C.ExecutionResult,
        started: float,
    ) -> None:
        from spec_eval.service.pipeline.semantic_stage import (
            _record_executor_statistics,
        )

        if self.statistics is not None:
            _record_executor_statistics(self.statistics, self.ctx.job_id, result)
        if self.invocations is None:
            return
        usage = dict(result.token_usage or {})
        usage["usage_reported"] = bool(result.usage_reported)
        telemetry = dict(result.telemetry or {})
        telemetry["telemetry_reported"] = bool(result.telemetry_reported)
        try:
            self.invocations.record_call(
                job_id=self.ctx.job_id,
                run_id=self.ctx.run_id,
                work_item_id=work.work_item_id,
                attempt_type=attempt_type,
                executor=self.executor.describe().get("type", "unknown"),
                status=result.status,
                duration_ms=max(0, int(round((time.monotonic() - started) * 1000))),
                usage=usage,
                telemetry=telemetry,
            )
        except Exception:  # noqa: BLE001 - telemetry must never fail a job
            pass

    # --- terminal helpers -----------------------------------------------------

    def _fail(self, event_type: str, payload: dict[str, Any], error: str) -> JudgmentOutcome:
        self.jobs.transition_status(
            self.ctx.job_id, S.FAILED, event_type=event_type, payload=payload
        )
        return JudgmentOutcome(C.STATUS_FAILED, error)

    # --- the flow --------------------------------------------------------------

    def run(
        self,
        *,
        work: C.WorkItemInput,
        output_path: Path,
        template: dict[str, Any],
        normalize: Callable[..., NormalizationResult],
        validate: Callable[..., list[TypedError]],
        base_contract: dict[str, Any],
        on_publish: Callable[[dict[str, Any]], None],
        fingerprint: str,
        stage_event: str,
    ) -> JudgmentOutcome:
        """Run one work item through the state machine.

        ``normalize(payload)`` expands a judgment payload into the published
        document; ``validate(document)`` returns typed errors; ``on_publish``
        persists the published document; ``base_contract`` seeds the correct
        turn's prompt.
        """
        candidate_path = output_path.with_name(f".{output_path.name}.candidate")
        errors_path = output_path.with_name(f".{output_path.name}.typed-errors.json")
        prior_state = SS.work_item_state(self.ctx.run_dir, work.work_item_id)
        resume_candidate = (
            prior_state in (SS.GENERATED_INVALID, SS.CORRECTION_PENDING)
            and candidate_path.is_file()
            and errors_path.is_file()
        )

        def typed_of(document: dict[str, Any]) -> list[TypedError]:
            return validate(document)

        def publish(document: dict[str, Any], catalog: list[dict[str, Any]]) -> None:
            _write_json(output_path, document)
            SS.set_work_item_state(self.ctx.run_dir, work.work_item_id, SS.VALIDATED)
            on_publish(document)
            candidate_path.unlink(missing_ok=True)
            errors_path.unlink(missing_ok=True)
            self.events.append(self.ctx.job_id, stage_event, {
                "work_item_id": work.work_item_id,
                "evidence_catalog_size": len(catalog),
            })

        if not resume_candidate:
            SS.set_work_item_state(
                self.ctx.run_dir, work.work_item_id, SS.GENERATE_PENDING
            )
            result, failure = self._execute(work, "observe")
            if failure == "cancelled":
                return JudgmentOutcome(C.STATUS_CANCELLED, "cancelled during observe")
            if failure == "awaiting":
                return JudgmentOutcome(C.STATUS_AWAITING, result.error if result else None)
            if failure is not None:
                return self._fail(
                    "semantic_failed",
                    {"work_item_id": work.work_item_id, "attempt_type": "observe",
                     "error": failure},
                    failure,
                )
            normalization = normalize(result.observation)
            if normalization.fatal:
                return self._fail(
                    "semantic_failed",
                    {"work_item_id": work.work_item_id,
                     "errors": [error.to_dict() for error in normalization.fatal]},
                    "fatal input: " + "; ".join(
                        f"{error.code}({error.actual})" for error in normalization.fatal
                    ),
                )
            if normalization.errors:
                _write_json(candidate_path, result.observation)
                _write_json(errors_path, {
                    "input_fingerprint": fingerprint,
                    "errors": [
                        error.to_dict() for error in normalization.errors
                    ],
                    "evidence_catalog": normalization.evidence_catalog,
                })
                SS.set_work_item_state(
                    self.ctx.run_dir, work.work_item_id, SS.GENERATED_INVALID
                )
                self.events.append(self.ctx.job_id, "candidate_invalid", {
                    "work_item_id": work.work_item_id,
                    "errors": [
                        error.to_dict() for error in normalization.errors
                    ],
                })
            else:
                typed = typed_of(normalization.document)
                if not blocking(typed):
                    publish(normalization.document, normalization.evidence_catalog)
                    return JudgmentOutcome(C.STATUS_COMPLETED, published=True)
                _write_json(candidate_path, normalization.document)
                _write_json(errors_path, {
                    "input_fingerprint": fingerprint,
                    "errors": [error.to_dict() for error in typed],
                    "evidence_catalog": normalization.evidence_catalog,
                })
                SS.set_work_item_state(
                    self.ctx.run_dir, work.work_item_id, SS.GENERATED_INVALID
                )
                self.events.append(self.ctx.job_id, "candidate_invalid", {
                    "work_item_id": work.work_item_id,
                    "errors": [error.to_dict() for error in typed],
                })
        else:
            breakpoint_data = json.loads(errors_path.read_text(encoding="utf-8"))
            if breakpoint_data.get("input_fingerprint") != fingerprint:
                # inputs changed since the candidate was stored: start over
                candidate_path.unlink(missing_ok=True)
                errors_path.unlink(missing_ok=True)
                return self.run(
                    work=work, output_path=output_path, template=template,
                    normalize=normalize, validate=validate,
                    base_contract=base_contract, on_publish=on_publish,
                    fingerprint=fingerprint, stage_event=stage_event,
                )
            prior_state = SS.GENERATED_INVALID  # stored candidate is reusable
            self.events.append(self.ctx.job_id, "candidate_resumed", {
                "work_item_id": work.work_item_id,
            })

        # -- the single correction turn -------------------------------------
        if prior_state == SS.CORRECTION_PENDING:
            # a completed correction already ran and its stored result was
            # invalid: terminal (design R3), no second correction
            return self._fail(
                "semantic_failed",
                {"work_item_id": work.work_item_id,
                 "state": SS.CORRECTION_INVALID_TERMINAL},
                "correction output still invalid; terminal",
            )
        breakpoint_data = json.loads(errors_path.read_text(encoding="utf-8"))
        typed_dicts = breakpoint_data.get("errors", [])
        SS.set_work_item_state(
            self.ctx.run_dir, work.work_item_id, SS.CORRECTION_PENDING
        )
        correct_work = self._correct_work_input(
            work, candidate_path, typed_dicts, breakpoint_data
        )
        result, failure = self._execute(correct_work, "correct")
        if failure == "cancelled":
            return JudgmentOutcome(C.STATUS_CANCELLED, "cancelled during correction")
        if failure == "awaiting":
            return JudgmentOutcome(C.STATUS_AWAITING, result.error if result else None)
        if failure is not None:
            return self._fail(
                "semantic_failed",
                {"work_item_id": work.work_item_id, "attempt_type": "correct",
                 "error": failure},
                failure,
            )
        normalization = normalize(result.observation)
        if normalization.fatal:
            return self._fail(
                "semantic_failed",
                {"work_item_id": work.work_item_id,
                 "errors": [error.to_dict() for error in normalization.fatal]},
                "fatal input: " + "; ".join(
                    f"{error.code}({error.actual})" for error in normalization.fatal
                ),
            )
        if normalization.errors:
            _write_json(candidate_path, result.observation)
            _write_json(errors_path, {
                "input_fingerprint": fingerprint,
                "errors": [error.to_dict() for error in normalization.errors],
                "evidence_catalog": normalization.evidence_catalog,
            })
            SS.set_work_item_state(
                self.ctx.run_dir, work.work_item_id,
                SS.CORRECTION_INVALID_TERMINAL,
            )
            return self._fail(
                "semantic_failed",
                {
                    "work_item_id": work.work_item_id,
                    "state": SS.CORRECTION_INVALID_TERMINAL,
                    "errors": [
                        error.to_dict() for error in normalization.errors
                    ],
                },
                "correction output still invalid: "
                + "; ".join(error.code for error in normalization.errors[:5]),
            )
        typed = typed_of(normalization.document)
        if not blocking(typed):
            publish(normalization.document, normalization.evidence_catalog)
            return JudgmentOutcome(C.STATUS_COMPLETED, published=True)
        _write_json(candidate_path, normalization.document)
        _write_json(errors_path, {
            "input_fingerprint": fingerprint,
            "errors": [error.to_dict() for error in typed],
            "evidence_catalog": normalization.evidence_catalog,
        })
        SS.set_work_item_state(
            self.ctx.run_dir, work.work_item_id, SS.CORRECTION_INVALID_TERMINAL
        )
        return self._fail(
            "semantic_failed",
            {
                "work_item_id": work.work_item_id,
                "state": SS.CORRECTION_INVALID_TERMINAL,
                "errors": [error.to_dict() for error in typed],
            },
            "correction output still invalid: "
            + "; ".join(error.code for error in typed[:5]),
        )

    def _correct_work_input(
        self,
        work: C.WorkItemInput,
        candidate_path: Path,
        typed_errors: list[dict[str, Any]],
        breakpoint_data: dict[str, Any],
    ) -> C.WorkItemInput:
        from dataclasses import replace

        result_path = Path(work.executor_result_path)
        correct_result_path = result_path.with_name(
            f"{result_path.stem}.correct-1{result_path.suffix}"
        )
        base_contract = dict(work.prompt_extras)
        machine_contract = dict(base_contract.get("machine_contract", {}))
        catalog = breakpoint_data.get("evidence_catalog", [])
        if catalog and isinstance(machine_contract, dict):
            machine_contract = dict(machine_contract)
            machine_contract["evidence_catalog"] = catalog
            base_contract["machine_contract"] = machine_contract
        input_paths = list(dict.fromkeys((
            str(candidate_path),
            *work.input_paths,
        )))
        return replace(
            work,
            input_paths=tuple(input_paths),
            executor_result_path=str(correct_result_path),
            prompt_extras=correct_prompt_contract(
                base_contract, candidate_path=candidate_path, typed_errors=typed_errors
            ),
        )
