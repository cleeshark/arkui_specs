from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from spec_eval.protocol_validator import validate_protocol
from spec_eval.stability import (
    StabilityInputError,
    build_stability_result,
    build_stability_result_from_paths,
)


class Next008StabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.schemas_root = cls.evaluation_root / "schemas"
        cls.fixtures_root = Path(__file__).resolve().parent / "fixtures" / "protocol"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)
        cls.criteria = {
            criterion["id"]: criterion
            for dimension in cls.rubric["dimensions"]
            for criterion in dimension["criteria"]
        }

    @staticmethod
    def static_result() -> dict:
        return {
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "tool_version": "0.5.0",
            "rule_version": "0.2.16",
            "gate": "pass",
            "findings": [],
            "metrics": {},
        }

    @staticmethod
    def evidence_manifest() -> dict:
        return {
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "metrics": {
                "claim_count": 0,
                "resolved_claim_count": 0,
                "evidence_coverage": 0,
            },
            "shards": [],
        }

    def semantic(self, run_id: str) -> dict:
        value = json.loads(
            (self.fixtures_root / "semantic-result.json").read_text(encoding="utf-8")
        )
        value["run_id"] = run_id
        value["evaluator_version"] = "skill:test-evaluator@1.0.0"
        return value

    def set_conclusion(self, semantic: dict, index: int, conclusion: str, marker: str) -> None:
        result = semantic["criterion_results"][index]
        result["conclusion"] = conclusion
        outcome = self.criteria[result["criterion_id"]]["outcomes"][conclusion]
        result["findings"] = [
            {
                "finding_id": "SEM-" + marker * 24,
                "criterion_id": result["criterion_id"],
                "severity": outcome["severity"],
                "conclusion": conclusion,
                "message": f"{result['criterion_id']} differs in {semantic['run_id']}",
                "recommendation": "Review the differing semantic conclusion.",
                "evidence_ids": [result["evidence"][0]["evidence_id"]],
            }
        ]

    def semantic_runs(self) -> list[dict]:
        run_a = self.semantic("run-a")
        run_b = self.semantic("run-b")
        run_c = self.semantic("run-c")
        for index in range(6):
            self.set_conclusion(run_b, index, "PARTIALLY_SUPPORTED", hex(index + 1)[2:])
        self.set_conclusion(run_b, 6, "PARTIALLY_SUPPORTED", "7")
        self.set_conclusion(run_c, 6, "CONTRADICTED", "8")
        return [run_a, run_b, run_c]

    @staticmethod
    def artifacts(runs: list[dict]) -> dict:
        return {
            "static_result": {
                "path": "static-result.json",
                "content_hash": "sha256:" + "a" * 64,
            },
            "evidence_manifest": {
                "path": "evidence-manifest.json",
                "content_hash": "sha256:" + "b" * 64,
            },
            "semantic_results": [
                {
                    "run_id": run["run_id"],
                    "path": f"{run['run_id']}/semantic-result.json",
                    "content_hash": "sha256:"
                    + hashlib.sha256(run["run_id"].encode("utf-8")).hexdigest(),
                }
                for run in runs
            ],
        }

    def build(self, runs: list[dict] | None = None, selected_run_id: str = "run-c") -> dict:
        values = runs or self.semantic_runs()
        return build_stability_result(
            static_result=self.static_result(),
            evidence_manifest=self.evidence_manifest(),
            semantic_results=values,
            selected_run_id=selected_run_id,
            rubric=self.rubric,
            complexity_rules=self.complexity,
            schemas_root=self.schemas_root,
            input_artifacts=self.artifacts(values),
        )

    def test_calculates_deterministic_raw_statistics_without_replacing_selected_run(self) -> None:
        result = self.build()
        scores = [item["raw_score"] for item in result["runs"]]
        expected_mean = round(sum(scores) / len(scores), 2)
        expected_stddev = round(math.sqrt(sum((score - expected_mean) ** 2 for score in scores) / 3), 2)
        statistics = result["score_statistics"]
        self.assertEqual(statistics["count"], 3)
        self.assertEqual(statistics["range"], max(scores) - min(scores))
        self.assertEqual(statistics["mean"], expected_mean)
        self.assertEqual(statistics["population_stddev"], expected_stddev)
        self.assertEqual(result["selected_run"]["run_id"], "run-c")
        selected = next(item for item in result["runs"] if item["run_id"] == "run-c")
        self.assertEqual(result["selected_run"]["raw_score"], selected["raw_score"])
        self.assertEqual(result["selected_run"]["selection_method"], "explicit")

    def test_reports_two_thirds_consensus_and_explicit_no_consensus(self) -> None:
        result = self.build()
        criteria = {item["criterion_id"]: item for item in result["criterion_consensus"]}
        first_id = self.rubric["dimensions"][0]["criteria"][0]["id"]
        seventh_id = [
            criterion["id"]
            for dimension in self.rubric["dimensions"]
            for criterion in dimension["criteria"]
        ][6]
        self.assertEqual(criteria[first_id]["status"], "CONSENSUS")
        self.assertEqual(criteria[first_id]["consensus_conclusion"], "SUPPORTED")
        self.assertEqual(criteria[first_id]["dissenting_run_ids"], ["run-b"])
        self.assertEqual(criteria[seventh_id]["status"], "NO_CONSENSUS")
        self.assertIsNone(criteria[seventh_id]["consensus_conclusion"])

    def test_marks_only_the_unique_consensus_deviation_outlier(self) -> None:
        result = self.build()
        runs = {item["run_id"]: item for item in result["runs"]}
        self.assertEqual(result["outlier_run_ids"], ["run-b"])
        self.assertEqual(runs["run-b"]["outlier_status"], "OUTLIER")
        self.assertEqual(runs["run-b"]["criterion_deviation_count"], 6)
        self.assertEqual(runs["run-a"]["outlier_status"], "INLIER")
        self.assertEqual(runs["run-c"]["criterion_deviation_count"], 0)

    def test_input_order_does_not_change_output(self) -> None:
        runs = self.semantic_runs()
        first = self.build(runs)
        reversed_runs = list(reversed(copy.deepcopy(runs)))
        second = build_stability_result(
            static_result=self.static_result(),
            evidence_manifest=self.evidence_manifest(),
            semantic_results=reversed_runs,
            selected_run_id="run-c",
            rubric=self.rubric,
            complexity_rules=self.complexity,
            schemas_root=self.schemas_root,
            input_artifacts=self.artifacts(reversed_runs),
        )
        self.assertEqual(first, second)

    def test_rejects_mixed_evaluator_versions_and_unknown_selection(self) -> None:
        runs = self.semantic_runs()
        runs[1]["evaluator_version"] = "skill:test-evaluator@2.0.0"
        with self.assertRaisesRegex(StabilityInputError, "evaluator_version"):
            self.build(runs)
        with self.assertRaisesRegex(StabilityInputError, "selected_run_id"):
            self.build(self.semantic_runs(), selected_run_id="missing")

    def test_path_entrypoint_and_cli_write_hashed_stability_result(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            static_path = root / "static-result.json"
            evidence_path = root / "evidence-manifest.json"
            static_path.write_text(json.dumps(self.static_result()) + "\n", encoding="utf-8")
            evidence_path.write_text(json.dumps(self.evidence_manifest()) + "\n", encoding="utf-8")
            semantic_paths = []
            for semantic in self.semantic_runs():
                path = root / f"{semantic['run_id']}.json"
                path.write_text(json.dumps(semantic) + "\n", encoding="utf-8")
                semantic_paths.append(path)
            output_path = root / "stability-result.json"
            command = [
                sys.executable,
                str(self.specs_root / "tools" / "spec_eval" / "cli.py"),
                "--json",
                "stability",
                "--static-result",
                str(static_path),
                "--evidence-manifest",
                str(evidence_path),
            ]
            for path in semantic_paths:
                command.extend(("--semantic-result", str(path)))
            command.extend(("--selected-run-id", "run-c", "--write", str(output_path)))
            completed = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["output_path"], str(output_path))
            result = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(
                result["input_artifacts"]["static_result"]["content_hash"],
                "sha256:" + hashlib.sha256(static_path.read_bytes()).hexdigest(),
            )
            direct = build_stability_result_from_paths(
                static_result_path=static_path,
                evidence_manifest_path=evidence_path,
                semantic_result_paths=semantic_paths,
                selected_run_id="run-c",
                evaluation_root=self.evaluation_root,
            )
            self.assertEqual(result, direct)


if __name__ == "__main__":
    unittest.main()
