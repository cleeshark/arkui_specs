"""Revision workspace and immutable dependency snapshot tests (issue #10)."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from spec_eval.service.domain.errors import SnapshotConflictError
from spec_eval.service.domain import states as S
from spec_eval.service.domain.models import CreateJobCommand, DependencySnapshot, Job, default_progress
from spec_eval.service.settings import ServiceSettings
from spec_eval.service.store.repositories import DependencySnapshotRepository, JobRepository
from spec_eval.service.store.sqlite_store import SqliteStore
from spec_eval.service.workspace.manager import RevisionWorkspaceManager, WorkspaceError


class RevisionWorkspaceManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.oh_root = root / "oh"
        self.ace = self.oh_root / "foundation" / "arkui" / "ace_engine"
        self.specs = self.ace / "specs"
        self.sdk_js = self.oh_root / "interface" / "sdk-js"
        self.sdk_c = self.oh_root / "interface" / "sdk_c"

        self._init_repo(self.ace, "source.txt", "ace-v1\n")
        self.ace_v1 = self._head(self.ace)
        (self.ace / "source.txt").write_text("ace-v2\n", encoding="utf-8")
        self._commit(self.ace, "ace v2")
        self.ace_v2 = self._head(self.ace)
        self._init_repo(self.specs, "spec.txt", "spec-v1\n")
        self._init_repo(self.sdk_js, "sdk.txt", "js-v1\n")
        self._init_repo(self.sdk_c, "sdk.txt", "c-v1\n")

        discovered = ServiceSettings.discover(data_root=root / "data")
        self.settings = replace(
            discovered,
            repo_root=self.ace,
            specs_root=self.specs,
            schemas_root=self.specs / "evaluation" / "schemas",
        )
        self.manager = RevisionWorkspaceManager(self.settings)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_requested_revision_isolated_from_current_dirty_checkout(self) -> None:
        (self.ace / "source.txt").write_text("dirty-host-content\n", encoding="utf-8")
        workspace = self.manager.prepare(self._job(self.ace_v1))

        self.assertEqual(self._head(workspace.repo_root), self.ace_v1)
        self.assertEqual((workspace.repo_root / "source.txt").read_text(), "ace-v1\n")
        self.assertEqual(self._head(workspace.specs_root), self._head(self.specs))
        self.assertEqual(workspace.revisions["ace_engine"], self.ace_v1)
        self.assertNotEqual(workspace.revisions["ace_engine"], self.ace_v2)

    def test_retry_reuses_reserved_dependency_revisions(self) -> None:
        job = self._job(self.ace_v1)
        first = self.manager.prepare(job)
        frozen_specs = first.revisions["specs"]
        (self.specs / "spec.txt").write_text("spec-v2\n", encoding="utf-8")
        self._commit(self.specs, "spec v2")

        second = self.manager.prepare(job)
        self.assertEqual(second.revisions["specs"], frozen_specs)
        self.assertEqual(self._head(second.specs_root), frozen_specs)

    def test_release_removes_worktrees_but_keeps_revision_reservation(self) -> None:
        job = self._job(self.ace_v1)
        workspace = self.manager.prepare(job)
        self.assertEqual(self.manager.release(job.job_id), [])
        self.assertFalse(workspace.repo_root.exists())
        self.assertFalse(workspace.specs_root.exists())
        self.assertTrue((workspace.workspace_root / "workspace-manifest.json").is_file())
        recreated = self.manager.prepare(job)
        self.assertEqual(self._head(recreated.repo_root), self.ace_v1)

    def test_unreachable_revision_fails_before_evaluation(self) -> None:
        with self.assertRaisesRegex(WorkspaceError, "cannot resolve revision"):
            self.manager.prepare(self._job("not-a-real-revision"))

    def _job(self, source_revision: str) -> Job:
        return Job(
            job_id="w" * 40,
            func_id="04-01-01",
            source_revision=source_revision,
            run_count=1,
            selected_run_ids=(),
            status="queued",
            stage=S.STAGE_PREPARING,
            progress=default_progress("queued"),
            executor_config={},
            protocol_version="0.1.0",
            evaluator_version="test",
            created_at="2026-08-14T00:00:00+00:00",
            updated_at="2026-08-14T00:00:00+00:00",
        )

    @staticmethod
    def _init_repo(path: Path, filename: str, content: str) -> None:
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        (path / filename).write_text(content, encoding="utf-8")
        RevisionWorkspaceManagerTest._commit(path, "initial")

    @staticmethod
    def _commit(path: Path, message: str) -> None:
        subprocess.run(["git", "-C", str(path), "add", "."], check=True)
        subprocess.run(
            [
                "git", "-C", str(path),
                "-c", "user.name=Spec Eval Test",
                "-c", "user.email=spec-eval@example.invalid",
                "commit", "-q", "-m", message,
            ],
            check=True,
        )

    @staticmethod
    def _head(path: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()


class DependencySnapshotImmutabilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = ServiceSettings.discover(data_root=Path(self.tmp.name))
        self.store = SqliteStore(self.settings)
        self.repo = DependencySnapshotRepository(self.store)
        JobRepository(self.store).create_job(
            CreateJobCommand(
                func_id="04-01-01", source_revision="a" * 40, run_count=1, job_id="job"
            ),
            evaluator_version="test",
        )

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_same_snapshot_is_idempotent_but_different_sha_is_rejected(self) -> None:
        first = DependencySnapshot("job", "ace_engine", "detached", "a" * 40, "frozen", "t1")
        retry = DependencySnapshot("job", "ace_engine", "detached", "a" * 40, "frozen", "t2")
        conflict = DependencySnapshot("job", "ace_engine", "detached", "b" * 40, "frozen", "t3")

        self.repo.freeze(first)
        self.assertEqual(self.repo.freeze(retry).created_at, "t1")
        with self.assertRaises(SnapshotConflictError):
            self.repo.freeze(conflict)
        self.assertEqual(self.repo.get("job", "ace_engine").sha, "a" * 40)  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()
