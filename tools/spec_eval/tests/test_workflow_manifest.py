"""Unit tests for workflow_manifest.py (P2 of the workflow-shards design).

Run from specs/tools/:

    PYTHONPATH=. python3 -m unittest spec_eval.tests.test_workflow_manifest -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from spec_eval.service.executors.workflow_manifest import (
    ManifestSpec,
    _DEFAULT_OUTPUT_RULES,
    build_manifest,
    make_spec_from_work_item,
    safe_filename,
    write_manifest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_CRITERION_IDS = [
    "CORRECTNESS-SOURCE-SUPPORT",
    "CORRECTNESS-SDK-CONTRACT",
    "CORRECTNESS-BOUNDARY-STATE",
    "CORRECTNESS-CROSS-DOC-CONSISTENCY",
    "SPEC-AC-TESTABILITY",
    "SPEC-RULE-COMPLETENESS",
    "SPEC-TRACEABILITY",
    "SPEC-SCOPE-BOUNDARY",
    "DESIGN-IMPLEMENTATION-PATH",
    "DESIGN-FEAT-RUNTIME-COVERAGE",
    "DESIGN-ALGORITHM-DATA-STATE",
    "DESIGN-DECISION-QUALITY",
    "DESIGN-IMPACT-COVERAGE",
    "DESIGN-VERIFICATION-PLAN",
    "COMPATIBILITY-API-VERSION",
    "COMPATIBILITY-SYSTEM-IMPACT",
    "COMPATIBILITY-MULTI-DEVICE",
    "FUNCTION-FEAT-COVERAGE",
    "FUNCTION-FEAT-DECOMPOSITION",
    "FUNCTION-FEAT-BOUNDARY",
]

_CLAIM_IDS = [
    "Feat-01/AC-1.1",
    "Feat-01/AC-1.2",
    "Feat-01/R-1",
    "Feat-01/API-139",
    "Feat-01/NFR-204",
    "Feat-01/COMPATIBILITY-183",
]

_WORK_ITEM = {
    "id": "feature:Feat-01",
    "type": "feature",
    "observation_profile": "feature",
    "feat_id": "Feat-01",
    "status": "pending",
    "expected_claim_ids": _CLAIM_IDS,
    "required_checks": [
        "claim_source_support",
        "boundary_state",
        "ac_testability",
        "rule_completeness",
        "runtime_design",
        "compatibility_scope",
        "feat_ownership",
        "evidence_reproducibility",
    ],
    "execution_state": "GENERATE_PENDING",
}


def _make_spec(**overrides) -> ManifestSpec:
    defaults = dict(
        feat_id="Feat-01",
        work_item_id="feature:Feat-01",
        expected_claim_ids=list(_CLAIM_IDS),
        valid_criterion_ids=list(_VALID_CRITERION_IDS),
        output_rules=dict(_DEFAULT_OUTPUT_RULES),
    )
    defaults.update(overrides)
    return ManifestSpec(**defaults)


# ---------------------------------------------------------------------------
# Tests: safe_filename
# ---------------------------------------------------------------------------

class TestSafeFilename(unittest.TestCase):
    def test_slash_replaced(self):
        self.assertEqual(safe_filename("Feat-01/AC-1.1"), "Feat-01__AC-1.1")

    def test_no_slash_unchanged(self):
        self.assertEqual(
            safe_filename("CORRECTNESS-SOURCE-SUPPORT"),
            "CORRECTNESS-SOURCE-SUPPORT",
        )

    def test_backslash_also_replaced(self):
        self.assertNotIn("\\", safe_filename("Feat-01\\AC-1.1"))

    def test_multiple_slashes(self):
        self.assertEqual(safe_filename("a/b/c"), "a__b__c")


# ---------------------------------------------------------------------------
# Tests: build_manifest
# ---------------------------------------------------------------------------

class TestBuildManifest(unittest.TestCase):
    def setUp(self):
        self.spec = _make_spec()
        self.manifest = build_manifest(self.spec)

    def test_shard_schemas_keys(self):
        self.assertIn("shard_schemas", self.manifest)
        ss = self.manifest["shard_schemas"]
        self.assertIn("claim_schema", ss)
        self.assertIn("criterion_item_schema", ss)
        self.assertIn("aux_schema", ss)
        self.assertIn("validate_script", ss)

    def test_feat_id(self):
        self.assertEqual(self.manifest["feat_id"], "Feat-01")

    def test_work_item_id(self):
        self.assertEqual(self.manifest["work_item_id"], "feature:Feat-01")

    def test_schema_version(self):
        self.assertEqual(self.manifest["schema_version"], 1)

    def test_aux_file(self):
        self.assertEqual(self.manifest["aux_file"], "aux.json")

    def test_claim_units_count(self):
        self.assertEqual(len(self.manifest["claim_units"]), len(_CLAIM_IDS))

    def test_criterion_units_count(self):
        self.assertEqual(
            len(self.manifest["criterion_units"]), len(_VALID_CRITERION_IDS)
        )

    def test_claim_units_order_preserved(self):
        actual_ids = [u["claim_id"] for u in self.manifest["claim_units"]]
        self.assertEqual(actual_ids, _CLAIM_IDS)

    def test_criterion_units_order_preserved(self):
        actual_ids = [u["criterion_id"] for u in self.manifest["criterion_units"]]
        self.assertEqual(actual_ids, _VALID_CRITERION_IDS)

    def test_claim_unit_has_file(self):
        for u in self.manifest["claim_units"]:
            self.assertIn("file", u)
            self.assertTrue(u["file"].startswith("claims/"))

    def test_criterion_unit_has_file(self):
        for u in self.manifest["criterion_units"]:
            self.assertIn("file", u)
            self.assertTrue(u["file"].startswith("criteria/"))

    def test_claim_file_names_safe(self):
        for u in self.manifest["claim_units"]:
            self.assertNotIn("/", u["file"].split("/", 1)[1],
                msg=f"Claim file name contains bare slash: {u['file']}")

    def test_criterion_file_names_safe(self):
        for u in self.manifest["criterion_units"]:
            self.assertNotIn("/", u["file"].split("/", 1)[1],
                msg=f"Criterion file name contains bare slash: {u['file']}")

    def test_claim_unit_required_keys(self):
        for u in self.manifest["claim_units"]:
            self.assertIn("claim_id", u)
            self.assertIn("file", u)

    def test_criterion_unit_required_keys(self):
        for u in self.manifest["criterion_units"]:
            self.assertIn("criterion_id", u)
            self.assertIn("file", u)

    def test_output_rules_present(self):
        self.assertIsInstance(self.manifest["output_rules"], dict)
        self.assertGreater(len(self.manifest["output_rules"]), 0)

    def test_all_20_criteria_included(self):
        actual = {u["criterion_id"] for u in self.manifest["criterion_units"]}
        self.assertEqual(actual, set(_VALID_CRITERION_IDS))


# ---------------------------------------------------------------------------
# Tests: write_manifest
# ---------------------------------------------------------------------------

class TestWriteManifest(unittest.TestCase):
    def test_creates_manifest_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "shards"
            spec = _make_spec()
            manifest_path = write_manifest(shard_dir, spec)
            self.assertTrue(manifest_path.exists())
            self.assertEqual(manifest_path.name, "_manifest.json")

    def test_creates_claims_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "shards"
            write_manifest(shard_dir, _make_spec())
            self.assertTrue((shard_dir / "claims").is_dir())

    def test_creates_criteria_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "shards"
            write_manifest(shard_dir, _make_spec())
            self.assertTrue((shard_dir / "criteria").is_dir())

    def test_manifest_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "shards"
            manifest_path = write_manifest(shard_dir, _make_spec())
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIsInstance(data, dict)

    def test_manifest_content_matches_build_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "shards"
            spec = _make_spec()
            manifest_path = write_manifest(shard_dir, spec)
            written = json.loads(manifest_path.read_text(encoding="utf-8"))
            expected = build_manifest(spec)
            self.assertEqual(written, expected)

    def test_idempotent_on_second_call(self):
        """Calling write_manifest twice on the same dir should not raise."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "shards"
            spec = _make_spec()
            write_manifest(shard_dir, spec)
            # Second call — should overwrite cleanly
            manifest_path = write_manifest(shard_dir, spec)
            self.assertTrue(manifest_path.exists())


