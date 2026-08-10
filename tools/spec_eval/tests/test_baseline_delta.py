from __future__ import annotations

import json
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from spec_eval.cli import main
from spec_eval.models.finding import Finding, Severity
from spec_eval.report.baseline_reporter import BaselineReporter


class BaselineDeltaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.reporter = BaselineReporter()

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def _finding(
        rule_id: str,
        message: str,
        *,
        line: int,
        node_id: str | None = None,
        severity: Severity = Severity.MAJOR,
    ) -> dict:
        details = {"node_id": node_id} if node_id else {}
        return Finding(
            rule_id,
            severity,
            message,
            "specs/05-ui-components/01-test/01-sample/Feat-01-sample-spec.md",
            line=line,
            func_id="05-01-01",
            feat_id="Feat-01",
            details=details,
        ).to_dict()

    def _write_results(
        self,
        name: str,
        findings: list[dict],
        *,
        rule_version: str = "1.0.0",
        complete: bool = False,
    ) -> tuple[Path, Path | None]:
        output = self.root / name
        revision = output / f"revision-{name}"
        target = revision / "05-01-01"
        target.mkdir(parents=True)
        (target / "static-result.json").write_text(
            json.dumps(
                {
                    "func_id": "05-01-01",
                    "source_revision": f"revision-{name}",
                    "tool_version": "1.0.0",
                    "rule_version": rule_version,
                    "gate": "fail" if findings else "pass",
                    "findings": findings,
                    "metrics": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        site_report = None
        if complete:
            site_report = output / "site-report.json"
            site_report.write_text(
                json.dumps(
                    {
                        "sourceRevision": f"revision-{name}",
                        "toolVersion": "1.0.0",
                        "ruleVersion": rule_version,
                        "summary": {
                            "registeredFunctionCount": 1,
                            "completedFunctionCount": 1,
                            "errorCount": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
        return revision, site_report

    def test_finding_id_ignores_markdown_line_movement(self) -> None:
        before = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        after = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=120, node_id="Feat-01/AC-1.1")
        self.assertEqual(before["identity_version"], 1)
        self.assertEqual(before["problem_key"], after["problem_key"])
        self.assertEqual(before["finding_id"], after["finding_id"])

    def test_finding_id_normalizes_dynamic_counts_lines_and_story_titles(self) -> None:
        before = Finding(
            "TEST-DYNAMIC-001",
            Severity.MAJOR,
            "candidate count: 3 at line 20",
            "specs/sample.md",
            func_id="05-01-01",
        ).to_dict()
        after = Finding(
            "TEST-DYNAMIC-001",
            Severity.MAJOR,
            "candidate count: 8 at line 120",
            "specs/sample.md",
            func_id="05-01-01",
        ).to_dict()
        self.assertEqual(before["finding_id"], after["finding_id"])

        story_before = Finding(
            "SPEC-STRUCT-USER-STORY-001",
            Severity.MAJOR,
            "invalid story",
            "specs/sample.md",
            func_id="05-01-01",
            feat_id="Feat-01",
            details={"user_story": "US-2: old title"},
        ).to_dict()
        story_after = Finding(
            "SPEC-STRUCT-USER-STORY-001",
            Severity.MAJOR,
            "invalid story after edit",
            "specs/sample.md",
            func_id="05-01-01",
            feat_id="Feat-01",
            details={"user_story": "US-2: new title"},
        ).to_dict()
        self.assertEqual(story_before["finding_id"], story_after["finding_id"])

    def test_compare_reports_added_resolved_unchanged_and_reclassified(self) -> None:
        stable_before = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        resolved = self._finding("TRACE-AC-NO-RULE-001", "AC has no Rule", line=30, node_id="Feat-01/AC-1.2")
        reclassified_before = self._finding(
            "TRACE-RULE-ORPHAN-001", "Rule is orphan", line=40, node_id="Feat-01/R-1", severity=Severity.MAJOR
        )
        stable_after = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=220, node_id="Feat-01/AC-1.1")
        added = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=50, node_id="Feat-01/AC-1.3")
        reclassified_after = self._finding(
            "TRACE-RULE-ORPHAN-001",
            "Rule remains orphan after calibration",
            line=240,
            node_id="Feat-01/R-1",
            severity=Severity.MINOR,
        )

        baseline_root, site_report = self._write_results(
            "baseline", [stable_before, resolved, reclassified_before], complete=True
        )
        current_root, _ = self._write_results("current", [stable_after, added, reclassified_after])
        baseline = self.reporter.build_manifest(baseline_root, site_report)
        baseline_path = self.root / "baseline.json"
        self.reporter.write_manifest(baseline, baseline_path)

        delta = self.reporter.compare(current_root, baseline_path)
        function = delta["functions"]["05-01-01"]
        self.assertEqual(delta["summary"], {"added": 1, "reclassified": 1, "resolved": 1, "unchanged": 1})
        self.assertEqual(function["baseline_status"], "existing")
        self.assertEqual(function["unchanged"], 1)
        self.assertEqual(function["added"][0]["finding_id"], added["finding_id"])
        self.assertEqual(function["resolved"][0]["finding_id"], resolved["finding_id"])
        self.assertEqual(function["reclassified"][0]["finding_id"], reclassified_before["finding_id"])
        self.assertEqual(function["reclassified"][0]["before"]["severity"], "Major")
        self.assertEqual(function["reclassified"][0]["after"]["severity"], "Minor")

        directory_delta = self.reporter.compare(current_root, baseline_root.parent)
        self.assertEqual(directory_delta["summary"], delta["summary"])

        baseline_document = self.reporter.load_baseline(baseline_path, expected_rule_version="1.0.0")
        current_document = json.loads((current_root / "05-01-01" / "static-result.json").read_text(encoding="utf-8"))
        memory_delta = self.reporter.compare_results([current_document], baseline_document)
        self.assertEqual(memory_delta["summary"], delta["summary"])

    def test_compare_rejects_rule_or_identity_version_mismatch(self) -> None:
        finding = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        baseline_root, site_report = self._write_results("baseline", [finding], complete=True)
        current_root, _ = self._write_results("current", [finding], rule_version="2.0.0")
        baseline_path = self.root / "baseline.json"
        self.reporter.write_manifest(self.reporter.build_manifest(baseline_root, site_report), baseline_path)
        with self.assertRaisesRegex(ValueError, "rule version mismatch"):
            self.reporter.compare(current_root, baseline_path)

        document = json.loads(baseline_path.read_text(encoding="utf-8"))
        document["identity_version"] = 999
        baseline_path.write_text(json.dumps(document), encoding="utf-8")
        current_root, _ = self._write_results("current-same-rule", [finding])
        with self.assertRaisesRegex(ValueError, "identity version mismatch"):
            self.reporter.compare(current_root, baseline_path)

    def test_formal_baseline_requires_complete_site_report(self) -> None:
        finding = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        baseline_root, _ = self._write_results("baseline", [finding])
        manifest = self.reporter.build_manifest(baseline_root)
        self.assertFalse(manifest["complete"])
        baseline_path = self.root / "baseline.json"
        self.reporter.write_manifest(manifest, baseline_path)
        current_root, _ = self._write_results("current", [finding])
        with self.assertRaisesRegex(ValueError, "baseline is incomplete"):
            self.reporter.compare(current_root, baseline_path)

    def test_formal_baseline_rejects_site_report_from_another_tool_version(self) -> None:
        finding = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        baseline_root, site_report = self._write_results("baseline-tool-version", [finding], complete=True)
        site = json.loads(site_report.read_text(encoding="utf-8"))
        site["toolVersion"] = "9.9.9"
        site_report.write_text(json.dumps(site), encoding="utf-8")
        manifest = self.reporter.build_manifest(baseline_root, site_report)
        self.assertFalse(manifest["complete"])

    def test_baseline_cli_writes_complete_manifest(self) -> None:
        finding = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        result_root, site_report = self._write_results("baseline-cli", [finding], complete=True)
        target = self.root / "current.json"
        with redirect_stdout(StringIO()):
            exit_code = main(
                [
                    "--json",
                    "baseline",
                    "--results",
                    str(result_root),
                    "--site-report",
                    str(site_report),
                    "--write",
                    str(target),
                ]
            )
        self.assertEqual(exit_code, 0)
        manifest = json.loads(target.read_text(encoding="utf-8"))
        self.assertTrue(manifest["complete"])
        self.assertEqual(manifest["finding_count"], 1)

    def test_duplicate_identity_is_compacted_with_count(self) -> None:
        first = self._finding("HYGIENE-PLACEHOLDER-001", "placeholder", line=20)
        second = self._finding("HYGIENE-PLACEHOLDER-001", "placeholder", line=120)
        result_root, site_report = self._write_results("baseline", [first, second], complete=True)
        manifest = self.reporter.build_manifest(result_root, site_report)
        self.assertEqual(manifest["finding_count"], 2)
        self.assertEqual(manifest["unique_finding_count"], 1)
        self.assertEqual(manifest["findings"][0]["count"], 2)

    def test_partial_current_does_not_resolve_unscanned_functions(self) -> None:
        finding = self._finding("TRACE-AC-NO-VM-001", "AC is not linked", line=20, node_id="Feat-01/AC-1.1")
        baseline_root, site_report = self._write_results("baseline", [finding], complete=True)
        baseline_path = self.root / "baseline.json"
        self.reporter.write_manifest(self.reporter.build_manifest(baseline_root, site_report), baseline_path)

        partial_root, _ = self._write_results("partial", [])
        delta = self.reporter.compare(partial_root, baseline_path)
        self.assertEqual(delta["scope"]["func_ids"], ["05-01-01"])
        self.assertEqual(delta["summary"]["resolved"], 1)

        empty_other = self.root / "other" / "revision-other" / "06-01-01"
        empty_other.mkdir(parents=True)
        (empty_other / "static-result.json").write_text(
            json.dumps(
                {
                    "func_id": "06-01-01",
                    "source_revision": "revision-other",
                    "tool_version": "1.0.0",
                    "rule_version": "1.0.0",
                    "gate": "pass",
                    "findings": [],
                    "metrics": {},
                }
            ),
            encoding="utf-8",
        )
        delta = self.reporter.compare(empty_other.parent, baseline_path)
        self.assertEqual(delta["scope"]["func_ids"], ["06-01-01"])
        self.assertEqual(delta["summary"]["resolved"], 0)
        self.assertEqual(delta["functions"]["06-01-01"]["baseline_status"], "new")

    def test_16000_finding_compare_completes_within_30_seconds(self) -> None:
        findings = [
            self._finding(
                "TRACE-AC-NO-VM-001",
                "AC is not linked",
                line=index + 1,
                node_id=f"Feat-01/AC-{index + 1}",
            )
            for index in range(16000)
        ]
        baseline_root, site_report = self._write_results("baseline", findings, complete=True)
        current_root, _ = self._write_results("current", findings)
        baseline_path = self.root / "baseline.json"
        self.reporter.write_manifest(self.reporter.build_manifest(baseline_root, site_report), baseline_path)
        started = time.monotonic()
        delta = self.reporter.compare(current_root, baseline_path)
        elapsed = time.monotonic() - started
        self.assertEqual(delta["summary"]["unchanged"], 16000)
        self.assertLess(elapsed, 30.0)


if __name__ == "__main__":
    unittest.main()
