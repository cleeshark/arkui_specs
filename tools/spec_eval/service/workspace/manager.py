"""Prepare restart-safe detached Git worktrees for semantic evaluation Jobs."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from ..domain.models import Job
from ..settings import ServiceSettings
from .models import EvaluationWorkspace

MANIFEST_VERSION = 1


class WorkspaceError(RuntimeError):
    """A requested revision cannot be resolved or isolated safely."""


class RevisionWorkspaceManager:
    """Create one immutable OpenHarmony-shaped workspace per Job.

    A reservation manifest is written before any worktree is created. If the
    process stops midway, a retry reuses those exact revisions instead of
    resolving moving branches again.
    """

    def __init__(self, settings: ServiceSettings) -> None:
        self.settings = settings

    def resolve_revisions(self, source_revision: str) -> dict[str, str]:
        """Resolve the requested ace revision and current dependency commits."""
        return self._resolve_revisions(source_revision)

    def prepare(
        self,
        job: Job,
        *,
        reserved_revisions: dict[str, str] | None = None,
    ) -> EvaluationWorkspace:
        root = self.settings.workspaces_root / job.job_id
        manifest_path = root / "workspace-manifest.json"
        document = self._read_manifest(manifest_path) if manifest_path.is_file() else None
        if document is None:
            revisions = reserved_revisions or self._resolve_revisions(job.source_revision)
            self._validate_revision_set(revisions)
            document = self._manifest(job, revisions, status="preparing")
            self._write_manifest(manifest_path, document)
        else:
            self._validate_manifest_job(document, job)
            revisions = self._manifest_revisions(document)

        paths = self._workspace_paths(root)
        sources = self._source_repositories()
        for name in ("ace_engine", "specs", "sdk-js", "sdk_c"):
            self._ensure_worktree(sources[name], paths[name], revisions[name])

        ready = self._manifest(job, revisions, status="ready")
        self._write_manifest(manifest_path, ready)
        return EvaluationWorkspace(
            workspace_root=root,
            repo_root=paths["ace_engine"],
            specs_root=paths["specs"],
            schemas_root=paths["specs"] / "evaluation" / "schemas",
            revisions=revisions,
        )

    def release(self, job_id: str) -> list[str]:
        """Best-effort removal of detached worktrees; keep the reservation manifest."""
        root = self.settings.workspaces_root / job_id
        paths = self._workspace_paths(root)
        sources = self._source_repositories()
        errors: list[str] = []
        for name in ("specs", "sdk-js", "sdk_c", "ace_engine"):
            target = paths[name]
            if not target.exists():
                continue
            cp = subprocess.run(
                ["git", "-C", str(sources[name]), "worktree", "remove", "--force", str(target)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if cp.returncode != 0:
                errors.append(f"{name}: {(cp.stderr or cp.stdout).strip()}")
        return errors

    def _source_repositories(self) -> dict[str, Path]:
        oh_root = self.settings.repo_root.parents[2]
        return {
            "ace_engine": self.settings.repo_root,
            "specs": self.settings.specs_root,
            "sdk-js": oh_root / "interface" / "sdk-js",
            "sdk_c": oh_root / "interface" / "sdk_c",
        }

    @staticmethod
    def _workspace_paths(root: Path) -> dict[str, Path]:
        oh_root = root / "oh"
        ace_root = oh_root / "foundation" / "arkui" / "ace_engine"
        return {
            "ace_engine": ace_root,
            "specs": ace_root / "specs",
            "sdk-js": oh_root / "interface" / "sdk-js",
            "sdk_c": oh_root / "interface" / "sdk_c",
        }

    def _resolve_revisions(self, source_revision: str) -> dict[str, str]:
        sources = self._source_repositories()
        refs = {
            "ace_engine": source_revision,
            "specs": "HEAD",
            "sdk-js": "HEAD",
            "sdk_c": "HEAD",
        }
        return {name: self._resolve_commit(sources[name], ref) for name, ref in refs.items()}

    @staticmethod
    def _resolve_commit(repo: Path, ref: str) -> str:
        if not repo.is_dir():
            raise WorkspaceError(f"dependency repository not found: {repo}")
        cp = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", f"{ref}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if cp.returncode != 0:
            detail = (cp.stderr or cp.stdout).strip()
            raise WorkspaceError(f"cannot resolve revision {ref!r} in {repo}: {detail}")
        return cp.stdout.strip()

    def _ensure_worktree(self, source: Path, target: Path, revision: str) -> None:
        if target.exists():
            actual = self._worktree_head(target)
            if actual is None and target.is_dir() and not any(target.iterdir()):
                target.rmdir()
            elif actual != revision:
                raise WorkspaceError(
                    f"workspace path already exists at wrong revision: {target}; "
                    f"expected {revision}, got {actual or 'not-a-git-worktree'}"
                )
            else:
                return
        target.parent.mkdir(parents=True, exist_ok=True)
        cp = subprocess.run(
            ["git", "-C", str(source), "worktree", "add", "--detach", str(target), revision],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if cp.returncode != 0:
            detail = (cp.stderr or cp.stdout).strip()
            raise WorkspaceError(f"cannot create worktree {target} at {revision}: {detail}")
        actual = self._worktree_head(target)
        if actual != revision:
            raise WorkspaceError(
                f"created worktree revision mismatch at {target}: expected {revision}, got {actual}"
            )

    @staticmethod
    def _worktree_head(path: Path) -> str | None:
        cp = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return cp.stdout.strip() if cp.returncode == 0 else None

    @staticmethod
    def _manifest(job: Job, revisions: dict[str, str], *, status: str) -> dict[str, Any]:
        return {
            "schema_version": MANIFEST_VERSION,
            "job_id": job.job_id,
            "requested_source_revision": job.source_revision,
            "status": status,
            "revisions": dict(sorted(revisions.items())),
        }

    @staticmethod
    def _read_manifest(path: Path) -> dict[str, Any]:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkspaceError(f"cannot read workspace manifest {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise WorkspaceError(f"workspace manifest is not an object: {path}")
        return value

    @staticmethod
    def _validate_manifest_job(document: dict[str, Any], job: Job) -> None:
        if document.get("schema_version") != MANIFEST_VERSION:
            raise WorkspaceError("unsupported workspace manifest version")
        if document.get("job_id") != job.job_id:
            raise WorkspaceError("workspace manifest Job mismatch")
        if document.get("requested_source_revision") != job.source_revision:
            raise WorkspaceError("workspace manifest requested revision mismatch")

    @staticmethod
    def _manifest_revisions(document: dict[str, Any]) -> dict[str, str]:
        revisions = document.get("revisions")
        required = ("ace_engine", "specs", "sdk-js", "sdk_c")
        if not isinstance(revisions, dict) or any(
            not isinstance(revisions.get(name), str) or not revisions[name] for name in required
        ):
            raise WorkspaceError("workspace manifest has incomplete revisions")
        return {name: revisions[name] for name in required}

    @staticmethod
    def _validate_revision_set(revisions: dict[str, str]) -> None:
        required = ("ace_engine", "specs", "sdk-js", "sdk_c")
        if any(not isinstance(revisions.get(name), str) or not revisions[name] for name in required):
            raise WorkspaceError("reserved workspace has incomplete revisions")

    @staticmethod
    def _write_manifest(path: Path, document: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
        tmp.write_text(
            json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp, path)
