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

from spec_eval.service.executors import contract as C
from spec_eval.service.executors.claude_cli import ClaudeCliExecutor
from spec_eval.service.executors.process import ProcessResult
from spec_eval.service.executors.registry import available as registry_available
from spec_eval.service.settings import ServiceSettings, executor_config_for


def _claude_output(
    *,
    structured_output: dict | None = None,
    is_error: bool = False,
    result: str | None = None,
    usage: dict | None = None,
) -> str:
    """Build a Claude CLI ``--output-format json`` envelope."""
    doc = {
        "type": "result",
        "subtype": "error" if is_error else "success",
        "is_error": is_error,
        "duration_ms": 100,
        "duration_api_ms": 80,
        "num_turns": 1,
        "result": result,
        "session_id": "test-session",
        "total_cost_usd": 0.01,
        "usage": usage or {
            "input_tokens": 100,
            "output_tokens": 50,
        },
    }
    if structured_output is not None:
        doc["structured_output"] = structured_output
    return json.dumps(doc)


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
            "output_schema": "executor-result.schema.json",
        }
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
        payload = {"observation_id": "feature:Feat-01", "claims": []}
        runner = _FakeRunner(
            stdout_content=_claude_output(structured_output={
                "schema_version": 3,
                "work_item_id": "feature:Feat-01",
                "status": "completed",
                "payload": payload,
                "notes": [],
                "error": None,
            }),
        )
        events = self._events()
        result = self._executor(runner).execute(
            self.work, self._emit(events),
        )
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertIsNotNone(result.observation)
        self.assertIn("observation_id", result.observation)

    # --- argv shape -------------------------------------------------------

    def test_argv_uses_print_mode(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIn("-p", runner.last_argv)

    def test_argv_has_output_format_json(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--output-format")
        self.assertEqual(runner.last_argv[idx + 1], "json")

    def test_argv_has_no_cd_flag(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertNotIn("--cd", runner.last_argv)

    def test_cwd_passed_to_runner(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(runner.last_cwd, self.work.repo_root)

    def test_json_schema_inline_content(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--json-schema")
        schema_arg = runner.last_argv[idx + 1]
        parsed = json.loads(schema_arg)
        self.assertIn("properties", parsed)

    def test_no_session_persistence_flag(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIn("--no-session-persistence", runner.last_argv)

    def test_permission_mode_flag(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--permission-mode")
        self.assertEqual(runner.last_argv[idx + 1], "bypassPermissions")

    def test_model_flag_present_when_configured(self):
        self.config["model"] = "opus"
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--model")
        self.assertEqual(runner.last_argv[idx + 1], "opus")

    def test_model_flag_absent_when_none(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
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

    def test_empty_stdout_is_failed(self):
        runner = _FakeRunner(stdout_content="")
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("not valid JSON", result.error)

    def test_invalid_json_stdout_is_failed(self):
        runner = _FakeRunner(stdout_content="not json")
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("not valid JSON", result.error)

    def test_claude_error_is_failed(self):
        runner = _FakeRunner(
            stdout_content=_claude_output(
                is_error=True, result="rate limit exceeded",
            ),
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("rate limit", result.error)

    def test_no_structured_output_is_failed(self):
        runner = _FakeRunner(
            stdout_content=_claude_output(result="just text, no schema"),
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("structured_output", result.error)

    def test_wrong_work_item_id_is_failed(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output={
                "schema_version": 3,
                "work_item_id": "WRONG",
                "status": "completed",
                "payload": {"x": 1},
                "notes": [],
                "error": None,
            },
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("work_item_id", result.error)

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

    # --- usage extraction -------------------------------------------------

    def test_usage_extracted_from_claude_envelope(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
            usage={"input_tokens": 500, "output_tokens": 200},
        ))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertTrue(result.usage_reported)
        self.assertGreaterEqual(result.token_usage.get("input_tokens", 0), 500)

    # --- prompt -----------------------------------------------------------

    def test_prompt_sent_via_stdin(self):
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIsNotNone(runner.last_stdin)
        prompt = json.loads(runner.last_stdin)
        self.assertIn("task", prompt)
        self.assertIn("func_id", prompt)

    # --- max_output_tokens env propagation ----------------------------------

    def test_max_output_tokens_env_propagated(self):
        self.config["max_output_tokens"] = 200_000
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
        ))
        self._executor(runner).execute(self.work, lambda e: None)
        self.assertIsNotNone(runner.last_env)
        self.assertEqual(
            runner.last_env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"], "200000",
        )

    def test_max_output_tokens_not_set_when_absent(self):
        self.config.pop("max_output_tokens", None)
        runner = _FakeRunner(stdout_content=_claude_output(
            structured_output=self._valid_envelope(),
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

    # --- helpers ----------------------------------------------------------

    def _valid_envelope(self) -> dict:
        return {
            "schema_version": 3,
            "work_item_id": "feature:Feat-01",
            "status": "completed",
            "payload": {"observation_id": "feature:Feat-01"},
            "notes": [],
            "error": None,
        }


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
