"""Tests for the Claude-only workflow-shards observation prompt (P3).

Verifies:
* The new output_transport="workflow_shards" branch produces a disk-driven
  workflow prompt with a tiny completion-signal output (not a big payload).
* C1/C3: the existing canonical_envelope (codex) and payload_root (claude
  one-shot) branches are byte-for-byte unchanged by the new branch.
* The shard directory convention is a single source of truth.

Run from specs/tools/:

    PYTHONPATH=. python3 -m unittest spec_eval.tests.test_workflow_prompt -v
"""

from __future__ import annotations

import json
import unittest

from spec_eval.service.executors import contract as C
from spec_eval.service.executors._prompt import (
    build_executor_prompt,
    workflow_shard_dir,
)


def _work(
    prompt_extras: dict | None = None,
    *,
    work_item: dict | None = None,
    run_dir: str = "/tmp/run",
) -> C.WorkItemInput:
    return C.WorkItemInput(
        job_id="job-1",
        func_id="03-05-02",
        run_id="run-1",
        work_item_id="feature:Feat-01",
        work_item=work_item if work_item is not None else {
            "kind": "feature",
            "feat_id": "Feat-01",
            "expected_claim_ids": ["Feat-01/AC-1.1", "Feat-01/R-1"],
        },
        run_dir=run_dir,
        input_paths=("/tmp/repo/foo.cpp",),
        executor_result_path="/tmp/out.json",
        repo_root="/tmp/repo",
        skill_version="skill@test",
        protocol_version="0.2.0",
        prompt_extras=prompt_extras if prompt_extras is not None else {
            "mode": "observe",
            "observation_profile": "feature",
        },
    )


class TestWorkflowShardDir(unittest.TestCase):
    """The shard-dir convention is deterministic and stable."""

    def test_path_convention(self):
        self.assertEqual(
            workflow_shard_dir("/tmp/run", "Feat-01"),
            "/tmp/run/observations/Feat-01",
        )

    def test_no_trailing_slash(self):
        self.assertFalse(workflow_shard_dir("/tmp/run/", "Feat-01").endswith("/"))

    def test_feat_id_used(self):
        self.assertIn("Feat-02", workflow_shard_dir("/tmp/run", "Feat-02"))


class TestUnknownTransportRejected(unittest.TestCase):
    def test_bad_transport_raises(self):
        with self.assertRaises(ValueError):
            build_executor_prompt(_work(), output_transport="bogus")


