from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from spec_eval.protocol_validator import validate_protocol, validate_score_result
from spec_eval.score import ScoreInputError, build_score_result


class Next008AggregationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.schemas_root = cls.evaluation_root / "schemas"
        cls.fixtures_root = Path(__file__).resolve().parent / "fixtures" / "protocol"
        cls.rubric, cls.complexity, cls.protocol_errors = validate_protocol(cls.evaluation_root)

    def semantic(self) -> dict:
        return json.loads(
            (self.fixtures_root / "semantic-result.json").read_text(encoding="utf-8")
        )

    @staticmethod
    def static_result(*, severity: str | None = None) -> dict:
        findings = []
        gate = "pass"
        if severity is not None:
            findings.append(
                {
                    "finding_id": "FND-" + "1" * 24,
                    "identity_version": 1,
                    "problem_key": "test finding",
                    "rule_id": "TEST-001",
                    "severity": severity,
                    "message": "test finding",
                    "path": "specs/example.md",
                }
            )
            gate = "fail" if severity in {"Major", "Critical"} else "warn"
        return {
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "tool_version": "0.5.0",
            "rule_version": "0.2.16",
            "gate": gate,
            "findings": findings,
            "metrics": {},
        }

    @staticmethod
    def evidence_manifest() -> dict:
        return {
            "func_id": "05-01-01",
            "source_revision": "abc123",
            "metrics": {
                "claim_count": 4,
                "resolved_claim_count": 3,
                "evidence_coverage": 0.75,
            },
            "shards": [],
        }

    def build(self, *, static_result: dict | None = None, semantic: dict | None = None) -> dict:
        return build_score_result(
            static_result=static_result or self.static_result(),
            evidence_manifest=self.evidence_manifest(),
            semantic_result=semantic or self.semantic(),
            rubric=self.rubric,
            complexity_rules=self.complexity,
            schemas_root=self.schemas_root,
        )

    def test_builds_a_protocol_valid_deterministic_score(self) -> None:
        first = self.build()
        second = self.build()
        self.assertEqual(first, second)
        self.assertEqual(validate_score_result(first, self.rubric, self.schemas_root), [])
        self.assertEqual(first["raw_score"], 100)
        self.assertEqual(first["published_score"], 100)
        self.assertEqual(first["gate"]["effective"], "pass")
        self.assertEqual(first["confidence"]["components"]["human_confirmation"], 0)
        self.assertEqual(first["confidence"]["score"], 0.6)
        self.assertEqual(first["admission"]["status"], "NOT_READY")

    def test_static_major_finding_preserves_fail_gate_and_caps_score(self) -> None:
        score = self.build(static_result=self.static_result(severity="Major"))
        self.assertEqual(score["caps"]["active_severities"], ["Major"])
        self.assertEqual(score["caps"]["applied"], {"severity": "Major", "limit": 59})
        self.assertEqual(score["published_score"], 59)
        self.assertEqual(score["gate"], {"static": "fail", "semantic": "pass", "effective": "fail"})
        self.assertEqual(score["admission"]["status"], "NOT_READY")

    def test_semantic_major_finding_also_fails_and_caps_score(self) -> None:
        semantic = copy.deepcopy(self.semantic())
        criterion = semantic["criterion_results"][0]
        criterion["conclusion"] = "PARTIALLY_SUPPORTED"
        criterion["findings"] = [
            {
                "finding_id": "SEM-" + "2" * 24,
                "criterion_id": criterion["criterion_id"],
                "severity": "Major",
                "conclusion": "PARTIALLY_SUPPORTED",
                "message": "semantic major finding",
                "recommendation": "resolve the semantic mismatch",
                "evidence_ids": [criterion["evidence"][0]["evidence_id"]],
            }
        ]
        score = self.build(semantic=semantic)
        self.assertEqual(score["caps"]["active_severities"], ["Major"])
        self.assertEqual(score["caps"]["applied"], {"severity": "Major", "limit": 59})
        self.assertLessEqual(score["published_score"], 59)
        self.assertEqual(score["gate"], {"static": "pass", "semantic": "fail", "effective": "fail"})

    def test_rejects_identity_and_revision_mismatch(self) -> None:
        evidence = self.evidence_manifest()
        evidence["func_id"] = "05-01-02"
        with self.assertRaisesRegex(ScoreInputError, "func_id mismatch"):
            build_score_result(
                static_result=self.static_result(),
                evidence_manifest=evidence,
                semantic_result=self.semantic(),
                rubric=self.rubric,
                complexity_rules=self.complexity,
                schemas_root=self.schemas_root,
            )

        semantic = self.semantic()
        semantic["source_revision"] = "different"
        with self.assertRaisesRegex(ScoreInputError, "source_revision mismatch"):
            self.build(semantic=semantic)

    def test_rejects_stale_protocol_versions(self) -> None:
        for field in ("rubric_version", "complexity_rules_version", "evaluator_protocol_version"):
            with self.subTest(field=field):
                semantic = copy.deepcopy(self.semantic())
                semantic[field] = "stale"
                with self.assertRaisesRegex(ScoreInputError, field):
                    self.build(semantic=semantic)

    def test_rejects_any_incomplete_execution_stage(self) -> None:
        for field in ("static_complete", "evidence_complete", "semantic_complete"):
            with self.subTest(field=field):
                semantic = copy.deepcopy(self.semantic())
                semantic["execution"][field] = False
                with self.assertRaisesRegex(ScoreInputError, field):
                    self.build(semantic=semantic)

    def test_cli_score_writes_a_valid_result(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            static_path = root / "static-result.json"
            evidence_path = root / "evidence-manifest.json"
            semantic_path = root / "semantic-result.json"
            output_path = root / "score-result.json"
            for path, document in (
                (static_path, self.static_result()),
                (evidence_path, self.evidence_manifest()),
                (semantic_path, self.semantic()),
            ):
                path.write_text(
                    json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self.specs_root / "tools" / "spec_eval" / "cli.py"),
                    "--json",
                    "score",
                    "--static-result",
                    str(static_path),
                    "--evidence-manifest",
                    str(evidence_path),
                    "--semantic-result",
                    str(semantic_path),
                    "--write",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["output_path"], str(output_path))
            score = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_score_result(score, self.rubric, self.schemas_root), [])

    def test_cli_score_keeps_fail_result_and_returns_one(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            static_path = root / "static-result.json"
            evidence_path = root / "evidence-manifest.json"
            semantic_path = root / "semantic-result.json"
            output_path = root / "score-result.json"
            for path, document in (
                (static_path, self.static_result(severity="Major")),
                (evidence_path, self.evidence_manifest()),
                (semantic_path, self.semantic()),
            ):
                path.write_text(
                    json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(self.specs_root / "tools" / "spec_eval" / "cli.py"),
                    "--json",
                    "score",
                    "--static-result",
                    str(static_path),
                    "--evidence-manifest",
                    str(evidence_path),
                    "--semantic-result",
                    str(semantic_path),
                    "--write",
                    str(output_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertTrue(output_path.is_file())
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["gate"], "fail")
            score = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_score_result(score, self.rubric, self.schemas_root), [])


if __name__ == "__main__":
    unittest.main()