# ---------------------------------------------------------------------------
# Tests: make_spec_from_work_item
# ---------------------------------------------------------------------------

class TestMakeSpecFromWorkItem(unittest.TestCase):
    def test_feat_id(self):
        spec = make_spec_from_work_item(_WORK_ITEM, _VALID_CRITERION_IDS)
        self.assertEqual(spec.feat_id, "Feat-01")

    def test_work_item_id(self):
        spec = make_spec_from_work_item(_WORK_ITEM, _VALID_CRITERION_IDS)
        self.assertEqual(spec.work_item_id, "feature:Feat-01")

    def test_claim_ids_match(self):
        spec = make_spec_from_work_item(_WORK_ITEM, _VALID_CRITERION_IDS)
        self.assertEqual(spec.expected_claim_ids, _CLAIM_IDS)

    def test_criterion_ids_match(self):
        spec = make_spec_from_work_item(_WORK_ITEM, _VALID_CRITERION_IDS)
        self.assertEqual(spec.valid_criterion_ids, list(_VALID_CRITERION_IDS))

    def test_default_output_rules_used_when_none(self):
        spec = make_spec_from_work_item(_WORK_ITEM, _VALID_CRITERION_IDS)
        self.assertEqual(spec.output_rules, _DEFAULT_OUTPUT_RULES)

    def test_custom_output_rules_respected(self):
        custom = {"language": "English only"}
        spec = make_spec_from_work_item(
            _WORK_ITEM, _VALID_CRITERION_IDS, output_rules=custom
        )
        self.assertEqual(spec.output_rules, custom)


