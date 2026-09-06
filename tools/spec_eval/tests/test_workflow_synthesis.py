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
        "unit_reviews": [{
            "unit_id": f"{claim_id.replace('/', '-')}-u1",
            "facet_type": "condition",
            "local_outcome": outcome,
            "evidence_refs": ["e1"],
            "fact": "测试事实",
            "verification_gap": None,
        }],
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
    anchor: str | None = None,
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
    output_rules: dict = {
        "language": "Simplified Chinese",
        "no_dump_large_json": True,
    }
    if anchor:
        output_rules["placeholder_anchor_path"] = anchor
    return {
        "feat_id": "Feat-01",
        "schema_version": 1,
        "claim_units": claim_units,
        "criterion_units": criterion_units,
        "aux_file": aux_file,
        "output_rules": output_rules,
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
    anchor: str | None = None,
) -> Path:
    """Write all shards + manifest; return manifest path."""
    (shard_dir / "claims").mkdir(exist_ok=True)
    (shard_dir / "criteria").mkdir(exist_ok=True)
    _write_claim_shards(shard_dir, claim_ids)
    _write_criterion_shards(shard_dir, criterion_ids, claim_ids)
    _write_aux(shard_dir)
    manifest = _build_manifest(shard_dir, claim_ids, criterion_ids, anchor=anchor)
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
    """Missing shard files → one placeholder per lost unit, all in one pass."""

    def test_missing_claim_file_placeholders_unit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            # Remove one claim shard
            target = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            target.unlink()
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            ids = [e.unit_id for e in result.placeholders]
            self.assertIn(_CLAIM_IDS[0], ids)
            row = next(r for r in result.envelope["payload"]["claim_reviews"]
                       if r["claim_id"] == _CLAIM_IDS[0])
            self.assertEqual(row["local_outcome"], "NOT_VERIFIABLE")

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
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            self.assertEqual(len(result.placeholders), 3)
            unit_ids = {e.unit_id for e in result.placeholders}
            self.assertIn(_CLAIM_IDS[0], unit_ids)
            self.assertIn(_CLAIM_IDS[1], unit_ids)
            self.assertIn(_CRIT_IDS[0], unit_ids)

    def test_missing_criterion_file_placeholders_unit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            (shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json").unlink()
            result = synthesize(manifest_path, _WORK_ITEM_ID)
            ids = [e.unit_id for e in result.placeholders]
            self.assertIn(_CRIT_IDS[0], ids)
            ph = [o for o in result.envelope["payload"]["observations"]
                  if o["criterion_ids"] == [_CRIT_IDS[0]]]
            self.assertEqual(len(ph), 1)
            self.assertEqual(ph[0]["local_outcome"], "NOT_VERIFIABLE")

    def test_manifest_damage_still_raises(self):
        """Service-owned manifest damage stays a hard synthesis error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            del manifest["claim_units"][0]["claim_id"]
            manifest_path.write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with self.assertRaises(SynthesisError):
                synthesize(manifest_path, _WORK_ITEM_ID)


class TestSynthesizeInvalidJson(unittest.TestCase):
    """Corrupt JSON → placeholder degradation naming the cause."""

    def test_corrupt_claim_shard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            self.assertIn(
                "not valid JSON",
                " ".join(p.reason for p in result.placeholders),
            )
            row = result.envelope["payload"]["claim_reviews"][0]
            self.assertEqual(row["local_outcome"], "NOT_VERIFIABLE")

    def test_corrupt_criterion_shard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            bad.write_text("[{broken", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            self.assertIn(
                "not valid JSON",
                " ".join(p.reason for p in result.placeholders),
            )
            ph = [o for o in result.envelope["payload"]["observations"]
                  if o["criterion_ids"] == [_CRIT_IDS[0]]]
            self.assertEqual(len(ph), 1)
            self.assertEqual(ph[0]["local_outcome"], "NOT_VERIFIABLE")


class TestSynthesizeShardRepair(unittest.TestCase):
    """Near-miss JSON syntax slips are repaired deterministically.

    Regression shape taken from job 68d585a210af1f3c851c9f07, where a claim
    shard lost the whole observe attempt because the model wrote
    Chinese-emphasis quoting as unescaped ASCII double quotes inside the
    ``fact`` value and the synthesis stage had no repair pass.
    """

    def _incident_text(self) -> str:
        """A valid claim shard serialized with unescaped inner quotes."""
        shard = _claim_shard(_CLAIM_IDS[0])
        shard["reason"] = "@@FACT@@"
        text = json.dumps(shard, ensure_ascii=False, indent=2)
        return text.replace(
            "@@FACT@@",
            "已注册基础图形标签，满足\"基础图形标签已注册\"触发条件。",
        )

    def test_unescaped_inner_quotes_repaired(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            raw = self._incident_text()
            bad.write_text(raw, encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                json.loads(raw)

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            fact = "已注册基础图形标签，满足\"基础图形标签已注册\"触发条件。"
            self.assertEqual(
                result.envelope["payload"]["claim_reviews"][0]["reason"], fact
            )
            self.assertEqual(len(result.repairs), 1)
            self.assertEqual(result.repairs[0]["file"],
                             f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json")
            self.assertEqual(result.repairs[0]["action"], "json_syntax_repair")

    def test_repaired_shard_persisted_with_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            raw = self._incident_text()
            bad.write_text(raw, encoding="utf-8")

            synthesize(manifest_path, _WORK_ITEM_ID)

            backup = Path(str(bad) + ".bad")
            self.assertTrue(backup.exists())
            self.assertEqual(backup.read_text(encoding="utf-8"), raw)
            self.assertEqual(
                json.loads(bad.read_text(encoding="utf-8"))["reason"],
                "已注册基础图形标签，满足\"基础图形标签已注册\"触发条件。",
            )

    def test_trailing_comma_repaired(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            good = json.dumps([_obs_item(_CRIT_IDS[0], _CLAIM_IDS)],
                              ensure_ascii=False)
            bad.write_text(good[:-1] + ",]", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            self.assertEqual(result.observation_count, len(_CRIT_IDS))
            self.assertEqual(len(result.repairs), 1)
            self.assertEqual(result.repairs[0]["file"],
                             f"criteria/obs-{_CRIT_IDS[0]}.json")

    def test_unrepairable_json_degrades_to_placeholder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            payload = result.envelope["payload"]
            rows = [r for r in payload["claim_reviews"]
                    if r["claim_id"] == _CLAIM_IDS[0]]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["local_outcome"], "NOT_VERIFIABLE")
            self.assertIn(
                "not valid JSON",
                " ".join(p.reason for p in result.placeholders),
            )
            self.assertTrue(any(
                _CLAIM_IDS[0] in note for note in payload["notes"]
            ))
            self.assertFalse(list(shard_dir.rglob("*.bad")))

    def test_invalid_aux_json_degrades_to_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            (shard_dir / "aux.json").write_text("{broken", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            payload = result.envelope["payload"]
            self.assertEqual(payload["evidence_declarations"], [])
            aux_ph = [p for p in result.placeholders if p.unit_type == "aux"]
            self.assertEqual(len(aux_ph), 1)
            self.assertEqual(aux_ph[0].file, "aux.json")
            self.assertTrue(any("aux.json" in n for n in payload["notes"]))


class TestSynthesizeSchemaMismatch(unittest.TestCase):
    """Structurally incomplete shards are repaired mechanically or degraded.

    The manifest's claim id is authoritative: a mismatched claim_id is
    re-identified, missing mechanical fields get structural defaults, and
    only rows without usable review content degrade to placeholders.
    """

    def test_claim_missing_reason_summarized_from_units(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            claim_path = (
                shard_dir
                / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            )
            data = json.loads(claim_path.read_text())
            del data["reason"]
            claim_path.write_text(json.dumps(data))

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            row = result.envelope["payload"]["claim_reviews"][0]
            self.assertEqual(row["claim_id"], _CLAIM_IDS[0])
            self.assertEqual(row["reason"], "测试事实")
            self.assertTrue(any(
                r["action"] == "claim_row_normalize" and "reason" in r["detail"]
                for r in result.repairs
            ))

    def test_claim_id_mismatch_reidentified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            claim_path = (
                shard_dir
                / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            )
            data = json.loads(claim_path.read_text())
            data["claim_id"] = "Feat-01/WRONG"
            claim_path.write_text(json.dumps(data))

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            row = result.envelope["payload"]["claim_reviews"][0]
            self.assertEqual(row["claim_id"], _CLAIM_IDS[0])
            self.assertEqual(row["reason"], "テスト理由")
            self.assertTrue(any(
                "claim_id re-identified" in r["detail"] for r in result.repairs
            ))

    def test_claim_without_valid_units_degrades(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            claim_path = (
                shard_dir
                / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            )
            data = json.loads(claim_path.read_text())
            data["unit_reviews"] = []
            claim_path.write_text(json.dumps(data))

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            row = result.envelope["payload"]["claim_reviews"][0]
            self.assertEqual(row["local_outcome"], "NOT_VERIFIABLE")
            self.assertEqual(len(row["unit_reviews"]), 1)
            self.assertTrue(any(
                p.unit_id == _CLAIM_IDS[0] and p.unit_type == "claim"
                for p in result.placeholders
            ))

    def test_observation_missing_field_degrades_criterion(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            crit_path = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            items = json.loads(crit_path.read_text())
            del items[0]["fact"]
            crit_path.write_text(json.dumps(items))

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            obs = result.envelope["payload"]["observations"]
            ph = [o for o in obs if o["criterion_ids"] == [_CRIT_IDS[0]]]
            self.assertEqual(len(ph), 1)
            self.assertEqual(ph[0]["local_outcome"], "NOT_VERIFIABLE")
            self.assertEqual(ph[0]["claim_ids"], _CLAIM_IDS)
            self.assertEqual(ph[0]["check_ids"], ["claim_source_support"])
            self.assertTrue(any(
                p.unit_id == _CRIT_IDS[0] and p.unit_type == "criterion"
                for p in result.placeholders
            ))

    def test_observation_criterion_id_not_in_list_degrades(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS
            )
            crit_path = shard_dir / f"criteria/obs-{_CRIT_IDS[0]}.json"
            items = json.loads(crit_path.read_text())
            items[0]["criterion_ids"] = ["WRONG-CRITERION"]
            crit_path.write_text(json.dumps(items))

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            obs = result.envelope["payload"]["observations"]
            ph = [o for o in obs if o["criterion_ids"] == [_CRIT_IDS[0]]]
            self.assertEqual(len(ph), 1)
            self.assertEqual(ph[0]["local_outcome"], "NOT_VERIFIABLE")
            self.assertIn(_CRIT_IDS[0],
                          " ".join(p.reason for p in result.placeholders))


class TestSynthesizeDegradedPublish(unittest.TestCase):
    """Lost shards yield a publishable envelope with honest placeholders.

    Per the "usable report first" principle, placeholder rows are
    NOT_VERIFIABLE with a truthful verification gap, anchored at one
    synthetic review_record evidence declaration so the published evidence
    invariants hold without inventing review content.
    """

    _ANCHOR = "test/unittest/core/pattern/image"

    def test_missing_claim_file_placeholders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor=self._ANCHOR
            )
            (shard_dir / f"claims/claim-{_CLAIM_IDS[1].replace('/', '__')}.json").unlink()

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            payload = result.envelope["payload"]
            self.assertEqual(result.claim_count, len(_CLAIM_IDS))
            row = next(r for r in payload["claim_reviews"]
                       if r["claim_id"] == _CLAIM_IDS[1])
            self.assertEqual(row["local_outcome"], "NOT_VERIFIABLE")
            self.assertEqual(row["evidence_refs"], ["e9001"])
            self.assertTrue(any(
                "shard file not found" in p.reason for p in result.placeholders
            ))

    def test_placeholder_anchor_declaration_appended(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor=self._ANCHOR
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            decls = result.envelope["payload"]["evidence_declarations"]
            self.assertEqual(len(decls), 2)
            anchor_decl = decls[-1]
            self.assertEqual(anchor_decl["key"], "e9001")
            self.assertEqual(anchor_decl["type"], "review_record")
            self.assertEqual(anchor_decl["path"], self._ANCHOR)

    def test_anchor_falls_back_to_aux_declaration_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor=None
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            decls = result.envelope["payload"]["evidence_declarations"]
            anchor_decl = decls[-1]
            self.assertEqual(anchor_decl["type"], "review_record")
            self.assertEqual(
                anchor_decl["path"],
                "adapter/ohos/entrance/subwindow/subwindow_ohos.cpp",
            )
            row = next(r for r in result.envelope["payload"]["claim_reviews"]
                       if r["claim_id"] == _CLAIM_IDS[0])
            self.assertEqual(row["evidence_refs"], ["e9001"])

    def test_no_anchor_leaves_empty_refs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor=None
            )
            (shard_dir / "aux.json").unlink()
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            row = next(r for r in result.envelope["payload"]["claim_reviews"]
                       if r["claim_id"] == _CLAIM_IDS[0])
            self.assertEqual(row["evidence_refs"], [])
            self.assertEqual(result.envelope["payload"]["evidence_declarations"], [])

    def test_happy_path_appends_no_anchor(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor=self._ANCHOR
            )

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            self.assertEqual(result.placeholders, [])
            payload = result.envelope["payload"]
            self.assertEqual(len(payload["evidence_declarations"]), 1)
            self.assertFalse(any(
                "e9001" in str(d) for d in payload["evidence_declarations"]
            ))

    def test_degraded_envelope_passes_generated_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            shard_dir = Path(tmpdir)
            manifest_path = _build_full_fixture(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor=self._ANCHOR
            )
            bad = shard_dir / f"claims/claim-{_CLAIM_IDS[0].replace('/', '__')}.json"
            bad.write_text("{broken json", encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            schemas_root = Path(tmpdir) / "schemas"
            schemas_root.mkdir()
            schema = build_envelope_schema("observation")
            schema_path = schemas_root / "envelope-observation.schema.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            validator = JsonSchemaSubsetValidator(schemas_root)
            errors = validator.validate_file(result.envelope, schema_path)
            self.assertEqual(
                errors, [],
                msg=f"Degraded envelope failed schema validation: {errors}",
            )

    def test_degraded_payload_publishes_through_kernel_pipeline(self):
        """The full publish gate: normalize + typed validation accept a
        degraded payload with zero fatal/error findings.

        This is the "usable report first" guarantee end to end: a lost claim
        shard becomes an honest NOT_VERIFIABLE row whose anchor review_record
        evidence normalize attaches to the first published observation, so
        the NV inspection-evidence invariant holds without inventing content.
        """
        from spec_eval.kernel.evidence_paths import FrozenEvidencePathResolver
        from spec_eval.kernel.normalize import (
            normalize_observation,
            project_observation_derived_fields,
        )
        from spec_eval.kernel.validate import validate_observation_document

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            frozen = root / "frozen"
            frozen.mkdir()
            (frozen / "input.txt").write_text(
                "frozen evidence content\n", encoding="utf-8"
            )
            shard_dir = root / "shards"
            shard_dir.mkdir()
            (shard_dir / "claims").mkdir()
            (shard_dir / "criteria").mkdir()
            _write_claim_shards(shard_dir, _CLAIM_IDS)
            (shard_dir / f"claims/claim-{_CLAIM_IDS[1].replace('/', '__')}.json").write_text(
                "{broken json", encoding="utf-8"
            )
            for crid, check in zip(
                _CRIT_IDS, ["claim_source_support", "boundary_state"]
            ):
                item = _obs_item(crid, _CLAIM_IDS)
                item["check_ids"] = [check]
                (shard_dir / f"criteria/obs-{crid}.json").write_text(
                    json.dumps([item]), encoding="utf-8"
                )
            (shard_dir / "aux.json").write_text(json.dumps({
                "evidence_declarations": [{
                    "key": "e1", "type": "source_citation",
                    "path": "input.txt", "lines": "1-1",
                    "description": "冻结证据",
                }],
                "open_questions": [], "notes": [],
            }), encoding="utf-8")
            manifest = _build_manifest(
                shard_dir, _CLAIM_IDS, _CRIT_IDS, anchor="input.txt"
            )
            manifest_path = shard_dir / "_manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = synthesize(manifest_path, _WORK_ITEM_ID)

            template = {
                "schema_version": 2, "func_id": "05-01-02",
                "source_revision": "a" * 40, "run_id": "run-1",
                "observation_id": "feature:Feat-01",
                "observation_type": "feature", "status": "pending",
                "expected_claim_ids": _CLAIM_IDS,
                "required_checks": ["claim_source_support",
                                    "boundary_state"],
                "reviewed_claim_ids": [], "claim_reviews": [],
                "completed_checks": [], "observations": [],
                "open_questions": [], "notes": [],
            }
            resolver = FrozenEvidencePathResolver.ace_engine_only(frozen)
            norm = normalize_observation(
                template, result.envelope["payload"], repo_root=frozen,
                evidence_resolver=resolver,
            )
            self.assertEqual(norm.fatal, [])
            self.assertEqual(norm.errors, [])
            document = project_observation_derived_fields(norm.document)
            residual = validate_observation_document(
                document, valid_criterion_ids=_CRIT_IDS
            )
            self.assertEqual(
                [e.code for e in residual], [],
                msg=f"Degraded document failed validation: "
                    f"{[e.code for e in residual]}",
            )
            nv_rows = [r for r in document["claim_reviews"]
                       if r["local_outcome"] == "NOT_VERIFIABLE"]
            self.assertEqual(len(nv_rows), 1)
            self.assertTrue(nv_rows[0]["evidence_ids"])


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
