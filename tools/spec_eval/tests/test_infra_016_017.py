from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import yaml

from spec_eval import cli
from spec_eval import ci_runner
from spec_eval.checks.reference_checks import ReferenceChecker
from spec_eval.checks.spec_structure_checks import SpecStructureChecker
from spec_eval.checks.traceability_checks import TraceabilityChecker
from spec_eval.config import EvaluationConfig
from spec_eval.discovery.function_locator import FunctionLocator
from spec_eval.errors import ParseError
from spec_eval.models.finding import Finding, Severity
from spec_eval.orchestrator import EvaluationOrchestrator
from spec_eval.parser.markdown_parser import MarkdownParser
from spec_eval.parser.table_parser import split_table_row
from spec_eval.rules.gate_engine import GateEngine
from spec_eval.rules.rule_loader import Exemption, RuleConfiguration
from spec_eval.tests.test_infra_001_003 import TemporaryRepository


class Infra016TestInfrastructureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[4]
        cls.manifest_path = cls.repo_root / "specs" / "evaluation" / "golden" / "manifest.yaml"

    def test_golden_functions_run_and_detect_declared_rules(self) -> None:
        manifest = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        evaluator = EvaluationOrchestrator(EvaluationConfig.discover())
        for entry in manifest["functions"]:
            with self.subTest(func_id=entry["func_id"]):
                run = evaluator.evaluate(entry["func_id"])
                actual_rules = {finding.rule_id for finding in run.static_result.findings}
                self.assertEqual(len(run.context.feature_specs), entry["expected_feature_count"])
                self.assertTrue(set(entry["expected_rule_ids"]).issubset(actual_rules))
                self.assertIn(run.static_result.gate, {"pass", "warn", "fail"})

    def test_mutations_detect_broken_path_range_id_and_missing_heading(self) -> None:
        fixture = TemporaryRepository()
        try:
            original = fixture.spec_path.read_text(encoding="utf-8")
            fixture.spec_path.write_text(
                original
                + "\n## 验收追溯\n"
                + "| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |\n"
                + "|---|---|---|---|---|\n"
                + "| AC-1.1-AC-1.2 | R-1 | TASK-1 | unit | `frameworks/core/missing.cpp:1` |\n",
                encoding="utf-8",
            )
            fixture.spec_path.write_text(
                fixture.spec_path.read_text(encoding="utf-8").replace("## 概述\n", "概述\n", 1),
                encoding="utf-8",
            )
            context = FunctionLocator(fixture.config).locate("05-01-01")
            parser = MarkdownParser(fixture.config)
            documents = [parser.parse(path) for path in context.all_documents() if path.is_file()]
            structure = SpecStructureChecker(fixture.config).run(context, documents)
            trace = TraceabilityChecker(fixture.config).run(context, documents)
            references = ReferenceChecker(fixture.config).run(context, documents)
            self.assertTrue(
                any(
                    item.rule_id == "SPEC-STRUCT-H2-MISSING-001" and item.details.get("section") == "概述"
                    for item in structure
                )
            )
            self.assertIn("TRACE-RANGE-ID-001", {item.rule_id for item in trace.findings})
            self.assertIn("REF-NOT-FOUND-001", {item.rule_id for item in references.findings})
        finally:
            fixture.cleanup()

    def test_full_result_json_is_stable_for_identical_inputs(self) -> None:
        evaluator = EvaluationOrchestrator(EvaluationConfig.discover())
        first = evaluator.evaluate("04-06-01").to_dict(self.repo_root)
        second = evaluator.evaluate("04-06-01").to_dict(self.repo_root)
        snapshot = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(snapshot(first), snapshot(second))

    def test_parser_error_unclosed_fence_and_escaped_pipe_paths(self) -> None:
        fixture = TemporaryRepository()
        try:
            missing = fixture.function_root / "Feat-02-missing-spec.md"
            with self.assertRaises(ParseError):
                MarkdownParser(fixture.config).parse(missing)
            fixture.spec_path.write_text("# 特性规格\n```cpp\nint value = 1;\n", encoding="utf-8")
            document = MarkdownParser(fixture.config).parse(fixture.spec_path)
            self.assertEqual(len(document.code_blocks), 1)
            self.assertEqual(document.code_blocks[0].end_line, 3)
            self.assertEqual(split_table_row(r"| A | x\|y | C |"), ("A", r"x\|y", "C"))
        finally:
            fixture.cleanup()

    def test_gate_engine_honors_active_function_exemption(self) -> None:
        configuration = RuleConfiguration(
            version="test",
            defaults={"Major": "fail"},
            policies=(),
            exemptions=(
                Exemption(
                    rule_id="TRACE-*",
                    func_id="05-01-01",
                    reason="test only",
                    owner="spec-eval",
                    expires=date.today() + timedelta(days=1),
                ),
            ),
        )
        finding = Finding("TRACE-AC-NO-VM-001", Severity.MAJOR, "gap", "spec.md", func_id="05-01-01")
        result = GateEngine(configuration).evaluate("05-01-01", [finding])
        self.assertEqual(result.gate, "pass")
        self.assertEqual(result.exempted_count, 1)

    def test_full_scan_continues_after_one_function_error(self) -> None:
        calls: list[str] = []

        class FakeLocator:
            @staticmethod
            def all_func_ids() -> tuple[str, ...]:
                return ("01-01-01", "01-01-02")

        class FakeOrchestrator:
            def __init__(self, _config: EvaluationConfig) -> None:
                self.locator = FakeLocator()

            def evaluate_and_write(self, func_id, output_root, use_cache=True):
                calls.append(func_id)
                if func_id == "01-01-01":
                    raise ParseError("injected parse failure")
                return {"static": {"gate": "pass"}}, False, Path(output_root) / "revision" / func_id

        with tempfile.TemporaryDirectory() as directory, mock.patch(
            "spec_eval.cli.EvaluationOrchestrator", FakeOrchestrator
        ), contextlib.redirect_stdout(io.StringIO()):
            exit_code = cli.main(["--output", directory, "--json", "scan", "--all"])
        self.assertEqual(calls, ["01-01-01", "01-01-02"])
        self.assertEqual(exit_code, 3)