class TestFunctionGlobalWorkItem(unittest.TestCase):
    """Function-global work items have no feat_id; id is used instead.

    Regression for real failure: 'cannot prepare workflow manifest: feat_id'.
    """

    _FG_WORK_ITEM = {
        "id": "function-global",
        "type": "function_global",
        "observation_profile": "function_global",
        "status": "pending",
        # NOTE: no "feat_id" key at all
        "expected_claim_ids": [
            "Func/GLOBAL-1", "Func/GLOBAL-2", "Func/GLOBAL-3",
        ],
        "required_checks": ["registry_and_cross_doc", "traceability_graph"],
    }

    def test_make_spec_falls_back_to_id(self):
        spec = make_spec_from_work_item(
            self._FG_WORK_ITEM, _VALID_CRITERION_IDS
        )
        self.assertEqual(spec.feat_id, "function-global")
        self.assertEqual(spec.work_item_id, "function-global")

    def test_make_spec_null_feat_id_falls_back(self):
        wi = dict(self._FG_WORK_ITEM, feat_id=None)
        spec = make_spec_from_work_item(wi, _VALID_CRITERION_IDS)
        self.assertEqual(spec.feat_id, "function-global")

    def test_build_manifest_no_keyerror(self):
        spec = make_spec_from_work_item(
            self._FG_WORK_ITEM, _VALID_CRITERION_IDS
        )
        manifest = build_manifest(spec)
        self.assertEqual(manifest["feat_id"], "function-global")
        self.assertEqual(len(manifest["claim_units"]), 3)
        self.assertEqual(len(manifest["criterion_units"]), 20)

    def test_write_manifest_creates_shard_tree(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir) / "function-global"
            spec = make_spec_from_work_item(
                self._FG_WORK_ITEM, _VALID_CRITERION_IDS
            )
            manifest_path = write_manifest(shard_dir, spec)
            self.assertTrue(manifest_path.exists())
            self.assertTrue((shard_dir / "claims").is_dir())
            self.assertTrue((shard_dir / "criteria").is_dir())


