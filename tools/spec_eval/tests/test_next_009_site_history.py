from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from generate_site import load_archived_evaluation_history, site_history_data
from spec_eval.report.site_evaluation_history import (
    build_site_evaluation_history,
    validate_site_evaluation_history,
)


class Next009SiteHistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.schemas_root = cls.specs_root / "evaluation" / "schemas"

    @staticmethod
    def report(revision: str, findings: list[dict], *, published: float = 60) -> dict:
        return {
            "schemaVersion": 1,
            "reportVersion": "test",
            "available": True,
            "sourceRevision": revision,
            "staticReport": {"path": "site-report.json", "sourceRevision": revision},
            "summary": {},
            "functions": [{
                "func_id": "05-01-01",
                "title": "Example",
                "source_revision": revision,
                "status": "CONFIRMED",
                "scores": {
                    "dimensions": {
                        "correctness": 18,
                        "spec_executability": 16,
                        "design_quality": 14,
                        "compatibility_system_impact": 7,
                        "function_modeling": 8,
                    },
                    "published_score": published,
                    "confidence": 0.9,
                    "admission": "NOT_READY",
                },
                "criterion_summaries": [],
                "findings": findings,
                "recommendations": [],
                "evidence_paths": [],
                "confirmation": {"confirmed_at": "2026-08-10T00:00:00Z"},
                "static_report_reference": {"gate": "fail"},
            }],
        }

    @staticmethod
    def finding(finding_id: str, *, source: str = "static", severity: str = "Major", message: str = "issue") -> dict:
        result = {
            "finding_id": finding_id,
            "source": source,
            "severity": severity,
            "message": message,
            "path": "specs/example.md",
        }
        if source == "static":
            result["rule_id"] = "TEST-001"
        else:
            result["criterion_id"] = "CORRECTNESS-SOURCE-SUPPORT"
        return result

    def test_builds_initial_compact_snapshot_and_schema_validates(self) -> None:
        report = self.report("rev-1", [self.finding("FND-1"), self.finding("SEM-1", source="semantic")])
        result = build_site_evaluation_history(current_report=report, snapshot_at="2026-08-20T00:00:00Z")
        self.assertEqual(result["summary"]["comparisonStatus"], "INITIAL")
        self.assertEqual(result["summary"]["snapshotCount"], 1)
        self.assertEqual(result["summary"]["currentFindingCount"], 2)
        self.assertEqual(result["snapshots"][0]["severityCounts"]["Major"], 2)
        self.assertEqual(result["snapshots"][0]["snapshotDay"], "2026-08-20")
        self.assertEqual(validate_site_evaluation_history(result, self.schemas_root), [])
        self.assertNotIn("activeFindings", site_history_data(result))

    def test_reports_added_resolved_persistent_and_reclassified(self) -> None:
        first = self.report("rev-1", [
            self.finding("FND-stable"),
            self.finding("FND-resolved"),
            self.finding("SEM-change", source="semantic", severity="Major", message="old"),
        ])
        history = build_site_evaluation_history(current_report=first, snapshot_at="2026-08-20T00:00:00Z")
        second = self.report("rev-2", [
            self.finding("FND-stable"),
            self.finding("FND-added", severity="Minor"),
            self.finding("SEM-change", source="semantic", severity="Critical", message="new"),
        ], published=55)
        result = build_site_evaluation_history(
            current_report=second, previous_history=history, snapshot_at="2026-08-21T00:00:00Z"
        )
        self.assertEqual(result["summary"]["comparisonStatus"], "REVISION_CHANGED")
        self.assertEqual(result["summary"]["snapshotCount"], 2)
        self.assertEqual(result["recentDelta"]["summary"], {
            "added": 1, "resolved": 1, "persistent": 1, "reclassified": 1,
        })
        self.assertEqual(result["recentDelta"]["functions"][0]["funcId"], "05-01-01")

    def test_same_revision_and_fingerprint_is_idempotent(self) -> None:
        report = self.report("rev-1", [self.finding("FND-1")])
        first = build_site_evaluation_history(current_report=report, snapshot_at="2026-08-20T09:00:00Z")
        second = build_site_evaluation_history(
            current_report=report, previous_history=first, snapshot_at="2026-08-20T18:00:00Z"
        )
        self.assertEqual(first, second)

    def test_same_day_new_content_replaces_the_day_point(self) -> None:
        first = self.report("rev-1", [self.finding("FND-1")], published=60)
        history = build_site_evaluation_history(current_report=first, snapshot_at="2026-08-20T08:00:00Z")
        second = self.report("rev-2", [self.finding("FND-1"), self.finding("FND-2")], published=50)
        result = build_site_evaluation_history(
            current_report=second, previous_history=history, snapshot_at="2026-08-20T20:00:00Z"
        )
        # Same calendar day -> one point (latest wins), not two.
        self.assertEqual(result["summary"]["snapshotCount"], 1)
        self.assertEqual(result["snapshots"][-1]["sourceRevision"], "rev-2")
        self.assertEqual(result["snapshots"][-1]["publishedScoreAverage"], 50)

    def test_new_day_appends_point_even_when_revision_unchanged(self) -> None:
        report = self.report("rev-1", [self.finding("FND-1")])
        day1 = build_site_evaluation_history(current_report=report, snapshot_at="2026-08-20T08:00:00Z")
        # Same revision, same content, but a new calendar day -> a fresh point so
        # a frozen revision reads as a continuous line, not a single dot.
        day2 = build_site_evaluation_history(
            current_report=report, previous_history=day1, snapshot_at="2026-08-21T08:00:00Z"
        )
        self.assertEqual(day2["summary"]["snapshotCount"], 2)
        self.assertEqual([s["snapshotDay"] for s in day2["snapshots"]], ["2026-08-20", "2026-08-21"])
        self.assertEqual({s["sourceRevision"] for s in day2["snapshots"]}, {"rev-1"})

    def test_cli_updates_history_and_generator_loader_reads_it(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            report_path = root / "site-evaluation-report.json"
            report_path.write_text(json.dumps(self.report("rev-1", [self.finding("FND-1")])), encoding="utf-8")
            history_path = root / "site-evaluation-history.json"
            command = [
                sys.executable,
                str(self.specs_root / "tools/spec_eval/cli.py"),
                "--json",
                "site-evaluation-history",
                "--site-evaluation-report",
                str(report_path),
                "--write",
                str(history_path),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["snapshot_count"], 1)
            loaded = load_archived_evaluation_history(root)
            self.assertEqual(loaded["currentRevision"], "rev-1")


if __name__ == "__main__":
    unittest.main()
