from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from spec_eval.config import EvaluationConfig
from spec_eval.models import Finding, Severity
from spec_eval.orchestrator import EvaluationOrchestrator
from spec_eval.rules import GateEngine, RuleLoader


class Infra012To015Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[4]

    def test_gate_engine_applies_function_level_policy(self) -> None:
        config = EvaluationConfig.discover(output_root=Path(tempfile.mkdtemp()))
        rules = RuleLoader(config).load()
        engine = GateEngine(rules)
        minor = Finding("HYGIENE-ABSOLUTE-PATH-001", Severity.MAJOR, "path", "spec.md")
        major = Finding("TRACE-AC-NO-VM-001", Severity.MAJOR, "trace", "spec.md")
        self.assertEqual(engine.evaluate("05-03-10", [minor]).gate, "warn")
        self.assertEqual(engine.evaluate("05-03-10", [minor, major]).gate, "fail")

    def test_orchestrator_writes_report_and_reuses_exact_input_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            config = EvaluationConfig.discover(output_root=output)
            orchestrator = EvaluationOrchestrator(config)
            first, first_cached, target = orchestrator.evaluate_and_write("04-06-01", output, use_cache=True)
            second, second_cached, second_target = orchestrator.evaluate_and_write("04-06-01", output, use_cache=True)
            self.assertFalse(first_cached)
            self.assertTrue(second_cached)
            self.assertEqual(first["static"]["func_id"], "04-06-01")
            self.assertEqual(target, second_target)
            for name in (
                "function-context.json",
                "static-result.json",
                "evidence-manifest.json",
                "performance.json",
                "report.md",
            ):
                self.assertTrue((target / name).is_file(), name)
            static = json.loads((target / "static-result.json").read_text(encoding="utf-8"))
            self.assertIn(static["gate"], {"pass", "warn", "fail"})
            self.assertEqual(static["func_id"], "04-06-01")
            performance = json.loads((target / "performance.json").read_text(encoding="utf-8"))
            self.assertTrue(performance["cached"])
            manifest = json.loads((target / "evidence-manifest.json").read_text(encoding="utf-8"))
            self.assertIn("budget", manifest["archive"])

    def test_direct_cli_discover_is_runnable(self) -> None:
        result = subprocess.run(
            [
                "python3",
                "specs/tools/spec_eval/cli.py",
                "--json",
                "discover",
                "--func-id",
                "04-06-01",
            ],
            cwd=self.repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value["func_id"], "04-06-01")
        self.assertTrue(value["feature_specs"])


if __name__ == "__main__":
    unittest.main()
