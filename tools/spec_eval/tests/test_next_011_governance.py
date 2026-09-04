"""Host unit tests for the governance layer (TASK-011-09): metrics, cleanup,
backup/restore, disk usage, and PII exclusion.

    python3 -m unittest spec_eval.tests.test_next_011_governance -v
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import Artifact, CreateJobCommand
from spec_eval.service.governance import backup_database, cleanup_temp, disk_usage
from spec_eval.service.store.sqlite_store import _SCHEMA_VERSION
from spec_eval.service.metrics import collect_metrics, write_metrics_csv, write_metrics_json
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import (
    ArtifactRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from spec_eval.service.store.sqlite_store import SqliteStore, utc_now

EVALUATOR_VERSION = "skill:ohos-design-arkui-spec-evaluator@0.1.19"


class _GovTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.jobs = JobRepository(self.store)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def _complete_job(self, job_id: str = "g" * 40) -> str:
        """Create a job and drive it through every state to completed."""
        self.jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=1, job_id=job_id),
            evaluator_version=EVALUATOR_VERSION,
        )
        self.jobs.transition_status(job_id, S.RUNNING, event_type="enter_running")
        for stage in (S.STAGE_PREPARING, S.STAGE_EVIDENCE, S.STAGE_OBSERVATION, S.STAGE_AGGREGATION, S.STAGE_REPORT, S.STAGE_ARCHIVE):
            self.jobs.transition_status(job_id, S.RUNNING, stage=stage, event_type=f"enter_{stage}")
        self.jobs.transition_status(job_id, S.COMPLETED, event_type="job_completed")
        return job_id


class MetricsTest(_GovTestBase):
    def test_status_counts_durations_and_bytes(self) -> None:
        job_id = self._complete_job()
        JobStatisticsRepository(self.store).record_executor_result(
            job_id,
            elapsed_seconds=2.5,
            token_usage={
                "input_tokens": 200,
                "cached_input_tokens": 50,
                "cache_write_input_tokens": 0,
                "output_tokens": 40,
                "reasoning_output_tokens": 10,
                "total_tokens": 240,
            },
            usage_reported=True,
            telemetry={
                "tool_calls": 9,
                "command_calls": 6,
                "input_paths_accessed": 5,
                "evidence_paths_accessed": 3,
            },
            telemetry_reported=True,
        )
        ArtifactRepository(self.store).record(
            Artifact(artifact_id="a", job_id=job_id, kind="function_context",
                     path=str(self.settings.data_root / "f.json"), sha256="sha256:" + "0" * 64,
                     size=123, created_at=utc_now())
        )
        # one extra queued job
        self.jobs.create_job(
            CreateJobCommand(func_id="04-02-02", source_revision="rev2", run_count=1, job_id="h" * 40),
            evaluator_version=EVALUATOR_VERSION,
        )
        metrics = collect_metrics(self.store, archives_root=self.settings.archives_root)
        self.assertEqual(metrics["status_counts"].get(S.COMPLETED), 1)
        self.assertEqual(metrics["status_counts"].get(S.QUEUED), 1)
        self.assertEqual(metrics["job_total"], 2)
        self.assertGreaterEqual(metrics["duration_summary"]["count"], 1)  # completed job has durations
        self.assertEqual(metrics["artifact_bytes"], 123)
        self.assertEqual(metrics["token_usage"]["total_tokens"], 240)
        self.assertEqual(metrics["token_usage"]["reported_jobs"], 1)
        self.assertEqual(metrics["token_usage"]["reporting_coverage"], 1.0)
        self.assertEqual(metrics["executor_invocations"], 1)
        self.assertEqual(metrics["executor_telemetry"]["command_calls"], 6)
        self.assertEqual(metrics["executor_telemetry"]["evidence_paths_accessed"], 3)
        self.assertEqual(metrics["executor_telemetry"]["reporting_coverage"], 1.0)

    def test_finding_deltas_from_automated_history(self) -> None:
        log = self.settings.archives_root / "site-history-automated.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        records = [
            {"func_id": "04-01-01", "finding_summary": {"total": 3, "by_severity": {"Major": 2, "Minor": 1}}},
            {"func_id": "04-01-01", "finding_summary": {"total": 2, "by_severity": {"Major": 1, "Minor": 1}}},  # -1 => resolved
            {"func_id": "04-02-02", "finding_summary": {"total": 2, "by_severity": {"Major": 1, "Minor": 1}}},
            {"func_id": "04-02-02", "finding_summary": {"total": 2, "by_severity": {"Major": 2, "Minor": 0}}},  # shifted => reclassified
        ]
        log.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        metrics = collect_metrics(self.store, archives_root=self.settings.archives_root)
        self.assertEqual(metrics["finding_deltas"]["resolved"], 1)
        self.assertEqual(metrics["finding_deltas"]["reclassified"], 1)
        self.assertEqual(metrics["finding_deltas"]["added"], 0)

    def test_export_json_and_csv(self) -> None:
        self._complete_job()
        metrics = collect_metrics(self.store, archives_root=self.settings.archives_root)
        j = self.settings.data_root / "m.json"
        c = self.settings.data_root / "m.csv"
        write_metrics_json(metrics, j)
        write_metrics_csv(metrics, c)
        self.assertTrue(j.is_file())
        self.assertIn("status_counts", json.loads(j.read_text(encoding="utf-8")))
        self.assertIn("metric,value", c.read_text(encoding="utf-8"))


class CleanupTest(_GovTestBase):
    def test_old_terminal_run_dir_removed_recent_kept(self) -> None:
        old_id = self._complete_job("o" * 40)
        new_id = self._complete_job("n" * 40)
        # backdate the old job's updated_at
        old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(timespec="seconds")
        self._set_updated_at(old_id, old_ts)
        # create disposable run dirs for both
        for jid in (old_id, new_id):
            run_dir = self.settings.jobs_root / jid / "runs" / "run-1" / "staged"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "x.json").write_text("{}", encoding="utf-8")

        summary = cleanup_temp(self.settings, self.store, retention_days=14)
        self.assertIn(old_id, summary["cleaned_job_ids"])
        self.assertNotIn(new_id, summary["cleaned_job_ids"])
        self.assertFalse((self.settings.jobs_root / old_id).exists())
        self.assertTrue((self.settings.jobs_root / new_id).exists())
        self.assertGreater(summary["freed_bytes"], 0)

    def test_old_terminal_workspace_removed_too(self) -> None:
        old_id = self._complete_job("o" * 40)
        new_id = self._complete_job("n" * 40)
        self._set_updated_at(old_id, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(timespec="seconds"))
        for jid in (old_id, new_id):
            run_dir = self.settings.jobs_root / jid / "runs" / "run-1"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "x.json").write_text("{}", encoding="utf-8")
            workspace = self.settings.workspaces_root / jid / "oh" / "foundation"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "big.bin").write_text("x" * 256, encoding="utf-8")

        summary = cleanup_temp(self.settings, self.store, retention_days=14)
        self.assertIn(old_id, summary["cleaned_job_ids"])
        self.assertFalse((self.settings.jobs_root / old_id).exists())
        self.assertFalse((self.settings.workspaces_root / old_id).exists())
        # the recent terminal job keeps both its run dir and its workspace
        self.assertNotIn(new_id, summary["cleaned_job_ids"])
        self.assertTrue((self.settings.jobs_root / new_id).exists())
        self.assertTrue((self.settings.workspaces_root / new_id).exists())
        self.assertGreaterEqual(summary["freed_bytes"], 256)

    def test_leaked_workspace_removed_even_when_run_dir_absent(self) -> None:
        # The field leak: cleanup_temp only ever deleted jobs/<id>, so old jobs
        # can have no staged dir left while their worktree workspace survives.
        leaked_id = self._complete_job("l" * 40)
        self._set_updated_at(leaked_id, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(timespec="seconds"))
        workspace = self.settings.workspaces_root / leaked_id / "oh"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "manifest.json").write_text("{}", encoding="utf-8")

        summary = cleanup_temp(self.settings, self.store, retention_days=14)
        self.assertIn(leaked_id, summary["cleaned_job_ids"])
        self.assertFalse((self.settings.workspaces_root / leaked_id).exists())
        self.assertGreater(summary["freed_bytes"], 0)

    def test_non_terminal_old_job_workspace_kept(self) -> None:
        # A queued (non-terminal) job is not expired even when its updated_at is
        # old: only terminal states are eligible for workspace removal.
        queued_id = self._create_job("q" * 40)
        self._set_updated_at(queued_id, (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(timespec="seconds"))
        workspace = self.settings.workspaces_root / queued_id / "oh"
        workspace.mkdir(parents=True, exist_ok=True)
        (workspace / "manifest.json").write_text("{}", encoding="utf-8")

        summary = cleanup_temp(self.settings, self.store, retention_days=14)
        self.assertNotIn(queued_id, summary["cleaned_job_ids"])
        self.assertTrue((self.settings.workspaces_root / queued_id).exists())

    def test_archives_are_never_deleted(self) -> None:
        job_id = self._complete_job("z" * 40)
        archive = self.settings.archives_root / "rev" / "04-01-01" / job_id
        archive.mkdir(parents=True)
        (archive / "archive-manifest.json").write_text("{}", encoding="utf-8")
        self._set_updated_at(job_id, (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(timespec="seconds"))
        cleanup_temp(self.settings, self.store, retention_days=1)
        self.assertTrue((archive / "archive-manifest.json").is_file())

    def _create_job(self, job_id: str) -> str:
        self.jobs.create_job(
            CreateJobCommand(func_id="04-01-01", source_revision="rev", run_count=1, job_id=job_id),
            evaluator_version=EVALUATOR_VERSION,
        )
        return job_id

    def _set_updated_at(self, job_id: str, ts: str) -> None:
        conn = sqlite3.connect(str(self.settings.db_path))
        conn.execute("UPDATE jobs SET updated_at = ? WHERE job_id = ?", (ts, job_id))
        conn.commit()
        conn.close()


class BackupDiskTest(_GovTestBase):
    def test_backup_is_verifiable(self) -> None:
        self._complete_job()
        dest = backup_database(self.settings)
        self.assertTrue(dest.is_file())
        conn = sqlite3.connect(str(dest))
        row = conn.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
        conn.close()
        self.assertEqual(row[0], _SCHEMA_VERSION)
        # the live DB still works after backup
        self.assertEqual(len(self.jobs.list_jobs()), 1)

    def test_disk_usage_shape(self) -> None:
        self._complete_job()
        usage = disk_usage(self.settings)
        self.assertIn("free_bytes", usage)
        self.assertGreaterEqual(usage["free_bytes"], 0)
        self.assertIn("used_bytes_by_subdir", usage)
        for sub in ("db", "jobs", "archives", "logs", "backups"):
            self.assertIn(sub, usage["used_bytes_by_subdir"])


class NoPiiTest(_GovTestBase):
    def test_metrics_exclude_secret_fields(self) -> None:
        self._complete_job()
        metrics = collect_metrics(self.store, archives_root=self.settings.archives_root)
        text = json.dumps(metrics)
        for secret in ("sk-", "api_key", "secret", "password", "Authorization"):
            self.assertNotIn(secret, text)


if __name__ == "__main__":
    unittest.main()
