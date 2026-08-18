"""Codex CLI semantic executor adapter (TASK-011-04, the only Phase-2 backend).

Drives ``codex exec`` as an ephemeral, read-only subprocess: the prompt (one
staged work item) goes via stdin, structured output goes to
``--output-last-message``, and progress JSONL is streamed from stdout, redacted,
and forwarded to the pipeline. The adapter never treats stdout events as
completion evidence: only a zero exit, a present result file and a passing
schema check yield ``completed``.
"""

from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.protocol_validator import (
    JsonSchemaSubsetValidator,
    validate_strict_output_schema,
)

from . import contract as C
from .process import ProcessResult, run_subprocess
from .redaction import redact_jsonl
from .telemetry import ExecutionTelemetryAccumulator
from .usage import TokenUsageAccumulator

DEFAULT_TIMEOUT = 3600.0


class CodexCliExecutor:
    """SemanticExecutor backed by the local ``codex`` CLI."""

    def __init__(
        self,
        config: dict[str, Any],
        *,
        schemas_root: Path,
        runner: Callable[..., ProcessResult] = run_subprocess,
    ) -> None:
        self._command = str(config.get("command", "codex"))
        self._sandbox = str(config.get("sandbox", "read-only"))
        self._model = config.get("model")  # None => use local codex config
        self._timeout = float(config.get("timeout_seconds", DEFAULT_TIMEOUT))
        self._schemas_root = Path(schemas_root)
        schema_name = str(config.get("output_schema", "executor-result.schema.json"))
        self._output_schema_path = self._schemas_root / schema_name
        self._validate_output_schema()
        self._validate_generated_output_schemas()
        self._runner = runner
        self._available: bool | None = None

    # --- SemanticExecutor protocol ----------------------------------------
    def is_available(self) -> bool:
        if self._available is None:
            try:
                proc = subprocess.run(  # noqa: S603,S607 - probing a configured CLI
                    [self._command, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self._available = proc.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                self._available = False
        return self._available

    def describe(self) -> dict[str, Any]:
        return {
            "type": "codex-cli",
            "command": self._command,
            "model": self._model,
            "sandbox": self._sandbox,
            "timeout_seconds": self._timeout,
            "executor_version": C.EXECUTOR_VERSION,
            "protocol_version": C.PROTOCOL_VERSION,
            "output_schema": self._output_schema_path.name,
        }

    def execute(
        self,
        work: C.WorkItemInput,
        emit: C.EventSink,
        cancel: threading.Event | None = None,
    ) -> C.ExecutionResult:
        schema_error = self._work_schema_error(work)
        if schema_error is not None:
            return C.ExecutionResult(status=C.STATUS_FAILED, error=schema_error)
        if not self.is_available():
            return C.ExecutionResult(
                status=C.STATUS_AWAITING,
                error="codex CLI not available",
            )

        argv = self._build_argv(work)
        prompt = self._build_prompt(work)
        result_parent = Path(work.executor_result_path).parent
        result_parent.mkdir(parents=True, exist_ok=True)
        stdout_log = str(result_parent / "codex.stdout.log")
        stderr_log = str(result_parent / "codex.stderr.log")

        event_count = 0
        usage = TokenUsageAccumulator()
        telemetry = ExecutionTelemetryAccumulator(work)

        def line_sink(line: str) -> None:
            nonlocal event_count
            event_count += 1
            usage.observe(line)
            telemetry.observe(line)
            emit(C.ExecutionEvent(kind="jsonl", message=redact_jsonl(line)))

        emit(C.ExecutionEvent(kind="command", message=" ".join(_redacted_argv(argv))))
        started = time.monotonic()
        proc_result = self._runner(
            argv,
            cwd=work.repo_root,
            stdin=prompt,
            timeout=self._timeout,
            stdout_log_path=stdout_log,
            stderr_log_path=stderr_log,
            cancel=cancel,
            line_sink=line_sink,
        )

        if proc_result.cancelled:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_CANCELLED,
                exit_code=proc_result.exit_code,
                error="executor cancelled",
                elapsed_seconds=proc_result.elapsed_seconds,
                event_count=event_count,
            )
        if proc_result.timed_out:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_TIMEOUT,
                exit_code=proc_result.exit_code,
                error=f"executor timed out after {self._timeout:.0f}s",
                elapsed_seconds=proc_result.elapsed_seconds,
                event_count=event_count,
            )
        if proc_result.exit_code != 0:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"codex exited with code {proc_result.exit_code}",
                elapsed_seconds=proc_result.elapsed_seconds,
                event_count=event_count,
            )

        return self._validate_result(work, proc_result, event_count, started, usage, telemetry)

    # --- internals --------------------------------------------------------
    def _validate_result(
        self,
        work: C.WorkItemInput,
        proc_result: ProcessResult,
        event_count: int,
        started: float,
        usage: TokenUsageAccumulator,
        telemetry: ExecutionTelemetryAccumulator,
    ) -> C.ExecutionResult:
        result_path = Path(work.executor_result_path)
        if not result_path.is_file():
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"codex produced no result file at {work.executor_result_path}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        try:
            document = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"result file is not valid JSON: {exc}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        validator = JsonSchemaSubsetValidator(self._schemas_root)
        errors = validator.validate_file(document, self._schema_path_for(work))
        if errors:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="result failed schema validation: " + "; ".join(errors),
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        if str(document.get("work_item_id")) != work.work_item_id:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="result work_item_id does not match the requested work item",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        status = document.get("status")
        if status == "failed":
            error = document.get("error")
            if not isinstance(error, str) or not error.strip():
                error = "executor reported failure without an error message"
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                executor_result_path=work.executor_result_path,
                error=error,
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        if document.get("error") is not None:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                executor_result_path=work.executor_result_path,
                error="completed executor result must set error to null",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        # Protocol 0.2.0 has one transport shape: envelope v3 with a real
        # nested payload. Historical observation_json (v2) is deliberately
        # rejected instead of being silently upgraded (D1).
        observation = document.get("payload")
        if not isinstance(observation, dict):
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                executor_result_path=work.executor_result_path,
                error="completed executor result must contain a payload object",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        return _execution_result(
            usage, telemetry,
            status=C.STATUS_COMPLETED,
            exit_code=proc_result.exit_code,
            executor_result_path=work.executor_result_path,
            observation=observation,
            elapsed_seconds=time.monotonic() - started,
            event_count=event_count,
        )

    def _validate_output_schema(self) -> None:
        try:
            schema = json.loads(self._output_schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"cannot load executor output schema {self._output_schema_path}: {exc}"
            ) from exc
        if not isinstance(schema, dict):
            raise ValueError(f"executor output schema is not an object: {self._output_schema_path}")
        errors = validate_strict_output_schema(schema)
        if errors:
            raise ValueError(
                f"executor output schema is not strict: {self._output_schema_path}: "
                + "; ".join(errors)
            )

    def _validate_generated_output_schemas(self) -> None:
        """Reject observation- or aggregation-only incompatibility at startup."""
        for payload_kind in ("observation", "aggregation"):
            errors = validate_strict_output_schema(
                build_envelope_schema(payload_kind)
            )
            if errors:
                raise ValueError(
                    f"generated {payload_kind} output schema is not compatible: "
                    + "; ".join(errors)
                )

    def _work_schema_error(self, work: C.WorkItemInput) -> str | None:
        """Validate the exact run-local schema before starting Codex."""
        schema_path = self._schema_path_for(work)
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return f"cannot load work output schema {schema_path}: {exc}"
        if not isinstance(schema, dict):
            return f"work output schema is not an object: {schema_path}"
        errors = validate_strict_output_schema(schema)
        if errors:
            return (
                f"work output schema is not compatible: {schema_path}: "
                + "; ".join(errors)
            )
        return None

    def _build_argv(self, work: C.WorkItemInput) -> list[str]:
        argv = [self._command, "exec"]
        if self._model:
            argv += ["--model", str(self._model)]
        argv += [
            "--cd", str(work.repo_root),
            "--sandbox", self._sandbox,
            "--add-dir", str(work.run_dir),
            "--ephemeral",
            "--json",
            "--output-schema", str(self._schema_path_for(work)),
            "--output-last-message", str(work.executor_result_path),
            "-",  # read prompt from stdin
        ]
        return argv

    def _schema_path_for(self, work: C.WorkItemInput) -> Path:
        """Resolve the generated protocol 0.2.0 schema for this work item."""
        schema_path = work.prompt_extras.get("schema_path")
        if isinstance(schema_path, str) and schema_path:
            return Path(schema_path)
        return self._output_schema_path

    @staticmethod
    def _build_prompt(work: C.WorkItemInput) -> str:
        contract = dict(work.prompt_extras)
        mode = contract.get("mode", "observe")
        correcting = mode == "correct"
        machine_contract = contract.get("machine_contract", {})
        result_kind = contract.get("result_kind", "staged_judgments")
        payload_fields = contract.get("payload_fields", [])
        declares_evidence = "evidence_declarations" in payload_fields
        constraints = [
            "Follow the declared evaluator Skill and the staged-run contract.",
            "Read only the declared input_paths and frozen source/SDK files.",
            "Treat input_resources.citable=false files as context only; never "
            "declare them as evidence.",
            "Evidence paths must be canonical repository-relative POSIX paths. "
            "Never emit absolute paths, '..', evidence/... or runs/... service paths.",
            "Do not read paths in forbidden_paths (confirmed reviews or other runs).",
            "Do not modify any formal Spec, Design, Registry, source or test file.",
            "Do not modify the initialized staged template; the service owns and publishes it.",
            "Provide judgments only; treat result_contract.machine_contract as normative.",
            "Write only the structured final result.",
        ]
        if correcting:
            evidence_correction = (
                "Re-declare every piece of evidence you keep or add in "
                "evidence_declarations; the service re-verifies hashes and "
                "re-assigns canonical IDs."
                if declares_evidence else
                "Do not declare evidence or use local evidence keys. Use only "
                "canonical evidence IDs listed for each Criterion in "
                "aggregation-context.json."
            )
            constraints = [
                "Correct one invalid evaluation candidate.",
                "Read the candidate at result_contract.candidate_path and every "
                "entry of result_contract.typed_errors.",
                "Fix the reported judgments; the typed errors carry code, path, "
                "entity and expected/actual values.",
                "Do not change document identity, ordering, derived fields or "
                "evidence you cannot verify from the frozen inputs.",
                evidence_correction,
                "Treat input_resources.citable=false files as context only. "
                "Replace rejected paths with canonical frozen repository paths.",
                "Treat result_contract.machine_contract as normative.",
                "Write only the structured final result.",
            ]
        payload_field_text = json.dumps(payload_fields, ensure_ascii=False)
        evidence_requirement = (
            "Local evidence keys (e1, e2, ...) are declared once in "
            "evidence_declarations and referenced via evidence_refs; never emit "
            "canonical EV- IDs."
            if declares_evidence else
            "For aggregation, do not emit evidence_declarations, evidence_refs, "
            "or local evidence keys. criterion_results[].evidence_ids and each "
            "finding evidence_ids must use canonical EV- IDs listed for that "
            "Criterion in aggregation-context.json."
        )
        task = (
            f"Correct one {result_kind} candidate after typed validation failure."
            if correcting else
            f"Produce one complete {result_kind} payload for the declared work item."
        )
        payload = {
            "task": task,
            "constraints": constraints,
            "func_id": work.func_id,
            "run_id": work.run_id,
            "work_item": work.work_item,
            "input_paths": list(work.input_paths),
            "input_resources": list(work.work_item.get("input_resources", [])),
            "forbidden_paths": list(work.forbidden_paths),
            "skill_version": work.skill_version,
            "protocol_version": work.protocol_version,
            "result_contract": contract,
            "machine_contract": machine_contract,
            "output": {
                "path": work.executor_result_path,
                "schema": contract.get("schema_path"),
                "requirement": (
                    "Return every envelope field. Use schema_version=3. For a "
                    "completed work item set status=completed, error=null, and "
                    f"payload to one {result_kind} object containing exactly "
                    f"these fields: {payload_field_text}, fully constrained by "
                    f"the declared schema. {evidence_requirement} Local "
                    "NOT_VERIFIABLE outcomes still use envelope status=completed. "
                    "Use status=failed only when no complete payload can be "
                    "produced; then set payload=null and provide a non-empty error."
                ),
            },
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)


def _redacted_argv(argv: list[str]) -> list[str]:
    """Mask any value following a key that may carry a model/secret (for logging)."""
    masked = {"--model"}
    out: list[str] = []
    for i, token in enumerate(argv):
        if i > 0 and argv[i - 1] in masked and token:
            out.append("<redacted>")
        else:
            out.append(token)
    return out


def _execution_result(
    usage: TokenUsageAccumulator,
    telemetry: ExecutionTelemetryAccumulator,
    **kwargs: Any,
) -> C.ExecutionResult:
    """Attach the invocation's usage snapshot to every post-start outcome."""
    return C.ExecutionResult(
        token_usage=usage.snapshot(),
        usage_reported=usage.reported,
        telemetry=telemetry.snapshot(),
        telemetry_reported=telemetry.reported,
        **kwargs,
    )
