from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from spec_eval.protocol_validator import validate_protocol, validate_semantic_result


class Next007EvaluatorSkillFrameworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.skill_root = cls.specs_root / "skills" / "ohos-design-arkui-spec-evaluator"
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)

    def test_skill_structure_and_frontmatter_are_versioned(self) -> None:
        skill_path = self.skill_root / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        _, frontmatter, _ = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual(metadata["name"], "ohos-design-arkui-spec-evaluator")
        self.assertEqual(metadata["metadata"]["version"], "0.1.4")
        self.assertEqual(metadata["metadata"]["rubric-version"], "0.3.0")
        self.assertLess(len(content.splitlines()), 500)
        for relative in (
            "references/input-output-contract.md",
            "references/criterion-guide.md",
            "scripts/create_pilot_template.py",
            "scripts/validate_semantic_result.py",
            "evals/evals.json",
        ):
            self.assertTrue((self.skill_root / relative).is_file(), relative)

    def test_eval_set_covers_three_representative_pilot_functions(self) -> None:
        document = json.loads((self.skill_root / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(document["skill_name"], "ohos-design-arkui-spec-evaluator")
        self.assertEqual([item["id"] for item in document["evals"]], [1, 2, 3])
        prompts = "\n".join(item["prompt"] for item in document["evals"])
        for func_id in ("05-01-02", "03-07-01", "05-03-10"):
            self.assertIn(func_id, prompts)
        for item in document["evals"]:
            self.assertGreaterEqual(len(item["expectations"]), 4)

    def test_template_and_validator_close_the_semantic_contract(self) -> None:
        self.assertEqual(self.protocol_errors, [])
        source_revision = yaml.safe_load(
            (self.evaluation_root / "golden" / "manifest.yaml").read_text(encoding="utf-8")
        )["revisions"]["ace_engine"]
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir = root / "input"
            evidence_dir = input_dir / "evidence"
            evidence_dir.mkdir(parents=True)
            common = {"func_id": "05-01-02", "source_revision": source_revision}
            (input_dir / "function-context.json").write_text(
                json.dumps(common), encoding="utf-8"
            )
            (input_dir / "static-result.json").write_text(
                json.dumps({**common, "gate": "fail"}), encoding="utf-8"
            )
            (input_dir / "evidence-manifest.json").write_text(
                json.dumps({**common, "shards": [{"path": "Feat-01.json"}]}),
                encoding="utf-8",
            )
            (evidence_dir / "Feat-01.json").write_text("{}", encoding="utf-8")
            result_path = root / "semantic-result.json"
            create = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "create_pilot_template.py"),
                    "--func-id",
                    "05-01-02",
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "framework-test-run",
                    "--output",
                    str(result_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(create.returncode, 0, create.stderr)
            semantic = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(
                semantic["evaluator_version"],
                "skill:ohos-design-arkui-spec-evaluator@0.1.4",
            )
            expected_ids = [
                criterion["id"]
                for dimension in self.rubric["dimensions"]
                for criterion in dimension["criteria"]
            ]
            self.assertEqual(
                [item["criterion_id"] for item in semantic["criterion_results"]],
                expected_ids,
            )
            self.assertEqual(len(expected_ids), 20)
            self.assertEqual(
                validate_semantic_result(
                    semantic,
                    self.rubric,
                    self.complexity,
                    self.evaluation_root / "schemas",
                ),
                [],
            )
            validate = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "validate_semantic_result.py"),
                    str(result_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stderr)
            self.assertIn("criteria=20", validate.stdout)

    def test_template_discovers_specs_root_from_installed_layout(self) -> None:
        source_revision = yaml.safe_load(
            (self.evaluation_root / "golden" / "manifest.yaml").read_text(encoding="utf-8")
        )["revisions"]["ace_engine"]
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed_script = root / "installed-skill" / "scripts" / "create_pilot_template.py"
            installed_script.parent.mkdir(parents=True)
            shutil.copy2(self.skill_root / "scripts" / "create_pilot_template.py", installed_script)
            input_dir = root / "input"
            evidence_dir = input_dir / "evidence"
            evidence_dir.mkdir(parents=True)
            common = {"func_id": "05-01-02", "source_revision": source_revision}
            (input_dir / "function-context.json").write_text(json.dumps(common), encoding="utf-8")
            (input_dir / "static-result.json").write_text(
                json.dumps({**common, "gate": "fail"}), encoding="utf-8"
            )
            (input_dir / "evidence-manifest.json").write_text(
                json.dumps({**common, "shards": [{"path": "Feat-01.json"}]}),
                encoding="utf-8",
            )
            (evidence_dir / "Feat-01.json").write_text("{}", encoding="utf-8")
            output = root / "semantic-result.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(installed_script),
                    "--func-id",
                    "05-01-02",
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "installed-layout-test",
                    "--output",
                    str(output),
                ],
                cwd=self.specs_root.parent,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8"))["evaluator_version"],
                "skill:ohos-design-arkui-spec-evaluator@0.1.4",
            )

    def test_skill_enforces_blind_mode_unit_coverage_and_aggregation(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        contract = (self.skill_root / "references" / "input-output-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("specs/evaluation/reviews/**", skill)
        self.assertIn("specs/.evaluator/next-007/**", skill)
        self.assertIn("scratch coverage matrix", skill)
        self.assertIn("every AC and Rule claim", skill)
        self.assertIn("Do not use “worst local observation wins.”", guide)
        self.assertIn("test target, produced binary, Suite.Case, filter", guide)
        self.assertIn("machine-verifiable AC/Rule/VM chain", contract)

    def test_skill_prioritizes_rubric_outcomes_and_deep_ac_checks(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Criterion's frozen `outcome_policy`", skill)
        self.assertIn("terminology, direction/axis", skill)
        self.assertIn("exact result assertion", skill)
        self.assertIn("`DESIGN-IMPACT-COVERAGE` is `MISSING`", guide)
        self.assertIn("main/cross axis", guide)
        self.assertIn("below-minimum, exact boundary", guide)
        self.assertIn("only says “no BUILD change”", guide)

    def test_skill_stabilizes_reset_state_and_verification_plan_outcomes(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Reset/default/update semantics", skill)
        self.assertIn("gates/API versions, prior state", skill)
        self.assertIn("For `DESIGN-VERIFICATION-PLAN`", skill)
        self.assertIn("Use `MISSING` only when no Function-specific verification direction", skill)
        self.assertIn("build an explicit state matrix", guide)
        self.assertIn("user-set marker, cached resource", guide)
        self.assertIn("the plan body exists", guide)
        self.assertIn("Never assign `MISSING` solely", guide)

    def test_skill_stabilizes_device_feat_ownership_and_finding_granularity(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        contract = (self.skill_root / "references" / "input-output-contract.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("An included device form makes `COMPATIBILITY-MULTI-DEVICE` applicable", skill)
        self.assertIn("Dedicated per-device tests improve confidence", guide)
        self.assertIn("implementation mechanisms rather than separate capabilities", guide)
        self.assertIn("independently observable and independently acceptable capability", skill)
        self.assertIn("Do not combine unrelated problems", contract)

    def test_divider_pilot_scope_is_visible_without_reading_review(self) -> None:
        manifest = yaml.safe_load(
            (self.evaluation_root / "golden" / "manifest.yaml").read_text(encoding="utf-8")
        )
        divider = next(item for item in manifest["pilot_functions"] if item["func_id"] == "05-01-02")
        self.assertEqual(
            divider["evaluation_scope"]["include"],
            ["OHOS phone、tablet、foldable设备形态"],
        )
        source_revision = manifest["revisions"]["ace_engine"]
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir = root / "input"
            evidence_dir = input_dir / "evidence"
            evidence_dir.mkdir(parents=True)
            common = {"func_id": "05-01-02", "source_revision": source_revision}
            (input_dir / "function-context.json").write_text(json.dumps(common), encoding="utf-8")
            (input_dir / "static-result.json").write_text(
                json.dumps({**common, "gate": "fail"}), encoding="utf-8"
            )
            (input_dir / "evidence-manifest.json").write_text(
                json.dumps({**common, "shards": [{"path": "Feat-01.json"}]}),
                encoding="utf-8",
            )
            (evidence_dir / "Feat-01.json").write_text("{}", encoding="utf-8")
            output = root / "result.json"
            create = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "create_pilot_template.py"),
                    "--func-id",
                    "05-01-02",
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "scope-test",
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(create.returncode, 0, create.stderr)
            notes = json.loads(output.read_text(encoding="utf-8"))["execution"]["notes"]
            self.assertIn(
                "Pilot evaluation scope include: OHOS phone、tablet、foldable设备形态",
                notes,
            )
            self.assertIn(
                "Pilot evaluation scope exclude: wearable Static Modifier支持",
                notes,
            )
            self.assertIn(
                "Pilot evaluation scope non-finding: 无可复现验证场景的1px硬件取整观察",
                notes,
            )

    def test_template_rejects_non_pilot_function(self) -> None:
        with TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "create_pilot_template.py"),
                    "--func-id",
                    "05-01-01",
                    "--input-dir",
                    temporary,
                    "--run-id",
                    "non-pilot",
                    "--output",
                    str(Path(temporary) / "result.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("outside the frozen NEXT-007 Pilot", result.stderr)


if __name__ == "__main__":
    unittest.main()
