"""Host unit tests for the Claude CLI executor adapter.

No real Claude call: the subprocess runner is faked. ``is_available`` is
bypassed by priming the cached probe. Run from specs/tools:

    PYTHONPATH=specs/tools python3 -m unittest spec_eval.tests.test_claude_executor -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spec_eval.kernel.schema_gen import (
    build_envelope_schema,
    write_envelope_schema,
)
from spec_eval.protocol_validator import validate_strict_output_schema
from spec_eval.service.executors import contract as C
from spec_eval.service.executors.claude_cli import (
    ClaudeCliExecutor,
    _build_transport_schema,
    _find_result_event,
    _normalize_model_usage,
)
from spec_eval.service.executors.process import ProcessResult
from spec_eval.service.executors.registry import available as registry_available
from spec_eval.service.settings import ServiceSettings, executor_config_for


def _stream_json_output(
    *,
    structured_output: object | None = None,
    is_error: bool = False,
    result_text: str | None = None,
    usage: dict | None = None,
    model_usage: dict | None = None,
    total_cost_usd: float | None = None,
    num_turns: int = 1,
    duration_ms: int = 100,
    duration_api_ms: int = 80,
    include_assistant: bool = True,
) -> str:
    """Build a Claude CLI ``--output-format stream-json --verbose`` NDJSON output.

    Emits the event types seen in real Claude stream-json output:
    system (init) -> assistant (per turn) -> result (final).
    """
    lines: list[str] = []

    # system init event
    init_event = {
        "type": "system",
        "subtype": "init",
        "cwd": "/tmp/test",
        "session_id": "test-session-123",
        "model": "claude-opus-4-6[1m]",
        "permissionMode": "bypassPermissions",
    }
    lines.append(json.dumps(init_event))

    # assistant event (per-turn, with per-turn usage)
    if include_assistant:
        assistant_event = {
            "type": "assistant",
            "message": {
                "model": "claude-opus-4-6[1m]",
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Processing..."},
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "/tmp/test/evidence/spec.md"},
                    },
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "ls /tmp"},
                    },
                ],
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cache_creation_input_tokens": 5000,
                    "cache_read_input_tokens": 0,
                },
            },
            "session_id": "test-session-123",
        }
        lines.append(json.dumps(assistant_event))

    # result event (final)
    result_event = {
        "type": "result",
        "subtype": "error" if is_error else "success",
        "is_error": is_error,
        "duration_ms": duration_ms,
        "duration_api_ms": duration_api_ms,
        "num_turns": num_turns,
        "result": result_text,
        "session_id": "test-session-123",
        "total_cost_usd": total_cost_usd or 0.01,
        "usage": usage or {
            "input_tokens": 200,
            "output_tokens": 100,
            "cache_creation_input_tokens": 5000,
            "cache_read_input_tokens": 0,
        },
    }
    if structured_output is not None:
        result_event["structured_output"] = structured_output
    if model_usage is not None:
        result_event["modelUsage"] = model_usage
    lines.append(json.dumps(result_event))

    return "\n".join(lines) + "\n"


class _FakeRunner:
    """Mimics process.run_subprocess for the Claude adapter."""

    def __init__(
        self,
        *,
        exit_code: int = 0,
        timed_out: bool = False,
        cancelled: bool = False,
        stdout_content: str = "",
    ) -> None:
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.cancelled = cancelled
        self.stdout_content = stdout_content
        self.last_argv: list[str] | None = None
        self.last_stdin: str | None = None
        self.last_cwd: str | None = None
        self.last_env: dict[str, str] | None = None

    def __call__(
        self, argv, *, cwd, stdin, timeout, stdout_log_path,
        stderr_log_path, cancel=None, line_sink=None, env=None,
    ):
        self.last_argv = list(argv)
        self.last_stdin = stdin
        self.last_cwd = cwd
        self.last_env = env
        Path(stdout_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(stdout_log_path).write_text(
            self.stdout_content, encoding="utf-8",
        )
        Path(stderr_log_path).write_text("", encoding="utf-8")
        if line_sink is not None:
            for line in self.stdout_content.splitlines():
                line_sink(line)
        return ProcessResult(
            exit_code=self.exit_code,
            timed_out=self.timed_out,
            cancelled=self.cancelled,
            elapsed_seconds=0.01,
            stdout_log_path=stdout_log_path,
            stderr_log_path=stderr_log_path,
        )


class ClaudeExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.config = {
            "type": "claude-cli",
            "command": "claude",
            "model": None,
            "permission_mode": "bypassPermissions",
            "timeout_seconds": 60,
            "max_parallel": 2,
            "max_output_tokens": 200_000,
            "output_schema": "executor-result.schema.json",
        }
        self.schema_path = write_envelope_schema(
            "observation", Path(self.tmp.name) / "envelope-observation.json"
        )
        self.work = C.WorkItemInput(
            job_id="j1",
            func_id="04-01-01",
            run_id="run-1",
            work_item_id="feature:Feat-01",
            work_item={
                "id": "feature:Feat-01",
                "input_paths": [],
                "output_path": "/tmp/obs.json",
            },
            run_dir=self.tmp.name,
            input_paths=(),
            executor_result_path=str(
                Path(self.tmp.name) / "Feat-01.executor-result.json"
            ),
            repo_root=self.settings.repo_root,
            skill_version="x",
            protocol_version="0.2.0",
            prompt_extras={
                "schema_path": str(self.schema_path),
                "result_kind": "staged_observation_judgments",
                "payload_fields": [
                    "evidence_declarations",
                    "claim_reviews",
                    "observations",
                    "open_questions",
                    "notes",
                ],
            },
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _executor(self, runner: _FakeRunner) -> ClaudeCliExecutor:
        ex = ClaudeCliExecutor(
            self.config,
            schemas_root=self.settings.schemas_root,
            runner=runner,
        )
        ex._available = True
        return ex

    def _events(self) -> list[C.ExecutionEvent]:
        events: list[C.ExecutionEvent] = []
        return events

    def _emit(self, events: list[C.ExecutionEvent]):
        def sink(event: C.ExecutionEvent) -> None:
            events.append(event)
        return sink

    # --- happy path -------------------------------------------------------

    def test_success_returns_completed_and_payload(self):
        runner = _FakeRunner(
            stdout_content=_stream_json_output(
                structured_output=self._valid_payload()
            ),
        )
        events = self._events()
        result = self._executor(runner).execute(
            self.work, self._emit(events),
        )
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertIsNotNone(result.observation)
        self.assertIn("evidence_declarations", result.observation)

    # --- argv shape -------------------------------------------------------

    def test_argv_uses_print_mode(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIn("-p", runner.last_argv)

    def test_argv_has_stream_json_format(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--output-format")
        self.assertEqual(runner.last_argv[idx + 1], "stream-json")

    def test_argv_has_verbose_flag(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIn("--verbose", runner.last_argv)

    def test_argv_has_no_cd_flag(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertNotIn("--cd", runner.last_argv)

    def test_cwd_passed_to_runner(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(runner.last_cwd, self.work.repo_root)

    def test_json_schema_inline_content(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--json-schema")
        schema_arg = runner.last_argv[idx + 1]
        parsed = json.loads(schema_arg)
        self.assertIn("properties", parsed)

    def test_generated_transport_schemas_are_strict_payload_roots(self):
        expected = {
            "observation": {
                "evidence_declarations", "claim_reviews", "observations",
                "open_questions", "notes",
            },
            "aggregation": {
                "cross_feat_contracts_reviewed", "contradiction_bases",
                "defect_ownership", "outcome_policy_bases",
                "criterion_results", "notes",
            },
            "correction": {"patches", "notes"},
        }
        for payload_kind, fields in expected.items():
            with self.subTest(payload_kind=payload_kind):
                transport = _build_transport_schema(
                    build_envelope_schema(payload_kind)
                )
                self.assertEqual(transport["type"], "object")
                self.assertEqual(set(transport["properties"]), fields)
                self.assertNotIn("payload", transport["properties"])
                self.assertNotIn("schema_version", transport["properties"])
                self.assertEqual(validate_strict_output_schema(transport), [])

    def test_no_session_persistence_flag(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIn("--no-session-persistence", runner.last_argv)

    def test_permission_mode_flag(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--permission-mode")
        self.assertEqual(runner.last_argv[idx + 1], "bypassPermissions")

    def test_model_flag_present_when_configured(self):
        self.config["model"] = "opus"
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--model")
        self.assertEqual(runner.last_argv[idx + 1], "opus")

    def test_model_flag_absent_when_none(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertNotIn("--model", runner.last_argv)

    # --- error paths ------------------------------------------------------

    def test_nonzero_exit_is_failed(self):
        runner = _FakeRunner(exit_code=1, stdout_content="")
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("code 1", result.error)

    def test_timeout_is_reported(self):
        runner = _FakeRunner(timed_out=True, stdout_content="")
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_TIMEOUT)

    def test_cancelled_is_reported(self):
        runner = _FakeRunner(cancelled=True, stdout_content="")
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_CANCELLED)

    def test_no_result_event_is_failed(self):
        init_only = json.dumps({"type": "system", "subtype": "init"}) + "\n"
        runner = _FakeRunner(stdout_content=init_only)
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("no result event", result.error)

    def test_empty_stdout_is_failed(self):
        runner = _FakeRunner(stdout_content="")
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("no result event", result.error)

    def test_claude_error_is_failed(self):
        runner = _FakeRunner(
            stdout_content=_stream_json_output(
                is_error=True, result_text="rate limit exceeded",
            ),
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("rate limit", result.error)

    def test_no_structured_output_is_failed(self):
        runner = _FakeRunner(
            stdout_content=_stream_json_output(result_text="just text, no schema"),
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("structured_output", result.error)

    def test_legacy_envelope_output_is_rejected_as_payload(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output={
                "schema_version": 3,
                "work_item_id": "feature:Feat-01",
                "status": "completed",
                "payload": {"x": 1},
                "notes": [],
                "error": None,
            },
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("schema validation", result.error)

    def test_non_object_structured_output_is_rejected(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=json.dumps(self._valid_payload()),
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("structured_output object", result.error)

    def test_payload_root_is_wrapped_in_service_owned_envelope(self):
        payload = self._valid_payload()
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=payload,
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertEqual(result.observation, payload)
        persisted = json.loads(Path(
            self.work.executor_result_path
        ).read_text(encoding="utf-8"))
        self.assertEqual(persisted["schema_version"], 3)
        self.assertEqual(persisted["work_item_id"], self.work.work_item_id)
        self.assertEqual(persisted["status"], "completed")
        self.assertEqual(persisted["payload"], payload)
        self.assertIsNone(persisted["error"])
        self.assertEqual(persisted["notes"], [])

        summary_path = (
            Path(self.work.executor_result_path).parent
            / "claude.feature_Feat-01.execution-summary.json"
        )
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["output_schema"]["payload_transport"],
                         "payload_root_object")
        self.assertIn("source_sha256", summary["output_schema"])
        self.assertEqual(
            summary["transport_normalizations"],
            ["payload_root_wrapped_in_canonical_envelope"],
        )

    def test_payload_strings_with_quotes_need_no_json_reparse(self):
        payload = self._valid_payload()
        payload["notes"] = [
            "agrees with code, not with spec R-7's 'entire strokeWidth'."
        ]
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=payload,
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertEqual(result.observation["notes"], payload["notes"])

    # --- streaming usage/telemetry extraction ------------------------------

    def test_usage_extracted_from_streaming(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
            usage={"input_tokens": 500, "output_tokens": 200},
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertTrue(result.usage_reported)
        self.assertGreaterEqual(result.token_usage.get("input_tokens", 0), 500)
        self.assertGreaterEqual(result.token_usage.get("output_tokens", 0), 200)

    def test_telemetry_counts_tool_calls_from_assistant_events(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
            include_assistant=True,
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertTrue(result.telemetry_reported)
        self.assertEqual(result.telemetry.get("tool_calls", 0), 2)
        self.assertEqual(result.telemetry.get("command_calls", 0), 1)

    # --- extended telemetry: cost / turns / model usage --------------------

    def test_cost_usd_extracted(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
            total_cost_usd=8.37,
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertAlmostEqual(result.cost_usd, 8.37)

    def test_num_turns_extracted(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
            num_turns=14,
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertEqual(result.num_turns, 14)

    def test_model_usage_normalized(self):
        raw_model_usage = {
            "claude-opus-4-6": {
                "inputTokens": 552, "outputTokens": 37,
                "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0,
                "costUSD": 0.011, "contextWindow": 200000,
            },
            "claude-opus-4-6[1m]": {
                "inputTokens": 2, "outputTokens": 10,
                "cacheReadInputTokens": 0, "cacheCreationInputTokens": 27360,
                "costUSD": 0.514, "contextWindow": 1000000,
            },
        }
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
            model_usage=raw_model_usage,
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertIsNotNone(result.model_usage)
        self.assertIn("claude-opus-4-6", result.model_usage)
        self.assertIn("claude-opus-4-6[1m]", result.model_usage)
        entry = result.model_usage["claude-opus-4-6[1m]"]
        self.assertEqual(entry["input_tokens"], 2)
        self.assertEqual(entry["output_tokens"], 10)
        self.assertAlmostEqual(entry["cost_usd"], 0.514)

    def test_execution_summary_written(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
            total_cost_usd=1.23,
            num_turns=3,
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        summary_path = Path(self.work.executor_result_path).parent / "claude.feature_Feat-01.execution-summary.json"
        self.assertTrue(summary_path.exists())
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        self.assertEqual(summary["executor"], "claude-cli")
        self.assertEqual(summary["work_item_id"], "feature:Feat-01")
        self.assertEqual(summary["func_id"], "04-01-01")
        self.assertAlmostEqual(summary["total_cost_usd"], 1.23)
        self.assertEqual(summary["num_turns"], 3)

    # --- max_output_tokens env propagation --------------------------------

    def test_max_output_tokens_env_propagated(self):
        self.config["max_output_tokens"] = 200_000
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIsNotNone(runner.last_env)
        self.assertEqual(
            runner.last_env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "200000",
        )

    def test_max_output_tokens_not_set_when_absent(self):
        self.config.pop("max_output_tokens", None)
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIsNone(runner.last_env)

    def test_max_output_tokens_in_describe(self):
        self.config["max_output_tokens"] = 128_000
        runner = _FakeRunner()
        ex = self._executor(runner)
        desc = ex.describe()
        self.assertEqual(desc["max_output_tokens"], 128_000)

    def test_max_output_tokens_absent_from_describe_when_none(self):
        self.config.pop("max_output_tokens", None)
        runner = _FakeRunner()
        ex = self._executor(runner)
        desc = ex.describe()
        self.assertNotIn("max_output_tokens", desc)

    def test_default_claude_config_has_max_output_tokens(self):
        config = executor_config_for("claude")
        self.assertEqual(config["max_output_tokens"], 200_000)

    # --- describe / availability ------------------------------------------

    def test_describe_returns_claude_cli_type(self):
        runner = _FakeRunner()
        ex = self._executor(runner)
        desc = ex.describe()
        self.assertEqual(desc["type"], "claude-cli")
        self.assertEqual(desc["executor_version"], C.CLAUDE_EXECUTOR_VERSION)

    def test_is_available_false_for_missing_command(self):
        self.config["command"] = "/nonexistent/claude"
        ex = ClaudeCliExecutor(
            self.config, schemas_root=self.settings.schemas_root,
        )
        self.assertFalse(ex.is_available())

    # --- prompt -----------------------------------------------------------

    def test_prompt_sent_via_stdin(self):
        runner = _FakeRunner(stdout_content=_stream_json_output(
            structured_output=self._valid_payload(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIsNotNone(runner.last_stdin)
        prompt_log = Path(self.work.executor_result_path).parent / "claude.feature_Feat-01.prompt.log"
        self.assertTrue(prompt_log.is_file())
        self.assertEqual(prompt_log.read_text(encoding="utf-8"), runner.last_stdin)
        prompt = json.loads(runner.last_stdin)
        self.assertIn("task", prompt)
        self.assertIn("func_id", prompt)
        self.assertEqual(prompt["output"]["transport"], "payload_root")
        self.assertNotIn("schema", prompt["output"])
        self.assertEqual(
            prompt["output"]["canonical_envelope_schema"],
            str(self.schema_path),
        )
        self.assertEqual(
            prompt["result_contract"]["output_transport"], "payload_root"
        )
        self.assertIn(
            "Do not emit schema_version, work_item_id, status, payload",
            prompt["output"]["requirement"],
        )

    # --- helpers ----------------------------------------------------------

    def _valid_payload(self) -> dict:
        return {
            "evidence_declarations": [],
            "claim_reviews": [],
            "observations": [],
            "open_questions": [],
            "notes": [],
        }


class FindResultEventTest(unittest.TestCase):
    """Tests for the _find_result_event NDJSON parser."""

    def test_finds_result_in_stream(self):
        lines = [
            json.dumps({"type": "system", "subtype": "init"}),
            json.dumps({"type": "assistant", "message": {}}),
            json.dumps({"type": "result", "is_error": False, "num_turns": 5}),
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("\n".join(lines) + "\n")
            path = f.name
        try:
            event = _find_result_event(path)
            self.assertIsNotNone(event)
            self.assertEqual(event["num_turns"], 5)
        finally:
            Path(path).unlink()

    def test_returns_none_for_no_result(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(json.dumps({"type": "system"}) + "\n")
            path = f.name
        try:
            self.assertIsNone(_find_result_event(path))
        finally:
            Path(path).unlink()

    def test_returns_none_for_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write("")
            path = f.name
        try:
            self.assertIsNone(_find_result_event(path))
        finally:
            Path(path).unlink()

    def test_returns_none_for_missing_file(self):
        self.assertIsNone(_find_result_event("/nonexistent/path.log"))


class NormalizeModelUsageTest(unittest.TestCase):
    def test_camel_to_snake_conversion(self):
        raw = {
            "opus": {
                "inputTokens": 100,
                "outputTokens": 50,
                "costUSD": 0.5,
                "contextWindow": 200000,
            },
        }
        normalized = _normalize_model_usage(raw)
        self.assertIsNotNone(normalized)
        self.assertEqual(normalized["opus"]["input_tokens"], 100)
        self.assertEqual(normalized["opus"]["output_tokens"], 50)
        self.assertAlmostEqual(normalized["opus"]["cost_usd"], 0.5)

    def test_none_for_empty(self):
        self.assertIsNone(_normalize_model_usage(None))
        self.assertIsNone(_normalize_model_usage({}))
        self.assertIsNone(_normalize_model_usage("not a dict"))


class ClaudeRegistryTest(unittest.TestCase):
    def test_claude_is_registered(self):
        self.assertIn("claude", registry_available())


class ClaudeSettingsTest(unittest.TestCase):
    def test_executor_config_for_claude(self):
        config = executor_config_for("claude")
        self.assertEqual(config["type"], "claude-cli")
        self.assertEqual(config["command"], "claude")

    def test_executor_config_for_codex(self):
        config = executor_config_for("codex")
        self.assertEqual(config["type"], "codex-cli")

    def test_executor_config_for_unknown_raises(self):
        with self.assertRaises(ValueError):
            executor_config_for("unknown")


if __name__ == "__main__":
    unittest.main()
