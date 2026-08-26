"""Unified judgment flow for evaluator protocol 0.2.0.

Implements the work item state machine (design v3 R3) shared by the
observation and aggregation stages:

    GENERATE_PENDING
      -> GENERATED_INVALID   (observe completed, typed validation failed)
      -> VALIDATED           (observe first pass)
    GENERATED_INVALID
      -> VALIDATED           (deterministic structural correction)
      -> CORRECTION_PENDING  (the single semantic/evidence patch turn)
    CORRECTION_PENDING
      -> VALIDATED                     (correction output validates)
      -> CORRECTION_INVALID_TERMINAL   (correction completed but still invalid:
                                        terminal, requires a new generation)
      -> CORRECTION_PENDING            (process interrupted before a complete
                                        result: the retry resumes the same
                                        attempt from the stored candidate)

Every executor call is recorded as one invocation (attempt) with executor,
timing and usage.  After the single Correction turn, callers may provide one
deterministic post-correction normalizer for representational ownership
recovery; semantic conclusions and evidence remain model-owned.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from spec_eval.kernel import staged_state as SS
from spec_eval.kernel.errors import (
    TypedError,
    has_hard_errors,
    is_non_blocking_warning,
    is_post_correction_warning,
)
from spec_eval.kernel.normalize import NormalizationResult
from spec_eval.service.domain import states as S
from spec_eval.service.executors import contract as C
from spec_eval.service.executors.base import SemanticExecutor
from spec_eval.service.pipeline.context import RunContext
from spec_eval.service.pipeline.result_payload import (
    correct_prompt_contract,
)
from spec_eval.service.pipeline.correction import (
    apply_deterministic_correction,
    apply_json_patch,
    is_deterministic_error,
    is_fatal_error,
    is_model_correction_error,
    resolve_typed_error_json_paths,
    validate_patch_scope,
    validate_patch_values,
)
from spec_eval.service.pipeline.aggregation_correction import (
    build_aggregation_correction_context,
    correction_evidence_catalog,
)
from spec_eval.service.store.repositories import (
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)


# A correction candidate can be either the executor's raw judgment payload
# (when normalization failed before a published document could be built) or
# the already-normalized published document (when typed validation failed).
# Keep this distinction explicit so JSON Patch correction can resume the
# correct half of the pipeline.
CANDIDATE_RAW_PAYLOAD = "raw_payload"
CANDIDATE_PUBLISHED_DOCUMENT = "published_candidate"


def _candidate_kind(document: dict[str, Any], metadata: dict[str, Any]) -> str:
    """Return the stored candidate representation, with legacy inference."""
    kind = metadata.get("candidate_kind")
    if kind in {CANDIDATE_RAW_PAYLOAD, CANDIDATE_PUBLISHED_DOCUMENT}:
        return kind
    # Runs created before candidate_kind was persisted may still be retried.
    # Raw judgment payloads declare evidence by local key; published
    # documents contain canonical observations instead.
    if isinstance(document.get("evidence_declarations"), list):
        return CANDIDATE_RAW_PAYLOAD
    return CANDIDATE_PUBLISHED_DOCUMENT

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


def _published_evidence_catalog(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the already verified evidence catalog for a published candidate."""
    catalog: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for collection in ("observations", "criterion_results"):
        rows.extend(
            row for row in document.get(collection, [])
            if isinstance(row, dict)
        )
    for row in rows:
        for evidence in row.get("evidence", []):
            if not isinstance(evidence, dict):
                continue
            evidence_id = evidence.get("evidence_id")
            if not isinstance(evidence_id, str) or evidence_id in catalog:
                continue
            catalog[evidence_id] = {
                "evidence_id": evidence_id,
                "type": evidence.get("type"),
                "path": evidence.get("path"),
                "description": evidence.get("description", ""),
            }
    return list(catalog.values())


