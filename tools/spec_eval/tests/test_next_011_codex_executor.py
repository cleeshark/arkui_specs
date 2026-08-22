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
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.service.executors import contract as C
from spec_eval.service.executors.codex_cli import CodexCliExecutor
from spec_eval.service.executors.process import ProcessResult
from spec_eval.service.executors.redaction import redact_jsonl
from spec_eval.service.settings import ServiceSettings


def _write_v3_envelope_schema(directory: str) -> str:
    """Write a minimal v3 envelope schema for validation tests."""
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["schema_version", "work_item_id", "status", "payload", "notes", "error"],
        "properties": {
            "schema_version": {"type": "integer", "const": 3},
            "work_item_id": {"type": "string", "minLength": 1},
            "status": {"type": "string", "enum": ["completed", "failed"]},
            "payload": {},
            "notes": {"type": "array", "items": {"type": "string"}},
            "error": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    }
    path = str(Path(directory) / "envelope-observation.schema.json")
    Path(path).write_text(json.dumps(schema), encoding="utf-8")
    return path


def _result_doc(
    work_item_id: str,
    *,
    observation: dict | None = None,
    status: str = "completed",
    error: str | None = None,
) -> dict:
    return {
        "schema_version": 3,
        "work_item_id": work_item_id,
        "status": status,
        "payload": (
            observation if observation is not None else {"observation_id": work_item_id}
        )
        if status == "completed"
        else None,
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
        self.assertTrue(result.telemetry_reported)
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

    def test_stable_codex_item_events_report_tool_and_input_path_counts(self) -> None:
        evidence_path = Path(self.tmp.name) / "input" / "evidence" / "Feat-01.json"
        evidence_path.parent.mkdir(parents=True)
        evidence_path.write_text("{}", encoding="utf-8")
        work = replace(self.work, input_paths=(str(evidence_path),))
        runner = _FakeRunner(
            result_doc=_result_doc(work.work_item_id),
            jsonl_lines=[
                '{"type":"thread.started"}',
                json.dumps({
                    "type": "item.completed",
                    "item": {
                        "type": "command_execution",
                        "command": f"sed -n '1,40p' {evidence_path}",
                    },
                }),
            ],
        )
        result = self._executor(runner).execute(work, lambda event: None)
        self.assertTrue(result.telemetry_reported)
        self.assertEqual(result.telemetry["tool_calls"], 1)
        self.assertEqual(result.telemetry["command_calls"], 1)
        self.assertEqual(result.telemetry["input_paths_accessed"], 1)
        self.assertEqual(result.telemetry["evidence_paths_accessed"], 1)

    def test_unknown_jsonl_shape_leaves_telemetry_unavailable(self) -> None:
        runner = _FakeRunner(
            result_doc=_result_doc(self.work.work_item_id),
            jsonl_lines=['{"type":"future.unknown","tool":"shell"}'],
        )
        result = self._executor(runner).execute(self.work, lambda event: None)
        self.assertFalse(result.telemetry_reported)
        self.assertEqual(result.telemetry["command_calls"], 0)

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

    def test_observe_prompt_is_normative_machine_contract(self) -> None:
        schema_path = _write_v3_envelope_schema(self.tmp.name)
        work = replace(
            self.work,
            work_item={
                **self.work.work_item,
                "expected_claim_ids": ["Feat-01/AC-1"],
                "required_checks": ["claim_source_support"],
                "input_resources": [{
                    "path": "/tmp/input/evidence/Feat-01.json",
                    "role": "semantic_input",
                    "citable": False,
                }, {
                    "path": "/tmp/specs/Feat-01-spec.md",
                    "role": "frozen_evidence",
                    "citable": True,
                    "canonical_path": "specs/Feat-01-spec.md",
                }],
            },
            input_paths=("/tmp/input/evidence/Feat-01.json", "/tmp/specs/Feat-01-spec.md"),
            prompt_extras={
                "mode": "observe",
                "evaluation_protocol_version": "0.2.0",
                "result_kind": "staged_observation_judgments",
                "payload_kind": "observation",
                "payload_fields": [
                    "evidence_declarations", "claim_reviews", "observations",
                    "open_questions", "notes",
                ],
                "service_derived_fields": ["ordering", "stable evidence IDs"],
                "schema_path": schema_path,
                "template_path": "/tmp/Feat-01.json",
                "phase_references": [{
                    "name": "observation-contract",
                    "path": "/tmp/references/observation-contract.md",
                    "content_hash": "sha256:" + "a" * 64,
                    "content": "Inspect frozen source before judging implementation claims.",
                }],
                "machine_contract": {
                    "expected_claim_ids": ["Feat-01/AC-1"],
                    "judgment_rules": ["evidence via declarations and refs"],
                },
            },
        )
        runner = _FakeRunner(result_doc=_result_doc(work.work_item_id))
        self._executor(runner).execute(work, lambda e: None)
        prompt = json.loads(runner.last_stdin or "{}")
        prompt_log = Path(work.executor_result_path).parent / "codex.feature_Feat-01.prompt.log"
        self.assertTrue(prompt_log.is_file())
        self.assertEqual(prompt_log.read_text(encoding="utf-8"), runner.last_stdin)
        self.assertIn("Produce one complete staged_observation_judgments payload", prompt["task"])
        constraints = " ".join(prompt["constraints"])
        self.assertIn("normative", constraints)
        self.assertIn("frozen source/SDK files", constraints)
        self.assertIn("forbidden_paths", constraints)
        self.assertIn("citable=false", constraints)
        self.assertIn("canonical repository-relative", constraints)
        self.assertEqual(prompt["input_resources"][0]["citable"], False)
        requirement = prompt["output"]["requirement"]
        self.assertIn("evidence_declarations", requirement)
        self.assertIn("evidence_refs", requirement)
        self.assertIn("never emit canonical EV- IDs", requirement)
        self.assertEqual(
            prompt["output"]["schema"], schema_path
        )
        self.assertEqual(
            prompt["machine_contract"]["expected_claim_ids"], ["Feat-01/AC-1"]
        )
        self.assertNotIn("expected_claim_ids", prompt["work_item"])
        self.assertNotIn("required_checks", prompt["work_item"])
        self.assertNotIn("input_resources", prompt["work_item"])
        self.assertNotIn("machine_contract", prompt["result_contract"])
        self.assertNotIn("phase_references", prompt["result_contract"])
        self.assertEqual(
            prompt["phase_references"][0]["name"], "observation-contract"
        )
        self.assertIn("already loaded", constraints)

    def test_correct_prompt_carries_candidate_and_typed_errors(self) -> None:
        schema_path = _write_v3_envelope_schema(self.tmp.name)
        work = replace(
            self.work,
            input_paths=("/tmp/run/.Feat-01.json.candidate", "/tmp/input/evidence/Feat-01.json"),
            prompt_extras={
                "mode": "correct",
                "evaluation_protocol_version": "0.2.0",
                "result_kind": "staged_observation_judgments",
                "payload_kind": "observation",
                "payload_fields": ["evidence_declarations", "claim_reviews", "observations"],
                "service_derived_fields": ["ordering"],
                "schema_path": schema_path,
                "candidate_path": "/tmp/run/.Feat-01.json.candidate",
                "typed_errors": [{
                    "code": "GAP_MISSING_FOR_NV",
                    "path": "claim_reviews[0].verification_gap",
                    "entity_type": "claim",
                    "entity_id": "Feat-01/AC-1",
                    "repairability": "MODEL_CORRECTION",
                }],
                "correction_constraints": ["Fix the reported judgments."],
                "phase_references": [{
                    "name": "observation-contract",
                    "content": "Normal observation instructions.",
                }],
                "machine_contract": {"expected_claim_ids": ["Feat-01/AC-1"]},
            },
        )
        runner = _FakeRunner(result_doc=_result_doc(work.work_item_id))
        self._executor(runner).execute(work, lambda e: None)
        prompt = json.loads(runner.last_stdin or "{}")
        self.assertIn("Correct one staged_observation_judgments candidate", prompt["task"])
        constraints = " ".join(prompt["constraints"])
        self.assertIn("candidate_path", constraints)
        self.assertIn("typed_errors", constraints)
        self.assertIn("RFC-6902-style add/remove/replace patches", constraints)
        self.assertIn("NEVER read SKILL.md", constraints)
        contract = prompt["result_contract"]
        self.assertEqual(prompt["phase_references"], [])
        self.assertEqual(
            contract["candidate_path"], "/tmp/run/.Feat-01.json.candidate"
        )
        self.assertEqual(
            contract["typed_errors"][0]["code"], "GAP_MISSING_FOR_NV"
        )

    def test_aggregation_prompt_uses_inherited_canonical_evidence(self) -> None:
        schema_path = _write_v3_envelope_schema(self.tmp.name)
        context_path = str(Path(self.tmp.name) / "aggregation-context.json")
        work = replace(
            self.work,
            work_item_id="function-aggregation",
            input_paths=(context_path,),
            prompt_extras={
                "mode": "observe",
                "evaluation_protocol_version": "0.2.0",
                "result_kind": "aggregation_judgments",
                "payload_kind": "aggregation",
                "payload_fields": [
                    "cross_feat_contracts_reviewed", "contradiction_bases",
                    "defect_ownership", "outcome_policy_bases",
                    "criterion_results", "notes",
                ],
                "schema_path": schema_path,
                "machine_contract": {
                    "aggregation_context_path": context_path,
                    "criterion_evidence_rule": "Use canonical Criterion evidence.",
                },
            },
        )
        runner = _FakeRunner(result_doc=_result_doc(work.work_item_id))
        self._executor(runner).execute(work, lambda event: None)
        prompt = json.loads(runner.last_stdin or "{}")
        requirement = prompt["output"]["requirement"]
        self.assertIn("canonical EV- IDs", requirement)
        self.assertIn("aggregation-context.json", requirement)
        self.assertIn("do not emit evidence_declarations", requirement)
        self.assertNotIn("never emit canonical EV- IDs", requirement)
        constraints = " ".join(prompt["constraints"])
        self.assertNotIn("Re-declare every piece of evidence", constraints)


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
        bad = {"schema_version": 2, "work_item_id": self.work.work_item_id}  # wrong version + missing fields
        runner = _FakeRunner(result_doc=bad)
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("schema", (result.error or "").lower())

    def test_invalid_payload_type_is_failed(self) -> None:
        document = _result_doc(self.work.work_item_id)
        document["payload"] = "not-an-object"
        result = self._executor(_FakeRunner(result_doc=document)).execute(
            self.work, lambda e: None
        )
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("payload", result.error or "")

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

    def test_generated_aggregation_schema_is_checked_at_executor_startup(self) -> None:
        original = build_envelope_schema

        def generated(kind: str) -> dict:
            schema = original(kind)
            if kind == "aggregation":
                schema["uniqueItems"] = True
            return schema

        with patch(
            "spec_eval.service.executors.codex_cli.build_envelope_schema",
            side_effect=generated,
        ):
            with self.assertRaisesRegex(
                ValueError, "generated aggregation output schema is not compatible"
            ):
                CodexCliExecutor(
                    self.config,
                    schemas_root=self.settings.schemas_root,
                    runner=_FakeRunner(),
                )

    def test_invalid_work_schema_is_rejected_without_starting_runner(self) -> None:
        schema_path = Path(_write_v3_envelope_schema(self.tmp.name))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        schema["uniqueItems"] = True
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        work = replace(
            self.work,
            prompt_extras={"schema_path": str(schema_path)},
        )
        runner = _FakeRunner(result_doc=_result_doc(work.work_item_id))
        result = self._executor(runner).execute(work, lambda event: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("uniqueItems", result.error or "")
        self.assertIsNone(runner.last_argv)


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
