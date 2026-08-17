"""SQLite Job Store: the sole write boundary for the semantic service.

Design (see service plan §6.1.2 and the four confirmed decisions):

* **Single writer** — one shared connection (``check_same_thread=False``) guarded
  by one re-entrant lock. Every write goes through :meth:`_tx`; nested ``_tx``
  calls share the outer transaction, so repository methods compose.
* **Monotonic event seq** — :meth:`_append_event` computes
  ``COALESCE(MAX(seq),0)+1`` and INSERTs inside the locked transaction; the
  ``events`` PRIMARY KEY (job_id, seq) is the hard backstop.
* **Crash recovery** — :meth:`recover_active_jobs` is a *privileged* startup
  path (not the worker transition matrix). It resets every worker-owned active
  job to ``queued`` and records a ``recovery_reset`` event. A recovered job is
  never reported ``completed`` (service plan §9 anti-fake-completion).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from ..domain import states as S
from ..settings import ServiceSettings

_SCHEMA_VERSION = "6"

_V4_STATISTICS_COLUMNS = {
    "telemetry_reported_invocations": "INTEGER NOT NULL DEFAULT 0 CHECK (telemetry_reported_invocations >= 0)",
    "executor_tool_calls": "INTEGER NOT NULL DEFAULT 0 CHECK (executor_tool_calls >= 0)",
    "executor_command_calls": "INTEGER NOT NULL DEFAULT 0 CHECK (executor_command_calls >= 0)",
    "input_paths_accessed": "INTEGER NOT NULL DEFAULT 0 CHECK (input_paths_accessed >= 0)",
    "evidence_paths_accessed": "INTEGER NOT NULL DEFAULT 0 CHECK (evidence_paths_accessed >= 0)",
}


def utc_now() -> str:
    """Current UTC timestamp as an ISO-8601 string (seconds precision)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SqliteStore:
    """Owns the single SQLite connection and serializes all access to it."""

    def __init__(self, settings: ServiceSettings) -> None:
        self.settings = settings
        self._conn = sqlite3.connect(str(settings.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.isolation_level = None  # explicit BEGIN/COMMIT via _tx
        self._lock = threading.RLock()
        self._tx_depth = 0
        self._apply_pragmas()
        self._run_migrations()
        # Crash recovery runs on every open: a fresh DB has no active jobs, so
        # it is a no-op there; a reopened DB resumes interrupted jobs to queued.
        self.recover_active_jobs()

    # --- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "SqliteStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # --- connection setup --------------------------------------------------
    def _apply_pragmas(self) -> None:
        with self._lock:
            # journal_mode is persistent and must not run inside a transaction.
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA busy_timeout=5000")

    def _run_migrations(self) -> None:
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        with self._lock:
            # schema.sql is idempotent (IF NOT EXISTS + INSERT OR IGNORE), so
            # re-running it on every open is safe. executescript issues its own
            # COMMIT, so it must NOT be called inside _tx.
            self._conn.executescript(schema_path.read_text(encoding="utf-8"))
            row = self._conn.execute(
                "SELECT value FROM schema_meta WHERE key = 'schema_version'"
            ).fetchone()
            version = row["value"] if row is not None else None
            self._migrate_v6_jobs()
            if version in {"1", "2", "3", "4"}:
                # v4 telemetry counters cannot be added by CREATE TABLE IF NOT
                # EXISTS on an existing table; add only the missing columns.
                columns = {
                    column["name"]
                    for column in self._conn.execute(
                        "PRAGMA table_info(job_statistics)"
                    ).fetchall()
                }
                for name, declaration in _V4_STATISTICS_COLUMNS.items():
                    if name not in columns:
                        self._conn.execute(
                            f"ALTER TABLE job_statistics ADD COLUMN {name} {declaration}"
                        )
            if version is not None and version not in {
                "1", "2", "3", "4", "5", _SCHEMA_VERSION,
            }:
                raise RuntimeError(
                    f"database has schema version '{version}' which is newer "
                    f"than the supported version '{_SCHEMA_VERSION}'; upgrade "
                    f"the service or use a compatible database"
                )
            if version != _SCHEMA_VERSION:
                self._conn.execute(
                    "UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
                    (_SCHEMA_VERSION,),
                )

    def _migrate_v6_jobs(self) -> None:
        """Rebuild a pre-v6 jobs table onto the six-status + stage model.

        The old eleven-value CHECK cannot be ALTERed, so the table is rebuilt.
        ``legacy_alter_table`` keeps child foreign keys (attempts, events, ...)
        pointing at the name ``jobs`` while the legacy copy is swapped out, so
        no child rows are ever dropped. 0.1.x statuses map onto
        (running|waiting, stage); completed jobs land on stage ``projection``
        for a fully-done stepper display.
        """
        columns = {
            column["name"]
            for column in self._conn.execute("PRAGMA table_info(jobs)").fetchall()
        }
        if "stage" in columns:
            return  # already v6
        # rebuild without touching child tables: FK enforcement off (outside
        # any transaction), swap the table, then re-enable enforcement
        self._conn.commit()
        self._conn.execute("PRAGMA foreign_keys = OFF")
        try:
            jobs_ddl = "\n".join(
                line for line in (
                    Path(__file__).resolve().parent / "schema.sql"
                ).read_text(encoding="utf-8").split("\n")
                if line.strip()
            )
            start = jobs_ddl.index("CREATE TABLE IF NOT EXISTS jobs (")
            end = jobs_ddl.index(");", start) + 2
            create_sql = (
                jobs_ddl[start:end]
                .replace(
                    "CREATE TABLE IF NOT EXISTS jobs",
                    "CREATE TABLE jobs_v6_rebuild", 1,
                )
            )
            self._conn.execute("DROP TABLE IF EXISTS jobs_v6_rebuild")
            self._conn.execute(create_sql)
            self._conn.execute(
                """
                INSERT INTO jobs_v6_rebuild (
                    job_id, func_id, source_revision, run_count, selected_run_ids,
                    status, stage, progress_json, executor_config,
                    protocol_version, evaluator_version, created_at, updated_at
                )
                SELECT
                    job_id, func_id, source_revision, run_count, selected_run_ids,
                    CASE status
                        WHEN 'queued' THEN 'queued'
                        WHEN 'awaiting_executor' THEN 'waiting'
                        WHEN 'completed' THEN 'completed'
                        WHEN 'failed' THEN 'failed'
                        WHEN 'cancelled' THEN 'cancelled'
                        ELSE 'running'
                    END,
                    CASE status
                        WHEN 'preparing' THEN 'preparing'
                        WHEN 'evidence' THEN 'evidence'
                        WHEN 'semantic' THEN 'observation'
                        WHEN 'aggregation' THEN 'aggregation'
                        WHEN 'archive' THEN 'archive'
                        WHEN 'site_history' THEN 'archive'
                        WHEN 'completed' THEN 'projection'
                        ELSE 'preparing'
                    END,
                    progress_json, executor_config, protocol_version,
                    evaluator_version, created_at, updated_at
                FROM jobs
                """
            )
            self._conn.execute("DROP TABLE jobs")
            self._conn.execute("PRAGMA legacy_alter_table = ON")
            self._conn.execute("ALTER TABLE jobs_v6_rebuild RENAME TO jobs")
            self._conn.execute("PRAGMA legacy_alter_table = OFF")
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_func_revision "
                "ON jobs (func_id, source_revision)"
            )
            self._conn.commit()
        finally:
            self._conn.execute("PRAGMA foreign_keys = ON")

    # --- transaction context manager --------------------------------------
    @contextmanager
    def _tx(self, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """Serialize a unit of work on the shared connection.

        Re-entrant: a ``_tx`` opened inside another ``_tx`` shares the outer
        transaction and does not issue a nested BEGIN/COMMIT.
        """
        with self._lock:
            outer = self._tx_depth == 0
            if outer:
                self._conn.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            self._tx_depth += 1
            try:
                yield self._conn
                if outer:
                    self._conn.commit()
            except BaseException:
                if outer:
                    self._conn.rollback()
                raise
            finally:
                self._tx_depth -= 1

    # --- low-level event append (callers must already hold _tx) ------------
    def _append_event(
        self,
        job_id: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        now: str | None = None,
    ) -> int:
        """Insert the next monotonic event for ``job_id`` and return its seq."""
        seq_row = self._conn.execute(
            "SELECT COALESCE(MAX(seq), 0) + 1 AS next_seq FROM events WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        seq = int(seq_row["next_seq"])
        self._conn.execute(
            "INSERT INTO events (job_id, seq, event_type, payload_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                job_id,
                seq,
                event_type,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                now or utc_now(),
            ),
        )
        return seq

    # --- crash recovery (privileged startup path) --------------------------
    def recover_active_jobs(self) -> int:
        """Reset every worker-owned active job to ``queued``.

        ``awaiting_executor`` is left untouched (it is scheduler-owned waiting,
        not a crashed worker). Each reset is one atomic transaction that also
        appends a ``recovery_reset`` event recording the prior status. Returns
        the number of jobs reset.
        """
        # crash recovery: both worker-owned running jobs and paused waiting
        # jobs resume from queued (design R6: no dead-end waiting state)
        active = tuple(S.ACTIVE_STATES | S.WAITING_STATES)
        placeholders = ",".join("?" for _ in active)
        with self._tx():
            rows = self._conn.execute(
                f"SELECT job_id, status FROM jobs WHERE status IN ({placeholders})",
                active,
            ).fetchall()
        for row in rows:
            now = utc_now()
            with self._tx(immediate=True):
                # Re-check inside the write tx: another recovery could have run.
                current = self._conn.execute(
                    "SELECT status FROM jobs WHERE job_id = ?", (row["job_id"],)
                ).fetchone()
                if current is None or current["status"] not in (
                    S.ACTIVE_STATES | S.WAITING_STATES
                ):
                    continue
                self._conn.execute(
                    "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
                    (S.QUEUED, now, row["job_id"]),
                )
                self._append_event(
                    row["job_id"],
                    "recovery_reset",
                    {"prior_status": current["status"]},
                    now=now,
                )
        return len(rows)
