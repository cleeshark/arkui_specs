"""Tests for workflow_shard_schema evidence-path existence checking.

The validate_shard.py "aux" subcommand checks that every evidence_declarations
path resolves to a real file/dir in the frozen repos.  These tests build a
temporary fake ace_engine tree so they do not depend on a real checkout, and
run the generated script with cwd == that fake repo root (mirroring how the
Claude session runs it with cwd == work.repo_root).

Run from specs/tools/:

    PYTHONPATH=. python3 -m unittest spec_eval.tests.test_workflow_shard_schema -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from spec_eval.service.executors.workflow_shard_schema import (
    VALIDATE_SCRIPT_FILE,
    aux_shard_schema,
    claim_shard_schema,
    criterion_item_schema,
    write_shard_schemas,
)


def _evidence(path: str, *, key: str = "e1", etype: str = "source_citation",
              lines="1-10") -> dict:
    return {
        "key": key, "type": etype, "path": path,
        "lines": lines, "description": "证据",
    }


class TestSubSchemas(unittest.TestCase):
    def test_claim_schema_has_verification_gap_arrays(self):
        s = claim_shard_schema()
        vg = s["$defs"]["verificationGap"]["properties"]
        self.assertEqual(vg["checked_scope"]["type"], "array")
        self.assertEqual(vg["missing_evidence"]["type"], "array")

    def test_aux_schema_requires_three_arrays(self):
        s = aux_shard_schema()
        self.assertEqual(
            set(s["required"]),
            {"evidence_declarations", "open_questions", "notes"},
        )

    def test_criterion_item_schema_is_object(self):
        s = criterion_item_schema()
        self.assertEqual(s["type"], "object")


class TestEvidencePathCheck(unittest.TestCase):
    """validate_shard.py aux verifies evidence paths exist under a repo root."""

    def setUp(self):
        # Fake ace_engine tree deep enough for resolver.parents[2] to exist.
        self.tmp = tempfile.TemporaryDirectory()
        oh_root = Path(self.tmp.name) / "foundation" / "arkui"
        self.repo_root = oh_root / "ace_engine"
        # a real file the aux can reference
        real = self.repo_root / "adapter" / "preview" / "entrance"
        real.mkdir(parents=True)
        (real / "subwindow_preview.cpp").write_text("// src", encoding="utf-8")
        # a real directory for review_record
        (self.repo_root / "test" / "unittest" / "core").mkdir(parents=True)

        self.shard_dir = Path(self.tmp.name) / "shards"
        write_shard_schemas(self.shard_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def _run_aux(self, aux: dict):
        (self.shard_dir / "aux.json").write_text(
            json.dumps(aux), encoding="utf-8"
        )
        return subprocess.run(
            [sys.executable, str(self.shard_dir / VALIDATE_SCRIPT_FILE),
             "aux", str(self.shard_dir / "aux.json")],
            capture_output=True, text=True, cwd=str(self.repo_root),
            env={**os.environ, "PYTHONPATH": str(Path.cwd())},
        )

    def test_existing_path_passes(self):
        aux = {
            "evidence_declarations": [
                _evidence("adapter/preview/entrance/subwindow_preview.cpp"),
            ],
            "open_questions": [], "notes": [],
        }
        r = self._run_aux(aux)
        self.assertEqual(r.returncode, 0, msg=r.stdout)
        self.assertIn("OK", r.stdout)

    def test_nonexistent_path_fails(self):
        # The real job b80336 error: an extra "subwindow/" directory level.
        aux = {
            "evidence_declarations": [
                _evidence("adapter/preview/entrance/subwindow/subwindow_preview.cpp"),
            ],
            "open_questions": [], "notes": [],
        }
        r = self._run_aux(aux)
        self.assertEqual(r.returncode, 1)
        self.assertIn("EVIDENCE_PATH_NOT_FOUND", r.stdout)
        self.assertIn("subwindow_preview.cpp", r.stdout)

    def test_specs_path_rejected(self):
        aux = {
            "evidence_declarations": [
                _evidence(
                    "specs/03-engine-framework/design.md",
                    etype="spec_location",
                ),
            ],
            "open_questions": [], "notes": [],
        }
        r = self._run_aux(aux)
        self.assertEqual(r.returncode, 1)
        self.assertIn("evidence_declarations[0].path", r.stdout)

    def test_review_record_directory_passes(self):
        aux = {
            "evidence_declarations": [
                _evidence("test/unittest/core", etype="review_record", lines=None),
            ],
            "open_questions": [], "notes": [],
        }
        r = self._run_aux(aux)
        self.assertEqual(r.returncode, 0, msg=r.stdout)

    def test_schema_error_reported_before_path_check(self):
        # Missing required 'notes' key -> schema error, path check skipped.
        aux = {
            "evidence_declarations": [
                _evidence("adapter/preview/entrance/subwindow_preview.cpp"),
            ],
            "open_questions": [],
        }
        r = self._run_aux(aux)
        self.assertEqual(r.returncode, 1)
        self.assertIn("notes", r.stdout)

    def test_multiple_bad_paths_all_reported(self):
        aux = {
            "evidence_declarations": [
                _evidence("does/not/exist/a.cpp", key="e1"),
                _evidence("adapter/preview/entrance/subwindow_preview.cpp", key="e2"),
                _evidence("also/missing/b.h", key="e3"),
            ],
            "open_questions": [], "notes": [],
        }
        r = self._run_aux(aux)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[0].path", r.stdout)
        self.assertIn("[2].path", r.stdout)
        # the valid one (index 1) should not be reported
        self.assertNotIn("[1].path", r.stdout)


if __name__ == "__main__":
    unittest.main()
