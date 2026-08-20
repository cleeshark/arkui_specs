"""Data governance (TASK-011-09): retention cleanup, backup/restore, disk usage.

* **cleanup** removes only disposable per-job run directories (staged evidence,
  logs) for jobs that reached a terminal state older than the retention window.
  Completed automated archives are retained by default; nothing under
  ``archives/`` is ever deleted here.
* **backup** checkpoints the WAL, copies the SQLite DB, and verifies the copy
  opens and reports the expected schema version.
* **disk_usage** reports bytes used per data subdir plus free space, so an
  operator can alert before the volume fills.

No credentials, prompts or PII are read or copied; backups contain DB state,
non-sensitive usage counters and archive manifests.
"""

from __future__ import annotations

import shutil
import sqlite3
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .domain import states as S
from .settings import ServiceSettings
from .store.repositories import JobRepository
from .store.sqlite_store import SqliteStore, utc_now

_EXPECTED_SCHEMA_VERSION = "7"


def cleanup_temp(
    settings: ServiceSettings,
    store: SqliteStore,
    *,
    retention_days: int,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Delete disposable run dirs for terminal jobs older than ``retention_days``.

    Archives are never touched. Returns a summary of freed bytes and affected
    job ids.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    jobs = JobRepository(store).list_jobs(limit=100_000)
    cleaned: list[str] = []
    freed = 0
    for job in jobs:
        if job.status not in S.TERMINAL_STATES:
            continue
        updated = _parse(job.updated_at)
        if updated is None or updated > cutoff:
            continue
        run_root = settings.jobs_root / job.job_id
        if not run_root.is_dir():
            continue
        size = _dir_size(run_root)
        shutil.rmtree(run_root, ignore_errors=True)
        cleaned.append(job.job_id)
        freed += size
    return {"cleaned_job_ids": cleaned, "freed_bytes": freed, "retention_days": retention_days}


def backup_database(
    settings: ServiceSettings,
    *,
    backup_root: Path | None = None,
) -> Path:
    """Checkpoint WAL, copy the DB to ``backups/``, verify it restores."""
    backup_root = backup_root or settings.backups_root
    backup_root.mkdir(parents=True, exist_ok=True)

    # Flush WAL into the main DB file so the copy is consistent.
    conn = sqlite3.connect(str(settings.db_path))
    try:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    stamp = utc_now().replace(":", "").replace("+", "_")
    dest = backup_root / f"service-{stamp}.sqlite3"
    shutil.copy2(settings.db_path, dest)
    # also copy sidecar WAL/SHM if present (post-checkpoint they are usually empty)
    for suffix in ("-wal", "-shm"):
        side = Path(str(settings.db_path) + suffix)
        if side.exists():
            shutil.copy2(side, Path(str(dest) + suffix))

    _verify_backup(dest)
    return dest


def disk_usage(settings: ServiceSettings) -> dict[str, Any]:
    """Report bytes used per data subdir plus device free space."""
    usage = shutil.disk_usage(settings.data_root)
    by_subdir: dict[str, int] = {}
    for name in ("db", "jobs", "archives", "locks", "logs", "backups", "workspaces"):
        path = settings.data_root / name
        by_subdir[name] = _dir_size(path) if path.is_dir() else 0
    return {
        "data_root": str(settings.data_root),
        "free_bytes": usage.free,
        "total_bytes": usage.total,
        "used_bytes_by_subdir": by_subdir,
    }


# --- helpers ----------------------------------------------------------------

def _verify_backup(dest: Path) -> None:
    conn = sqlite3.connect(str(dest))
    try:
        row = conn.execute("SELECT value FROM schema_meta WHERE key='schema_version'").fetchone()
    finally:
        conn.close()
    if row is None or row[0] != _EXPECTED_SCHEMA_VERSION:
        raise RuntimeError(f"backup verification failed for {dest}: schema_version={row}")


def _dir_size(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                continue
    return total


def _parse(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def purge_all(
    settings: ServiceSettings,
    *,
    export_first: bool = False,
) -> dict[str, Any]:
    """Delete all service runtime data for a cold protocol restart (0.2.0, D1).

    Clears every runtime data subdirectory (db, jobs, archives, locks, logs,
    backups, workspaces, exports) so the next start rebuilds an empty schema.
    With ``export_first`` a DB backup snapshot is taken before anything is
    removed. Idempotent: re-running on an already purged root is a no-op.

    Never touches the repository itself: ``evaluation/reviews/`` (confirmed
    human baselines), static baselines and any code stay untouched.
    """
    export_path: str | None = None
    if export_first and settings.db_path.is_file():
        # Keep the snapshot outside the tree that is about to be deleted.
        export_root = settings.data_root.parent / (settings.data_root.name + "-purge-export")
        export_path = str(backup_database(settings, backup_root=export_root))

    removed: dict[str, int] = {}
    for name in (
        "jobs", "archives", "locks", "logs", "backups", "workspaces", "exports",
    ):
        path = settings.data_root / name
        # empty skeleton directories are left alone so a repeated purge is a
        # true no-op
        if path.is_dir() and any(path.iterdir()):
            shutil.rmtree(path)
            removed[name] = 1
        else:
            removed[name] = 0
    db_removed = 0
    for suffix in ("", "-wal", "-shm"):
        db_side = Path(str(settings.db_path) + suffix)
        if db_side.exists():
            db_side.unlink()
            db_removed = 1
    removed["db"] = db_removed
    # Recreate the empty skeleton the settings object expects to exist.
    for name in (
        "db", "jobs", "archives", "locks", "logs", "backups", "workspaces",
        "exports",
    ):
        (settings.data_root / name).mkdir(parents=True, exist_ok=True)
    return {
        "data_root": str(settings.data_root),
        "exported": bool(export_first),
        "export_path": export_path,
        "removed": removed,
    }


def purge_legacy_artifacts(settings: ServiceSettings) -> dict[str, Any]:
    """Remove staged/archive artifacts from pre-0.2.0 runs only.

    Current archive manifests also use a small manifest schema number, so the
    legacy decision is based on the evaluator version for archives and on the
    staged schema/evaluator identity for job run files.  The operation is
    deliberately file-scoped and idempotent; it never touches the SQLite DB,
    confirmed reviews, or static baselines.
    """
    removed: list[str] = []
    roots = (settings.jobs_root, settings.archives_root)
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(value, dict):
                continue
            evaluator = value.get("evaluator_version")
            schema = value.get("schema_version")
            legacy = isinstance(evaluator, str) and "@0.1." in evaluator
            if root == settings.jobs_root:
                legacy = legacy or (isinstance(schema, int) and schema < 2)
            elif root == settings.archives_root and path.name != "archive-manifest.json":
                legacy = legacy or (isinstance(schema, int) and schema < 3)
            if legacy:
                path.unlink(missing_ok=True)
                removed.append(str(path))
    return {"data_root": str(settings.data_root), "removed": removed}
