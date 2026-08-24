from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SKILL_SCRIPTS = Path(__file__).resolve().parents[3] / "skills" / "ohos-design-arkui-spec-evaluator" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from assemble_semantic_result import (  # noqa: E402
    record_ownership_warning,
    split_aggregation_warnings,
)


class AssembleSemanticResultWarningTest(unittest.TestCase):
    def test_only_criticality_ownership_errors_are_warnings(self) -> None:
        blocking, warnings = split_aggregation_warnings([
            "aggregation.defect_ownership[1]: one defect may produce at most one Critical Finding",
            "aggregation.defect_ownership[2]: a Critical Finding must belong to the primary Criterion",
            "aggregation.defect_ownership[3].finding_ids: unknown Finding SEM-x",
        ])
        self.assertEqual(len(warnings), 2)
        self.assertEqual(len(blocking), 1)

    def test_ownership_warning_deducts_confidence_once(self) -> None:
        with TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "confidence-result.json").write_text(
                json.dumps({
                    "confidence_score": 100,
                    "confidence_level": "HIGH",
                    "hard_errors": [],
                    "major_violations": [],
                    "minor_violations": [],
                    "total_checks_failed": 0,
                    "deduction_total": 0,
                }),
                encoding="utf-8",
            )
            record_ownership_warning(run_dir, ["warning-1", "warning-2"])
            record_ownership_warning(run_dir, ["warning-3"])
            result = json.loads((run_dir / "confidence-result.json").read_text())
        self.assertEqual(result["confidence_score"], 80)
        self.assertEqual(result["deduction_total"], 20)
        self.assertEqual(len(result["major_violations"]), 1)
        self.assertEqual(result["major_violations"][0]["code"], "OWNERSHIP_CRITICALITY")


if __name__ == "__main__":
    unittest.main()
