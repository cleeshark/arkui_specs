from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from spec_eval.function_analysis import (
    FunctionAnalysisInputError,
    build_function_analysis,
    build_function_analysis_from_paths,
)
from spec_eval.protocol_validator import validate_protocol
from spec_eval.score import build_score_result


class Next008FunctionAnalysisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.schemas_root = cls.evaluation_root / "schemas"
        cls.fixtures_root = Path(__file__).resolve().parent / "fixtures" / "protocol"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)

    @staticmethod
    def static_result() -> dict:
        return {
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "tool_version": "0.5.0",
            "rule_version": "0.2.16",
            "gate": "fail",
            "findings": [
                {
                    "finding_id": "FND-" + "1" * 24,
                    "identity_version": 1,
                    "problem_key": "trace gap",
                    "rule_id": "TRACE-001",
                    "severity": "Major",
                    "message": "Feat-01 trace gap",
                    "path": "specs/sample/Feat-01-sample-spec.md",
                    "feat_id": "Feat-01",
                    "claim_id": "Feat-01/AC-1.1",
                    "recommendation": "Close the traceability gap.",
                },
                {
                    "finding_id": "FND-" + "2" * 24,
                    "identity_version": 1,
                    "problem_key": "minor hygiene",
                    "rule_id": "HYGIENE-001",
                    "severity": "Minor",
                    "message": "Feat-02 hygiene issue",
                    "path": "specs/sample/Feat-02-sample-spec.md",
                    "feat_id": "Feat-02",
                },
            ],
            "metrics": {
                "traceability": {
                    "per_feat": {
                        "Feat-01": {"ac_count": 2, "closed_ac_count": 1, "closure_rate": 0.5},
                        "Feat-02": {"ac_count": 2, "closed_ac_count": 2, "closure_rate": 1.0},
                    }
                }
            },
        }

    @staticmethod
    def evidence_manifest() -> dict:
        return {
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "metrics": {
                "claim_count": 4,
                "resolved_claim_count": 2,
                "evidence_coverage": 0.5,
            },
            "shards": [
                {"name": "Feat-01", "path": "Feat-01.json", "claim_count": 2},
                {"name": "Feat-02", "path": "Feat-02.json", "claim_count": 2},
            ],
        }

    @staticmethod
    def evidence_shards() -> dict[str, dict]:
        common = {"func_id": "05-01-01", "source_revision": "abc123"}
        return {
            "Feat-01": {
                **common,
                "claims": [
                    {
                        "claim_id": "Feat-01/AC-1.1",
                        "feat_id": "Feat-01",
                        "evidence_status": "RESOLVED",
                    },
                    {
                        "claim_id": "Feat-01/R-1",
                        "feat_id": "Feat-01",
                        "evidence_status": "NO_EVIDENCE",
                    },
                ],
            },
            "Feat-02": {
                **common,
                "claims": [
                    {
                        "claim_id": "Feat-02/AC-1.1",
                        "feat_id": "Feat-02",
                        "evidence_status": "PARTIALLY_RESOLVED",
                    },
                    {
                        "claim_id": "Feat-02/R-1",
                        "feat_id": "Feat-02",
                        "evidence_status": "RESOLVED",
                    },
                ],
            },
        }

    def semantic_result(self) -> dict:
        semantic = json.loads(
            (self.fixtures_root / "semantic-result.json").read_text(encoding="utf-8")
        )
        for index, feat_id in enumerate(("Feat-01", "Feat-02")):
            criterion = semantic["criterion_results"][index]
            criterion["conclusion"] = "PARTIALLY_SUPPORTED"
            criterion["claim_ids"] = [f"{feat_id}/AC-1.1"]
            criterion["findings"] = [
                {
                    "finding_id": "SEM-" + str(index + 3) * 24,
                    "criterion_id": criterion["criterion_id"],
                    "severity": "Major",
                    "conclusion": "PARTIALLY_SUPPORTED",
                    "message": "Shared semantic root cause.",
                    "recommendation": "Correct the shared behavior contract.",
                    "evidence_ids": [criterion["evidence"][0]["evidence_id"]],
                }
            ]
        return semantic

    def build(self) -> dict:
        static = self.static_result()
        evidence = self.evidence_manifest()
        semantic = self.semantic_result()
        score = self.score_result(static=static, evidence=evidence, semantic=semantic)
        return build_function_analysis(
            static_result=static,
            evidence_manifest=evidence,
            evidence_shards=self.evidence_shards(),
            semantic_result=semantic,
            score_result=score,
            input_artifacts=self.input_artifacts(),
        )

    @staticmethod
    def input_artifacts() -> dict:
        return {
            "static_result": {"path": "static-result.json", "content_hash": "sha256:" + "a" * 64},
            "evidence_manifest": {
                "path": "evidence-manifest.json",
                "content_hash": "sha256:" + "b" * 64,
            },
            "semantic_result": {
                "path": "semantic-result.json",
                "content_hash": "sha256:" + "c" * 64,
            },
            "evidence_shards": [
                {
                    "name": "Feat-01",
                    "path": "evidence/Feat-01.json",
                    "content_hash": "sha256:" + "d" * 64,
                },
                {
                    "name": "Feat-02",
                    "path": "evidence/Feat-02.json",
                    "content_hash": "sha256:" + "e" * 64,
                },
            ],
        }

    def score_result(
        self,
        *,
        static: dict | None = None,
        evidence: dict | None = None,
        semantic: dict | None = None,
    ) -> dict:
        return build_score_result(
            static_result=static or self.static_result(),
            evidence_manifest=evidence or self.evidence_manifest(),
            semantic_result=semantic or self.semantic_result(),
            rubric=self.rubric,
            complexity_rules=self.complexity,
            schemas_root=self.schemas_root,
        )

    def test_records_complete_version_and_input_fingerprint_envelope(self) -> None:
        analysis = self.build()
        self.assertEqual(
            analysis["versions"],
            {
                "static_tool_version": "0.5.0",
                "static_rule_version": "0.2.16",
                "evaluator_protocol_version": "0.3.0",
                "evaluator_version": "fixture-1.0.0",
                "rubric_version": "0.3.0",
                "complexity_rules_version": "0.2.0",
                "aggregator_protocol_version": "0.1.0",
                "aggregator_version": "spec-eval-score@0.1.0",
            },
        )
        self.assertEqual(set(analysis["input_artifacts"]), {
            "static_result", "evidence_manifest", "semantic_result", "evidence_shards"
        })

    def test_rejects_score_and_semantic_version_mismatch(self) -> None:
        score = self.score_result()
        score["rubric_version"] = "stale"
        with self.assertRaisesRegex(FunctionAnalysisInputError, "rubric_version mismatch"):
            build_function_analysis(
                static_result=self.static_result(),
                evidence_manifest=self.evidence_manifest(),
                evidence_shards=self.evidence_shards(),
                semantic_result=self.semantic_result(),
                score_result=score,
                input_artifacts=self.input_artifacts(),
            )

    def test_groups_and_ranks_top_remediations_deterministically(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        top = first["top_remediations"]
        self.assertEqual(top[0]["source"], "semantic")
        self.assertEqual(top[0]["priority"], "P1")
        self.assertEqual(len(top[0]["finding_ids"]), 2)
        self.assertEqual(top[0]["feat_ids"], ["Feat-01", "Feat-02"])
        self.assertEqual(top[0]["claim_ids"], ["Feat-01/AC-1.1", "Feat-02/AC-1.1"])
        self.assertEqual(top[1]["rule_ids"], ["TRACE-001"])

    def test_builds_feat_risk_distribution_from_findings_claims_and_traceability(self) -> None:
        analysis = self.build()
        risks = {item["feat_id"]: item for item in analysis["feat_risks"]}
        self.assertEqual(risks["Feat-01"]["risk_level"], "Major")
        self.assertEqual(risks["Feat-01"]["claims"]["support_rate"], 0.5)
        self.assertEqual(risks["Feat-01"]["traceability"]["closure_rate"], 0.5)
        self.assertEqual(risks["Feat-01"]["finding_counts"], {
            "Critical": 0, "Major": 2, "Minor": 0, "Info": 0
        })
        self.assertEqual(risks["Feat-02"]["claims"]["partially_resolved"], 1)
        self.assertEqual(risks["Feat-02"]["finding_counts"]["Minor"], 1)

    def test_rejects_evidence_shard_from_another_revision(self) -> None:
        shards = copy.deepcopy(self.evidence_shards())
        shards["Feat-01"]["source_revision"] = "different"
        with self.assertRaisesRegex(FunctionAnalysisInputError, "source_revision"):
            build_function_analysis(
                static_result=self.static_result(),
                evidence_manifest=self.evidence_manifest(),
                evidence_shards=shards,
                semantic_result=self.semantic_result(),
                score_result=self.score_result(),
                input_artifacts=self.input_artifacts(),
            )

    def test_path_entrypoint_hashes_inputs_and_cli_writes_analysis(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence_dir = root / "evidence"
            evidence_dir.mkdir()
            documents = {
                "static-result.json": self.static_result(),
                "evidence-manifest.json": self.evidence_manifest(),
                "semantic-result.json": self.semantic_result(),
            }
            for name, document in documents.items():
                (root / name).write_text(
                    json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            for name, document in self.evidence_shards().items():
                (evidence_dir / f"{name}.json").write_text(
                    json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            score_path = root / "score-result.json"
            analysis_path = root / "function-analysis.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self.specs_root / "tools" / "spec_eval" / "cli.py"),
                    "--json",
                    "score",
                    "--static-result",
                    str(root / "static-result.json"),
                    "--evidence-manifest",
                    str(root / "evidence-manifest.json"),
                    "--semantic-result",
                    str(root / "semantic-result.json"),
                    "--write",
                    str(score_path),
                    "--analysis-write",
                    str(analysis_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["analysis_path"], str(analysis_path))
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            static_bytes = (root / "static-result.json").read_bytes()
            self.assertEqual(
                analysis["input_artifacts"]["static_result"]["content_hash"],
                "sha256:" + hashlib.sha256(static_bytes).hexdigest(),
            )
            self.assertEqual(
                [item["name"] for item in analysis["input_artifacts"]["evidence_shards"]],
                ["Feat-01", "Feat-02"],
            )
            direct = build_function_analysis_from_paths(
                static_result_path=root / "static-result.json",
                evidence_manifest_path=root / "evidence-manifest.json",
                semantic_result_path=root / "semantic-result.json",
                score_result=json.loads(score_path.read_text(encoding="utf-8")),
            )
            self.assertEqual(analysis, direct)


if __name__ == "__main__":
    unittest.main()
