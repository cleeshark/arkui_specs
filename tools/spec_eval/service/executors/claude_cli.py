"""Claude CLI semantic executor adapter.

Drives ``claude -p`` (print mode) as a non-interactive subprocess: the prompt
goes via stdin, structured output is captured from stdout via
``--output-format json`` + ``--json-schema``, and the adapter writes the
pipeline-expected v3 envelope to ``work.executor_result_path``.

Phase 1 uses ``--output-format json`` (single JSON object on stdout). Real-time
streaming (``--output-format stream-json``) and live token-usage reporting can
be added in a future phase.
"""

from __future__ import annotations

import json
import os
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
from ._prompt import build_executor_prompt
from .process import ProcessResult, run_subprocess
from .redaction import redact_jsonl
from .telemetry import ExecutionTelemetryAccumulator
from .usage import TokenUsageAccumulator

DEFAULT_TIMEOUT = 3600.0


class ClaudeCliExecutor:
    """SemanticExecutor backed by the local ``claude`` CLI."""

    def __init__(
        self,
        config: dict[str, Any],
        *,
        schemas_root: Path,
        runner: Callable[..., ProcessResult] = run_subprocess,
    ) -> None:
        self._command = str(config.get("command", "claude"))
        self._model = config.get("model")
        self._permission_mode = str(
            config.get("permission_mode", "bypassPermissions")
        )
        self._timeout = float(config.get("timeout_seconds", DEFAULT_TIMEOUT))
        self._max_output_tokens = config.get("max_output_tokens")
        self._schemas_root = Path(schemas_root)
        schema_name = str(
            config.get("output_schema", "executor-result.schema.json")
        )
        self._output_schema_path = self._schemas_root / schema_name
        self._validate_output_schema()
        self._validate_generated_output_schemas()
        self._runner = runner
        self._available: bool | None = None

    # --- SemanticExecutor protocol ----------------------------------------
    def is_available(self) -> bool:
        if self._available is None:
            try:
                proc = subprocess.run(  # noqa: S603,S607
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
        desc = {
            "type": "claude-cli",
            "command": self._command,
            "model": self._model,
            "permission_mode": self._permission_mode,
            "timeout_seconds": self._timeout,
            "executor_version": C.CLAUDE_EXECUTOR_VERSION,
            "protocol_version": C.PROTOCOL_VERSION,
            "output_schema": self._output_schema_path.name,
        }
        if self._max_output_tokens is not None:
            desc["max_output_tokens"] = self._max_output_tokens
        return desc

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
                error="claude CLI not available",
            )

        argv = self._build_argv(work)
        prompt = build_executor_prompt(work)
        result_parent = Path(work.executor_result_path).parent
        result_parent.mkdir(parents=True, exist_ok=True)
        stdout_log = str(result_parent / "claude.stdout.log")
        stderr_log = str(result_parent / "claude.stderr.log")

        event_count = 0
        usage = TokenUsageAccumulator()
        telemetry = ExecutionTelemetryAccumulator(work)

        def line_sink(line: str) -> None:
            nonlocal event_count
            event_count += 1
            emit(C.ExecutionEvent(kind="jsonl", message=redact_jsonl(line)))

        emit(C.ExecutionEvent(
            kind="command", message=" ".join(_redacted_argv(argv))
        ))
        started = time.monotonic()
        env = self._build_env()
        proc_result = self._runner(
            argv,
            cwd=work.repo_root,
            stdin=prompt,
            timeout=self._timeout,
            stdout_log_path=stdout_log,
            stderr_log_path=stderr_log,
            cancel=cancel,
            line_sink=line_sink,
            env=env,
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
                error=f"claude exited with code {proc_result.exit_code}",
                elapsed_seconds=proc_result.elapsed_seconds,
                event_count=event_count,
            )

        return self._capture_and_validate(
            work, proc_result, event_count, started, usage, telemetry,
            stdout_log,
        )

    # --- internals --------------------------------------------------------
    def _capture_and_validate(
        self,
        work: C.WorkItemInput,
        proc_result: ProcessResult,
        event_count: int,
        started: float,
        usage: TokenUsageAccumulator,
        telemetry: ExecutionTelemetryAccumulator,
        stdout_log: str,
    ) -> C.ExecutionResult:
        try:
            raw = Path(stdout_log).read_text(encoding="utf-8")
        except OSError as exc:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"cannot read claude stdout log: {exc}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        try:
            claude_envelope = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"claude stdout is not valid JSON: {exc}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        if not isinstance(claude_envelope, dict):
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="claude stdout is not a JSON object",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        if claude_envelope.get("is_error"):
            error_msg = claude_envelope.get("result") or "claude reported an error"
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"claude error: {error_msg}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        claude_usage = claude_envelope.get("usage")
        if isinstance(claude_usage, dict):
            usage.observe(json.dumps({"usage": claude_usage}))

        structured = claude_envelope.get("structured_output")
        if not isinstance(structured, dict):
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="claude produced no structured_output object",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )

        # structured_output is already the v3 envelope (constrained by
        # --json-schema to match the executor-result schema).
        try:
            Path(work.executor_result_path).write_text(
                json.dumps(structured, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"cannot write result file: {exc}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )

        return self._validate_result(
            work, proc_result, event_count, started, usage, telemetry,
        )

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
                error=f"no result file at {work.executor_result_path}",
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
            schema = json.loads(
                self._output_schema_path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"cannot load executor output schema "
                f"{self._output_schema_path}: {exc}"
            ) from exc
        if not isinstance(schema, dict):
            raise ValueError(
                f"executor output schema is not an object: "
                f"{self._output_schema_path}"
            )
        errors = validate_strict_output_schema(schema)
        if errors:
            raise ValueError(
                f"executor output schema is not strict: "
                f"{self._output_schema_path}: " + "; ".join(errors)
            )

    def _validate_generated_output_schemas(self) -> None:
        for payload_kind in ("observation", "aggregation"):
            errors = validate_strict_output_schema(
                build_envelope_schema(payload_kind)
            )
            if errors:
                raise ValueError(
                    f"generated {payload_kind} output schema is not "
                    "compatible: " + "; ".join(errors)
                )

    def _work_schema_error(self, work: C.WorkItemInput) -> str | None:
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

    def _build_env(self) -> dict[str, str] | None:
        if self._max_output_tokens is None:
            return None
        env = os.environ.copy()
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(int(self._max_output_tokens))
        return env

    def _build_argv(self, work: C.WorkItemInput) -> list[str]:
        schema_path = self._schema_path_for(work)
        schema_content = schema_path.read_text(encoding="utf-8")

        argv = [self._command, "-p"]
        if self._model:
            argv += ["--model", str(self._model)]
        argv += [
            "--output-format", "json",
            "--json-schema", schema_content,
            "--add-dir", str(work.run_dir),
            "--no-session-persistence",
            "--permission-mode", self._permission_mode,
            "--allowedTools", "Bash Read",
        ]
        return argv

    def _schema_path_for(self, work: C.WorkItemInput) -> Path:
        schema_path = work.prompt_extras.get("schema_path")
        if isinstance(schema_path, str) and schema_path:
            return Path(schema_path)
        return self._output_schema_path


def _redacted_argv(argv: list[str]) -> list[str]:
    masked = {"--model", "--json-schema"}
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
    return C.ExecutionResult(
        token_usage=usage.snapshot(),
        usage_reported=usage.reported,
        telemetry=telemetry.snapshot(),
        telemetry_reported=telemetry.reported,
        **kwargs,
    )
