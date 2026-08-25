"""Tests for generate_site.py dynamic (B-lite) mode.

Covers the filesystem archive reader (newest job per Function, bypassing the
service DB), the reuse of the CI service's report converters to produce the
site's spec/semantic/history shapes, and the data-only refresh that mirrors into
an already-built site so a reload reflects new reports without a rebuild.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import generate_site as gs


def _write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _make_eval_report(func_id: str, revision: str, *, gate: str, findings: list[dict]) -> dict:
    severity_counts = {"Critical": 0, "Major": 0, "Minor": 0, "Info": 0}
    for finding in findings:
        severity_counts[finding.get("severity", "Info")] = (
            severity_counts.get(finding.get("severity", "Info"), 0) + 1
        )
    return {
        "func_id": func_id,
        "source_revision": revision,
        "schema_version": 1,
        "static": {
            "func_id": func_id,
            "source_revision": revision,
            "gate": gate,
            "tool_version": "spec-eval@test",
            "rule_version": "rules@test",
            "findings": findings,
            "metrics": {
                "feature_count": 1,
                "document_count": 2,
                "severity_counts": severity_counts,
                "evidence": {
                    "claim_count": 10,
                    "resolved_claim_count": 4,
                    "evidence_coverage": 0.4,
                },
            },
        },
        "semantic": {
            "func_id": func_id,
            "source_revision": revision,
            "criterion_results": [],
        },
        "score": {
            "func_id": func_id,
            "gate": gate,
            "raw_score": 50,
            "published_score": 40,
            "confidence": {"score": 0.5},
            "admission": {"status": "NOT_READY"},
            "dimensions": [
                {"dimension_id": "correctness", "score": 22},
                {"dimension_id": "spec_executability", "score": 15},
                {"dimension_id": "design_quality", "score": 17},
                {"dimension_id": "compatibility_system_impact", "score": 8},
                {"dimension_id": "function_modeling", "score": 6},
            ],
        },
    }


def _archive_job(
    archive_root: Path,
    *,
    func_id: str,
    job_id: str,
    revision: str,
    created_at: str,
    gate: str = "fail",
    findings: list[dict] | None = None,
) -> None:
    findings = findings if findings is not None else [
        {"rule_id": "RULE-A", "severity": "Major", "message": "m", "path": "p", "line": 1}
    ]
    job_dir = archive_root / revision / func_id / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        job_dir / "aggregate-report_json-evaluation-report.json",
        _make_eval_report(func_id, revision, gate=gate, findings=findings),
    )
    line = {
        "created_at": created_at,
        "func_id": func_id,
        "job_id": job_id,
        "source_revision": revision,
    }
    with (archive_root / gs.AUTOMATED_HISTORY_LOG).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")


class DynamicArchiveReaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.archive_root = self.root / "archives" / "automated"
        self.archive_root.mkdir(parents=True)
        self.functions = [
            {"id": "01-01-01", "l1": {"id": "01", "title": "L1"}, "l2": {"id": "01", "title": "L2"},
             "l3": {"id": "01", "title": "Build"}, "path": "01-a/01-b/01-c/", "design": "01-a/01-b/01-c/design.md"},
            {"id": "02-01-01", "l1": {"id": "02", "title": "L1b"}, "l2": {"id": "01", "title": "L2b"},
             "l3": {"id": "01", "title": "Other"}, "path": "02-a/01-b/01-c/"},
        ]
        self.features = [
            {"func_id": "01-01-01", "id": "Feat-01", "title": "F1", "spec": "01-a/01-b/01-c/Feat-01-spec.md"},
        ]

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_latest_job_per_func_selected_by_created_at(self) -> None:
        _archive_job(self.archive_root, func_id="01-01-01", job_id="old", revision="rev1",
                     created_at="2026-08-20T10:00:00+00:00")
        _archive_job(self.archive_root, func_id="01-01-01", job_id="new", revision="rev1",
                     created_at="2026-08-21T10:00:00+00:00")
        latest = gs._latest_jobs_by_func(self.archive_root)
        self.assertEqual(set(latest), {"01-01-01"})
        self.assertEqual(latest["01-01-01"].name, "new")

    def test_missing_job_dir_is_skipped(self) -> None:
        # A history line whose job directory is absent must not be selected.
        with (self.archive_root / gs.AUTOMATED_HISTORY_LOG).open("w", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "created_at": "2026-08-20T10:00:00+00:00", "func_id": "09-09-09",
                "job_id": "ghost", "source_revision": "rev1",
            }) + "\n")
        self.assertEqual(gs._latest_jobs_by_func(self.archive_root), {})

    def test_spec_evaluation_shape(self) -> None:
        _archive_job(self.archive_root, func_id="01-01-01", job_id="j1", revision="rev1",
                     created_at="2026-08-21T10:00:00+00:00", gate="fail")
        latest = gs._latest_jobs_by_func(self.archive_root)
        report = gs.build_dynamic_spec_evaluation(
            latest, self.functions, self.features, observed_revision="rev1"
        )
        self.assertTrue(report["available"])
        self.assertEqual(report["sourceRevision"], "rev1")
        self.assertEqual(len(report["functions"]), 1)
        entry = report["functions"][0]
        self.assertEqual(entry["funcId"], "01-01-01")
        self.assertEqual(entry["title"], "Build")
        self.assertEqual(entry["gate"], "fail")
        self.assertEqual(entry["findingCount"], 1)
        self.assertEqual(entry["ruleCounts"], {"RULE-A": 1})
        self.assertEqual(entry["evidence"], {"claimCount": 10, "resolvedClaimCount": 4, "coverage": 0.4})
        # docs joined from the registry (design + feature spec)
        self.assertTrue(any(doc["label"] == "Design" for doc in entry["docs"]))
        self.assertEqual(report["summary"]["gateCounts"]["fail"], 1)

    def test_semantic_evaluation_shape(self) -> None:
        _archive_job(self.archive_root, func_id="01-01-01", job_id="j1", revision="rev1",
                     created_at="2026-08-21T10:00:00+00:00")
        latest = gs._latest_jobs_by_func(self.archive_root)
        report = gs.build_dynamic_semantic_evaluation(
            latest, self.functions, observed_revision="rev1"
        )
        self.assertTrue(report["available"])
        self.assertEqual(len(report["functions"]), 1)
        entry = report["functions"][0]
        self.assertEqual(entry["func_id"], "01-01-01")
        self.assertEqual(entry["status"], "CONFIRMED")

    def test_semantic_scores_include_five_dimensions(self) -> None:
        # Regression: dimensions are keyed by ``dimension_id`` in the archive;
        # the converter must map them so the radar chart is not empty.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            ar = Path(tmp) / "automated"
            ar.mkdir(parents=True)
            _archive_job(ar, func_id="01-01-01", job_id="j1", revision="rev1",
                         created_at="2026-08-21T10:00:00+00:00")
            latest = gs._latest_jobs_by_func(ar)
            report = gs.build_dynamic_semantic_evaluation(
                latest, self.functions, observed_revision="rev1"
            )
        scores = report["functions"][0]["scores"]
        self.assertEqual(
            scores["dimensions"],
            {
                "correctness": 22,
                "spec_executability": 15,
                "design_quality": 17,
                "compatibility_system_impact": 8,
                "function_modeling": 6,
            },
        )
        self.assertEqual(scores["published_score"], 40)
        self.assertEqual(scores["confidence"], 0.5)
        spec, semantic, history = gs.load_dynamic_evaluation(
            self.functions, self.features, archive_root=self.archive_root
        )
        self.assertFalse(spec["available"])
        self.assertFalse(semantic["available"])
        self.assertFalse(history["available"])

    def test_observed_revision_is_most_common(self) -> None:
        _archive_job(self.archive_root, func_id="01-01-01", job_id="j1", revision="rev1",
                     created_at="2026-08-21T10:00:00+00:00")
        _archive_job(self.archive_root, func_id="02-01-01", job_id="j2", revision="rev1",
                     created_at="2026-08-21T11:00:00+00:00")
        latest = gs._latest_jobs_by_func(self.archive_root)
        self.assertEqual(gs._observed_revision(latest), "rev1")


class WriteEvaluationDataTest(unittest.TestCase):
    """write_evaluation_data publishes runtime files + descriptor under static/data."""

    def test_runtime_descriptor_and_mirrors(self) -> None:
        with TemporaryDirectory() as tmp:
            static_dir = Path(tmp) / "static" / "data"
            src_dir = Path(tmp) / "src" / "data"
            patches = {
                "STATIC_DATA_DIR": static_dir,
                "DATA_DIR": src_dir,
                "SPEC_EVAL_STATIC_JSON": static_dir / "spec-evaluation.json",
                "SEMANTIC_EVAL_STATIC_JSON": static_dir / "semantic-evaluation.json",
                "SPEC_EVAL_SUMMARY_JSON": src_dir / "spec-evaluation-summary.json",
                "SEMANTIC_EVAL_SUMMARY_JSON": src_dir / "semantic-evaluation-summary.json",
                "SPEC_EVAL_HISTORY_JSON": src_dir / "spec-evaluation-history.json",
                "SPEC_EVAL_SUMMARY_STATIC_JSON": static_dir / "spec-evaluation-summary.json",
                "SEMANTIC_EVAL_SUMMARY_STATIC_JSON": static_dir / "semantic-evaluation-summary.json",
                "SPEC_EVAL_HISTORY_STATIC_JSON": static_dir / "spec-evaluation-history.json",
                "SITE_RUNTIME_JSON": static_dir / "site-runtime.json",
            }
            saved = {name: getattr(gs, name) for name in patches}
            for name, value in patches.items():
                setattr(gs, name, value)
            try:
                spec = gs.empty_spec_evaluation_data()
                spec["available"] = True
                gs.write_evaluation_data(spec, {"available": False, "functions": []},
                                         {"available": False}, mode="dynamic")
            finally:
                for name, value in saved.items():
                    setattr(gs, name, value)
            runtime = json.loads((static_dir / "site-runtime.json").read_text(encoding="utf-8"))
            self.assertEqual(runtime["mode"], "dynamic")
            # summary is mirrored into static/data for runtime fetch
            self.assertTrue((static_dir / "spec-evaluation-summary.json").is_file())
            self.assertTrue((static_dir / "spec-evaluation.json").is_file())


if __name__ == "__main__":
    unittest.main()
