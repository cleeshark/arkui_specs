"""Two-stack contract tests for the skill warning policy (issue #98).

The kernel publishes post-correction residuals with
``record_post_correction_warnings``; the skill preflight
(``validate_staged_run.py``) must downgrade the matching checkpoint errors
via ``aggregation_warning_policy.split_observation_warnings``.  These tests
pin that contract for the claim/unit empty-citation rule.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / "skills" / "ohos-design-arkui-spec-evaluator" / "scripts"
)
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

from aggregation_warning_policy import (  # noqa: E402
    OBSERVATION_WARNING_MARKERS,
    split_observation_warnings,
)

CLAIM_ERROR = (
    "observation[feature:Feat-01].claim_reviews[27].evidence_ids: "
    "evidence is required for this outcome"
)
UNIT_ERROR = (
    "observation[feature:Feat-01].claim_reviews[27].unit_reviews[0]"
    ".evidence_ids: evidence is required"
)
NV_ERROR = (
    "observation[feature:Feat-01].claim_reviews[28].evidence_ids: "
    "inspection evidence is required for NOT_VERIFIABLE"
)


class EvidenceRequiredWarningPolicyTest(unittest.TestCase):
    def test_evidence_required_marker_is_registered(self) -> None:
        self.assertIn("EVIDENCE_REQUIRED_MISSING", OBSERVATION_WARNING_MARKERS)

    def test_claim_and_unit_errors_downgrade_via_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "post-correction-warnings.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "warnings": [{
                        "work_item_id": "feature:Feat-01",
                        "error": {"code": "EVIDENCE_REQUIRED_MISSING"},
                    }],
                }),
                encoding="utf-8",
            )
            blocking, warnings = split_observation_warnings(
                run_dir, [CLAIM_ERROR, UNIT_ERROR, NV_ERROR]
            )
        self.assertEqual(blocking, [NV_ERROR])
        self.assertEqual(warnings, [CLAIM_ERROR, UNIT_ERROR])

    def test_unregistered_work_item_stays_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "post-correction-warnings.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "warnings": [{
                        "work_item_id": "feature:Feat-02",
                        "error": {"code": "EVIDENCE_REQUIRED_MISSING"},
                    }],
                }),
                encoding="utf-8",
            )
            blocking, warnings = split_observation_warnings(
                run_dir, [CLAIM_ERROR]
            )
        self.assertEqual(blocking, [CLAIM_ERROR])
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
