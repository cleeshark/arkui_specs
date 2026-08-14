"""Host unit tests for the Codex CLI executor adapter (TASK-011-04).

No real Codex call: the subprocess runner is faked. ``is_available`` is bypassed
by priming the cached probe. Run from specs/tools:

    python3 -m unittest spec_eval.tests.test_next_011_codex_executor -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from spec_eval.protocol_validator import JsonSchemaSubsetValidator, validate_strict_output_schema
from spec_eval.service.executors import contract as C
from spec_eval.service.executors.codex_cli import CodexCliExecutor
from spec_eval.service.executors.process import ProcessResult
from spec_eval.service.executors.redaction import redact_jsonl
from spec_eval.service.settings import ServiceSettings


def _result_doc(
    work_item_id: str,
    *,
    observation: dict | None = None,
    status: str = "completed",
    error: str | None = None,
) -> dict:
    return {
        "schema_version": 2,
        "work_item_id": work_item_id,
        "status": status,
        "observation_json": (
            json.dumps(
                observation if observation is not None else {"observation_id": work_item_id}
            )
            if status == "completed"
            else None
        ),
        "notes": [],
        "error": error,
    }


class _FakeRunner:
    """Mimics process.run_subprocess for the Codex adapter."""

    def __init__(
        self,
        *,
        exit_code: int = 0,
        timed_out: bool = False,
        cancelled: bool = False,
        result_doc: dict | None = None,
        write_result: bool = True,
        jsonl_lines: list[str] | None = None,
        stdout_log: str = "",
        stderr_log: str = "",
    ) -> None:
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.cancelled = cancelled
        self.result_doc = result_doc
        self.write_result = write_result
        self.jsonl_lines = jsonl_lines or []
        self.stdout_log = stdout_log
        self.stderr_log = stderr_log
        self.last_argv: list[str] | None = None
        self.last_stdin: str | None = None
        self.lines_seen: list[str] = []

    def __call__(self, argv, *, cwd, stdin, timeout, stdout_log_path, stderr_log_path, cancel=None, line_sink=None, env=None):
        self.last_argv = list(argv)
        self.last_stdin = stdin
        Path(stdout_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(stdout_log_path).write_text(self.stdout_log, encoding="utf-8")
        Path(stderr_log_path).write_text(self.stderr_log, encoding="utf-8")
        for line in self.jsonl_lines:
            if line_sink is not None:
                line_sink(line)
        if self.write_result and self.result_doc is not None:
            out_path = _argv_value(argv, "--output-last-message")
            if out_path:
                Path(out_path).parent.mkdir(parents=True, exist_ok=True)
                Path(out_path).write_text(json.dumps(self.result_doc), encoding="utf-8")
        return ProcessResult(
            exit_code=self.exit_code,
            timed_out=self.timed_out,
            cancelled=self.cancelled,
            elapsed_seconds=0.01,
            stdout_log_path=stdout_log_path,
            stderr_log_path=stderr_log_path,
        )


def _argv_value(argv: list[str], flag: str) -> str | None:
    for i, token in enumerate(argv):
        if token == flag and i + 1 < len(argv):
            return argv[i + 1]
    return None


class CodexExecutorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.config = {
            "type": "codex-cli",
            "command": "codex",
            "model": None,
            "sandbox": "read-only",
            "timeout_seconds": 60,
            "max_parallel": 2,
            "output_schema": "executor-result.schema.json",
        }
        self.work = C.WorkItemInput(
            job_id="j1",
            func_id="04-01-01",
            run_id="run-1",
            work_item_id="feature:Feat-01",
            work_item={"id": "feature:Feat-01", "input_paths": [], "output_path": "/tmp/obs.json"},
            run_dir=self.tmp.name,
            input_paths=(),
            executor_result_path=str(Path(self.tmp.name) / "Feat-01.executor-result.json"),
            repo_root=self.settings.repo_root,
            skill_version="x",
            protocol_version="0.1.0",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _executor(self, runner: _FakeRunner) -> CodexCliExecutor:
        ex = CodexCliExecutor(self.config, schemas_root=self.settings.schemas_root, runner=runner)
        ex._available = True  # bypass the real codex --version probe
        return ex

    def _collected_events(self) -> list:
        out: list[C.ExecutionEvent] = []

        def emit(ev: C.ExecutionEvent) -> None:
            out.append(ev)

        return out, emit

    def test_success_returns_completed_and_writes_result(self) -> None:
        runner = _FakeRunner(
            result_doc=_result_doc(self.work.work_item_id),
            jsonl_lines=[
                '{"type":"message"}',
                '{"type":"turn.completed","usage":{"input_tokens":120,'
                '"cached_input_tokens":20,"output_tokens":30}}',
            ],
        )
        ex = self._executor(runner)
        out, emit = self._collected_events()
        result = ex.execute(self.work, emit)
        self.assertTrue(result.succeeded)
        self.assertEqual(result.status, C.STATUS_COMPLETED)
        self.assertEqual(result.executor_result_path, self.work.executor_result_path)
        self.assertEqual(result.observation, {"observation_id": self.work.work_item_id})
        self.assertTrue(result.usage_reported)
        self.assertEqual(
            result.token_usage,
            {
                "input_tokens": 120,
                "cached_input_tokens": 20,
                "cache_write_input_tokens": 0,
                "output_tokens": 30,
                "reasoning_output_tokens": 0,
                "total_tokens": 150,
            },
        )
        # JSONL + command events were forwarded
        kinds = [e.kind for e in out]
        self.assertIn("command", kinds)
        self.assertIn("jsonl", kinds)

    def test_argv_uses_readonly_sandbox_ephemeral_and_stdin(self) -> None:
        runner = _FakeRunner(result_doc=_result_doc(self.work.work_item_id))
        ex = self._executor(runner)
        ex.execute(self.work, lambda e: None)
        argv = runner.last_argv
        self.assertIn("exec", argv)
        self.assertIn("--sandbox", argv)
        self.assertEqual(_argv_value(argv, "--sandbox"), "read-only")
        self.assertIn("--ephemeral", argv)
        self.assertIn("--json", argv)
        self.assertEqual(argv[-1], "-")  # stdin prompt
        self.assertEqual(_argv_value(argv, "--cd"), str(self.settings.repo_root))
        self.assertEqual(_argv_value(argv, "--add-dir"), self.work.run_dir)
        self.assertEqual(_argv_value(argv, "--output-last-message"), self.work.executor_result_path)

    def test_prompt_requests_only_executor_owned_payload_fields(self) -> None:
        work = replace(
            self.work,
            prompt_extras={
                "result_kind": "staged_observation_payload",
                "template_path": "/tmp/Feat-01.json",
                "payload_fields": [
                    "claim_reviews", "observations", "open_questions", "notes"
                ],
                "service_derived_fields": [
                    "status", "reviewed_claim_ids", "completed_checks"
                ],
            },
        )
        runner = _FakeRunner(result_doc=_result_doc(work.work_item_id))
        self._executor(runner).execute(work, lambda e: None)
        prompt = json.loads(runner.last_stdin or "{}")
        self.assertEqual(
            prompt["result_contract"]["result_kind"], "staged_observation_payload"
        )
        requirement = prompt["output"]["requirement"]
        self.assertIn("containing exactly these fields", requirement)
        self.assertIn("service-owned fields", requirement)
        self.assertNotIn("initialized identity, input", requirement)

    def test_repair_prompt_is_bounded_to_candidate_and_machine_contract(self) -> None:
        work = replace(
            self.work,
            input_paths=("/tmp/.Feat-01.json.candidate", "/tmp/Feat-01.json", "/tmp/output-contract.json"),
            prompt_extras={
                "mode": "repair_candidate",
                "result_kind": "staged_observation_payload",
                "template_path": "/tmp/Feat-01.json",
                "output_contract_path": "/tmp/output-contract.json",
                "candidate_path": "/tmp/.Feat-01.json.candidate",
                "validation_errors": ["evidence_id: invalid evidence ID"],
                "payload_fields": ["claim_reviews", "observations", "open_questions", "notes"],
                "service_derived_fields": ["status", "reviewed_claim_ids", "completed_checks"],
                "machine_contract": {"common": {"evidence": {"evidence_id_pattern": "^EV-"}}},
            },
        )
        runner = _FakeRunner(result_doc=_result_doc(work.work_item_id))
        self._executor(runner).execute(work, lambda e: None)
        prompt = json.loads(runner.last_stdin or "{}")
        self.assertIn("Repair one staged", prompt["task"])
        self.assertIn("do not redo semantic evaluation", " ".join(prompt["constraints"]))
        self.assertEqual(prompt["result_contract"]["mode"], "repair_candidate")

    def test_nonzero_exit_is_failed(self) -> None:
        runner = _FakeRunner(exit_code=2, write_result=False)
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIsNotNone(result.error)

    def test_missing_result_file_is_failed(self) -> None:
        runner = _FakeRunner(result_doc=_result_doc(self.work.work_item_id), write_result=False)
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)

    def test_bad_schema_result_is_failed(self) -> None:
        bad = {"schema_version": 2, "work_item_id": self.work.work_item_id}  # missing required fields
        runner = _FakeRunner(result_doc=bad)
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("schema", (result.error or "").lower())

    def test_invalid_observation_json_is_failed(self) -> None:
        document = _result_doc(self.work.work_item_id)
        document["observation_json"] = "not-json"
        result = self._executor(_FakeRunner(result_doc=document)).execute(
            self.work, lambda e: None
        )
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("observation_json", result.error or "")

    def test_reported_failed_status_is_not_promoted_to_completed(self) -> None:
        document = _result_doc(
            self.work.work_item_id, status="failed", error="cannot complete work item"
        )
        result = self._executor(_FakeRunner(result_doc=document)).execute(
            self.work, lambda e: None
        )
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertEqual(result.error, "cannot complete work item")

    def test_wrong_work_item_id_is_failed(self) -> None:
        runner = _FakeRunner(result_doc=_result_doc("feature:Feat-99"))
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)

    def test_timeout_is_reported(self) -> None:
        runner = _FakeRunner(timed_out=True, write_result=False)
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_TIMEOUT)

    def test_cancelled_is_reported(self) -> None:
        runner = _FakeRunner(
            cancelled=True,
            write_result=False,
            jsonl_lines=[
                '{"type":"token_count","info":{"total_token_usage":'
                '{"input_tokens":42,"cached_input_tokens":8,"output_tokens":9,'
                '"reasoning_output_tokens":3,"total_tokens":51}}}',
            ],
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_CANCELLED)
        self.assertEqual(result.token_usage["total_tokens"], 51)
        self.assertTrue(result.usage_reported)

    def test_describe_masks_model_and_redacts(self) -> None:
        cfg = dict(self.config, model="secret-model")
        runner = _FakeRunner(result_doc=_result_doc(self.work.work_item_id))
        ex = CodexCliExecutor(cfg, schemas_root=self.settings.schemas_root, runner=runner)
        ex._available = True
        desc = ex.describe()
        self.assertEqual(desc["type"], "codex-cli")
        self.assertEqual(desc["model"], "secret-model")
        self.assertEqual(desc["sandbox"], "read-only")
        # command argv logging masks the --model value
        masked: list[str] = []
        ex.execute(self.work, lambda e: masked.append(e.message))
        cmd_line = next(m for m in masked if m.startswith("codex"))
        self.assertIn("<redacted>", cmd_line)
        self.assertNotIn("secret-model", cmd_line)

    def test_is_available_false_for_missing_command(self) -> None:
        cfg = dict(self.config, command="definitely-not-a-real-codex-binary-xyz")
        ex = CodexCliExecutor(cfg, schemas_root=self.settings.schemas_root)
        self.assertFalse(ex.is_available())
        result = ex.execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_AWAITING)

    def test_invalid_output_schema_fails_before_executor_start(self) -> None:
        schemas_root = Path(self.tmp.name) / "schemas"
        schemas_root.mkdir()
        (schemas_root / "invalid.json").write_text(
            json.dumps({
                "type": "object",
                "required": ["payload"],
                "properties": {"payload": {"type": "object"}},
                "additionalProperties": False,
            }),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "not strict"):
            CodexCliExecutor(
                dict(self.config, output_schema="invalid.json"),
                schemas_root=schemas_root,
                runner=_FakeRunner(),
            )


class StrictOutputSchemaTest(unittest.TestCase):
    def test_executor_result_schema_is_strict(self) -> None:
        root = ServiceSettings.discover().schemas_root
        schema = json.loads((root / "executor-result.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_strict_output_schema(schema), [])

    def test_nested_open_object_and_optional_property_are_rejected(self) -> None:
        schema = {
            "type": "object",
            "required": ["payload"],
            "properties": {
                "payload": {
                    "type": "object",
                    "properties": {"value": {"type": "string"}},
                },
                "notes": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        }
        errors = validate_strict_output_schema(schema)
        self.assertTrue(any("$.required" in error and "notes" in error for error in errors))
        self.assertTrue(
            any("$.properties.payload.additionalProperties" in error for error in errors)
        )


class RedactionTest(unittest.TestCase):
    def test_redacts_token_in_jsonl(self) -> None:
        line = '{"msg":"Authorization: Bearer sk-abcdef1234567890", "n":1}'
        out = redact_jsonl(line)
        self.assertNotIn("sk-abcdef1234567890", out)
        self.assertIn("<redacted>", out)

    def test_preserves_non_secret_jsonl(self) -> None:
        line = '{"type":"message","content":"hello"}'
        self.assertEqual(json.loads(redact_jsonl(line)), json.loads(line))

    def test_redacts_plain_text(self) -> None:
        out = redact_jsonl("not json token=sk-abcdefghijklmnop1234567890 trailing")
        self.assertNotIn("sk-abcdefghijklmnop1234567890", out)


if __name__ == "__main__":
    unittest.main()
