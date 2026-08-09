from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from generate_site import load_archived_semantic_evaluation
from spec_eval.protocol_validator import validate_protocol
from spec_eval.report.site_evaluation_reporter import (
    SiteEvaluationInputError,
    build_site_evaluation_report,
    validate_site_evaluation_report,
)


class Next009SiteEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs_root = Path(__file__).resolve().parents[3]
        cls.evaluation_root = cls.specs_root / "evaluation"
        cls.schemas_root = cls.evaluation_root / "schemas"
        _, _, cls.protocol_errors = validate_protocol(cls.evaluation_root)

    @staticmethod
    def review(func_id: str, status: str = "confirmed", revision: str = "abc123") -> dict:
        return {
            "schema_version": 1,
            "func_id": func_id,
            "source_revision": revision,
            "status": status,
            "scores": {
                "dimensions": {"correctness": 16}, "raw_score": 55,
                "published_score": 55, "confidence": 1, "admission": "NOT_READY",
            },
            "confirmation": {"confirmed_by": "reviewer", "confirmed_at": "2026-01-01T00:00:00Z", "conclusion": "accepted", "notes": ["confirmed"]},
            "semantic_result": {
                "criterion_results": [{
                    "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                    "dimension_id": "correctness",
                    "conclusion": "PARTIALLY_SUPPORTED",
                    "reason": "one gap",
                    "evidence": [{"path": "frameworks/example.cpp"}],
                    "findings": [{
                        "finding_id": "SEM-" + "1" * 24,
                        "criterion_id": "CORRECTNESS-SOURCE-SUPPORT",
                        "severity": "Major", "conclusion": "PARTIALLY_SUPPORTED",
                        "message": "semantic issue", "recommendation": "Fix the contract.",
                        "evidence_ids": ["EV-1"],
                    }],
                }],
            },
        }

    @staticmethod
    def site_report(revision: str = "abc123") -> dict:
        return {
            "sourceRevision": revision,
            "functions": [{
                "funcId": "05-01-01", "title": "Example", "gate": "fail",
                "findings": [{
                    "finding_id": "FND-" + "2" * 24,
                    "rule_id": "TEST-001", "severity": "Major",
                    "message": "static issue", "recommendation": "Fix the static issue.",
                    "path": "specs/example.md", "line": 3,
                }],
            }],
        }

    def test_exports_only_confirmed_and_marks_revision_mismatch_expired(self) -> None:
        reviews = [
            self.review("05-01-01"),
            self.review("05-01-02", status="draft"),
            self.review("05-01-03", revision="oldrev"),
        ]
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            review_root = root / "reviews"
            review_root.mkdir()
            for index, value in enumerate(reviews):
                (review_root / f"{index}.yaml").write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")
            result = build_site_evaluation_report(reviews_root=review_root, site_report=self.site_report())
        self.assertEqual(result["summary"], {"confirmedFunctionCount": 1, "expiredFunctionCount": 1, "functionCount": 2, "findingCount": 2, "expiredFindingCount": 1})
        statuses = {item["func_id"]: item["status"] for item in result["functions"]}
        self.assertEqual(statuses, {"05-01-01": "CONFIRMED", "05-01-03": "EXPIRED"})
        confirmed = next(item for item in result["functions"] if item["status"] == "CONFIRMED")
        criterion = confirmed["criterion_summaries"][0]
        self.assertEqual(criterion["findings"][0]["recommendation"], "Fix the contract.")
        self.assertEqual(criterion["evidence"][0]["path"], "frameworks/example.cpp")
        expired = next(item for item in result["functions"] if item["status"] == "EXPIRED")
        self.assertEqual(expired["staleness"]["reason"], "review_source_revision_mismatch")

    def test_is_schema_valid_and_byte_deterministic(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            review_root = root / "reviews"
            review_root.mkdir()
            for name, func_id in (("b.yaml", "05-01-02"), ("a.yaml", "05-01-01")):
                review_root.joinpath(name).write_text(
                    yaml.safe_dump(self.review(func_id), allow_unicode=True, sort_keys=False), encoding="utf-8"
                )
            first = build_site_evaluation_report(reviews_root=review_root, site_report=self.site_report())
            second = build_site_evaluation_report(reviews_root=review_root, site_report=self.site_report())
        self.assertEqual(first, second)
        self.assertEqual(validate_site_evaluation_report(first, self.schemas_root), [])

    def test_rejects_missing_site_revision(self) -> None:
        with self.assertRaisesRegex(SiteEvaluationInputError, "sourceRevision"):
            build_site_evaluation_report(reviews_root=Path("."), site_report={"functions": []})

    def test_cli_writes_confirmed_site_archive(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            review_root = root / "reviews"
            review_root.mkdir()
            (review_root / "review.yaml").write_text(
                yaml.safe_dump(self.review("05-01-01"), allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            site_path = root / "site-report.json"
            site_path.write_text(json.dumps(self.site_report()), encoding="utf-8")
            output_path = root / "site-evaluation-report.json"
            command = [
                sys.executable, str(self.specs_root / "tools/spec_eval/cli.py"), "--json", "site-evaluation",
                "--reviews-root", str(review_root), "--site-report", str(site_path), "--write", str(output_path),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["confirmed_function_count"], 1)
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["summary"]["functionCount"], 1)

    def test_site_generator_reads_only_archived_semantic_json(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertFalse(load_archived_semantic_evaluation(root)["available"])
            value = {
                "schemaVersion": 1, "reportVersion": "test", "available": True,
                "sourceRevision": "abc123", "staticReport": {}, "summary": {}, "functions": [],
            }
            (root / "site-evaluation-report.json").write_text(json.dumps(value), encoding="utf-8")
            self.assertEqual(load_archived_semantic_evaluation(root), value)


if __name__ == "__main__":
    unittest.main()
