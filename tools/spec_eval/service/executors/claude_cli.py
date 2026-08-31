"""Claude CLI semantic executor adapter.

Drives ``claude -p`` (print mode) as a non-interactive subprocess: the prompt
goes via stdin, structured output is captured from stdout via
``--output-format stream-json --verbose`` + ``--json-schema``, and the adapter
writes the pipeline-expected v3 envelope to ``work.executor_result_path``.

Stream-json mode emits per-turn JSONL events (``system``, ``assistant``,
``result``) which are captured for live telemetry and saved as a complete
execution trace.  The final ``result`` event carries ``structured_output``,
aggregate usage, per-model ``modelUsage``, ``total_cost_usd``, ``num_turns``
and ``duration_api_ms``—all written to ``claude.execution-summary.json`` for
post-hoc cost analysis.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from spec_eval.kernel.contracts import ENVELOPE_SCHEMA_VERSION
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.protocol_validator import (
    JsonSchemaSubsetValidator,
    validate_strict_output_schema,
)

from . import contract as C
from ._prompt import build_executor_prompt, workflow_shard_dir
from .process import ProcessResult, run_subprocess
from .redaction import redact_jsonl
from .telemetry import ExecutionTelemetryAccumulator
from .usage import TokenUsageAccumulator
from .workflow_manifest import make_spec_from_work_item, write_manifest
from .workflow_synthesis import SynthesisError, synthesize

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
            "payload_transport": "payload_root_object",
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
        # The payload_root transport-schema check does not apply to the
        # workflow-shards path (it uses the small completion-signal schema).
        if not _use_workflow_shards(work):
            schema_error = self._work_schema_error(work)
            if schema_error is not None:
                return C.ExecutionResult(
                    status=C.STATUS_FAILED, error=schema_error
                )
        if not self.is_available():
            return C.ExecutionResult(
                status=C.STATUS_AWAITING,
                error="claude CLI not available",
            )

        use_workflow = _use_workflow_shards(work)
        if use_workflow:
            # Claude-only observation path: disk-driven workflow shards.
            # correction / aggregation still use the payload_root path below.
            schema_content, schema_metadata = _workflow_signal_schema()
            argv = self._build_argv(work, schema_content, allow_write=True)
            prompt = build_executor_prompt(
                work, output_transport="workflow_shards"
            )
        else:
            schema_content, schema_metadata = self._transport_schema(work)
            argv = self._build_argv(work, schema_content)
            prompt = build_executor_prompt(work, output_transport="payload_root")

        result_parent = Path(work.executor_result_path).parent
        result_parent.mkdir(parents=True, exist_ok=True)

        if use_workflow:
            # Pre-generate the manifest + empty shard directories BEFORE the
            # session starts, so the model only consumes them (design §4.4).
            try:
                self._prepare_workflow_manifest(work)
            except Exception as exc:  # noqa: BLE001 - surface as executor failure
                return C.ExecutionResult(
                    status=C.STATUS_FAILED,
                    error=f"cannot prepare workflow manifest: {exc}",
                )

        log_tag = _safe_work_item_tag(work.work_item_id)
        mode = work.prompt_extras.get("mode", "observe")
        if mode != "observe":
            log_tag = f"{log_tag}.{mode}"
        stdout_log = str(result_parent / f"claude.{log_tag}.stdout.log")
        stderr_log = str(result_parent / f"claude.{log_tag}.stderr.log")
        prompt_log = result_parent / f"claude.{log_tag}.prompt.log"
        try:
            prompt_log.write_text(prompt, encoding="utf-8")
        except OSError as exc:
            # Prompt capture is diagnostic; do not turn a logging failure into
            # an executor failure when the CLI can still run.
            emit(C.ExecutionEvent(
                kind="error",
                message=f"cannot write prompt log {prompt_log}: {exc}",
            ))

        event_count = 0
        usage = TokenUsageAccumulator()
        telemetry = ExecutionTelemetryAccumulator(work)

        def line_sink(line: str) -> None:
            nonlocal event_count
            event_count += 1
            # Feed streaming events to usage/telemetry accumulators
            # (like the Codex executor does).
            usage.observe(line)
            telemetry.observe(line)
            emit(C.ExecutionEvent(kind="jsonl", message=redact_jsonl(line)))

        emit(C.ExecutionEvent(
            kind="command", message=" ".join(_redacted_argv(argv))
        ))
        emit(C.ExecutionEvent(
            kind="info",
            message="claude output schema prepared",
            data=schema_metadata,
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
            stdout_log, schema_metadata, use_workflow=use_workflow,
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
        schema_metadata: dict[str, Any],
        use_workflow: bool = False,
    ) -> C.ExecutionResult:
        # stdout_log is a stream-json NDJSON file; find the final result event.
        result_event = _find_result_event(stdout_log)
        if result_event is None:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="no result event found in claude stream-json output",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
            )
        # Extract aggregate usage from the result event (supplements
        # streaming accumulation with the authoritative final totals).
        result_usage = result_event.get("usage")
        if isinstance(result_usage, dict):
            usage.observe(json.dumps({"usage": result_usage}))

        # Extract extended telemetry: cost, turns, per-model breakdown.
        cost_usd = _float_or_none(result_event.get("total_cost_usd"))
        num_turns = _int_or_none(result_event.get("num_turns"))
        model_usage = _normalize_model_usage(result_event.get("modelUsage"))

        # Write execution summary for post-hoc cost analysis.
        summary = _build_execution_summary(
            result_event, work, telemetry.snapshot(),
        )
        summary["output_schema"] = schema_metadata

        if result_event.get("is_error"):
            summary["result_status"] = "error"
            _write_execution_summary(work, summary)
            error_msg = result_event.get("result") or "claude reported an error"
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"claude error: {error_msg}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
                cost_usd=cost_usd,
                num_turns=num_turns,
                model_usage=model_usage,
            )

        # Extract structured_output from the result event.
        structured = result_event.get("structured_output")
        if not isinstance(structured, dict):
            summary["result_status"] = "missing_structured_output"
            _write_execution_summary(work, summary)
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="claude produced no structured_output object",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
                cost_usd=cost_usd,
                num_turns=num_turns,
                model_usage=model_usage,
            )

        if use_workflow:
            # structured is only a tiny completion signal; the real product is
            # the shard files on disk. Synthesize the canonical envelope from
            # them (design §6.3). Failure is attributed per-unit for retry.
            return self._synthesize_workflow_result(
                work, proc_result, event_count, started, usage, telemetry,
                summary, structured,
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
            )

        structured = _wrap_payload_root(work, structured)
        summary["transport_normalizations"] = [
            "payload_root_wrapped_in_canonical_envelope"
        ]

        summary["result_status"] = "structured_output_captured"
        _write_execution_summary(work, summary)

        # Write the structured output as the executor result file.
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
                cost_usd=cost_usd,
                num_turns=num_turns,
                model_usage=model_usage,
            )

        return self._validate_result(
            work, proc_result, event_count, started, usage, telemetry,
            cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
        )

    def _validate_result(
        self,
        work: C.WorkItemInput,
        proc_result: ProcessResult,
        event_count: int,
        started: float,
        usage: TokenUsageAccumulator,
        telemetry: ExecutionTelemetryAccumulator,
        *,
        cost_usd: float | None = None,
        num_turns: int | None = None,
        model_usage: dict[str, Any] | None = None,
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
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
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
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
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
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
            )
        if str(document.get("work_item_id")) != work.work_item_id:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error="result work_item_id does not match the requested work item",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
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
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
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
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
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
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
            )
        return _execution_result(
            usage, telemetry,
            status=C.STATUS_COMPLETED,
            exit_code=proc_result.exit_code,
            executor_result_path=work.executor_result_path,
            observation=observation,
            elapsed_seconds=time.monotonic() - started,
            event_count=event_count,
            cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
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
        for payload_kind in ("observation", "aggregation", "correction"):
            canonical = build_envelope_schema(payload_kind)
            canonical_errors = validate_strict_output_schema(canonical)
            if canonical_errors:
                raise ValueError(
                    f"generated {payload_kind} output schema is not "
                    "compatible: " + "; ".join(canonical_errors)
                )
            transport_errors = validate_strict_output_schema(
                _build_transport_schema(canonical)
            )
            if transport_errors:
                raise ValueError(
                    f"generated {payload_kind} Claude transport schema is not "
                    "compatible: " + "; ".join(transport_errors)
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
        try:
            transport_schema = _build_transport_schema(schema)
        except ValueError as exc:
            return f"work transport schema is not compatible: {schema_path}: {exc}"
        transport_errors = validate_strict_output_schema(transport_schema)
        if transport_errors:
            return (
                f"work transport schema is not compatible: {schema_path}: "
                + "; ".join(transport_errors)
            )
        return None

    def _build_env(self) -> dict[str, str] | None:
        if self._max_output_tokens is None:
            return None
        env = os.environ.copy()
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(int(self._max_output_tokens))
        return env

    def _build_argv(
        self, work: C.WorkItemInput, schema_content: str,
        *, allow_write: bool = False,
    ) -> list[str]:
        argv = [self._command, "-p"]
        if self._model:
            argv += ["--model", str(self._model)]
        allowed_tools = "Bash Read Grep Write" if allow_write else "Bash Read Grep"
        argv += [
            "--output-format", "stream-json",
            "--verbose",
            "--json-schema", schema_content,
            "--add-dir", str(work.run_dir),
            "--no-session-persistence",
            "--permission-mode", self._permission_mode,
            "--allowedTools", allowed_tools,
        ]
        return argv

    def _transport_schema(
        self, work: C.WorkItemInput
    ) -> tuple[str, dict[str, Any]]:
        schema_path = self._schema_path_for(work)
        source = schema_path.read_bytes()
        canonical = json.loads(source)
        transport = _build_transport_schema(canonical)
        content = json.dumps(
            transport, ensure_ascii=False, separators=(",", ":")
        )
        encoded = content.encode("utf-8")
        return content, {
            "path": str(schema_path),
            "source_bytes": len(source),
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "transport_bytes": len(encoded),
            "transport_sha256": hashlib.sha256(encoded).hexdigest(),
            "payload_transport": "payload_root_object",
        }

    def _schema_path_for(self, work: C.WorkItemInput) -> Path:
        schema_path = work.prompt_extras.get("schema_path")
        if isinstance(schema_path, str) and schema_path:
            return Path(schema_path)
        return self._output_schema_path

    # --- workflow-shards observation path (Claude-only) -------------------
    def _prepare_workflow_manifest(self, work: C.WorkItemInput) -> Path:
        """Write _manifest.json + empty shard dirs before the session starts."""
        feat_id = str(work.work_item.get("feat_id", work.work_item_id))
        shard_dir = Path(workflow_shard_dir(work.run_dir, feat_id))
        machine_contract = work.prompt_extras.get("machine_contract", {})
        valid_criterion_ids = list(
            machine_contract.get("valid_criterion_ids", ())
        )
        spec = make_spec_from_work_item(work.work_item, valid_criterion_ids)
        return write_manifest(shard_dir, spec)

    def _synthesize_workflow_result(
        self,
        work: C.WorkItemInput,
        proc_result: ProcessResult,
        event_count: int,
        started: float,
        usage: TokenUsageAccumulator,
        telemetry: ExecutionTelemetryAccumulator,
        summary: dict[str, Any],
        signal: dict[str, Any],
        *,
        cost_usd: float | None,
        num_turns: int | None,
        model_usage: dict[str, Any] | None,
    ) -> C.ExecutionResult:
        """Assemble the canonical envelope from on-disk shards, then validate."""
        feat_id = str(work.work_item.get("feat_id", work.work_item_id))
        shard_dir = Path(workflow_shard_dir(work.run_dir, feat_id))
        manifest_path = shard_dir / "_manifest.json"

        # Model may self-report failure via the completion signal.
        if signal.get("status") == "failed":
            summary["result_status"] = "workflow_model_reported_failure"
            _write_execution_summary(work, summary)
            error = signal.get("error")
            if not isinstance(error, str) or not error.strip():
                error = "workflow session reported failure without an error message"
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=error,
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
            )

        try:
            result = synthesize(manifest_path, work.work_item_id)
        except SynthesisError as exc:
            summary["result_status"] = "workflow_synthesis_failed"
            summary["workflow_shard_errors"] = [
                {
                    "unit_type": e.unit_type,
                    "unit_id": e.unit_id,
                    "file": e.file,
                    "reason": e.reason,
                }
                for e in exc.shard_errors
            ]
            _write_execution_summary(work, summary)
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=str(exc),
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
            )

        summary["result_status"] = "workflow_synthesized"
        summary["transport_normalizations"] = ["synthesized_from_shards"]
        summary["workflow_counts"] = {
            "claims": result.claim_count,
            "observations": result.observation_count,
            "evidence": result.evidence_count,
        }
        _write_execution_summary(work, summary)

        try:
            Path(work.executor_result_path).write_text(
                json.dumps(result.envelope, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            return _execution_result(
                usage, telemetry,
                status=C.STATUS_FAILED,
                exit_code=proc_result.exit_code,
                error=f"cannot write synthesized result file: {exc}",
                elapsed_seconds=time.monotonic() - started,
                event_count=event_count,
                cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
            )

        # Same final schema gate as the payload_root path (design C2).
        return self._validate_result(
            work, proc_result, event_count, started, usage, telemetry,
            cost_usd=cost_usd, num_turns=num_turns, model_usage=model_usage,
        )


# --- NDJSON result extraction -------------------------------------------------

def _find_result_event(ndjson_path: str) -> dict[str, Any] | None:
    """Find the ``type=result`` event in a stream-json NDJSON file.

    Scans from the end since the result event is always the last line.
    Returns None if no result event is found (e.g. process killed).
    """
    try:
        lines = Path(ndjson_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            return event
    return None


def _build_transport_schema(canonical: dict[str, Any]) -> dict[str, Any]:
    """Expose the canonical payload object as Claude's structured-output root.

    Claude Code implements ``--json-schema`` through its internal
    ``StructuredOutput`` tool. Keeping a large payload nested inside an
    executor envelope can encourage compatible providers to serialize that
    payload as opaque JSON text. Make the payload itself the tool input so its
    nested fields remain schema-constrained, then let the adapter construct
    the service-owned canonical envelope.
    """
    payload_schema = canonical.get("properties", {}).get("payload")
    target = _resolve_local_schema_ref(canonical, payload_schema)
    if not isinstance(target, dict):
        raise ValueError("canonical schema payload is not resolvable")
    transport = copy.deepcopy(target)
    declared = target.get("type")
    if declared == "object":
        transport["type"] = "object"
    elif isinstance(declared, list) and "object" in declared:
        transport["type"] = "object"
    else:
        raise ValueError("canonical schema payload root must allow an object")
    transport["$schema"] = canonical.get(
        "$schema", "http://json-schema.org/draft-07/schema#"
    )
    definitions = canonical.get("$defs")
    if isinstance(definitions, dict):
        transport["$defs"] = copy.deepcopy(definitions)
    return transport


def _resolve_local_schema_ref(
    document: dict[str, Any], node: Any
) -> dict[str, Any] | None:
    if not isinstance(node, dict):
        return None
    reference = node.get("$ref")
    if not isinstance(reference, str) or not reference.startswith("#/"):
        return node
    target: Any = document
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or token not in target:
            return None
        target = target[token]
    return target if isinstance(target, dict) else None


def _wrap_payload_root(
    work: C.WorkItemInput, payload: dict[str, Any]
) -> dict[str, Any]:
    """Construct the canonical envelope from Claude's payload-root output."""
    return {
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "work_item_id": work.work_item_id,
        "status": "completed",
        "payload": payload,
        "notes": [],
        "error": None,
    }


