"""TASK-012-01 report registry, FunctionHead, and freshness policy tests."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.errors import (
    FreshnessPolicyError,
    ReportConflictError,
    ReportPromotionError,
)
from spec_eval.service.domain.models import CreateJobCommand, EvaluationReportRecord, FreshnessPolicy
from spec_eval.service.freshness import (
    EXPIRED_TIME,
    EXPIRING,
    FRESH,
    MISSING,
    SPEC_CHANGED,
    STALE_INPUT,
    FreshnessManager,
    calculate_freshness,
)
from spec_eval.service.app import SemanticServiceApp
from spec_eval.service.manual_refresh import ManualRefreshService
from spec_eval.service.http.routes import route_request
from spec_eval.service.report_registry import ReportRegistry, fingerprint_named_documents
from spec_eval.service.report_delta import build_report_delta
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    EvaluationReportRepository,
    FreshnessPolicyRepository,
    FunctionReportHeadRepository,
    JobRepository,
    RefreshTargetRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore
from spec_eval.protocol_validator import JsonSchemaSubsetValidator


class _RollingBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)
        self.reports = EvaluationReportRepository(self.store)
        self.heads = FunctionReportHeadRepository(self.store)
        self.policies = FreshnessPolicyRepository(self.store)
        self.policies.ensure_default()
        self.registry = ReportRegistry(self.settings, self.reports, self.heads, self.policies)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _job(self, job_id: str, revision: str):
        return self.jobs.create_job(
            CreateJobCommand(
                func_id="04-01-01", source_revision=revision, run_count=1, job_id=job_id
            ),
            evaluator_version="skill:test@1",
        )

    def _report(
        self,
        job_id: str,
        revision: str,
        generation: int,
        fingerprint: str,
        *,
        completed_at: str = "2026-08-01T00:00:00+00:00",
    ) -> EvaluationReportRecord:
        archive = self.settings.archives_root / revision / "04-01-01" / job_id
        archive.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": 1,
            "namespace": "automated",
            "job_id": job_id,
            "func_id": "04-01-01",
            "source_revision": revision,
            "files": [],
        }
        manifest_path = archive / "archive-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True), encoding="utf-8"
        )
        digest = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        return EvaluationReportRecord(
            report_id="report-" + job_id,
            job_id=job_id,
            func_id="04-01-01",
            source_revision=revision,
            revision_set={"ace_engine": revision, "specs": "s" * 40},
            input_fingerprint=fingerprint,
            evidence_fingerprint="sha256:" + "e" * 64,
            evaluator_version="skill:test@1",
            protocol_version="0.1.0",
            rubric_version="0.3.0",
            selected_run_id="run-1",
            run_count=1,
            target_generation=generation,
            completed_at=completed_at,
            archive_path=str(archive),
            manifest_sha256=digest,
            summary={
                "gate": "fail", "raw_score": 60, "published_score": 59,
                "confidence": 0.8, "admission": "NOT_READY",
            },
        )


class ReportRegistryTest(_RollingBase):
    def test_promotes_verified_immutable_report(self) -> None:
        job = self._job("a" * 40, "1" * 40)
        target = self.heads.set_desired_target(
            job.func_id,
            revision=job.source_revision,
            input_fingerprint="sha256:" + "1" * 64,
            active_job_id=job.job_id,
        )
        report = self._report(
            job.job_id, job.source_revision, target.desired_generation,
            target.desired_input_fingerprint or "",
        )

        result = self.registry.register_and_promote(report)
        self.assertEqual(result.promotion_status, "PROMOTED")
        self.assertEqual(
            self.registry.register_and_promote(report).promotion_status,
            "ALREADY_CURRENT",
        )
        head = self.heads.get(job.func_id)
        self.assertEqual(head.current_report_id, report.report_id)  # type: ignore[union-attr]
        self.assertEqual(head.freshness, FRESH)  # type: ignore[union-attr]
        self.assertEqual(head.refresh_status, "IDLE")  # type: ignore[union-attr]
        self.assertIsNone(head.active_job_id)  # type: ignore[union-attr]
        self.assertEqual(len(self.reports.list_for_func(job.func_id)), 1)

    def test_report_row_is_immutable(self) -> None:
        job = self._job("b" * 40, "2" * 40)
        target = self.heads.set_desired_target(
            job.func_id, revision=job.source_revision,
            input_fingerprint="sha256:" + "2" * 64, active_job_id=job.job_id,
        )
        report = self._report(job.job_id, job.source_revision, target.desired_generation,
                              target.desired_input_fingerprint or "")
        self.reports.insert(report)
        self.assertEqual(self.reports.insert(report), report)
        changed = EvaluationReportRecord(**{**report.__dict__, "summary": {"gate": "pass"}})
        with self.assertRaises(ReportConflictError):
            self.reports.insert(changed)

    def test_late_old_generation_is_archived_without_pointer_rollback(self) -> None:
        old_job = self._job("c" * 40, "3" * 40)
        first = self.heads.set_desired_target(
            old_job.func_id, revision=old_job.source_revision,
            input_fingerprint="sha256:" + "3" * 64, active_job_id=old_job.job_id,
        )
        old_report = self._report(
            old_job.job_id, old_job.source_revision, first.desired_generation,
            first.desired_input_fingerprint or "",
        )

        new_job = self._job("d" * 40, "4" * 40)
        second = self.heads.set_desired_target(
            new_job.func_id, revision=new_job.source_revision,
            input_fingerprint="sha256:" + "4" * 64, active_job_id=new_job.job_id,
        )
        new_report = self._report(
            new_job.job_id, new_job.source_revision, second.desired_generation,
            second.desired_input_fingerprint or "",
        )
        self.assertEqual(self.registry.register_and_promote(new_report).promotion_status, "PROMOTED")
        self.assertEqual(
            self.registry.register_and_promote(old_report).promotion_status,
            "SUPERSEDED_ON_ARRIVAL",
        )
        head = self.heads.get(new_job.func_id)
        self.assertEqual(head.current_report_id, new_report.report_id)  # type: ignore[union-attr]
        self.assertEqual(len(self.reports.list_for_func(new_job.func_id)), 2)

    def test_manifest_tamper_blocks_registration(self) -> None:
        job = self._job("e" * 40, "5" * 40)
        target = self.heads.set_desired_target(
            job.func_id, revision=job.source_revision,
            input_fingerprint="sha256:" + "5" * 64, active_job_id=job.job_id,
        )
        report = self._report(job.job_id, job.source_revision, target.desired_generation,
                              target.desired_input_fingerprint or "")
        Path(report.archive_path, "archive-manifest.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ReportConflictError, "hash mismatch"):
            self.registry.register_and_promote(report)


class FreshnessTest(_RollingBase):
    def test_missing_stale_warn_and_expire_precedence(self) -> None:
        head = self.heads.ensure("04-01-01")
        policy = self.policies.ensure_default()
        self.assertEqual(calculate_freshness(head, None, policy).status, MISSING)

        job = self._job("f" * 40, "6" * 40)
        target = self.heads.set_desired_target(
            job.func_id, revision=job.source_revision,
            input_fingerprint="sha256:" + "6" * 64, active_job_id=job.job_id,
            stale_reasons=(SPEC_CHANGED,),
        )
        report = self._report(
            job.job_id, job.source_revision, target.desired_generation,
            "sha256:" + "0" * 64,
        )
        stale = calculate_freshness(
            target, report, policy, now=datetime(2030, 1, 1, tzinfo=timezone.utc)
        )
        self.assertEqual(stale.status, STALE_INPUT)
        self.assertEqual(stale.stale_reasons, (SPEC_CHANGED,))

        matching = EvaluationReportRecord(
            **{**report.__dict__, "input_fingerprint": target.desired_input_fingerprint}
        )
        self.assertEqual(
            calculate_freshness(
                target, matching, policy,
                now=datetime(2026, 8, 25, tzinfo=timezone.utc),
            ).status,
            EXPIRING,
        )
        self.assertEqual(
            calculate_freshness(
                target, matching, policy,
                now=datetime(2026, 9, 1, tzinfo=timezone.utc),
            ).status,
            EXPIRED_TIME,
        )

    def test_policy_override_and_versioned_recompute(self) -> None:
        default = self.policies.ensure_default()
        self.assertEqual((default.max_age_days, default.warning_days), (30, 7))
        override = FreshnessPolicy(
            "func", "04-01-01", 14, 3, 1, "2026-08-14T00:00:00+00:00"
        )
        manager = FreshnessManager(self.reports, self.heads, self.policies)
        manager.set_policy(override)
        self.assertEqual(self.policies.effective_for("04-01-01"), override)
        with self.assertRaises(FreshnessPolicyError):
            manager.set_policy(override)
        with self.assertRaises(FreshnessPolicyError):
            self.policies.set(
                FreshnessPolicy("func", "04-01-01", 7, 7, 2, override.updated_at)
            )


class ReportDeltaTest(unittest.TestCase):
    def test_finding_and_score_delta_uses_stable_finding_identity(self) -> None:
        previous = {
            "summary": {"published_score": 50, "raw_score": 55, "gate": "fail", "confidence": 0.7},
            "findings": [
                {"finding_id": "A", "severity": "Major", "message": "old"},
                {"finding_id": "B", "severity": "Minor", "message": "fixed"},
            ],
        }
        current = {
            "summary": {"published_score": 59, "raw_score": 62, "gate": "fail", "confidence": 0.8},
            "findings": [
                {"finding_id": "A", "severity": "Critical", "message": "old"},
                {"finding_id": "C", "severity": "Minor", "message": "new"},
            ],
        }
        delta = build_report_delta(previous, current)
        self.assertEqual(delta["summary"]["added"], 1)
        self.assertEqual(delta["summary"]["resolved"], 1)
        self.assertEqual(delta["summary"]["reclassified"], 1)
        self.assertEqual(delta["summary"]["published_score_delta"], 9)

    def test_input_fingerprint_ignores_revision_identity_when_content_is_same(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.json"
            second = Path(temporary) / "second.json"
            first.write_text(
                json.dumps({"source_revision": "a" * 40, "claims": [{"id": "AC-1"}]}),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps({"source_revision": "b" * 40, "claims": [{"id": "AC-1"}]}),
                encoding="utf-8",
            )
            self.assertEqual(
                fingerprint_named_documents(
                    [("evidence.json", first)], normalize_revision_fields=True
                ),
                fingerprint_named_documents(
                    [("evidence.json", second)], normalize_revision_fields=True
                ),
            )


class SchemaMigrationTest(unittest.TestCase):
    def test_v1_database_is_upgraded_additively_to_v3(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            settings = ServiceSettings.discover(data_root=Path(temporary))
            conn = sqlite3.connect(settings.db_path)
            conn.execute("CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("INSERT INTO schema_meta VALUES ('schema_version', '1')")
            conn.commit()
            conn.close()

            store = SqliteStore(settings)
            row = store._conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            tables = {
                item[0]
                for item in store._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            self.assertEqual(row[0], "3")
            self.assertTrue(
                {
                    "evaluation_reports", "function_report_heads", "freshness_policies",
                    "report_deltas", "job_statistics",
                }
                <= tables
            )
            store.close()

    def test_v2_database_backfills_job_statistics_from_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            settings = ServiceSettings.discover(data_root=Path(temporary))
            store = SqliteStore(settings)
            jobs = JobRepository(store)
            job = jobs.create_job(
                CreateJobCommand(
                    func_id="04-01-01",
                    source_revision="a" * 40,
                    run_count=1,
                    job_id="m" * 40,
                ),
                evaluator_version="test",
            )
            jobs.transition_status(job.job_id, S.PREPARING, event_type="enter_preparing")
            jobs.transition_status(job.job_id, S.FAILED, event_type="failed")
            store.close()

            conn = sqlite3.connect(settings.db_path)
            conn.execute("DROP TABLE job_statistics")
            conn.execute(
                "UPDATE schema_meta SET value='2' WHERE key='schema_version'"
            )
            conn.commit()
            conn.close()

            migrated = SqliteStore(settings)
            row = migrated._conn.execute(
                "SELECT started_at, finished_at FROM job_statistics WHERE job_id = ?",
                (job.job_id,),
            ).fetchone()
            version = migrated._conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()[0]
            self.assertEqual(version, "3")
            self.assertIsNotNone(row[0])
            self.assertIsNotNone(row[1])
            migrated.close()

    def test_future_database_version_is_not_silently_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            settings = ServiceSettings.discover(data_root=Path(temporary))
            conn = sqlite3.connect(settings.db_path)
            conn.execute("CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("INSERT INTO schema_meta VALUES ('schema_version', '99')")
            conn.commit()
            conn.close()
            with self.assertRaisesRegex(RuntimeError, "schema version '99'"):
                SqliteStore(settings)


class _FakeWorkspaceManager:
    def __init__(self) -> None:
        self.prepared: list[str] = []

    def resolve_revisions(self, source_revision: str) -> dict[str, str]:
        ace = source_revision if len(source_revision) == 40 else (source_revision[0] * 40)
        return {
            "ace_engine": ace,
            "specs": "s" * 40,
            "sdk-js": "j" * 40,
            "sdk_c": "c" * 40,
        }

    def prepare(self, job, *, reserved_revisions=None):
        self.prepared.append(job.job_id)
        return None


class ManualRefreshTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.app = SemanticServiceApp(
            self.settings, job_runner=lambda job_id, cancel: None, max_workers=1
        )
        self.manager = _FakeWorkspaceManager()
        service = ManualRefreshService(self.app)
        service._workspace_manager = self.manager
        self.app.manual_refresh = service

    def tearDown(self) -> None:
        self.app.stop()
        self.tmp.cleanup()

    def test_duplicate_manual_click_returns_existing_active_job(self) -> None:
        first = self.app.refresh_function(
            func_id="04-01-01", source_revision="1" * 40, run_count=1
        )
        second = self.app.refresh_function(
            func_id="04-01-01", source_revision="1" * 40, run_count=1
        )
        self.assertFalse(first.deduplicated)
        self.assertTrue(second.deduplicated)
        self.assertEqual(first.job.job_id, second.job.job_id)
        self.assertEqual(first.target.generation, 1)
        self.assertEqual(self.manager.prepared, [first.job.job_id])

    def test_new_target_advances_generation_without_killing_old_job(self) -> None:
        first = self.app.refresh_function(
            func_id="04-01-01", source_revision="1" * 40, run_count=1
        )
        second = self.app.refresh_function(
            func_id="04-01-01", source_revision="2" * 40, run_count=1
        )
        self.assertNotEqual(first.job.job_id, second.job.job_id)
        self.assertEqual((first.target.generation, second.target.generation), (1, 2))
        stored = RefreshTargetRepository(self.app.store).get(first.job.job_id)
        self.assertEqual(stored.status, "ACTIVE")  # type: ignore[union-attr]

    def test_http_refresh_endpoint_returns_202_then_deduplicated_200(self) -> None:
        body = json.dumps({"source_revision": "3" * 40, "run_count": 1}).encode()
        first = route_request(
            "POST", "/api/functions/04-01-01/refresh", body, {}, self.app
        )
        second = route_request(
            "POST", "/api/functions/04-01-01/refresh", body, {}, self.app
        )
        self.assertEqual((first.status, second.status), (202, 200))
        self.assertFalse(json.loads(first.body)["deduplicated"])
        self.assertTrue(json.loads(second.body)["deduplicated"])

    def test_function_policy_api_and_static_export(self) -> None:
        listing = route_request("GET", "/api/functions?freshness=MISSING", b"", {}, self.app)
        self.assertEqual(listing.status, 200)
        functions = json.loads(listing.body)
        self.assertTrue(any(item["func_id"] == "04-01-01" for item in functions))

        policy = route_request(
            "PUT",
            "/api/freshness-policies/04-01-01",
            json.dumps({"max_age_days": 14, "warning_days": 3}).encode(),
            {},
            self.app,
        )
        self.assertEqual(policy.status, 200)
        self.assertEqual(json.loads(policy.body)["version"], 1)

        exported = self.app.export_site()
        index = json.loads(exported["index"].read_text(encoding="utf-8"))
        self.assertEqual(index["mode"], "archive")
        self.assertIsNone(index["semantic_revision"])
        self.assertIn("generated_at", index)
        validator = JsonSchemaSubsetValidator(self.settings.schemas_root)
        self.assertEqual(
            validator.validate_file(
                index, self.settings.schemas_root / "automated-function-index.schema.json"
            ),
            [],
        )
        history = self.settings.exports_root / "automated-function-history" / "04-01-01.json"
        self.assertTrue(history.is_file())


if __name__ == "__main__":
    unittest.main()
