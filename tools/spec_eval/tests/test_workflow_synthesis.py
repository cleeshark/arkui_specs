"""Unit tests for workflow_synthesis.py (P1 of the workflow-shards design).

No LLM calls, no network.  All tests run in a temporary directory.
Run from specs/tools/:

    PYTHONPATH=. python3 -m unittest spec_eval.tests.test_workflow_synthesis -v

Test strategy
-------------
* Happy-path: all shards present and valid → envelope is schema-compatible
  with a real successful sample.
* Missing shards: each missing file → a ShardError naming that unit.
* Invalid JSON: corrupt shard → ShardError with reason starting "not valid JSON"
* Schema mismatch: shard missing a required field → ShardError.
* claim_id mismatch inside shard → ShardError.
* criterion_id not in criterion_ids list → ShardError.
* All-errors collected: multiple bad units → all reported in one pass.
* Manifest ordering preserved in assembled claim_reviews / observations.
* Absent aux.json → empty evidence_declarations / open_questions / notes, no error.
* Envelope shape matches real sample key sets at every nesting level (C2 parity).
* Envelope passes JsonSchemaSubsetValidator with the real schema used in job
  bb27674471d5209683afdd12.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from spec_eval.kernel.contracts import (
    CLAIM_JUDGMENT_FIELDS,
    ENVELOPE_SCHEMA_VERSION,
    EVIDENCE_DECLARATION_FIELDS,
    OBSERVATION_JUDGMENT_ENTRY_FIELDS,
    OBSERVATION_JUDGMENT_FIELDS,
)
from spec_eval.kernel.schema_gen import build_envelope_schema
from spec_eval.protocol_validator import JsonSchemaSubsetValidator
from spec_eval.service.executors.workflow_synthesis import (
    ShardError,
    SynthesisError,
    SynthesisResult,
    synthesize,
)


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

_WORK_ITEM_ID = "feature:Feat-01"

# Minimal valid claim shard (all CLAIM_JUDGMENT_FIELDS present)
def _claim_shard(claim_id: str, outcome: str = "SUPPORTED") -> dict:
    return {
        "claim_id": claim_id,
        "local_outcome": outcome,
        "evidence_refs": ["e1"],
        "reason": "テスト理由",
        "verification_gap": None,
        "defect_keys": [],
        "unit_reviews": [],
    }


# Minimal valid observationJudgment item
def _obs_item(criterion_id: str, claim_ids: list[str]) -> dict:
    return {
        "criterion_ids": [criterion_id],
        "check_ids": ["claim_source_support"],
        "claim_ids": claim_ids,
        "local_outcome": "SUPPORTED",
        "breadth": "feat_core",
        "contract_family": "test-family",
        "fact": "测试事实",
        "defect_key": None,
        "primary_criterion_id": None,
        "evidence_refs": ["e1"],
    }


def _evidence_item(key: str = "e1") -> dict:
    return {
        "key": key,
        "type": "source_citation",
        "path": "adapter/ohos/entrance/subwindow/subwindow_ohos.cpp",
        "lines": "1-10",
        "description": "测试证据",
    }


def _build_manifest(
    shard_dir: Path,
    claim_ids: list[str],
    criterion_ids: list[str],
    aux_file: str = "aux.json",
) -> dict:
    claim_units = [
        {
            "claim_id": cid,
            "file": f"claims/claim-{cid.replace('/', '__')}.json",
        }
        for cid in claim_ids
    ]
    criterion_units = [
        {
            "criterion_id": crid,
            "file": f"criteria/obs-{crid}.json",
            "check_ids": ["claim_source_support"],
        }
        for crid in criterion_ids
    ]
    return {
        "feat_id": "Feat-01",
        "schema_version": 1,
        "claim_units": claim_units,
        "criterion_units": criterion_units,
        "aux_file": aux_file,
        "output_rules": {
            "language": "Simplified Chinese",
            "no_dump_large_json": True,
        },
    }


def _write_manifest(shard_dir: Path, manifest: dict) -> Path:
    p = shard_dir / "_manifest.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    return p


def _write_claim_shards(shard_dir: Path, claim_ids: list[str]) -> None:
    claims_dir = shard_dir / "claims"
    claims_dir.mkdir(exist_ok=True)
    for cid in claim_ids:
        fname = f"claim-{cid.replace('/', '__')}.json"
        (claims_dir / fname).write_text(
            json.dumps(_claim_shard(cid)), encoding="utf-8"
        )


def _write_criterion_shards(
    shard_dir: Path, criterion_ids: list[str], claim_ids: list[str]
) -> None:
    crit_dir = shard_dir / "criteria"
    crit_dir.mkdir(exist_ok=True)
    for crid in criterion_ids:
        fname = f"obs-{crid}.json"
        items = [_obs_item(crid, claim_ids)]
        (crit_dir / fname).write_text(json.dumps(items), encoding="utf-8")


def _write_aux(shard_dir: Path, evidence_keys: list[str] = None) -> None:
    keys = evidence_keys or ["e1"]
    aux = {
        "evidence_declarations": [_evidence_item(k) for k in keys],
        "open_questions": ["测试问题"],
        "notes": ["测试注释"],
    }
    (shard_dir / "aux.json").write_text(json.dumps(aux), encoding="utf-8")


def _build_full_fixture(
    shard_dir: Path,
    claim_ids: list[str],
    criterion_ids: list[str],
) -> Path:
    """Write all shards + manifest; return manifest path."""
    (shard_dir / "claims").mkdir(exist_ok=True)
    (shard_dir / "criteria").mkdir(exist_ok=True)
    _write_claim_shards(shard_dir, claim_ids)
    _write_criterion_shards(shard_dir, criterion_ids, claim_ids)
    _write_aux(shard_dir)
    manifest = _build_manifest(shard_dir, claim_ids, criterion_ids)
    return _write_manifest(shard_dir, manifest)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

_CLAIM_IDS = ["Feat-01/AC-1.1", "Feat-01/AC-1.2", "Feat-01/R-1"]
_CRIT_IDS = ["CORRECTNESS-SOURCE-SUPPORT", "SPEC-AC-TESTABILITY"]


class TestSynthesizeHappyPath(unittest.TestCase):
    """All shards present and valid → SynthesisResult returned."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.shard_dir = Path(self.tmp.name)
        self.manifest_path = _build_full_fixture(
            self.shard_dir, _CLAIM_IDS, _CRIT_IDS
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_returns_synthesis_result(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertIsInstance(result, SynthesisResult)

    def test_claim_count(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(result.claim_count, len(_CLAIM_IDS))

    def test_observation_count(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        # one obs item per criterion
        self.assertEqual(result.observation_count, len(_CRIT_IDS))

    def test_evidence_count(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(result.evidence_count, 1)

    def test_envelope_top_keys(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(
            set(result.envelope.keys()),
            {"schema_version", "work_item_id", "status", "payload", "notes", "error"},
        )

    def test_envelope_schema_version(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(result.envelope["schema_version"], ENVELOPE_SCHEMA_VERSION)

    def test_envelope_work_item_id(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(result.envelope["work_item_id"], _WORK_ITEM_ID)

    def test_envelope_status_completed(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(result.envelope["status"], "completed")

    def test_envelope_error_none(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertIsNone(result.envelope["error"])

    def test_payload_keys(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        self.assertEqual(
            set(result.envelope["payload"].keys()),
            set(OBSERVATION_JUDGMENT_FIELDS),
        )

    def test_claim_review_field_sets(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        for cr in result.envelope["payload"]["claim_reviews"]:
            self.assertEqual(set(cr.keys()), set(CLAIM_JUDGMENT_FIELDS))

    def test_observation_field_sets(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        for obs in result.envelope["payload"]["observations"]:
            self.assertEqual(set(obs.keys()), set(OBSERVATION_JUDGMENT_ENTRY_FIELDS))

    def test_evidence_declaration_field_sets(self):
        result = synthesize(self.manifest_path, _WORK_ITEM_ID)
        for ev in result.envelope["payload"]["evidence_declarations"]:
            self.assertEqual(set(ev.keys()), set(EVIDENCE_DECLARATION_FIELDS))


class TestSynthesizeManifestOrder(unittest.TestCase):
    """claim_reviews order follows manifest order, not filesystem order."""

    def test_claim_reviews_ordered_by_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            # Deliberately write shards in reverse filesystem order
            reversed_ids = list(reversed(_CLAIM_IDS))
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS  # manifest lists original order
            )
            # Overwrite claim shards in reversed order to confuse any fs-sorting
            for cid in reversed_ids:
                fname = f"claims/claim-{cid.replace('/', '__')}.json"
                (shard_dir / fname).write_text(
                    json.dumps(_claim_shard(cid)), encoding="utf-8"
                )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            actual_ids = [
                cr["claim_id"] for cr in result.envelope["payload"]["claim_reviews"]
            ]
            self.assertEqual(actual_ids, _CLAIM_IDS)


class TestSynthesizeMissingShards(unittest.TestCase):
    """Missing shard files → ShardError per unit, not just the first."""

    def test_missing_claim_file_raises_synthesis_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Remove one claim shard
            target = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            target.unlink()
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            ids = [e.unit_id for e in ctx.exception.shard_errors]
            self.assertIn(_CLAIM_IDS[0], ids)

    def test_all_missing_units_reported_not_just_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Remove two claim shards and one criterion shard
            (shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json").unlink()
            (shard_dir / f"claims/claim-{_CLAIM_IDS[1].replace('/', '__')}.json").unlink()
            (shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json").unlink()
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            self.assertEqual(len(ctx.exception.shard_errors), 3)
            unit_ids = {e.unit_id for e in ctx.exception.shard_errors}
            self.assertIn(_CLAIM_IDS[0], unit_ids)
            self.assertIn(_CLAIM_IDS[1], unit_ids)
            self.assertIn(_CRIT_IDS[0], unit_ids)

    def test_missing_criterion_file_raises_synthesis_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            (shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json").unlink()
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            ids = [e.unit_id for e in ctx.exception.shard_errors]
            self.assertIn(_CRIT_IDS[0], ids)


class TestSynthesizeInvalidJson(unittest.TestCase):
    """Corrupt JSON → ShardError mentioning 'not valid JSON'."""

    def test_corrupt_claim_shard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            reasons = " ".join(e.reason for e in ctx.exception.shard_errors)
            self.assertIn("not valid JSON", reasons)

    def test_corrupt_criterion_shard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            bad.write_text("[{broken", encoding="utf-8")
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            reasons = " ".join(e.reason for e in ctx.exception.shard_errors)
            self.assertIn("not valid JSON", reasons)


class TestSynthesizeSchemaMismatch(unittest.TestCase):
    """Shard missing a required field → ShardError mentioning the field."""

    def test_claim_missing_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Remove 'reason' from a claim shard
            claim_path = (
                shard_dir
                / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            )
            data = json.loads(claim_path.read_text())
            del data["reason"]
            claim_path.write_text(json.dumps(data))
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            reasons = " ".join(e.reason for e in ctx.exception.shard_errors)
            self.assertIn("reason", reasons)

    def test_claim_id_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Write wrong claim_id in a shard
            claim_path = (
                shard_dir
                / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            )
            data = json.loads(claim_path.read_text())
            data["claim_id"] = "Feat-01/WRONG"
            claim_path.write_text(json.dumps(data))
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            reasons = " ".join(e.reason for e in ctx.exception.shard_errors)
            self.assertIn("mismatch", reasons)

    def test_observation_missing_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            crit_path = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            items = json.loads(crit_path.read_text())
            del items[0]["fact"]  # remove required field
            crit_path.write_text(json.dumps(items))
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            reasons = " ".join(e.reason for e in ctx.exception.shard_errors)
            self.assertIn("fact", reasons)

    def test_observation_criterion_id_not_in_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            crit_path = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            items = json.loads(crit_path.read_text())
            items[0]["criterion_ids"] = ["WRONG-CRITERION"]
            crit_path.write_text(json.dumps(items))
            with self.assertRaises(SynthesisError) as ctx:
                synthesize(manifest_path, _WORK_ITEM_ID)
            reasons = " ".join(e.reason for e in ctx.exception.shard_errors)
            self.assertIn(_CRIT_IDS[0], reasons)


class TestSynthesizeAuxHandling(unittest.TestCase):
    """Absent aux.json → defaults, no error; present → fields loaded."""

    def test_absent_aux_no_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Remove aux.json
            aux_path = shard_dir / "aux.json"
            if aux_path.exists():
                aux_path.unlink()
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            payload = result.envelope["payload"]
            self.assertEqual(payload["evidence_declarations"], [])
            self.assertEqual(payload["open_questions"], [])
            self.assertEqual(payload["notes"], [])

    def test_present_aux_loaded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            payload = result.envelope["payload"]
            self.assertEqual(len(payload["evidence_declarations"]), 1)
            self.assertEqual(payload["open_questions"], ["测试问题"])
            self.assertEqual(payload["notes"], ["测试注释"])


class TestSynthesizeSchemaValidation(unittest.TestCase):
    """Assembled envelope passes JsonSchemaSubsetValidator."""

    def _get_schema_path(self) -> Path | None:
        """Return path to the real envelope schema from job bb27674471d5209683afdd12."""
        schema_path = Path(
            "/home/sunfei/workspace/openHarmony/foundation/arkui/ace_engine/specs"
            "/.evaluator/service-data/jobs/bb27674471d5209683afdd12"
            "/runs/run-1/staged/envelope-observation.schema.json"
        )
        return schema_path if schema_path.exists() else None

    def test_envelope_passes_generated_schema(self):
        """Passes against a freshly generated envelope schema (no real job needed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Build envelope
            result = synthesize(manifest_path, _WORK_ITEM_ID)

            # Write schema to tmp dir
            schemas_root = Path(tmpdir) / "schemas"
            schemas_root.mkdir()
            schema = build_envelope_schema("observation")
            schema_path = schemas_root / "envelope-observation.schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            validator = JsonSchemaSubsetValidator(schemas_root)
            errors = validator.validate_file(result.envelope, schema_path)
            self.assertEqual(
                errors, [],
                msg=f"Envelope failed schema validation: {errors}",
            )

    def test_envelope_passes_real_job_schema(self):
        """Passes against the real schema from job bb27674471d5209683afdd12.

        Skipped gracefully when the file is not present (CI environment).
        """
        schema_path = self._get_schema_path()
        if schema_path is None:
            self.skipTest("Real job schema not found; skipping.")

        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            # Use work_item_id matching real job
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            validator = JsonSchemaSubsetValidator(schema_path.parent)
            errors = validator.validate_file(result.envelope, schema_path)
            self.assertEqual(
                errors, [],
                msg=f"Envelope failed real schema validation: {errors}",
            )


class TestSynthesizeShapeParityWithRealSample(unittest.TestCase):
    """Key-set parity with real successful sample at every nesting level (C2)."""

    _REAL_SAMPLE = Path(
        "/home/sunfei/workspace/openHarmony/foundation/arkui/ace_engine/specs"
        "/.evaluator/service-data/jobs/83b82ef3740959b8d9faf63f"
        "/runs/run-1/staged/observations/Feat-01.executor-result.json"
    )

    def setUp(self):
        if not self._REAL_SAMPLE.exists():
            self.skipTest("Real sample not found; skipping shape-parity test.")
        self.real = json.loads(self._REAL_SAMPLE.read_text(encoding="utf-8"))

    def test_envelope_key_set_parity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            self.assertEqual(
                set(result.envelope.keys()),
                set(self.real.keys()),
            )

    def test_payload_key_set_parity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            self.assertEqual(
                set(result.envelope["payload"].keys()),
                set(self.real["payload"].keys()),
            )

    def test_claim_review_key_set_parity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            # Compare against first real claim_review
            real_cr = self.real["payload"]["claim_reviews"][0]
            synth_cr = result.envelope["payload"]["claim_reviews"][0]
            self.assertEqual(set(synth_cr.keys()), set(real_cr.keys()))

    def test_observation_key_set_parity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            real_obs = self.real["payload"]["observations"][0]
            synth_obs = result.envelope["payload"]["observations"][0]
            self.assertEqual(set(synth_obs.keys()), set(real_obs.keys()))

    def test_evidence_declaration_key_set_parity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            real_ev = self.real["payload"]["evidence_declarations"][0]
            synth_ev = result.envelope["payload"]["evidence_declarations"][0]
            self.assertEqual(set(synth_ev.keys()), set(real_ev.keys()))


if __name__ == "__main__":
    unittest.main()