def _use_workflow_shards(work: C.WorkItemInput) -> bool:
    """Whether this work item uses the Claude disk-driven workflow path.

    Only feature / function-global Observation turns (mode=observe,
    payload_kind=observation) use workflow shards.  Correction (mode=correct)
    and Aggregation (payload_kind=aggregation) keep the payload_root path.
    """
    extras = work.prompt_extras
    mode = extras.get("mode", "observe")
    if mode != "observe":
        return False
    payload_kind = extras.get("payload_kind")
    if payload_kind is not None:
        return payload_kind == "observation"
    # Fall back to the machine contract's observation_profile.
    profile = extras.get("machine_contract", {}).get("observation_profile")
    return profile in {"feature", "function_global"}


def _workflow_signal_schema() -> tuple[str, dict[str, Any]]:
    """The tiny completion-signal schema for the workflow-shards path.

    This is what ``--json-schema`` constrains: a small object reporting only
    success/failure and the files written.  It never carries the payload, so it
    cannot truncate.  Returns (json_string, metadata).
    """
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "status", "written_claim_files", "written_criterion_files",
            "aux_written", "error",
        ],
        "properties": {
            "status": {"type": "string", "enum": ["completed", "failed"]},
            "written_claim_files": {"type": "array", "items": {"type": "string"}},
            "written_criterion_files": {
                "type": "array", "items": {"type": "string"},
            },
            "aux_written": {"type": "string"},
            "error": {"type": ["string", "null"]},
        },
    }
    content = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    return content, {
        "path": "<workflow-signal>",
        "transport_bytes": len(content.encode("utf-8")),
        "payload_transport": "workflow_completion_signal",
    }