class Infra017CiRunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[4]
        config = EvaluationConfig.discover()
        locator = EvaluationOrchestrator(config).locator
        cls.changed_spec = config.repo_relative(locator.locate("04-06-01").feature_specs[0])
        cls.changed_multi_spec = config.repo_relative(locator.locate("02-01-04").feature_specs[0])

    def _run_ci(
        self,
        directory: Path,
        enforce: bool = False,
        changed_file: str | None = None,
        *,
        delta_enforce: bool = False,
        baseline: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        files = directory / "changed-files.txt"
        files.write_text((changed_file or self.changed_spec) + "\n", encoding="utf-8")
        output = directory / ("enforce" if enforce else "report-only")
        command = [
            sys.executable,
            "specs/tools/spec_eval/ci_runner.py",
            "--files-from",
            str(files),
            "--output",
            str(output),
            "--json",
            "--no-cache",
        ]
        if enforce:
            command.append("--enforce")
        if delta_enforce:
            command.append("--delta-enforce")
        if baseline is not None:
            command.extend(["--baseline", str(baseline)])
        return subprocess.run(command, cwd=self.repo_root, check=False, capture_output=True, text=True)

    def test_report_only_writes_summary_and_does_not_block_gate_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run_ci(Path(directory))
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["mode"], "report-only")
            self.assertEqual(summary["affected_function_count"], 1)
            self.assertEqual(summary["functions"][0]["func_id"], "04-06-01")
            self.assertEqual(summary["functions"][0]["gate"], "fail")
            self.assertEqual(summary["functions"][0]["feature_count"], 1)
            self.assertEqual(summary["exit_reasons"], [])
            self.assertTrue(Path(summary["summary_path"]).is_file())

    def test_changed_feature_evaluates_its_complete_multi_feature_function(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run_ci(Path(directory), changed_file=self.changed_multi_spec)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["functions"][0]["func_id"], "02-01-04")
            self.assertEqual(summary["functions"][0]["feature_count"], 3)
            self.assertEqual(summary["functions"][0]["document_count"], 4)

    def test_enforce_blocks_gate_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run_ci(Path(directory), enforce=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["mode"], "enforce")
            self.assertEqual(summary["gate_failed_count"], 1)
            self.assertEqual(summary["exit_reasons"][0]["code"], "ABSOLUTE_GATE_FAILED")

    def test_delta_enforce_allows_unchanged_historical_gate_failure(self) -> None:
        baseline = self.repo_root / "specs" / "evaluation" / "baselines" / "current.json"
        with tempfile.TemporaryDirectory() as directory:
            result = self._run_ci(Path(directory), delta_enforce=True, baseline=baseline)
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            function = summary["functions"][0]
            self.assertEqual(summary["mode"], "delta-enforce")
            self.assertEqual(function["absolute_gate"], "fail")
            self.assertEqual(function["delta_gate"], "pass")
            self.assertEqual(function["baseline_status"], "existing")
            self.assertEqual(function["delta"]["added"], 0)
            self.assertGreater(function["delta"]["unchanged"], 0)

    def test_delta_enforce_blocks_injected_added_major(self) -> None:
        config = EvaluationConfig.discover()
        real_orchestrator = EvaluationOrchestrator(config)
        finding = Finding(
            "TRACE-AC-NO-VM-001",
            Severity.MAJOR,
            "injected gap",
            self.changed_spec,
            func_id="04-06-01",
            feat_id="Feat-01",
            details={"node_id": "Feat-01/AC-injected"},
        ).to_dict()

        class AddedMajorOrchestrator:
            def __init__(self, _config: EvaluationConfig) -> None:
                self.locator = real_orchestrator.locator
                self.rule_configuration = real_orchestrator.rule_configuration

            @staticmethod
            def evaluate_and_write(func_id, output_root, use_cache=True):
                target = Path(output_root) / config.git_revision() / func_id
                return (
                    {
                        "static": {
                            "func_id": func_id,
                            "source_revision": config.git_revision(),
                            "tool_version": config.tool_version,
                            "rule_version": real_orchestrator.rule_configuration.version,
                            "gate": "fail",
                            "findings": [finding],
                            "metrics": {"feature_count": 1, "document_count": 2, "severity_counts": {"Major": 1}},
                        }
                    },
                    False,
                    target,
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = root / "changed-files.txt"
            files.write_text(self.changed_spec + "\n", encoding="utf-8")
            baseline = root / "baseline.json"
            baseline.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "identity_version": 1,
                        "source_revision": "baseline-revision",
                        "tool_version": config.tool_version,
                        "rule_version": real_orchestrator.rule_configuration.version,
                        "complete": True,
                        "scope": {"function_count": 1, "func_ids": ["04-06-01"]},
                        "finding_count": 0,
                        "unique_finding_count": 0,
                        "findings": [],
                    }
                ),
                encoding="utf-8",
            )
            args = ci_runner.build_parser().parse_args(
                [
                    "--files-from",
                    str(files),
                    "--output",
                    str(root / "output"),
                    "--baseline",
                    str(baseline),
                    "--delta-enforce",
                ]
            )
            with mock.patch("spec_eval.ci_runner.EvaluationOrchestrator", AddedMajorOrchestrator):
                summary, exit_code = ci_runner.run(args)
            self.assertEqual(exit_code, 1)
            self.assertEqual(summary["delta_gate_failed_count"], 1)
            self.assertEqual(summary["functions"][0]["delta_gate"], "fail")
            self.assertEqual(summary["functions"][0]["delta"]["added"], 1)
            self.assertEqual(summary["exit_reasons"][0]["code"], "DELTA_MAJOR_ADDED")

    def test_delta_enforce_requires_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self._run_ci(Path(directory), delta_enforce=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires --baseline", json.loads(result.stdout)["error"])

    def test_missing_change_list_is_a_tool_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "specs/tools/spec_eval/ci_runner.py",
                    "--files-from",
                    str(Path(directory) / "missing.txt"),
                    "--output",
                    str(Path(directory) / "output"),
                    "--json",
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "error")

    def test_git_base_head_mode_accepts_an_empty_diff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "specs/tools/spec_eval/ci_runner.py",
                    "--base",
                    "HEAD",
                    "--head",
                    "HEAD",
                    "--output",
                    str(Path(directory) / "output"),
                    "--json",
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["affected_function_count"], 0)

    def test_function_evaluation_error_uses_incomplete_exit_code(self) -> None:
        class FailingOrchestrator:
            def __init__(self, config: EvaluationConfig) -> None:
                self.locator = EvaluationOrchestrator(config).locator

            @staticmethod
            def evaluate_and_write(func_id, output_root, use_cache=True):
                raise ParseError(f"injected failure for {func_id}")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = root / "changed-files.txt"
            files.write_text(self.changed_spec + "\n", encoding="utf-8")
            args = ci_runner.build_parser().parse_args(
                ["--files-from", str(files), "--output", str(root / "output")]
            )
            with mock.patch("spec_eval.ci_runner.EvaluationOrchestrator", FailingOrchestrator):
                summary, exit_code = ci_runner.run(args)
            self.assertEqual(exit_code, 3)
            self.assertEqual(summary["error_count"], 1)
            self.assertEqual(summary["functions"][0]["gate"], "error")
            self.assertEqual(summary["exit_reasons"][0]["code"], "FUNCTION_EVALUATION_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
