"""Data governance (TASK-011-09): retention cleanup, backup/restore, disk usage.

* **cleanup** removes only disposable per-job run directories (staged evidence,
  logs) for jobs that reached a terminal state older than the retention window.
  Completed automated archives are retained by default; nothing under
  ``archives/`` is ever deleted here.
* **backup** checkpoints the WAL, copies the SQLite DB, and verifies the copy
  opens and reports the expected schema version.
* **disk_usage** reports bytes used per data subdir plus free space, so an
  operator can alert before the volume fills.

No token/PII-bearing content is read or copied; backups contain only DB state
and archive manifests, which already exclude secrets by construction.
"""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .domain import states as S
from .settings import ServiceSettings
from .store.repositories import JobRepository
from .store.sqlite_store import SqliteStore, utc_now

_SCHEMA_VERSION = "2"


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
    if row is None or row[0] != _SCHEMA_VERSION:
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