def _write_execution_summary(
    work: C.WorkItemInput, summary: dict[str, Any]
) -> None:
    summary_tag = _safe_work_item_tag(work.work_item_id)
    summary_mode = work.prompt_extras.get("mode", "observe")
    if summary_mode != "observe":
        summary_tag = f"{summary_tag}.{summary_mode}"
    summary_path = (
        Path(work.executor_result_path).parent
        / f"claude.{summary_tag}.execution-summary.json"
    )
    try:
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass  # telemetry must never fail a job


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _normalize_model_usage(raw: Any) -> dict[str, Any] | None:
    """Normalize the ``modelUsage`` dict from a Claude result event.

    Renames camelCase keys to snake_case for consistency with the service's
    token field naming.
    """
    if not isinstance(raw, dict) or not raw:
        return None
    normalized: dict[str, Any] = {}
    _KEY_MAP = {
        "inputTokens": "input_tokens",
        "outputTokens": "output_tokens",
        "cacheReadInputTokens": "cache_read_input_tokens",
        "cacheCreationInputTokens": "cache_creation_input_tokens",
        "webSearchRequests": "web_search_requests",
        "costUSD": "cost_usd",
        "contextWindow": "context_window",
        "maxOutputTokens": "max_output_tokens",
    }
    for model_name, model_data in raw.items():
        if not isinstance(model_data, dict):
            continue
        entry: dict[str, Any] = {}
        for camel, snake in _KEY_MAP.items():
            if camel in model_data:
                entry[snake] = model_data[camel]
        normalized[model_name] = entry
    return normalized or None


def _build_execution_summary(
    result_event: dict[str, Any],
    work: C.WorkItemInput,
    telemetry_snapshot: dict[str, int],
) -> dict[str, Any]:
    """Build the ``claude.execution-summary.json`` from a result event."""
    summary: dict[str, Any] = {
        "executor": "claude-cli",
        "work_item_id": work.work_item_id,
        "func_id": work.func_id,
        "num_turns": result_event.get("num_turns"),
        "duration_ms": result_event.get("duration_ms"),
        "duration_api_ms": result_event.get("duration_api_ms"),
        "total_cost_usd": result_event.get("total_cost_usd"),
        "usage": result_event.get("usage"),
        "model_usage": _normalize_model_usage(result_event.get("modelUsage")),
        "session_id": result_event.get("session_id"),
        "tool_calls": telemetry_snapshot,
    }
    return summary


# --- helpers ------------------------------------------------------------------

def _safe_work_item_tag(work_item_id: str) -> str:
    """Derive a filesystem-safe tag from a work_item_id for per-item log files."""
    return re.sub(r"[^a-zA-Z0-9._-]", "_", work_item_id)


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
