from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from spec_eval.evidence.sdk_reader import SdkReader
from spec_eval.evidence.source_reader import SourceReader
from spec_eval.models import Claim, EvaluationRun, EvidenceBundle, StaticResult
from spec_eval.report import JsonReporter, PerformanceReporter
from test_infra_009_011 import EvidenceFixture


class Next004IndexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = EvidenceFixture()

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def test_source_index_and_content_cache_are_reused(self) -> None:
        reader = SourceReader(self.fixture.config)
        stats = reader.prepare()
        self.assertGreater(stats["repository_file_count"], 0)
        resolved, state = reader.resolve("sample.cpp", self.fixture.spec_path.parent)
        self.assertEqual(state, "resolved")
        self.assertEqual(resolved, self.fixture.source_path.resolve())
        reader.read_ranges(resolved, ((1, 2),))
        reader.read_ranges(resolved, ((2, 3),))
        self.assertEqual(reader.stats()["content_cache_misses"], 1)
        self.assertEqual(reader.stats()["content_cache_hits"], 1)

    def test_sdk_batch_index_avoids_per_api_subprocess_and_caps_evidence(self) -> None:
        sdk_dir = self.fixture.oh_root / "interface" / "sdk-js" / "api" / "arkui"
        for index in range(25):
            (sdk_dir / f"common_{index:02d}.d.ts").write_text(
                "declare function CommonApi(): void;\n",
                encoding="utf-8",
            )
        reader = SdkReader(self.fixture.config)
        stats = reader.prepare({"SampleApi", "CommonApi"})
        self.assertEqual(stats["scan_count"], 1)
        with mock.patch("spec_eval.evidence.sdk_reader.subprocess.run") as run:
            self.assertTrue(reader.locate("SampleApi"))
            self.assertEqual(len(reader.locate("CommonApi")), reader.MAX_DECLARATIONS_PER_API)
        run.assert_not_called()

    def test_performance_reporter_calculates_phase_totals_and_percentiles(self) -> None:
        report = PerformanceReporter().build(
            [
                {"schema_version": 1, "func_id": "01-01-01", "cached": False, "total_ms": 10, "phases_ms": {"sdk": 4}},
                {"schema_version": 1, "func_id": "01-01-02", "cached": True, "total_ms": 20, "phases_ms": {"sdk": 6}},
                {"schema_version": 1, "func_id": "01-01-03", "cached": False, "total_ms": 30, "phases_ms": {"sdk": 8}},
            ],
            source_revision="abc",
            total_ms=75,
            preparation={"total_ms": 5},
        )
        self.assertEqual(report["cached_function_count"], 1)
        self.assertEqual(report["function_duration_ms"], {"p50": 20.0, "p95": 30.0, "max": 30.0})
        self.assertEqual(report["phase_totals_ms"]["sdk"], 18.0)

    def test_evidence_manifest_warns_when_shard_exceeds_budget(self) -> None:
        claim = Claim(
            claim_id="Feat-01/API-1",
            claim_type="api",
            text="sample",
            path="specs/sample.md",
            line=1,
            feat_id="Feat-01",
            sdk_declarations=[{"declaration": "x" * (JsonReporter.MAX_EVIDENCE_SHARD_BYTES + 1024)}],
        )
        run = EvaluationRun(
            self.fixture.context,
            StaticResult(
                func_id=self.fixture.context.func_id,
                source_revision=self.fixture.context.source_revision,
                tool_version=self.fixture.context.tool_version,
                rule_version=self.fixture.context.rule_version,
                gate="pass",
                findings=[],
            ),
            EvidenceBundle(
                self.fixture.context.func_id,
                self.fixture.context.source_revision,
                [claim],
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            target = JsonReporter().write(run, Path(directory), self.fixture.config.repo_root)
            manifest = json.loads((target / "evidence-manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["archive"]["over_budget"])
        self.assertEqual(manifest["archive"]["warnings"][0]["code"], "EVIDENCE_SHARD_BUDGET_EXCEEDED")


if __name__ == "__main__":
    unittest.main()