# ---------------------------------------------------------------------------
# Integration: manifest produced from real job work-item is
# compatible with workflow_synthesis (round-trip shape check)
# ---------------------------------------------------------------------------

class TestManifestRoundTripWithRealJobData(unittest.TestCase):
    """Build a manifest from the actual failed job's work-item, then verify
    that workflow_synthesis.synthesize() can consume it (with empty shard dirs,
    we expect a SynthesisError listing all claim/criterion units as missing —
    not a crash)."""

    _WORK_ITEMS_PATH = Path(
        "/home/sunfei/workspace/openHarmony/foundation/arkui/ace_engine/specs"
        "/.evaluator/service-data/jobs/bb27674471d5209683afdd12"
        "/runs/run-1/staged/work-items.json"
    )
    _OUTPUT_CONTRACT_PATH = Path(
        "/home/sunfei/workspace/openHarmony/foundation/arkui/ace_engine/specs"
        "/.evaluator/service-data/jobs/bb27674471d5209683afdd12"
        "/runs/run-1/staged/output-contract.json"
    )

    def setUp(self):
        if not self._WORK_ITEMS_PATH.exists():
            self.skipTest("Real job data not found; skipping.")

    def test_manifest_generated_from_real_feat01(self):
        work_items = json.loads(
            self._WORK_ITEMS_PATH.read_text(encoding="utf-8")
        )
        output_contract = json.loads(
            self._OUTPUT_CONTRACT_PATH.read_text(encoding="utf-8")
        )
        feat01 = next(
            i for i in work_items["items"] if i["id"] == "feature:Feat-01"
        )
        valid_criterion_ids = output_contract["valid_criterion_ids"]

        spec = make_spec_from_work_item(feat01, valid_criterion_ids)
        manifest = build_manifest(spec)

        # Claim count matches expected_claim_ids
        self.assertEqual(
            len(manifest["claim_units"]),
            len(feat01["expected_claim_ids"]),
        )
        # Criterion count is the full 20
        self.assertEqual(len(manifest["criterion_units"]), 20)
        # All claim IDs preserved and in order
        self.assertEqual(
            [u["claim_id"] for u in manifest["claim_units"]],
            feat01["expected_claim_ids"],
        )
        # All criterion IDs preserved and in order
        self.assertEqual(
            [u["criterion_id"] for u in manifest["criterion_units"]],
            valid_criterion_ids,
        )

    def test_empty_shards_produce_synthesis_error_with_correct_units(self):
        """write_manifest + synthesize with empty shard dirs →
        SynthesisError listing every claim and criterion as missing."""
        from spec_eval.service.executors.workflow_synthesis import (
            SynthesisError,
            synthesize,
        )

        work_items = json.loads(
            self._WORK_ITEMS_PATH.read_text(encoding="utf-8")
        )
        output_contract = json.loads(
            self._OUTPUT_CONTRACT_PATH.read_text(encoding="utf-8")
        )
        feat01 = next(
            i for i in work_items["items"] if i["id"] == "feature:Feat-01"
        )
        valid_criterion_ids = output_contract["valid_criterion_ids"]

        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            spec = make_spec_from_work_item(feat01, valid_criterion_ids)
            manifest_path = write_manifest(shard_dir, spec)

            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, feat01["id"])

            # Every claim and criterion should appear as a missing error
            error_unit_ids = {e.unit_id for e in ctx.exception.shard_errors}
            for cid in feat01["expected_claim_ids"]:
                self.assertIn(
                    cid, error_unit_ids,
                    msg=f"Expected missing claim {cid} in shard_errors",
                )
            for crid in valid_criterion_ids:
                self.assertIn(
                    crid, error_unit_ids,
                    msg=f"Expected missing criterion {crid} in shard_errors",
                )


if __name__ == "__main__":
    unittest.main()
