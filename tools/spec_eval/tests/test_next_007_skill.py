from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from spec_eval.protocol_validator import validate_protocol, validate_semantic_result

SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / "skills" / "ohos-design-arkui-spec-evaluator" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from staged_run_support import (  # noqa: E402
    EVIDENCE_TYPES,
    OUTCOME_POLICY_BASIS_CRITERIA,
    build_aggregation_context,
    staged_output_contract,
    validate_aggregation_document,
    validate_observation_document,
)


class Next007EvaluatorSkillFrameworkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.skill_root = cls.specs_root / "skills" / "ohos-design-arkui-spec-evaluator"
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)

    def _staged_identity(self) -> dict[str, object]:
        return {
            "schema_version": 2,
            "evaluator_version": "skill:ohos-design-arkui-spec-evaluator@0.1.14",
            "func_id": "05-01-02",
            "source_revision": "d91b4e4990a990da2bfe809514e573e35852193e",
            "run_id": "validator-unit-test",
        }

    def _valid_observation(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        state = self._staged_identity()
        item = {
            "id": "feature:Feat-01",
            "type": "feature",
            "expected_claim_ids": ["Feat-01/AC-1", "Feat-01/AC-2"],
            "required_checks": ["claim_source_support", "boundary_state"],
        }
        evidence = {
            "evidence_id": "EV-unit",
            "type": "source_citation",
            "path": "frameworks/example.cpp",
            "source_revision": state["source_revision"],
            "content_hash": "sha256:" + "0" * 64,
            "description": "Unit-test evidence.",
        }
        document = {
            **state,
            "observation_id": item["id"],
            "observation_type": item["type"],
            "status": "complete",
            "expected_claim_ids": item["expected_claim_ids"],
            "reviewed_claim_ids": item["expected_claim_ids"],
            "completed_checks": item["required_checks"],
            "claim_reviews": [
                {
                    "claim_id": claim_id,
                    "status": "complete",
                    "local_outcome": "SUPPORTED",
                        "reviewed_units": ["dynamic", "static"],
                        "unit_reviews": [
                            {
                                "unit_id": "dynamic",
                                "facet_type": "observable_result",
                                "local_outcome": "SUPPORTED",
                                "evidence_ids": ["EV-unit"],
                                "fact": "The dynamic result is supported by the cited source.",
                            },
                            {
                                "unit_id": "static",
                                "facet_type": "observable_result",
                                "local_outcome": "SUPPORTED",
                                "evidence_ids": ["EV-unit"],
                                "fact": "The static result is supported by the cited source.",
                            },
                        ],
                    "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                    "evidence_ids": ["EV-unit"],
                    "defect_keys": [],
                    "reason": "Both initialized frontend units were checked.",
                }
                for claim_id in item["expected_claim_ids"]
            ],
            "observations": [
                {
                    "observation_id": "OBS-unit",
                    "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                    "check_ids": item["required_checks"],
                    "claim_ids": item["expected_claim_ids"],
                    "local_outcome": "SUPPORTED",
                    "breadth": "feat_core",
                    "contract_family": "unit-contract",
                    "fact": "The initialized claims were checked.",
                    "evidence": [evidence],
                }
            ],
        }
        return document, item, state

    def _criterion_results(self) -> list[dict[str, object]]:
        return [
            {
                "criterion_id": criterion["id"],
                "conclusion": "SUPPORTED",
                "reason": "Validated unit-test result.",
                "evidence": [],
                "findings": [],
            }
            for dimension in self.rubric["dimensions"]
            for criterion in dimension["criteria"]
        ]

    def test_skill_structure_and_frontmatter_are_versioned(self) -> None:
        skill_path = self.skill_root / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        _, frontmatter, _ = content.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
        self.assertEqual(metadata["name"], "ohos-design-arkui-spec-evaluator")
        self.assertEqual(metadata["metadata"]["version"], "0.1.14")
        self.assertEqual(metadata["metadata"]["rubric-version"], "0.3.0")
        self.assertLess(len(content.splitlines()), 500)
        for relative in (
            "references/input-output-contract.md",
            "references/criterion-guide.md",
            "references/staged-run-contract.md",
            "scripts/create_pilot_template.py",
            "scripts/initialize_staged_run.py",
            "scripts/show_next_work_item.py",
            "scripts/validate_staged_run.py",
            "scripts/assemble_semantic_result.py",
            "scripts/build_aggregation_context.py",
            "scripts/staged_run_support.py",
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
                "skill:ohos-design-arkui-spec-evaluator@0.1.14",
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
                "skill:ohos-design-arkui-spec-evaluator@0.1.14",
            )

    def test_machine_output_contract_matches_validator_and_rubric(self) -> None:
        source_revision = "a" * 40
        contract = staged_output_contract(source_revision=source_revision)
        expected_criteria = [
            criterion["id"]
            for dimension in self.rubric["dimensions"]
            for criterion in dimension["criteria"]
        ]
        self.assertEqual(contract["valid_criterion_ids"], expected_criteria)
        evidence = contract["common"]["evidence"]
        self.assertEqual(evidence["type_enum"], list(EVIDENCE_TYPES))
        self.assertEqual(evidence["evidence_id_pattern"], "^EV-[A-Za-z0-9._-]+$")
        self.assertEqual(
            evidence["content_hash_pattern"], "^sha256:[0-9a-f]{64}$"
        )
        example = evidence["format_example_only"]
        self.assertEqual(example["source_revision"], source_revision)
        self.assertTrue(example["content_hash"].startswith("sha256:"))
        mapping_contract = contract["aggregation_payload"]["mapping_context"]
        self.assertEqual(mapping_contract["schema_version"], 1)
        self.assertIn("claim_reviews[].criterion_ids", mapping_contract["mapping_authority"]["claims"])
        self.assertTrue(any("NOT_VERIFIABLE" in rule for rule in mapping_contract["mixed_outcome_policy"]))
        historical = staged_output_contract(
            source_revision=source_revision,
            evaluator_version="skill:ohos-design-arkui-spec-evaluator@0.1.12",
        )
        self.assertNotIn("mapping_context", historical["aggregation_payload"])
        previous = staged_output_contract(
            source_revision=source_revision,
            evaluator_version="skill:ohos-design-arkui-spec-evaluator@0.1.13",
        )
        self.assertIn("mapping_context", previous["aggregation_payload"])

    def test_observation_evidence_cardinality_is_machine_readable_and_enforced(self) -> None:
        contract = staged_output_contract(source_revision="a" * 40)
        minimums = contract["observation_payload"]["observations"][
            "evidence_cardinality"
        ]["minimum_items_by_local_outcome"]
        self.assertEqual(minimums, {
            "CONFLICT": 1,
            "MISSING": 1,
            "NOT_APPLICABLE": 1,
            "NOT_VERIFIABLE": 0,
            "SUPPORTED": 1,
        })
        na_example = contract["observation_payload"]["observations"][
            "evidence_cardinality"
        ]["not_applicable_example_only"]
        self.assertEqual(na_example["local_outcome"], "NOT_APPLICABLE")
        self.assertEqual(len(na_example["evidence"]), 1)

        for outcome, minimum in minimums.items():
            with self.subTest(outcome=outcome):
                document, item, state = self._valid_observation()
                observation = document["observations"][0]
                observation["local_outcome"] = outcome
                observation["evidence"] = []
                if outcome in {"CONFLICT", "MISSING"}:
                    observation["defect_key"] = "missing-observation-evidence"
                    observation["primary_criterion_id"] = "CORRECTNESS-SOURCE-SUPPORT"
                errors = validate_observation_document(document, item, state)
                has_cardinality_error = any(
                    "evidence is required for this local outcome" in error
                    for error in errors
                )
                self.assertEqual(has_cardinality_error, minimum > 0)

    def test_aggregation_context_is_deterministic_and_inherits_claim_unit_mapping(self) -> None:
        document, item, state = self._valid_observation()
        document["observations"][0]["criterion_ids"] *= 2
        document["claim_reviews"][0]["criterion_ids"] *= 2
        document["claim_reviews"][0]["local_outcome"] = "CONFLICT"
        document["claim_reviews"][0]["unit_reviews"][0]["local_outcome"] = "CONFLICT"
        document["claim_reviews"][0]["defect_keys"] = ["unit-defect"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(json.dumps(document), encoding="utf-8")
            item["output_path"] = str(observation_path)
            work_items = {"items": [item]}
            first = build_aggregation_context(state, work_items)
            second = build_aggregation_context(state, work_items)
        self.assertEqual(first, second)
        mapping = next(
            row
            for row in first["criterion_mappings"]
            if row["criterion_id"] == "CORRECTNESS-SOURCE-SUPPORT"
        )
        self.assertEqual(len(mapping["observations"]), 1)
        self.assertEqual(len(mapping["claims"]), 2)
        self.assertEqual(len(mapping["atomic_units"]), 4)
        self.assertIn("Feat-01/AC-1", mapping["mapped_claim_ids"])
        self.assertTrue(mapping["constraints"]["adverse_unit_refs"])
        self.assertEqual(
            mapping["constraints"]["forbidden_conclusions"],
            ["SUPPORTED", "NOT_APPLICABLE"],
        )

    def test_aggregation_context_does_not_treat_observation_claim_refs_as_claim_mapping(self) -> None:
        document, item, state = self._valid_observation()
        document["claim_reviews"][1]["criterion_ids"] = ["SPEC-SCOPE-BOUNDARY"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(json.dumps(document), encoding="utf-8")
            item["output_path"] = str(observation_path)
            context = build_aggregation_context(state, {"items": [item]})
        source_mapping = next(
            row
            for row in context["criterion_mappings"]
            if row["criterion_id"] == "CORRECTNESS-SOURCE-SUPPORT"
        )
        self.assertEqual(
            source_mapping["observations"][0]["claim_ids"], item["expected_claim_ids"]
        )
        self.assertEqual(source_mapping["mapped_claim_ids"], ["Feat-01/AC-1"])

    def test_aggregation_rejects_claim_cited_only_by_observation_mapping(self) -> None:
        document, item, state = self._valid_observation()
        document["claim_reviews"][1]["criterion_ids"] = ["SPEC-SCOPE-BOUNDARY"]
        results = self._criterion_results()
        results[0]["claim_ids"] = ["Feat-01/AC-2"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(json.dumps(document), encoding="utf-8")
            item["output_path"] = str(observation_path)
            aggregation = {
                **state,
                "status": "complete",
                "source_observation_ids": [item["id"]],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
                "outcome_policy_bases": self._valid_policy_bases(),
            }
            errors = validate_aggregation_document(
                aggregation, state, {"items": [item]}
            )
        self.assertTrue(any("claim_ids: not mapped to Criterion" in error for error in errors))

    def test_automated_template_accepts_explicit_non_pilot_revision(self) -> None:
        func_id = "01-01-02"  # registered Function, deliberately outside the frozen Pilot
        source_revision = "a" * 40
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            input_dir = root / "input"
            evidence_dir = input_dir / "evidence"
            evidence_dir.mkdir(parents=True)
            common = {"func_id": func_id, "source_revision": source_revision}
            (input_dir / "function-context.json").write_text(json.dumps(common), encoding="utf-8")
            (input_dir / "static-result.json").write_text(
                json.dumps({**common, "gate": "fail"}), encoding="utf-8"
            )
            (input_dir / "evidence-manifest.json").write_text(
                json.dumps({**common, "shards": [{"path": "dummy.json"}]}), encoding="utf-8"
            )
            (evidence_dir / "dummy.json").write_text("{}", encoding="utf-8")

            golden = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "create_pilot_template.py"),
                    "--func-id", func_id,
                    "--input-dir", str(input_dir),
                    "--run-id", "golden-must-stay-strict",
                    "--output", str(root / "golden.json"),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(golden.returncode, 2)
            self.assertIn("outside the frozen NEXT-007 Pilot", golden.stderr)

            output = root / "automated.json"
            automated = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "create_pilot_template.py"),
                    "--func-id", func_id,
                    "--input-dir", str(input_dir),
                    "--run-id", "automated-run",
                    "--output", str(output),
                    "--evaluation-mode", "automated",
                    "--source-revision", source_revision,
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(automated.returncode, 0, automated.stderr)
            semantic = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(semantic["func_id"], func_id)
            self.assertEqual(semantic["source_revision"], source_revision)

    def test_staged_run_externalizes_context_and_assembles_result(self) -> None:
        source_revision = yaml.safe_load(
            (self.evaluation_root / "golden" / "manifest.yaml").read_text(encoding="utf-8")
        )["revisions"]["ace_engine"]
        input_dir = self.specs_root / ".evaluator" / source_revision / "05-01-02"
        self.assertTrue(input_dir.is_dir(), input_dir)
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            initialize = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "initialize_staged_run.py"),
                    "--func-id",
                    "05-01-02",
                    "--input-dir",
                    str(input_dir),
                    "--run-id",
                    "staged-framework-test",
                    "--run-dir",
                    str(run_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(initialize.returncode, 0, initialize.stderr)
            state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
            work_items = json.loads((run_dir / "work-items.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_phase"], "feature_observations")
            self.assertEqual(
                [item["id"] for item in work_items["items"]],
                ["feature:Feat-01", "function-global"],
            )
            show_next = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "show_next_work_item.py"),
                    "--run-dir",
                    str(run_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(show_next.returncode, 0, show_next.stderr)
            next_payload = json.loads(show_next.stdout)
            self.assertEqual(next_payload["work_item"]["id"], "feature:Feat-01")
            self.assertNotIn("function-global", show_next.stdout)
            feature_inputs = work_items["items"][0]["input_paths"]
            self.assertFalse(any(path.endswith("static-result.json") for path in feature_inputs))
            self.assertFalse(any(path.endswith("report.md") for path in feature_inputs))
            self.assertTrue(any(path.endswith("static-Feat-01.json") for path in feature_inputs))

            for item in work_items["items"]:
                output = Path(item["output_path"])
                observation = json.loads(output.read_text(encoding="utf-8"))
                evidence_path = Path(item["input_paths"][1])
                digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
                observation["status"] = "complete"
                observation["reviewed_claim_ids"] = item["expected_claim_ids"]
                observation["completed_checks"] = item["required_checks"]
                evidence_id = "EV-" + item["id"].replace(":", "-")
                observation["claim_reviews"] = [
                    {
                        "claim_id": claim_id,
                        "status": "complete",
                        "local_outcome": "SUPPORTED",
                        "reviewed_units": ["initialized claim scope"],
                        "unit_reviews": [
                            {
                                "unit_id": "initialized claim scope",
                                "facet_type": "observable_result",
                                "local_outcome": "SUPPORTED",
                                "evidence_ids": [evidence_id],
                                "fact": "The initialized unit was checked against run-local evidence.",
                            }
                        ],
                        "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                        "evidence_ids": [evidence_id],
                        "defect_keys": [],
                        "reason": "The atomic claim scope was checked against run-local evidence.",
                    }
                    for claim_id in item["expected_claim_ids"]
                ]
                observation["observations"] = [
                    {
                        "observation_id": "OBS-" + item["id"].replace(":", "-"),
                        "criterion_ids": ["CORRECTNESS-SOURCE-SUPPORT"],
                        "check_ids": item["required_checks"],
                        "claim_ids": item["expected_claim_ids"],
                        "local_outcome": "SUPPORTED",
                        "breadth": "feat_core" if item["type"] == "feature" else "function_shared",
                        "contract_family": "staged-framework-test",
                        "fact": "The initialized work-item scope was reviewed for the staged framework test.",
                        "evidence": [
                            {
                                "evidence_id": evidence_id,
                                "type": "spec_location"
                                if item["type"] == "feature"
                                else "design_location",
                                "path": str(evidence_path),
                                "source_revision": source_revision,
                                "content_hash": f"sha256:{digest}",
                                "description": "Run-local staged framework test evidence.",
                            }
                        ],
                    }
                ]
                output.write_text(
                    json.dumps(observation, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )

            aggregation_path = run_dir / "aggregation.json"
            aggregation = json.loads(aggregation_path.read_text(encoding="utf-8"))
            aggregation["status"] = "complete"
            aggregation["source_observation_ids"] = [
                item["id"] for item in work_items["items"]
            ]
            aggregation["cross_feat_contracts_reviewed"] = True
            aggregation["contradiction_bases"] = []
            aggregation["defect_ownership"] = []
            aggregation["outcome_policy_bases"] = [
                {
                    "criterion_id": criterion_id,
                    "content_status": "PRESENT",
                    "evidence_status": "VERIFIED",
                    "conflict_scope": "NONE",
                    "reason": "The framework test provides a complete policy basis.",
                }
                for criterion_id in OUTCOME_POLICY_BASIS_CRITERIA
            ]
            criteria = {
                criterion["id"]: criterion
                for dimension in self.rubric["dimensions"]
                for criterion in dimension["criteria"]
            }
            rubric_path = self.evaluation_root / "rubric.yaml"
            rubric_digest = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
            for index, result in enumerate(aggregation["criterion_results"]):
                result["conclusion"] = "SUPPORTED"
                result["reason"] = "All staged observations were reviewed for the framework test."
                result.pop("missing_evidence", None)
                result["evidence"] = [
                    {
                        "evidence_id": f"EV-staged-criterion-{index:02d}",
                        "type": criteria[result["criterion_id"]]["required_evidence_types"][0],
                        "path": str(rubric_path),
                        "source_revision": source_revision,
                        "content_hash": f"sha256:{rubric_digest}",
                        "description": "Reproducible staged framework test evidence.",
                    }
                ]
            aggregation_path.write_text(
                json.dumps(aggregation, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            validate_observations = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "validate_staged_run.py"),
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    "observations",
                    "--update-state",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate_observations.returncode, 0, validate_observations.stderr)
            assemble = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "assemble_semantic_result.py"),
                    "--run-dir",
                    str(run_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(assemble.returncode, 0, assemble.stderr)
            validate_final = subprocess.run(
                [
                    sys.executable,
                    str(self.skill_root / "scripts" / "validate_staged_run.py"),
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    "final",
                    "--update-state",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validate_final.returncode, 0, validate_final.stderr)
            semantic = json.loads(
                (run_dir / "semantic-result.json").read_text(encoding="utf-8")
            )
            self.assertTrue(semantic["execution"]["semantic_complete"])
            self.assertEqual(semantic["coverage"]["not_verifiable_criteria"], 0)
            state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["current_phase"], "complete")

    def test_staged_v2_rejects_missing_atomic_claim_review(self) -> None:
        document, item, state = self._valid_observation()
        document["claim_reviews"] = document["claim_reviews"][:-1]
        errors = validate_observation_document(document, item, state)
        self.assertTrue(any("must contain every expected claim exactly once" in error for error in errors))

    def test_staged_v2_rejects_unmapped_required_check(self) -> None:
        document, item, state = self._valid_observation()
        document["observations"][0]["check_ids"] = ["claim_source_support"]
        document["completed_checks"] = ["claim_source_support"]
        errors = validate_observation_document(document, item, state)
        self.assertTrue(any("observations.check_ids: missing=['boundary_state']" in error for error in errors))

    def test_staged_v2_rejects_noncanonical_evaluator_version(self) -> None:
        document, item, state = self._valid_observation()
        state["evaluator_version"] = "0.1.11"
        document["evaluator_version"] = "0.1.11"
        errors = validate_observation_document(document, item, state)
        self.assertTrue(any("staged schema v2 requires" in error for error in errors))

    def test_staged_v2_017_historical_observation_remains_readable(self) -> None:
        document, item, state = self._valid_observation()
        historical = "skill:ohos-design-arkui-spec-evaluator@0.1.7"
        state["evaluator_version"] = historical
        document["evaluator_version"] = historical
        self.assertEqual(validate_observation_document(document, item, state), [])

    def test_staged_v2_018_historical_observation_remains_readable(self) -> None:
        document, item, state = self._valid_observation()
        historical = "skill:ohos-design-arkui-spec-evaluator@0.1.8"
        state["evaluator_version"] = historical
        document["evaluator_version"] = historical
        for review in document["claim_reviews"]:
            review.pop("unit_reviews")
        self.assertEqual(validate_observation_document(document, item, state), [])

    def test_staged_v2_019_historical_observation_remains_readable(self) -> None:
        document, item, state = self._valid_observation()
        historical = "skill:ohos-design-arkui-spec-evaluator@0.1.9"
        state["evaluator_version"] = historical
        document["evaluator_version"] = historical
        self.assertEqual(validate_observation_document(document, item, state), [])

    def test_staged_v2_013_historical_observation_remains_readable(self) -> None:
        document, item, state = self._valid_observation()
        historical = "skill:ohos-design-arkui-spec-evaluator@0.1.13"
        state["evaluator_version"] = historical
        document["evaluator_version"] = historical
        self.assertEqual(validate_observation_document(document, item, state), [])

    def test_staged_v2_019_requires_atomic_unit_reviews(self) -> None:
        document, item, state = self._valid_observation()
        document["claim_reviews"][0]["unit_reviews"] = []
        errors = validate_observation_document(document, item, state)
        self.assertTrue(any("unit_reviews: expected at least one atomic unit review" in error for error in errors))

    def test_staged_v2_019_requires_modeling_basis_for_feat_boundary_defect(self) -> None:
        document, item, state = self._valid_observation()
        observation = document["observations"][0]
        observation.update({
            "criterion_ids": ["FUNCTION-FEAT-BOUNDARY"],
            "local_outcome": "CONFLICT",
            "defect_key": "unit-ownership-overlap",
            "primary_criterion_id": "FUNCTION-FEAT-BOUNDARY",
        })
        for review in document["claim_reviews"]:
            review["local_outcome"] = "CONFLICT"
            review["criterion_ids"] = ["FUNCTION-FEAT-BOUNDARY"]
            review["defect_keys"] = ["unit-ownership-overlap"]
            review["unit_reviews"][0]["local_outcome"] = "CONFLICT"
        errors = validate_observation_document(document, item, state)
        self.assertTrue(any("modeling_basis: required" in error for error in errors))

    def test_staged_v1_historical_observation_remains_readable(self) -> None:
        document, item, state = self._valid_observation()
        state["schema_version"] = 1
        state["evaluator_version"] = "skill:ohos-design-arkui-spec-evaluator@0.1.6"
        document["schema_version"] = 1
        document["evaluator_version"] = state["evaluator_version"]
        document.pop("claim_reviews")
        document["observations"][0].pop("check_ids")
        self.assertEqual(validate_observation_document(document, item, state), [])

    def test_staged_v2_requires_basis_for_every_contradicted_criterion(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        results[0]["conclusion"] = "CONTRADICTED"
        document = {
            **state,
            "status": "complete",
            "source_observation_ids": [],
            "cross_feat_contracts_reviewed": True,
            "criterion_results": results,
            "defect_ownership": [],
            "contradiction_bases": [],
        }
        errors = validate_aggregation_document(document, state, {"items": []})
        self.assertTrue(any("must contain every CONTRADICTED Criterion" in error for error in errors))

    def _valid_policy_bases(self) -> list[dict[str, str]]:
        return [
            {
                "criterion_id": criterion_id,
                "content_status": "PRESENT",
                "evidence_status": "VERIFIED",
                "conflict_scope": "NONE",
                "reason": "The policy-sensitive content and evidence are complete for this unit test.",
            }
            for criterion_id in OUTCOME_POLICY_BASIS_CRITERIA
        ]

    def test_staged_v2_011_rejects_missing_when_policy_content_is_present(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        criterion_id = "SPEC-AC-TESTABILITY"
        next(item for item in results if item["criterion_id"] == criterion_id)["conclusion"] = "MISSING"
        with TemporaryDirectory() as temporary:
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": [],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
                "outcome_policy_bases": self._valid_policy_bases(),
            }
            errors = validate_aggregation_document(document, state, {"items": []})
        self.assertTrue(any("statuses require SUPPORTED" in error for error in errors))

    def test_staged_v2_011_accepts_partial_policy_evidence_for_present_content(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        criterion_id = "SPEC-AC-TESTABILITY"
        next(item for item in results if item["criterion_id"] == criterion_id)["conclusion"] = "PARTIALLY_SUPPORTED"
        bases = self._valid_policy_bases()
        next(item for item in bases if item["criterion_id"] == criterion_id)["evidence_status"] = "PARTIAL"
        with TemporaryDirectory() as temporary:
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": [],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
                "outcome_policy_bases": bases,
            }
            errors = validate_aggregation_document(document, state, {"items": []})
        self.assertEqual(errors, [])

    def test_staged_v2_011_allows_secondary_criterion_contradiction_basis(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        primary = results[0]["criterion_id"]
        secondary = results[1]["criterion_id"]
        next(item for item in results if item["criterion_id"] == primary)["conclusion"] = "PARTIALLY_SUPPORTED"
        next(item for item in results if item["criterion_id"] == secondary)["conclusion"] = "CONTRADICTED"
        results[0]["findings"] = [{
            "finding_id": "SEM-secondary-root-primary",
            "criterion_id": primary,
            "severity": "Major",
            "evidence_ids": [],
        }]
        results[1]["findings"] = [{
            "finding_id": "SEM-secondary-root-impact",
            "criterion_id": secondary,
            "severity": "Major",
            "evidence_ids": [],
        }]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(json.dumps({"observations": [{
                "local_outcome": "CONFLICT",
                "criterion_ids": [primary, secondary],
                "defect_key": "shared-secondary-root",
                "primary_criterion_id": primary,
            }]}), encoding="utf-8")
            work_items = {"items": [{"id": "feature:Feat-01", "output_path": str(observation_path)}]}
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": ["feature:Feat-01"],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [{
                    "criterion_id": secondary,
                    "core_claim": "A shared root defect overturns the secondary Criterion core.",
                    "affected_feat_ids": ["Feat-01"],
                    "independent_contract_families": ["family-a", "family-b"],
                    "function_shared_assertion": False,
                    "core_scope": "secondary-core",
                    "correction_scope": "replace_core",
                    "why_partial_is_insufficient": "The shared defect requires replacing the Criterion core.",
                    "primary_defect_key": "shared-secondary-root",
                }],
                "defect_ownership": [{
                    "defect_key": "shared-secondary-root",
                    "primary_criterion_id": primary,
                    "finding_ids": ["SEM-secondary-root-primary", "SEM-secondary-root-impact"],
                    "secondary_criterion_ids": [secondary],
                }],
                "outcome_policy_bases": self._valid_policy_bases(),
            }
            errors = validate_aggregation_document(document, state, work_items)
        self.assertEqual(errors, [])

    def test_staged_v2_019_rejects_supported_criterion_with_adverse_observation(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        criterion_id = results[0]["criterion_id"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(
                json.dumps({"observations": [{
                    "local_outcome": "CONFLICT",
                    "criterion_ids": [criterion_id],
                    "defect_key": "adverse-unit-defect",
                    "primary_criterion_id": criterion_id,
                }]}),
                encoding="utf-8",
            )
            work_items = {"items": [{"id": "feature:Feat-01", "output_path": str(observation_path)}]}
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": ["feature:Feat-01"],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
            }
            errors = validate_aggregation_document(document, state, work_items)
        self.assertTrue(any("mapped adverse units" in error for error in errors))

    def test_staged_v2_013_claim_conflict_blocks_supported_without_adverse_observation(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        criterion_id = results[0]["criterion_id"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(
                json.dumps({
                    "observations": [],
                    "claim_reviews": [{
                        "claim_id": "Feat-01/AC-1.1",
                        "local_outcome": "CONFLICT",
                        "criterion_ids": [criterion_id],
                        "defect_keys": ["claim-conflict"],
                        "unit_reviews": [{
                            "unit_id": "ownership",
                            "facet_type": "ownership",
                            "local_outcome": "CONFLICT",
                        }],
                    }],
                }),
                encoding="utf-8",
            )
            work_items = {"items": [{"id": "feature:Feat-01", "output_path": str(observation_path)}]}
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": ["feature:Feat-01"],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
            }
            errors = validate_aggregation_document(document, state, work_items)
        self.assertTrue(any("claim:feature:Feat-01:Feat-01/AC-1.1=CONFLICT" in error for error in errors))

    def test_staged_v2_010_rejects_supported_criterion_with_unverifiable_claim_unit(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        criterion_id = results[0]["criterion_id"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(
                json.dumps({
                    "observations": [],
                    "claim_reviews": [{
                        "claim_id": "Feat-01/AC-1.1",
                        "local_outcome": "NOT_VERIFIABLE",
                        "criterion_ids": [criterion_id],
                        "unit_reviews": [{
                            "unit_id": "source-proof",
                            "local_outcome": "NOT_VERIFIABLE",
                        }],
                    }],
                }),
                encoding="utf-8",
            )
            work_items = {"items": [{"id": "feature:Feat-01", "output_path": str(observation_path)}]}
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": ["feature:Feat-01"],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
            }
            errors = validate_aggregation_document(document, state, work_items)
        self.assertTrue(any("mapped NOT_VERIFIABLE" in error for error in errors))

    def test_staged_v2_019_historical_aggregation_keeps_prior_unverifiable_policy(self) -> None:
        state = self._staged_identity()
        historical = "skill:ohos-design-arkui-spec-evaluator@0.1.9"
        state["evaluator_version"] = historical
        results = self._criterion_results()
        criterion_id = results[0]["criterion_id"]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(
                json.dumps({
                    "observations": [{
                        "local_outcome": "NOT_VERIFIABLE",
                        "criterion_ids": [criterion_id],
                    }],
                }),
                encoding="utf-8",
            )
            work_items = {"items": [{"id": "feature:Feat-01", "output_path": str(observation_path)}]}
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": ["feature:Feat-01"],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [],
            }
            errors = validate_aggregation_document(document, state, work_items)
        self.assertFalse(any("mapped NOT_VERIFIABLE" in error for error in errors))

    def test_skill_requires_helper_reachability_ac_assets_adr_facets_and_scope_isolation(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        evals = (self.skill_root / "evals" / "evals.json").read_text(encoding="utf-8")
        normalized = " ".join((skill + guide + evals).split())
        self.assertIn("parent entry", normalized)
        self.assertIn("direct-success", normalized)
        self.assertIn("produced Host binary", normalized)
        self.assertIn("six substantive facets", normalized)
        self.assertIn("WithInstance", normalized)
        self.assertIn("mapped `NOT_VERIFIABLE`", normalized)

    def test_staged_v2_rejects_multiple_critical_findings_for_one_defect(self) -> None:
        state = self._staged_identity()
        results = self._criterion_results()
        first_id = results[0]["criterion_id"]
        second_id = results[1]["criterion_id"]
        results[0]["findings"] = [
            {"finding_id": "SEM-unit-a", "criterion_id": first_id, "severity": "Critical", "evidence_ids": []}
        ]
        results[1]["findings"] = [
            {"finding_id": "SEM-unit-b", "criterion_id": second_id, "severity": "Critical", "evidence_ids": []}
        ]
        with TemporaryDirectory() as temporary:
            observation_path = Path(temporary) / "observation.json"
            observation_path.write_text(
                json.dumps({"observations": [{
                    "local_outcome": "CONFLICT",
                    "defect_key": "shared-root-defect",
                    "primary_criterion_id": first_id,
                }]}),
                encoding="utf-8",
            )
            work_items = {"items": [{"id": "feature:Feat-01", "output_path": str(observation_path)}]}
            document = {
                **state,
                "status": "complete",
                "source_observation_ids": ["feature:Feat-01"],
                "cross_feat_contracts_reviewed": True,
                "criterion_results": results,
                "contradiction_bases": [],
                "defect_ownership": [{
                    "defect_key": "shared-root-defect",
                    "primary_criterion_id": first_id,
                    "finding_ids": ["SEM-unit-a", "SEM-unit-b"],
                    "secondary_criterion_ids": [second_id],
                }],
            }
            errors = validate_aggregation_document(document, state, work_items)
        self.assertTrue(any("at most one Critical Finding" in error for error in errors))

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

    def test_skill_uses_progressive_loading_and_durable_checkpoints(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        staged = (self.skill_root / "references" / "staged-run-contract.md").read_text(
            encoding="utf-8"
        )
        normalized_skill = " ".join(skill.split())
        self.assertIn("Do not preload full `work-items.json`, `static-result.json`", normalized_skill)
        self.assertIn("durable handoff after context compaction", skill)
        self.assertIn("Do not assign final Criterion conclusions", skill)
        self.assertIn("cross_feat_contracts_reviewed=true", skill)
        self.assertIn("disposable run-local state", staged)
        self.assertIn("Feature workers record local facts", staged)

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

    def test_skill_stabilizes_function_wide_contradiction_and_impact_precedence(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("two independent core contract families", " ".join(skill.split()))
        self.assertIn("`contradiction_bases`", skill)
        self.assertIn("`defect_ownership`", skill)
        self.assertIn("do not use “most rows are supported”", guide)
        self.assertIn("contradiction precedence", guide)
        normalized_guide = " ".join(guide.lower().split())
        self.assertIn("recognizes no ac or no closure across the function", normalized_guide)
        self.assertIn("a dependency, not automatically duplicate ownership", normalized_guide)

    def test_skill_keeps_existing_material_adrs_applicable_for_simple_functions(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        normalized_skill = " ".join(skill.split())
        normalized_guide = " ".join(guide.split())
        self.assertIn("complexity controls whether the evaluator should demand a new ADR", normalized_skill)
        self.assertIn("this Criterion is applicable even for a simple Function", normalized_skill)
        self.assertIn("it does not make an existing material ADR disappear", normalized_guide)
        self.assertIn("An inaccurate existing ADR is `PARTIALLY_SUPPORTED` or `CONTRADICTED`", normalized_guide)

    def test_skill_requires_atomic_contract_facets_and_acceptance_ownership_evidence(self) -> None:
        skill = (self.skill_root / "SKILL.md").read_text(encoding="utf-8")
        staged = (self.skill_root / "references" / "staged-run-contract.md").read_text(
            encoding="utf-8"
        )
        guide = (self.skill_root / "references" / "criterion-guide.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("`unit_reviews`", skill)
        self.assertIn("callback result", skill)
        self.assertIn("`modeling_basis`", skill)
        self.assertIn("two owner Feats with independent acceptance claims", staged)
        self.assertIn("source-file overlap", guide)

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