class TestWorkflowShardsPrompt(unittest.TestCase):
    """The workflow_shards branch drives a disk-based workflow."""

    def _prompt(self, **kw) -> dict:
        raw = build_executor_prompt(
            _work(**kw), output_transport="workflow_shards"
        )
        return json.loads(raw)

    def test_returns_valid_json(self):
        self.assertIsInstance(self._prompt(), dict)

    def test_output_transport_is_workflow_shards(self):
        p = self._prompt()
        self.assertEqual(p["output"]["transport"], "workflow_shards")

    def test_output_is_completion_signal_not_payload(self):
        p = self._prompt()
        req = p["output"]["requirement"]
        self.assertIn("Do NOT emit the observation payload", req)
        self.assertIn("completion signal", req)

    def test_output_names_signal_fields(self):
        p = self._prompt()
        req = p["output"]["requirement"]
        for field in (
            "status", "written_claim_files", "written_criterion_files",
            "aux_written", "error",
        ):
            self.assertIn(field, req)

    def test_manifest_path_present(self):
        p = self._prompt()
        self.assertIn("manifest", p)
        self.assertTrue(p["manifest"]["path"].endswith("/_manifest.json"))

    def test_shard_dir_matches_convention(self):
        p = self._prompt()
        expected = workflow_shard_dir("/tmp/run", "Feat-01")
        self.assertEqual(p["output"]["shard_dir"], expected)
        self.assertEqual(p["manifest"]["shard_dir"], expected)

    def test_result_contract_marks_transport(self):
        p = self._prompt()
        self.assertEqual(
            p["result_contract"]["output_transport"], "workflow_shards"
        )

    def test_disk_is_source_of_truth_rule(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn("DISK IS THE ONLY SOURCE OF TRUTH", text)

    def test_self_recovery_reread_manifest(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn("start of EVERY unit", text)
        self.assertIn("cat", text)

    def test_atomic_write_rule(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn(".tmp", text)

    def test_chinese_output_rule_present(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn("Simplified Chinese", text)

    def test_no_dump_rule_present(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn("Never print, cat", text)

    def test_criterion_empty_array_when_na(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn("empty array", text)

    def test_feature_scope_note(self):
        p = self._prompt()
        text = " ".join(p["constraints"])
        self.assertIn("Feature Observation", text)

    def test_function_global_scope_note(self):
        p = self._prompt(prompt_extras={
            "mode": "observe",
            "observation_profile": "function_global",
        })
        text = " ".join(p["constraints"])
        self.assertIn("Function-global Observation", text)

    def test_forbidden_paths_forwarded(self):
        p = self._prompt()
        self.assertIn("forbidden_paths", p)

    def test_machine_contract_forwarded(self):
        extras = {
            "mode": "observe",
            "observation_profile": "feature",
            "machine_contract": {"sentinel": "abc"},
        }
        p = self._prompt(prompt_extras=extras)
        self.assertEqual(p["machine_contract"], {"sentinel": "abc"})

    def test_feat_id_falls_back_to_work_item_id(self):
        # work_item without feat_id → use work_item_id for the shard dir
        p = self._prompt(work_item={"kind": "feature"})
        # work_item_id is "feature:Feat-01"
        self.assertIn("feature:Feat-01", p["output"]["shard_dir"])


class TestExistingBranchesUnchanged(unittest.TestCase):
    """C1/C3: adding workflow_shards must not alter codex / payload_root."""

    def _extras(self) -> dict:
        return {
            "mode": "observe",
            "observation_profile": "feature",
            "result_kind": "staged_judgments",
            "payload_fields": ["claim_reviews", "observations",
                               "open_questions", "notes"],
            "schema_path": "envelope-observation.schema.json",
            "machine_contract": {"x": 1},
        }

    def test_canonical_envelope_still_builds(self):
        raw = build_executor_prompt(
            _work(prompt_extras=self._extras()),
            output_transport="canonical_envelope",
        )
        p = json.loads(raw)
        # canonical envelope path uses the "schema" output key + envelope fields
        self.assertEqual(p["output"]["transport"], "canonical_envelope")
        self.assertIn("schema", p["output"])
        self.assertIn("Return every envelope field", p["output"]["requirement"])

    def test_canonical_envelope_has_no_workflow_keys(self):
        raw = build_executor_prompt(
            _work(prompt_extras=self._extras()),
            output_transport="canonical_envelope",
        )
        p = json.loads(raw)
        self.assertNotIn("manifest", p)
        self.assertNotIn("shard_dir", p["output"])

    def test_payload_root_still_builds(self):
        raw = build_executor_prompt(
            _work(prompt_extras=self._extras()),
            output_transport="payload_root",
        )
        p = json.loads(raw)
        self.assertEqual(p["output"]["transport"], "payload_root")
        self.assertIn("structured-output", p["output"]["requirement"])

    def test_payload_root_has_no_workflow_keys(self):
        raw = build_executor_prompt(
            _work(prompt_extras=self._extras()),
            output_transport="payload_root",
        )
        p = json.loads(raw)
        self.assertNotIn("manifest", p)

    def test_default_transport_is_canonical_envelope(self):
        """Codex calls build_executor_prompt with no transport arg."""
        raw = build_executor_prompt(_work(prompt_extras=self._extras()))
        p = json.loads(raw)
        self.assertEqual(p["output"]["transport"], "canonical_envelope")


if __name__ == "__main__":
    unittest.main()
