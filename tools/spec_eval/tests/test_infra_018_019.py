from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from generate_site import load_archived_spec_evaluation, spec_evaluation_summary
from spec_eval.cli import build_parser
from spec_eval.config import EvaluationConfig
from spec_eval.evidence.sdk_reader import SdkReader
from spec_eval.report.site_reporter import SiteReporter


class Infra018SiteReportTest(unittest.TestCase):
    def test_site_report_aggregates_completed_and_error_functions(self) -> None:
        context = {
            "function_registry_entry": {
                "id": "05-01-01",
                "path": "05-ui-components/01-layout/01-sample/",
                "design": "05-ui-components/01-layout/01-sample/design.md",
                "status": "active",
                "l1": {"id": "05", "title": "组件层"},
                "l2": {"id": "01", "title": "布局"},
                "l3": {"id": "01", "title": "Sample"},
            },
            "feature_registry_entries": [
                {
                    "id": "Feat-01",
                    "title": "Sample feature",
                    "spec": "05-ui-components/01-layout/01-sample/Feat-01-sample-spec.md",
                }
            ],
        }
        completed = {
            "func_id": "05-01-01",
            "context": context,
            "cached": True,
            "output_path": "/tmp/05-01-01",
            "result": {
                "static": {
                    "gate": "fail",
                    "metrics": {"feature_count": 1, "document_count": 2},
                    "findings": [
                        {
                            "rule_id": "TRACE-TEST-001",
                            "severity": "Major",
                            "message": "missing trace",
                            "details": {"internal": "not published"},
                        },
                        {"rule_id": "LINK-TEST-001", "severity": "Minor", "message": "dead link"},
                    ],
                },
                "evidence": {
                    "metrics": {"claim_count": 4, "resolved_claim_count": 3, "evidence_coverage": 0.75}
                },
            },
        }
        failed_context = {
            "function_registry_entry": {
                "id": "05-01-02",
                "path": "05-ui-components/01-layout/02-missing/",
                "status": "active",
                "l1": {"id": "05", "title": "组件层"},
                "l2": {"id": "01", "title": "布局"},
                "l3": {"id": "02", "title": "Missing"},
            },
            "feature_registry_entries": [],
        }
        report = SiteReporter().build(
            [completed, {"func_id": "05-01-02", "context": failed_context, "error": "boom"}],
            source_revision="abc123",
            tool_version="1.0.0",
            rule_version="2.0.0",
            generated_at="2026-08-01T00:00:00+00:00",
            report_only=True,
        )

        self.assertEqual(report["mode"], "report-only")
        self.assertEqual(report["summary"]["registeredFunctionCount"], 2)
        self.assertEqual(report["summary"]["completedFunctionCount"], 1)
        self.assertEqual(report["summary"]["gateCounts"], {"pass": 0, "warn": 0, "fail": 1, "error": 1})
        self.assertEqual(report["summary"]["severityCounts"]["Major"], 1)
        self.assertEqual(report["summary"]["ruleCounts"]["TRACE-TEST-001"], 1)
        self.assertEqual(report["summary"]["evidenceCoverage"], 0.75)
        self.assertEqual(report["functions"][0]["docs"][0]["docId"], "05-ui-components/01-layout/01-sample/design")
        self.assertNotIn("details", report["functions"][0]["findings"][0])
        self.assertNotIn("outputPath", report["functions"][0])
        self.assertEqual(report["functions"][1]["gate"], "error")

    def test_site_report_writer_creates_archive_and_latest_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / ".evaluator"
            target = SiteReporter().write_archive(
                output,
                "abc123",
                {"available": True, "generatedAt": "2026-08-01T00:00:00+00:00"},
            )
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["available"], True)
            pointer = json.loads((output / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(pointer["siteReport"], "site-report.json")


class Infra019ScanCliTest(unittest.TestCase):
    def test_scan_parser_supports_report_only_archive(self) -> None:
        args = build_parser().parse_args(["--output", ".evaluator", "scan", "--all", "--report-only"])
        self.assertEqual(args.command, "scan")
        self.assertTrue(args.report_only)

    def test_site_generator_reads_latest_archived_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / ".evaluator"
            report = {
                "available": True,
                "sourceRevision": "abc123",
                "summary": {"registeredFunctionCount": 1},
                "functions": [{"funcId": "05-01-01"}],
            }
            SiteReporter().write_archive(archive, "abc123", report)
            loaded = load_archived_spec_evaluation(archive)
            self.assertEqual(loaded, report)
            self.assertNotIn("functions", spec_evaluation_summary(loaded))

    def test_sdk_scan_replaces_non_utf8_output_instead_of_aborting_function(self) -> None:
        config = EvaluationConfig.discover()
        with mock.patch("spec_eval.evidence.sdk_reader.subprocess.run") as run:
            run.return_value.stdout = ""
            SdkReader(config).locate("NonUtf8RegressionApi")
        self.assertTrue(run.called)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs["encoding"], "utf-8")
            self.assertEqual(call.kwargs["errors"], "replace")


if __name__ == "__main__":
    unittest.main()
