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

_SCHEMA_VERSION = "7"

def utc_now() -> str:
    """Current UTC timestamp as an ISO-8601 string (seconds precision)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SqliteStore:
    """Owns the single SQLite connection and serializes all access to it."""

    def __init__(
        self, settings: ServiceSettings, *, run_recovery: bool = True,
    ) -> None:
        self.settings = settings
        self._conn = sqlite3.connect(str(settings.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.isolation_level = None  # explicit BEGIN/COMMIT via _tx
        self._lock = threading.RLock()
        self._tx_depth = 0
        self._apply_pragmas()
        self._run_migrations()
        # Crash recovery is a *startup-only* concern: it resets running jobs
        # left behind by a previous process crash.  Non-startup callers (e.g.
        # projector opening a temporary store) must pass run_recovery=False to
        # avoid killing jobs that are still executing in parallel workers.
        if run_recovery:
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
            # D1 is a cold-start boundary: historical service databases are
            # intentionally not migrated or silently relabeled as 0.2.0.
            # Operators must run `service_cli.py purge --yes` and start empty.
            if version == "6":
                self._conn.executescript("""
                    CREATE TABLE IF NOT EXISTS finding_ledger (
                      finding_id TEXT PRIMARY KEY,
                      func_id TEXT NOT NULL,
                      criterion_id TEXT NOT NULL,
                      severity TEXT NOT NULL DEFAULT 'Major',
                      message TEXT NOT NULL DEFAULT '',
                      status TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','resolved','refuted','superseded','out_of_scope')),
                      first_seen_run_id TEXT NOT NULL,
                      first_seen_at TEXT NOT NULL,
                      last_confirmed_run_id TEXT,
                      last_confirmed_at TEXT,
                      confirmation_count INTEGER NOT NULL DEFAULT 1,
                      executor_set TEXT NOT NULL DEFAULT '[]',
                      disposition_history TEXT NOT NULL DEFAULT '[]'
                    );
                    CREATE INDEX IF NOT EXISTS idx_ledger_func ON finding_ledger (func_id);
                    CREATE INDEX IF NOT EXISTS idx_ledger_status ON finding_ledger (func_id, status);
                    UPDATE schema_meta SET value = '7' WHERE key = 'schema_version';
                """)
                version = "7"
            if version != _SCHEMA_VERSION:
                raise RuntimeError(
                    f"database has incompatible schema version {version!r}; "
                    f"expected {_SCHEMA_VERSION!r}; purge the runtime data "
                    "for a protocol 0.2.0 cold start"
                )
            columns = {
                column["name"]
                for column in self._conn.execute("PRAGMA table_info(jobs)").fetchall()
            }
            if "stage" not in columns:
                raise RuntimeError(
                    "database uses a pre-0.2.0 jobs schema; purge the runtime "
                    "data for a protocol 0.2.0 cold start"
                )

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
