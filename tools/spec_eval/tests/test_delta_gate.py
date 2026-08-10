from __future__ import annotations

import unittest
from datetime import date, timedelta

from spec_eval.rules.delta_gate_engine import DeltaGateEngine
from spec_eval.rules.rule_loader import Exemption, RuleConfiguration, RulePolicy
from spec_eval.models.finding import Severity


class DeltaGateEngineTest(unittest.TestCase):
    @staticmethod
    def _configuration(*, exemptions: tuple[Exemption, ...] = ()) -> RuleConfiguration:
        return RuleConfiguration(
            version="1.0.0",
            defaults={"Critical": "fail", "Major": "fail", "Minor": "warn", "Info": "pass"},
            policies=(RulePolicy("LINK-*", severity=Severity.MINOR, gate="warn"),),
            exemptions=exemptions,
        )

    @staticmethod
    def _finding(
        finding_id: str,
        severity: str,
        *,
        rule_id: str = "TRACE-AC-NO-VM-001",
        count: int = 1,
    ) -> dict:
        return {
            "finding_id": finding_id,
            "rule_id": rule_id,
            "severity": severity,
            "message": "problem",
            "path": "specs/sample.md",
            "count": count,
        }

    def test_existing_function_blocks_added_major_and_counts_duplicates(self) -> None:
        delta = {
            "baseline_status": "existing",
            "added": [self._finding("FND-major", "Major", count=2)],
            "resolved": [],
            "reclassified": [],
            "unchanged": 5,
        }
        result = DeltaGateEngine(self._configuration()).evaluate("05-01-01", "fail", delta)
        self.assertEqual(result.gate, "fail")
        self.assertEqual(result.added_counts["Major"], 2)
        self.assertEqual(result.reason_codes, ("DELTA_MAJOR_ADDED",))

    def test_existing_function_warns_for_minor_but_ignores_history_and_resolved(self) -> None:
        delta = {
            "baseline_status": "existing",
            "added": [self._finding("FND-minor", "Major", rule_id="LINK-DEAD-001")],
            "resolved": [self._finding("FND-resolved", "Major")],
            "reclassified": [],
            "unchanged": 100,
        }
        result = DeltaGateEngine(self._configuration()).evaluate("05-01-01", "fail", delta)
        self.assertEqual(result.gate, "warn")
        self.assertEqual(result.added_counts["Minor"], 1)
        self.assertEqual(result.resolved_count, 1)
        self.assertEqual(result.reason_codes, ("DELTA_MINOR_ADDED",))

    def test_resolving_historical_major_is_pass(self) -> None:
        result = DeltaGateEngine(self._configuration()).evaluate(
            "05-01-01",
            "pass",
            {
                "baseline_status": "existing",
                "added": [],
                "resolved": [self._finding("FND-resolved", "Major")],
                "reclassified": [],
                "unchanged": 20,
            },
        )
        self.assertEqual(result.gate, "pass")
        self.assertEqual(result.resolved_count, 1)
        self.assertEqual(result.reason_codes, ())

    def test_reclassification_only_blocks_severity_increase(self) -> None:
        increased = {
            "finding_id": "FND-up",
            "rule_id": "TRACE-AC-NO-VM-001",
            "count": 1,
            "before": {"severity": "Minor", "message": "old"},
            "after": {"severity": "Major", "message": "new"},
        }
        decreased = {
            "finding_id": "FND-down",
            "rule_id": "TRACE-AC-NO-VM-001",
            "count": 1,
            "before": {"severity": "Major", "message": "old"},
            "after": {"severity": "Minor", "message": "new"},
        }
        message_only = {
            "finding_id": "FND-message",
            "rule_id": "TRACE-AC-NO-VM-001",
            "count": 1,
            "before": {"severity": "Major", "message": "old"},
            "after": {"severity": "Major", "message": "new"},
        }
        engine = DeltaGateEngine(self._configuration())

        result = engine.evaluate(
            "05-01-01",
            "fail",
            {
                "baseline_status": "existing",
                "added": [],
                "resolved": [],
                "reclassified": [increased],
                "unchanged": 0,
            },
        )
        self.assertEqual(result.gate, "fail")
        self.assertIn("DELTA_SEVERITY_INCREASED", result.reason_codes)

        result = engine.evaluate(
            "05-01-01",
            "fail",
            {
                "baseline_status": "existing",
                "added": [],
                "resolved": [],
                "reclassified": [decreased],
                "unchanged": 0,
            },
        )
        self.assertEqual(result.gate, "pass")

        result = engine.evaluate(
            "05-01-01",
            "fail",
            {
                "baseline_status": "existing",
                "added": [],
                "resolved": [],
                "reclassified": [message_only],
                "unchanged": 0,
            },
        )
        self.assertEqual(result.gate, "warn")
        self.assertIn("DELTA_MESSAGE_RECLASSIFIED", result.reason_codes)

    def test_new_function_uses_absolute_gate(self) -> None:
        engine = DeltaGateEngine(self._configuration())
        failed = engine.evaluate(
            "05-01-02",
            "fail",
            {"baseline_status": "new", "added": [], "resolved": [], "reclassified": [], "unchanged": 0},
        )
        warned = engine.evaluate(
            "05-01-02",
            "warn",
            {"baseline_status": "new", "added": [], "resolved": [], "reclassified": [], "unchanged": 0},
        )
        self.assertEqual(failed.gate, "fail")
        self.assertEqual(failed.reason_codes, ("NEW_FUNCTION_ABSOLUTE_GATE_FAILED",))
        self.assertEqual(warned.gate, "warn")
        self.assertEqual(warned.reason_codes, ("NEW_FUNCTION_ABSOLUTE_GATE_WARN",))

    def test_active_exemption_prevents_added_finding_from_blocking(self) -> None:
        exemption = Exemption(
            rule_id="TRACE-*",
            func_id="05-01-01",
            reason="migration",
            owner="spec-eval",
            expires=date.today() + timedelta(days=1),
        )
        result = DeltaGateEngine(self._configuration(exemptions=(exemption,))).evaluate(
            "05-01-01",
            "fail",
            {
                "baseline_status": "existing",
                "added": [self._finding("FND-exempt", "Major")],
                "resolved": [],
                "reclassified": [],
                "unchanged": 0,
            },
        )
        self.assertEqual(result.gate, "pass")
        self.assertEqual(result.exempted_added_count, 1)
        self.assertEqual(result.reason_codes, ())


if __name__ == "__main__":
    unittest.main()
