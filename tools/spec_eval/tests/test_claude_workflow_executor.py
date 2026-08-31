"""Integration tests for the Claude workflow-shards observation path (P4).

Verifies the end-to-end wiring in ClaudeCliExecutor:
* observation work items take the workflow path (manifest pre-generated, argv
  gains Write, completion-signal schema, synthesis from shards);
* correction / aggregation keep the payload_root path (C1/C3);
* synthesis failures degrade to a per-unit-attributable executor failure.

The fake runner simulates a Claude session: it writes the shard files the model
would produce, then emits a stream-json result event carrying the tiny
completion signal as structured_output.

Run from specs/tools/:

    PYTHONPATH=. python3 -m unittest spec_eval.tests.test_claude_workflow_executor -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from spec_eval.kernel.schema_gen import write_envelope_schema
from spec_eval.service.executors import contract as C
from spec_eval.service.executors._prompt import workflow_shard_dir
from spec_eval.service.executors.claude_cli import (
    ClaudeCliExecutor,
    _use_workflow_shards,
    _workflow_signal_schema,
)
from spec_eval.service.executors.process import ProcessResult
from spec_eval.service.settings import ServiceSettings


# ---------------------------------------------------------------------------
# Judgment shard builders (valid shapes)
# ---------------------------------------------------------------------------

def _claim_shard(claim_id: str) -> dict:
    return {
        "claim_id": claim_id,
        "local_outcome": "SUPPORTED",
        "evidence_refs": ["e1"],
        "reason": "源码已确认",
        "verification_gap": None,
        "defect_keys": [],
        "unit_reviews": [],
    }


def _obs_item(criterion_id: str, claim_ids: list[str]) -> dict:
    return {
        "criterion_ids": [criterion_id],
        "check_ids": ["claim_source_support"],
        "claim_ids": claim_ids,
        "local_outcome": "SUPPORTED",
        "breadth": "feat_core",
        "contract_family": "test-family",
        "fact": "已验证",
        "defect_key": None,
        "primary_criterion_id": None,
        "evidence_refs": ["e1"],
    }


def _aux() -> dict:
    return {
        "evidence_declarations": [
            {
                "key": "e1",
                "type": "source_citation",
                "path": "adapter/foo.cpp",
                "lines": "1-10",
                "description": "证据",
            }
        ],
        "open_questions": [],
        "notes": [],
    }


def _stream_json_with_signal(signal: dict) -> str:
    """Build a minimal stream-json NDJSON carrying a completion signal."""
    lines = [
        json.dumps({"type": "system", "subtype": "init",
                    "session_id": "s1", "model": "claude-opus-4-6[1m]"}),
        json.dumps({
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "duration_ms": 100,
            "duration_api_ms": 80,
            "num_turns": 12,
            "session_id": "s1",
            "total_cost_usd": 0.5,
            "usage": {
                "input_tokens": 100, "output_tokens": 50,
                "cache_creation_input_tokens": 1000,
                "cache_read_input_tokens": 2000,
            },
            "structured_output": signal,
        }),
    ]
    return "\n".join(lines) + "\n"


_CLAIM_IDS = ["Feat-01/AC-1.1", "Feat-01/R-1"]
_CRIT_IDS = [
    "CORRECTNESS-SOURCE-SUPPORT",
    "SPEC-AC-TESTABILITY",
]


class _WorkflowFakeRunner:
    """Simulates a Claude session that writes shard files, then reports done.

    ``write_shards`` controls whether the "model" actually produces the shard
    files, letting tests exercise both the happy path and synthesis failure.
    """

    def __init__(
        self,
        *,
        run_dir: str,
        feat_id: str,
        write_shards: bool = True,
        signal_status: str = "completed",
        signal_error=None,
        omit_claim: str | None = None,
    ) -> None:
        self.run_dir = run_dir
        self.feat_id = feat_id
        self.write_shards = write_shards
        self.signal_status = signal_status
        self.signal_error = signal_error
        self.omit_claim = omit_claim
        self.last_argv: list[str] | None = None
        self.last_stdin: str | None = None

    def __call__(
        self, argv, *, cwd, stdin, timeout, stdout_log_path,
        stderr_log_path, cancel=None, line_sink=None, env=None,
    ):
        self.last_argv = list(argv)
        self.last_stdin = stdin

        shard_dir = Path(workflow_shard_dir(self.run_dir, self.feat_id))
        written_claims: list[str] = []
        written_criteria: list[str] = []
        aux_written = ""

        if self.write_shards:
            # The manifest + dirs were pre-created by the executor.
            manifest = json.loads(
                (shard_dir / "_manifest.json").read_text(encoding="utf-8")
            )
            for cu in manifest["claim_units"]:
                if cu["claim_id"] == self.omit_claim:
                    continue
                (shard_dir / cu["file"]).write_text(
                    json.dumps(_claim_shard(cu["claim_id"])),
                    encoding="utf-8",
                )
                written_claims.append(cu["file"])
            for cru in manifest["criterion_units"]:
                items = []
                # Only the two criteria we exercise get real observations;
                # the rest are NOT_APPLICABLE (empty array).
                if cru["criterion_id"] in _CRIT_IDS:
                    items = [_obs_item(cru["criterion_id"], _CLAIM_IDS)]
                (shard_dir / cru["file"]).write_text(
                    json.dumps(items), encoding="utf-8"
                )
                written_criteria.append(cru["file"])
            (shard_dir / manifest["aux_file"]).write_text(
                json.dumps(_aux()), encoding="utf-8"
            )
            aux_written = manifest["aux_file"]

        signal = {
            "status": self.signal_status,
            "written_claim_files": written_claims,
            "written_criterion_files": written_criteria,
            "aux_written": aux_written,
            "error": self.signal_error,
        }
        content = _stream_json_with_signal(signal)
        Path(stdout_log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(stdout_log_path).write_text(content, encoding="utf-8")
        Path(stderr_log_path).write_text("", encoding="utf-8")
        if line_sink is not None:
            for line in content.splitlines():
                line_sink(line)
        return ProcessResult(
            exit_code=0, timed_out=False, cancelled=False,
            elapsed_seconds=0.01,
            stdout_log_path=stdout_log_path, stderr_log_path=stderr_log_path,
        )


_VALID_CRITERION_IDS = [
    "CORRECTNESS-SOURCE-SUPPORT", "CORRECTNESS-SDK-CONTRACT",
    "CORRECTNESS-BOUNDARY-STATE", "CORRECTNESS-CROSS-DOC-CONSISTENCY",
    "SPEC-AC-TESTABILITY", "SPEC-RULE-COMPLETENESS", "SPEC-TRACEABILITY",
    "SPEC-SCOPE-BOUNDARY", "DESIGN-IMPLEMENTATION-PATH",
    "DESIGN-FEAT-RUNTIME-COVERAGE", "DESIGN-ALGORITHM-DATA-STATE",
    "DESIGN-DECISION-QUALITY", "DESIGN-IMPACT-COVERAGE",
    "DESIGN-VERIFICATION-PLAN", "COMPATIBILITY-API-VERSION",
    "COMPATIBILITY-SYSTEM-IMPACT", "COMPATIBILITY-MULTI-DEVICE",
    "FUNCTION-FEAT-COVERAGE", "FUNCTION-FEAT-DECOMPOSITION",
    "FUNCTION-FEAT-BOUNDARY",
]


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.config = {
            "type": "claude-cli",
            "command": "claude",
            "model": None,
            "permission_mode": "bypassPermissions",
            "timeout_seconds": 60,
            "max_output_tokens": 200_000,
            "output_schema": "executor-result.schema.json",
        }
        self.schema_path = write_envelope_schema(
            "observation",
            Path(self.tmp.name) / "envelope-observation.json",
            valid_criterion_ids=_VALID_CRITERION_IDS,
        )
        self.work = C.WorkItemInput(
            job_id="j1",
            func_id="03-05-02",
            run_id="run-1",
            work_item_id="feature:Feat-01",
            work_item={
                "id": "feature:Feat-01",
                "feat_id": "Feat-01",
                "expected_claim_ids": _CLAIM_IDS,
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
                "mode": "observe",
                "payload_kind": "observation",
                "result_kind": "staged_observation_judgments",
                "payload_fields": [
                    "evidence_declarations", "claim_reviews", "observations",
                    "open_questions", "notes",
                ],
                "machine_contract": {
                    "observation_profile": "feature",
                    "valid_criterion_ids": _VALID_CRITERION_IDS,
                },
            },
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _executor(self, runner) -> ClaudeCliExecutor:
        ex = ClaudeCliExecutor(
            self.config, schemas_root=self.settings.schemas_root, runner=runner,
        )
        ex._available = True
        return ex


# ---------------------------------------------------------------------------
# Trigger predicate
# ---------------------------------------------------------------------------

class TestUseWorkflowShards(_Base):
    def test_observation_uses_workflow(self):
        self.assertTrue(_use_workflow_shards(self.work))

    def test_correction_does_not(self):
        w = self.work
        w.prompt_extras["mode"] = "correct"
        self.assertFalse(_use_workflow_shards(w))

    def test_aggregation_does_not(self):
        w = self.work
        w.prompt_extras["payload_kind"] = "aggregation"
        self.assertFalse(_use_workflow_shards(w))

    def test_fallback_to_profile_when_no_payload_kind(self):
        w = self.work
        del w.prompt_extras["payload_kind"]
        self.assertTrue(_use_workflow_shards(w))


class TestWorkflowSignalSchema(unittest.TestCase):
    def test_schema_is_small_and_valid_json(self):
        content, meta = _workflow_signal_schema()
        parsed = json.loads(content)
        self.assertEqual(parsed["type"], "object")
        self.assertIn("status", parsed["properties"])
        self.assertEqual(meta["payload_transport"], "workflow_completion_signal")


# ---------------------------------------------------------------------------
# End-to-end happy path
# ---------------------------------------------------------------------------

class TestWorkflowHappyPath(_Base):
    def test_completed_and_synthesized(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_COMPLETED)

    def test_manifest_created_before_session(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
        )
        self._executor(runner).execute(self.work, lambda e: None)
        shard_dir = Path(workflow_shard_dir(self.tmp.name, "Feat-01"))
        self.assertTrue((shard_dir / "_manifest.json").exists())

    def test_argv_includes_write_tool(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
        )
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--allowedTools")
        self.assertIn("Write", runner.last_argv[idx + 1])

    def test_json_schema_is_completion_signal(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
        )
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--json-schema")
        parsed = json.loads(runner.last_argv[idx + 1])
        self.assertIn("written_claim_files", parsed["properties"])

    def test_result_file_is_valid_envelope(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
        )
        self._executor(runner).execute(self.work, lambda e: None)
        doc = json.loads(
            Path(self.work.executor_result_path).read_text(encoding="utf-8")
        )
        self.assertEqual(doc["work_item_id"], "feature:Feat-01")
        self.assertEqual(doc["status"], "completed")
        self.assertEqual(len(doc["payload"]["claim_reviews"]), len(_CLAIM_IDS))
        # Two criteria produced observations, rest are empty arrays.
        self.assertEqual(len(doc["payload"]["observations"]), len(_CRIT_IDS))

    def test_stream_json_still_used(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
        )
        self._executor(runner).execute(self.work, lambda e: None)
        idx = runner.last_argv.index("--output-format")
        self.assertEqual(runner.last_argv[idx + 1], "stream-json")


# ---------------------------------------------------------------------------
# Failure degradation
# ---------------------------------------------------------------------------

class TestWorkflowFailureDegradation(_Base):
    def test_missing_shard_fails_with_unit_attribution(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
            omit_claim="Feat-01/AC-1.1",
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("Feat-01/AC-1.1", result.error)

    def test_model_reported_failure_propagates(self):
        runner = _WorkflowFakeRunner(
            run_dir=self.tmp.name, feat_id="Feat-01",
            write_shards=False,
            signal_status="failed",
            signal_error="source unavailable",
        )
        result = self._executor(runner).execute(self.work, lambda e: None)
        self.assertEqual(result.status, C.STATUS_FAILED)
        self.assertIn("source unavailable", result.error)


# ---------------------------------------------------------------------------
# C1/C3: non-observation paths unchanged
# ---------------------------------------------------------------------------

class TestNonWorkflowPathsUnchanged(_Base):
    def test_correction_takes_payload_root(self):
        w = self.work
        w.prompt_extras["mode"] = "correct"
        # No shards written; a payload_root run would call the transport schema
        # path. We only assert the trigger predicate keeps it off the workflow.
        self.assertFalse(_use_workflow_shards(w))

    def test_aggregation_takes_payload_root(self):
        w = self.work
        w.prompt_extras["payload_kind"] = "aggregation"
        self.assertFalse(_use_workflow_shards(w))


if __name__ == "__main__":
    unittest.main()