def _guard_correction_regression(
    corrected: dict[str, Any],
    candidate_path: Path,
    typed_error_dicts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Roll back criterion changes that the correction was not asked to fix.

    When the executor re-generates the full aggregation document during a
    correction turn, it may unintentionally change conclusions for criteria
    that were not mentioned in the typed errors.  This guard restores the
    original values for any criterion not targeted by the errors.
    """
    if not candidate_path.is_file():
        return corrected
    try:
        original = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return corrected

    error_criteria: set[str] = set()
    for error_dict in typed_error_dicts:
        entity_type = error_dict.get("entity_type", "")
        entity_id = error_dict.get("entity_id", "")
        path = error_dict.get("path", "")
        if entity_type == "criterion" and entity_id:
            error_criteria.add(entity_id)
        elif "criterion_results" in path:
            for segment in path.replace("]", "").split("["):
                if segment and not segment.startswith("$") and not segment.startswith("."):
                    error_criteria.add(segment)

    if not error_criteria:
        return corrected

    original_by_id = {
        row.get("criterion_id"): row
        for row in original.get("criterion_results", [])
        if isinstance(row, dict)
    }
    corrected_results = corrected.get("criterion_results")
    if not isinstance(corrected_results, list):
        return corrected

    for i, row in enumerate(corrected_results):
        if not isinstance(row, dict):
            continue
        cid = row.get("criterion_id")
        if not isinstance(cid, str) or cid in error_criteria:
            continue
        orig = original_by_id.get(cid)
        if orig is None:
            continue
        if row.get("conclusion") != orig.get("conclusion"):
            corrected_results[i] = orig

    return corrected


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
        if result.cost_usd is not None:
            usage["cost_usd"] = result.cost_usd
        if result.num_turns is not None:
            usage["num_turns"] = result.num_turns
        if result.model_usage is not None:
            usage["model_usage"] = result.model_usage
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
        on_publish: Callable[[dict[str, Any]], bool | None],
        fingerprint: str,
        stage_event: str,
        reproject: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        normalize_after_correction: Callable[..., NormalizationResult] | None = None,
        allow_degraded_publish: bool = False,
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
            return [
                error for error in validate(document)
                if not is_non_blocking_warning(error)
            ]

        def projected(document: dict[str, Any]) -> dict[str, Any]:
            return reproject(document) if reproject is not None else document

        def publish(document: dict[str, Any], catalog: list[dict[str, Any]]) -> bool:
            document = projected(document)
            _write_json(output_path, document)
            publish_succeeded = on_publish(document)
            if publish_succeeded is False:
                return False
            SS.set_work_item_state(self.ctx.run_dir, work.work_item_id, SS.VALIDATED)
            candidate_path.unlink(missing_ok=True)
            errors_path.unlink(missing_ok=True)
            self.events.append(self.ctx.job_id, stage_event, {
                "work_item_id": work.work_item_id,
                "evidence_catalog_size": len(catalog),
            })
            return True

        def degraded_publish(
            document: dict[str, Any],
            catalog: list[dict[str, Any]],
            residual: list[TypedError],
        ) -> bool:
            """Publish a usable report after the single correction turn.

            Only the final report (``allow_degraded_publish``) may take this
            path.  When every residual error is non-HARD/non-fatal, the report
            is structurally assemblable, so publish it and let ``on_publish``
            apply its HARD-only gate and confidence deduction.  A HARD or fatal
            residual still blocks; observation work items never degrade.
            """
            if not allow_degraded_publish:
                return False
            if has_hard_errors(residual) or any(
                is_fatal_error(error) for error in residual
            ):
                return False
            published = publish(document, catalog)
            if published:
                self.events.append(
                    self.ctx.job_id, "correction_completed_degraded", {
                        "work_item_id": work.work_item_id,
                        "residual_errors": [
                            error.to_dict() for error in residual
                        ],
                    },
                )
            return published

        def repair_after_model_correction(
            document: dict[str, Any], typed: list[TypedError]
        ) -> tuple[dict[str, Any], list[TypedError]]:
            """Apply one final service-owned repair before publishing/failing.

            A legacy full-payload Correction can reintroduce a structural or
            ownership error outside the semantic paths it was asked to fix.
            Do not spend another model turn on such errors; apply only the
            deterministic repairs already owned by the service and revalidate.
            """
            downgraded: list[TypedError] = []
            downgraded_identities: set[tuple[str, str, str, str]] = set()

            def downgrade_warnings(errors: list[TypedError]) -> list[TypedError]:
                for error in errors:
                    # Once the single model Correction turn has completed,
                    # any remaining MODEL_CORRECTION issue is a report-quality
                    # warning.  Keep its original code so aggregation can
                    # apply the registered confidence deduction.  Fatal and
                    # service-owned structural errors remain blocking.
                    if not (
                        is_post_correction_warning(error)
                        or is_model_correction_error(error)
                    ):
                        continue
                    identity = (
                        error.code, error.path,
                        error.entity_type, error.entity_id,
                    )
                    if identity not in downgraded_identities:
                        downgraded_identities.add(identity)
                        downgraded.append(error)
                return [
                    error for error in errors
                    if not (
                        is_post_correction_warning(error)
                        or is_model_correction_error(error)
                    )
                ]

            def record_downgraded() -> None:
                if not downgraded:
                    return
                self.events.append(
                    self.ctx.job_id, "correction_completed_with_warnings", {
                        "work_item_id": work.work_item_id,
                        "warnings": [error.to_dict() for error in downgraded],
                    },
                )

            typed = downgrade_warnings(typed)
            deterministic = [
                error for error in typed
                if is_deterministic_error(error)
            ]
            if not deterministic:
                record_downgraded()
                return document, typed
            corrected, changes, _unresolved = apply_deterministic_correction(
                document, deterministic,
            )
            if not changes:
                record_downgraded()
                return document, typed
            corrected = projected(corrected)
            # Revalidation may surface the same residual mapping warning again
            # after a deterministic repair.  Preserve the post-Correction
            # downgrade policy on this final path as well.
            remaining = downgrade_warnings(typed_of(corrected))
            record_downgraded()
            self.events.append(
                self.ctx.job_id, "correction_deterministic_repaired", {
                    "work_item_id": work.work_item_id,
                    "changes": changes,
                    "remaining_errors": [
                        error.to_dict() for error in remaining
                    ],
                },
            )
            return corrected, remaining

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
                combined_errors = list(normalization.errors)
                if normalization.document is not None:
                    combined_errors.extend(typed_of(normalization.document))
                deduplicated_errors: list[TypedError] = []
                seen_errors: set[tuple[str, str, str, str]] = set()
                for error in combined_errors:
                    identity = (
                        error.code, error.path,
                        error.entity_type, error.entity_id,
                    )
                    if identity in seen_errors:
                        continue
                    seen_errors.add(identity)
                    deduplicated_errors.append(error)
                _write_json(candidate_path, result.observation)
                _write_json(errors_path, {
                    "input_fingerprint": fingerprint,
                    "candidate_kind": CANDIDATE_RAW_PAYLOAD,
                    "errors": [
                        error.to_dict() for error in deduplicated_errors
                    ],
                    "evidence_catalog": normalization.evidence_catalog,
                })
                SS.set_work_item_state(
                    self.ctx.run_dir, work.work_item_id, SS.GENERATED_INVALID
                )
                self.events.append(self.ctx.job_id, "candidate_invalid", {
                    "work_item_id": work.work_item_id,
                    "errors": [
                        error.to_dict() for error in deduplicated_errors
                    ],
                })
            else:
                typed = typed_of(normalization.document)
                if not typed:
                    published = publish(
                        normalization.document, normalization.evidence_catalog,
                    )
                    return JudgmentOutcome(C.STATUS_COMPLETED, published=published)
                _write_json(candidate_path, normalization.document)
                _write_json(errors_path, {
                    "input_fingerprint": fingerprint,
                    "candidate_kind": CANDIDATE_PUBLISHED_DOCUMENT,
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
                    reproject=reproject,
                    normalize_after_correction=normalize_after_correction,
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

        fatal_dicts = [
            error for error in typed_dicts if is_fatal_error(error)
        ]
        if fatal_dicts:
            SS.set_work_item_state(
                self.ctx.run_dir, work.work_item_id,
                SS.CORRECTION_INVALID_TERMINAL,
            )
            return self._fail(
                "semantic_failed",
                {
                    "work_item_id": work.work_item_id,
                    "state": SS.CORRECTION_INVALID_TERMINAL,
                    "errors": fatal_dicts,
                    "repair": "fatal_input",
                },
                "fatal correction input: "
                + "; ".join(str(error.get("code")) for error in fatal_dicts[:5]),
            )

        # Safe structural/ownership errors are repaired by the service.  They
        # never consume a model correction turn.  If a repair is ambiguous,
        # fail explicitly rather than asking the model to invent a mapping.
        deterministic_dicts = [
            error for error in typed_dicts if is_deterministic_error(error)
        ]
        model_dicts = [
            error for error in typed_dicts if is_model_correction_error(error)
        ]
        if deterministic_dicts:
            try:
                candidate_document = json.loads(
                    candidate_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                return self._fail(
                    "semantic_failed",
                    {"work_item_id": work.work_item_id, "error": str(exc)},
                    f"cannot read correction candidate: {exc}",
                )
            working_candidate_kind = breakpoint_data.get(
                "candidate_kind", CANDIDATE_PUBLISHED_DOCUMENT
            )
            # Fix 1: identity-keyed service repairs (e.g. SEVERITY_BELOW_FLOOR
            # located by canonical SEM- id) target the normalized document.  A
            # raw executor candidate still carries provisional finding keys, so
            # normalize it first (with the first-pass normalizer, matching the
            # identity space the validator used) or those repairs cannot locate
            # their targets and would dead-end the whole work item.  The error
            # set is then rebuilt by re-validation below, so stale raw-keyed
            # normalization errors (e.g. duplicate provisional keys already
            # resolved into distinct canonical ids) are dropped rather than
            # carried into an inconsistent identity space.
            repair_base = candidate_document
            if working_candidate_kind == CANDIDATE_RAW_PAYLOAD:
                pre = normalize(candidate_document)
                if not pre.fatal and pre.document is not None:
                    repair_base = pre.document
                    working_candidate_kind = CANDIDATE_PUBLISHED_DOCUMENT
            corrected_document, changes, _unresolved = apply_deterministic_correction(
                repair_base, deterministic_dicts,
            )
            corrected_document = projected(corrected_document)

            # Re-validate the (possibly normalized + repaired) document to get
            # the true residual set instead of trusting the stale pre-repair
            # error list.  Normalization errors keyed to raw provisional
            # identities (dropped by re-normalization) are not carried forward;
            # fatal input was already handled by ``fatal_dicts`` above, so any
            # residual here is a service or model validation error.
            remaining = typed_of(corrected_document)
            if not remaining:
                published = publish(
                    corrected_document,
                    _published_evidence_catalog(corrected_document),
                )
                if published and changes:
                    self.events.append(
                        self.ctx.job_id, "candidate_deterministic_repaired", {
                            "work_item_id": work.work_item_id,
                            "changes": changes,
                        },
                    )
                return JudgmentOutcome(C.STATUS_COMPLETED, published=published)

            remaining_fatal = [
                error for error in remaining if is_fatal_error(error)
            ]
            if remaining_fatal:
                self.events.append(self.ctx.job_id, "correction_skipped", {
                    "work_item_id": work.work_item_id,
                    "reason": "service_deterministic_error",
                    "errors": [error.to_dict() for error in remaining_fatal],
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
                        "errors": [error.to_dict() for error in remaining_fatal],
                        "repair": "deterministic_only",
                    },
                    "deterministic correction still invalid: "
                    + "; ".join(error.code for error in remaining_fatal[:5]),
                )

            # Fix 2: a service error the deterministic repair could not resolve
            # is reclassified into the single model correction turn together
            # with the naturally model-correctable residuals, instead of ending
            # the work item.  Only fold a code whose correction path resolves so
            # ``_correct_work_input`` cannot raise on an unmappable selector.
            model_remaining = [
                error for error in remaining if is_model_correction_error(error)
            ]
            foldable_service: list[TypedError] = []
            for error in remaining:
                if not is_deterministic_error(error):
                    continue
                try:
                    resolve_typed_error_json_paths(corrected_document, error)
                except (ValueError, KeyError, TypeError, IndexError):
                    continue
                foldable_service.append(error)

            turn_errors = model_remaining + foldable_service
            if not turn_errors:
                # Nothing a model turn can fix (no model-correctable errors and
                # no service error with a resolvable path).  For the final
                # report, degrade to a usable artifact when the residual is
                # non-HARD; observations still terminate.
                if degraded_publish(
                    corrected_document,
                    _published_evidence_catalog(corrected_document),
                    remaining,
                ):
                    return JudgmentOutcome(C.STATUS_COMPLETED, published=True)
                self.events.append(self.ctx.job_id, "correction_skipped", {
                    "work_item_id": work.work_item_id,
                    "reason": "service_deterministic_error",
                    "errors": [error.to_dict() for error in remaining],
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
                        "errors": [error.to_dict() for error in remaining],
                        "repair": "deterministic_only",
                    },
                    "deterministic correction still invalid: "
                    + "; ".join(error.code for error in remaining[:5]),
                )
            _write_json(candidate_path, corrected_document)
            _write_json(errors_path, {
                "input_fingerprint": fingerprint,
                "candidate_kind": working_candidate_kind,
                "errors": [error.to_dict() for error in remaining],
                "evidence_catalog": _published_evidence_catalog(corrected_document),
                "deterministic_changes": changes,
            })
            if changes:
                self.events.append(
                    self.ctx.job_id, "candidate_deterministic_repaired", {
                        "work_item_id": work.work_item_id,
                        "changes": changes,
                    },
                )
            breakpoint_data = {
                **breakpoint_data, "candidate_kind": working_candidate_kind,
            }
            typed_dicts = [error.to_dict() for error in remaining]
            model_dicts = [error.to_dict() for error in turn_errors]

        if not model_dicts:
            self.events.append(self.ctx.job_id, "correction_skipped", {
                "work_item_id": work.work_item_id,
                "reason": "no_model_correctable_error",
                "errors": typed_dicts,
            })
            return self._fail(
                "semantic_failed",
                {
                    "work_item_id": work.work_item_id,
                    "state": SS.CORRECTION_INVALID_TERMINAL,
                    "errors": typed_dicts,
                    "repair": "no_model_correction",
                },
                "no model-correctable Observation errors remain",
            )

        try:
            correct_work = self._correct_work_input(
                work, candidate_path, model_dicts,
                {**breakpoint_data, "errors": model_dicts},
            )
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            SS.set_work_item_state(
                self.ctx.run_dir, work.work_item_id,
                SS.CORRECTION_INVALID_TERMINAL,
            )
            return self._fail(
                "semantic_failed",
                {
                    "work_item_id": work.work_item_id,
                    "state": SS.CORRECTION_INVALID_TERMINAL,
                    "error": f"correction path resolution failed: {exc}",
                },
                f"correction path resolution failed: {exc}",
            )
        SS.set_work_item_state(
            self.ctx.run_dir, work.work_item_id, SS.CORRECTION_PENDING
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
        # New Correction turns return JSON Patch against the candidate.  The
        # candidate kind determines whether patch application resumes from a
        # raw judgment payload or an already-normalized published document.
        # Keep the full-payload fallback for old executors and fixtures while
        # the protocol rolls forward.
        correction_payload = result.observation or {}
        corrected_candidate_for_failure = correction_payload
        if isinstance(correction_payload, dict) and "patches" in correction_payload:
            try:
                candidate_document = json.loads(
                    candidate_path.read_text(encoding="utf-8")
                )
                patches = correction_payload.get("patches")
                if not isinstance(patches, list):
                    raise ValueError("correction patches must be an array")
                correction_contract = correct_work.prompt_extras.get(
                    "correction_contract", {}
                )
                violations = validate_patch_scope(
                    patches,
                    allowed_paths=correction_contract.get("allowed_paths", []),
                    immutable_paths=correction_contract.get("immutable_paths", []),
                )
                violations.extend(validate_patch_values(
                    patches,
                    allowed_values_by_path=correction_contract.get(
                        "allowed_values_by_path", {}
                    ),
                ))
                if violations:
                    raise ValueError("; ".join(violations))
                corrected_payload = apply_json_patch(candidate_document, patches)
                corrected_candidate_for_failure = corrected_payload
            except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
                return self._fail(
                    "semantic_failed",
                    {
                        "work_item_id": work.work_item_id,
                        "state": SS.CORRECTION_INVALID_TERMINAL,
                        "error": f"invalid JSON Patch: {exc}",
                    },
                    f"invalid JSON Patch: {exc}",
                )
            candidate_kind = _candidate_kind(corrected_payload, breakpoint_data)
            if candidate_kind == CANDIDATE_RAW_PAYLOAD:
                # An initial normalization error leaves the raw executor
                # payload in .candidate.  Re-enter normalization after the
                # patch so the template identity, canonical evidence, claim
                # ordering and derived fields are rebuilt before validation.
                correction_normalizer = normalize_after_correction or normalize
                normalization = correction_normalizer(corrected_payload)
                if not normalization.fatal and not normalization.errors:
                    corrected_payload = projected(normalization.document)
                    corrected_candidate_for_failure = corrected_payload
                    typed = typed_of(corrected_payload)
                    if typed:
                        corrected_payload, typed = repair_after_model_correction(
                            corrected_payload, typed,
                        )
                        corrected_candidate_for_failure = corrected_payload
                    if not typed:
                        published = publish(
                            corrected_payload,
                            normalization.evidence_catalog,
                        )
                        return JudgmentOutcome(
                            C.STATUS_COMPLETED, published=published,
                        )
                    normalization = NormalizationResult(
                        document=corrected_payload,
                        errors=typed,
                        evidence_catalog=normalization.evidence_catalog,
                    )
            else:
                # Validation-only failures already have a published candidate;
                # preserve the existing patch -> project -> validate path.
                corrected_payload = projected(corrected_payload)
                corrected_candidate_for_failure = corrected_payload
                typed = typed_of(corrected_payload)
                if typed:
                    corrected_payload, typed = repair_after_model_correction(
                        corrected_payload, typed,
                    )
                    corrected_candidate_for_failure = corrected_payload
                if not typed:
                    published = publish(
                        corrected_payload,
                        _published_evidence_catalog(corrected_payload),
                    )
                    return JudgmentOutcome(C.STATUS_COMPLETED, published=published)
                normalization = NormalizationResult(
                    document=None,
                    errors=typed,
                    evidence_catalog=_published_evidence_catalog(corrected_payload),
                )
        else:
            corrected_payload = _guard_correction_regression(
                result.observation, candidate_path, model_dicts,
            )
            correction_normalizer = normalize_after_correction or normalize
            normalization = correction_normalizer(corrected_payload)
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
            # A correction against a raw payload can fail during
            # normalization before a validator-visible document is produced.
            # If the normalizer did produce a structurally usable document and
            # every remaining error is model-correctable, apply the same
            # post-Correction warning policy instead of entering the terminal
            # state.  Without a document, publishing would be unsafe.
            if (
                normalization.document is not None
                and normalization.errors
                and all(is_model_correction_error(error)
                        for error in normalization.errors)
            ):
                normalized_document, normalized_typed = (
                    repair_after_model_correction(
                        normalization.document,
                        list(normalization.errors)
                        + typed_of(normalization.document),
                    )
                )
                if not normalized_typed:
                    publish(
                        normalized_document,
                        normalization.evidence_catalog,
                    )
                    return JudgmentOutcome(C.STATUS_COMPLETED, published=True)
            # The single correction turn has run.  For the final report, a
            # structurally usable document whose residual errors are all
            # non-HARD degrades to a usable artifact instead of terminating.
            if normalization.document is not None and degraded_publish(
                projected(normalization.document),
                normalization.evidence_catalog,
                list(normalization.errors),
            ):
                return JudgmentOutcome(C.STATUS_COMPLETED, published=True)
            _write_json(candidate_path, corrected_candidate_for_failure)
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
        corrected_document, typed = repair_after_model_correction(
            normalization.document, typed_of(normalization.document),
        )
        if not typed:
            published = publish(
                corrected_document, normalization.evidence_catalog,
            )
            return JudgmentOutcome(C.STATUS_COMPLETED, published=published)
        # Post-correction residual on a structurally usable document: degrade
        # the final report when nothing residual is HARD/fatal.
        if degraded_publish(
            corrected_document, normalization.evidence_catalog, typed,
        ):
            return JudgmentOutcome(C.STATUS_COMPLETED, published=True)
        _write_json(candidate_path, corrected_document)
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
        from spec_eval.kernel.machine_contract import (
            build_aggregation_correction_machine_contract,
            build_correction_machine_contract,
        )

        result_path = Path(work.executor_result_path)
        correct_result_path = result_path.with_name(
            f"{result_path.stem}.correct-1{result_path.suffix}"
        )
        base_contract = dict(work.prompt_extras)
        payload_kind = str(base_contract.get("payload_kind", "observation"))
        observation_profile = str(
            work.work_item.get("observation_profile")
            or (
                "aggregation" if work.work_item.get("observation_type") == "aggregation"
                else "function_global" if work.work_item.get("type") == "function_global"
                else "feature"
            )
        )
        catalog = breakpoint_data.get("evidence_catalog", [])
        error_codes = {str(error.get("code")) for error in typed_errors}
        needs_evidence = any(
            code.startswith("EVIDENCE_")
            or code.startswith("NV_")
            or code.startswith("GAP_")
            for code in error_codes
        )
        candidate_document = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate_kind = _candidate_kind(candidate_document, breakpoint_data)
        paths_by_error = [
            resolve_typed_error_json_paths(candidate_document, error)
            for error in typed_errors
        ]
        allowed_paths = [
            path for paths in paths_by_error for path in paths
        ]
        valid_criterion_ids = tuple(
            base_contract.get("machine_contract", {}).get(
                "valid_criterion_ids", ()
            )
        )
        allowed_values_by_path = {}
        if valid_criterion_ids:
            for error, paths in zip(typed_errors, paths_by_error):
                if error.get("code") == "CRITERION_UNKNOWN":
                    for path in paths:
                        allowed_values_by_path[path] = list(valid_criterion_ids)
        correction_contract = {
            "format": "json_patch",
            "base": candidate_kind,
            "allowed_paths": list(dict.fromkeys(allowed_paths)),
            "allowed_values_by_path": allowed_values_by_path,
            "immutable_paths": [
                "/func_id", "/source_revision", "/run_id", "/observation_id",
                "/expected_claim_ids", "/required_checks", "/reviewed_claim_ids",
                "/completed_checks", "/status",
            ],
        }
        aggregation_correction_context: dict[str, Any] | None = None
        aggregation_correction_context_path: Path | None = None
        if observation_profile == "aggregation":
            source_context_path = next((
                Path(path) for path in work.input_paths
                if Path(path).name == "aggregation-context.json"
                and Path(path).is_file()
            ), None)
            if source_context_path is not None:
                source_context = json.loads(
                    source_context_path.read_text(encoding="utf-8")
                )
                aggregation_correction_context = (
                    build_aggregation_correction_context(
                        source_context, candidate_document, typed_errors,
                    )
                )
                aggregation_correction_context_path = (
                    self.ctx.run_dir / "aggregation-correction-context.json"
                )
                _write_json(
                    aggregation_correction_context_path,
                    aggregation_correction_context,
                )
            machine_contract = build_aggregation_correction_machine_contract(
                typed_errors=typed_errors,
                allowed_paths=allowed_paths,
                evidence_catalog=(
                    correction_evidence_catalog(aggregation_correction_context)
                    if aggregation_correction_context is not None else ()
                ),
                valid_criterion_ids=valid_criterion_ids,
                correction_context_path=(
                    str(aggregation_correction_context_path)
                    if aggregation_correction_context_path is not None else None
                ),
                target_criterion_ids=(
                    aggregation_correction_context.get("target_criterion_ids", [])
                    if aggregation_correction_context is not None else ()
                ),
            )
        else:
            machine_contract = build_correction_machine_contract(
                payload_kind=payload_kind,
                typed_errors=typed_errors,
                observation_profile=observation_profile,
                allowed_paths=allowed_paths,
                evidence_catalog=catalog if needs_evidence else (),
                valid_criterion_ids=valid_criterion_ids,
            )

        # Correction never needs the embedded workflow references.  Keep only
        # the candidate and declared frozen inputs relevant to semantic or
        # evidence errors; SKILL.md and the two Observation markdown files are
        # explicitly excluded from the correction input set.
        excluded_names = {
            "SKILL.md", "observation-contract.md", "observation-guide.md",
            "aggregation-contract.md", "aggregation-guide.md",
            "aggregation-workflow.md", "criterion-guide.md",
            "staged-run-contract.md", "output-contract.json", "work-items.json",
            "run-state.json",
        }

        def correction_input_allowed(path: str) -> bool:
            candidate = Path(path)
            # Never expose evaluator workflow/reference material in a
            # Correction turn.  Feature/spec Markdown outside the skill tree
            # remains available because semantic correction may need it.
            if candidate.name in excluded_names:
                return False
            if "ohos-design-arkui-spec-evaluator" in candidate.parts:
                return False
            return True

        if observation_profile == "aggregation":
            input_paths = [str(candidate_path)]
            if aggregation_correction_context_path is not None:
                input_paths.append(str(aggregation_correction_context_path))
        else:
            input_paths = [
                str(candidate_path),
                *[
                    path for path in work.input_paths
                    if correction_input_allowed(path)
                ],
            ]
        input_paths = list(dict.fromkeys(input_paths))
        work_item = dict(work.work_item)
        if observation_profile == "aggregation":
            resources = []
            if aggregation_correction_context_path is not None:
                resources.append({
                    "path": str(aggregation_correction_context_path),
                    "role": "aggregation_correction_context",
                    "citable": False,
                })
        else:
            resources = [
                dict(resource)
                for resource in work_item.get("input_resources", [])
                if isinstance(resource, dict)
                and correction_input_allowed(str(resource.get("path", "")))
            ]
        work_item["input_resources"] = resources
        prompt_contract = correct_prompt_contract(
            base_contract,
            candidate_path=candidate_path,
            typed_errors=typed_errors,
            schema_dir=self.ctx.run_dir,
            correction_contract=correction_contract,
            machine_contract=machine_contract,
            observation_profile=observation_profile,
        )
        if aggregation_correction_context_path is not None:
            prompt_contract["correction_context_path"] = str(
                aggregation_correction_context_path
            )
        return replace(
            work,
            work_item=work_item,
            input_paths=tuple(input_paths),
            executor_result_path=str(correct_result_path),
            prompt_extras=prompt_contract,
        )
