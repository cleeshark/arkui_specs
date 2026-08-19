"""Tests for Finding Ledger and convergence metrics (0.2.1 S3-S5, #48)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import FindingLedgerRepository
from spec_eval.service.store.sqlite_store import SqliteStore
from spec_eval.service.pipeline.convergence import compute_convergence


class FindingLedgerRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.ledger = FindingLedgerRepository(self.store)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_upsert_new_finding_creates_active_entry(self):
        self.ledger.upsert_finding(
            finding_id="SEM-abc123",
            func_id="01-01-01",
            criterion_id="CORRECTNESS-SOURCE-SUPPORT",
            severity="Major",
            message="test finding",
            run_id="run-1",
            executor="claude",
        )
        active = self.ledger.get_active("01-01-01")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["finding_id"], "SEM-abc123")
        self.assertEqual(active[0]["status"], "active")
        self.assertEqual(active[0]["confirmation_count"], 1)
        self.assertEqual(json.loads(active[0]["executor_set"]), ["claude"])

    def test_upsert_existing_increments_confirmation(self):
        self.ledger.upsert_finding(
            finding_id="SEM-abc123", func_id="01-01-01",
            criterion_id="C1", severity="Major", message="f1",
            run_id="run-1", executor="claude",
        )
        self.ledger.upsert_finding(
            finding_id="SEM-abc123", func_id="01-01-01",
            criterion_id="C1", severity="Major", message="f1",
            run_id="run-2", executor="codex",
        )
        active = self.ledger.get_active("01-01-01")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["confirmation_count"], 2)
        self.assertEqual(
            sorted(json.loads(active[0]["executor_set"])),
            ["claude", "codex"],
        )
        self.assertEqual(active[0]["last_confirmed_run_id"], "run-2")

    def test_mark_resolved_removes_absent_findings(self):
        self.ledger.upsert_finding(
            finding_id="SEM-keep", func_id="01-01-01",
            criterion_id="C1", severity="Major", message="keep",
            run_id="run-1", executor="claude",
        )
        self.ledger.upsert_finding(
            finding_id="SEM-gone", func_id="01-01-01",
            criterion_id="C2", severity="Minor", message="gone",
            run_id="run-1", executor="claude",
        )
        resolved = self.ledger.mark_resolved(
            "01-01-01", {"SEM-keep"}, "run-2",
        )
        self.assertEqual(resolved, 1)
        active = self.ledger.get_active("01-01-01")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["finding_id"], "SEM-keep")
        all_findings = self.ledger.get_all("01-01-01")
        resolved_entry = next(f for f in all_findings if f["finding_id"] == "SEM-gone")
        self.assertEqual(resolved_entry["status"], "resolved")

    def test_get_active_filters_by_func_id(self):
        self.ledger.upsert_finding(
            finding_id="SEM-a", func_id="01-01-01",
            criterion_id="C1", severity="Major", message="a",
            run_id="r1", executor="claude",
        )
        self.ledger.upsert_finding(
            finding_id="SEM-b", func_id="05-01-02",
            criterion_id="C1", severity="Major", message="b",
            run_id="r1", executor="claude",
        )
        self.assertEqual(len(self.ledger.get_active("01-01-01")), 1)
        self.assertEqual(len(self.ledger.get_active("05-01-02")), 1)
        self.assertEqual(len(self.ledger.get_active("99-99-99")), 0)


class ConvergenceMetricsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.ledger = FindingLedgerRepository(self.store)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_empty_ledger_is_volatile(self):
        result = compute_convergence(
            self.store, func_id="01-01-01", run_id="run-1",
            evaluator_version="0.2.1", rubric_version="0.3.0",
            source_revision="abc123",
        )
        self.assertEqual(result["convergence_level"], "volatile")
        self.assertEqual(result["finding_summary"]["active"], 0)

    def test_single_run_is_volatile(self):
        self.ledger.upsert_finding(
            finding_id="SEM-1", func_id="01-01-01",
            criterion_id="C1", severity="Major", message="f",
            run_id="run-1", executor="claude",
        )
        result = compute_convergence(
            self.store, func_id="01-01-01", run_id="run-1",
            evaluator_version="0.2.1", rubric_version="0.3.0",
            source_revision="abc123",
        )
        self.assertEqual(result["convergence_level"], "volatile")
        self.assertEqual(result["finding_summary"]["active"], 1)
        self.assertEqual(result["finding_summary"]["new_this_run"], 1)

    def test_multi_run_converging(self):
        for run in ("run-1", "run-2"):
            self.ledger.upsert_finding(
                finding_id="SEM-1", func_id="01-01-01",
                criterion_id="C1", severity="Major", message="f",
                run_id=run, executor="claude",
            )
        result = compute_convergence(
            self.store, func_id="01-01-01", run_id="run-2",
            evaluator_version="0.2.1", rubric_version="0.3.0",
            source_revision="abc123",
        )
        self.assertEqual(result["convergence_level"], "converging")

    def test_stable_after_three_confirmations_low_change(self):
        for run in ("run-1", "run-2", "run-3"):
            self.ledger.upsert_finding(
                finding_id="SEM-1", func_id="01-01-01",
                criterion_id="C1", severity="Major", message="f",
                run_id=run, executor="claude",
            )
        result = compute_convergence(
            self.store, func_id="01-01-01", run_id="run-4",
            evaluator_version="0.2.1", rubric_version="0.3.0",
            source_revision="abc123",
        )
        self.assertEqual(result["convergence_level"], "stable")
        self.assertEqual(result["finding_summary"]["new_this_run"], 0)

    def test_epoch_includes_revision_and_rubric(self):
        result = compute_convergence(
            self.store, func_id="01-01-01", run_id="run-1",
            evaluator_version="0.2.1", rubric_version="0.3.0",
            source_revision="d91b4e4",
        )
        self.assertIn("d91b4e4", result["epoch"])
        self.assertIn("0.3.0", result["epoch"])


if __name__ == "__main__":
    unittest.main()
