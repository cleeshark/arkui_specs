"""Bounded job dispatcher (TASK-011-05).

A fixed pool of worker threads pulls ``queued`` jobs and runs each through an
injectable ``job_runner``. Concurrency is bounded by ``max_workers``; jobs for
the same FuncID are serialized via a named resource lock so two evaluations of
one Function never overlap (different Functions do). The store is thread-safe,
so workers share one connection.

The dispatcher is the only component that starts work; the HTTP layer and tests
only ``submit``/``cancel``/``retry``. Recovery is automatic: on ``start`` every
``queued`` job (including those reset from a crash by the store) is enqueued.
"""

from __future__ import annotations

import logging
import queue
import threading
from typing import Callable, Optional

from ..domain import states as S
from ..store.repositories import JobRepository
from ..store.sqlite_store import SqliteStore
from .cancellation import CancelRegistry
from .resource_lock import NamedLockManager

log = logging.getLogger(__name__)

# A job runner executes one job id, honouring a cooperative cancel flag.
JobRunner = Callable[[str, threading.Event], None]


class Dispatcher:
    def __init__(
        self,
        store: SqliteStore,
        *,
        job_runner: JobRunner,
        max_workers: int = 2,
        lock_manager: Optional[NamedLockManager] = None,
        cancel_registry: Optional[CancelRegistry] = None,
    ) -> None:
        self._store = store
        self._job_runner = job_runner
        self._max_workers = max(1, max_workers)
        self._locks = lock_manager or NamedLockManager(store.settings.locks_root)
        self._cancels = cancel_registry or CancelRegistry()
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._stop = threading.Event()
        self._workers: list[threading.Thread] = []
        self._enqueued: set[str] = set()
        self._enqueued_guard = threading.Lock()

    # --- lifecycle --------------------------------------------------------
    def start(self) -> None:
        """Start workers and enqueue every job currently ``queued``."""
        jobs = JobRepository(self._store).list_jobs(status=S.QUEUED, limit=10_000)
        for job in jobs:
            self._enqueue(job.job_id, job.func_id)
        for i in range(self._max_workers):
            t = threading.Thread(target=self._loop, name=f"semantic-worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def shutdown(self, *, timeout: float = 5.0) -> None:
        self._stop.set()
        for t in self._workers:
            t.join(timeout=timeout)
        self._workers.clear()

    # --- commands ---------------------------------------------------------
    def submit(self, job_id: str, func_id: str) -> None:
        self._enqueue(job_id, func_id)

    def cancel(self, job_id: str) -> bool:
        return self._cancels.cancel(job_id)

    def retry(self, job_id: str) -> str:
        """Reset a failed/cancelled job to queued and enqueue it. Returns status."""
        jobs = JobRepository(self._store)
        try:
            job = jobs.retry(job_id)
        except Exception:  # JobNotFoundError or IllegalTransitionError
            return jobs.get_job(job_id).status if self._job_exists(job_id) else S.FAILED
        self._enqueue(job.job_id, job.func_id)
        return job.status

    def _job_exists(self, job_id: str) -> bool:
        try:
            JobRepository(self._store).get_job(job_id)
            return True
        except Exception:
            return False

    def _enqueue(self, job_id: str, func_id: str) -> None:
        self._cancels.register(job_id)
        with self._enqueued_guard:
            if job_id in self._enqueued:
                return
            self._enqueued.add(job_id)
        self._queue.put(job_id)

    # --- worker loop ------------------------------------------------------
    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                job_id = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._run_one(job_id)
            except Exception:  # pragma: no cover - defensive
                log.exception("worker crashed on job %s", job_id)
            finally:
                self._queue.task_done()

    def _run_one(self, job_id: str) -> None:
        job = JobRepository(self._store).get_job(job_id)
        cancel = self._cancels.register(job_id)
        if cancel.is_set():
            self._finalize(job_id)
            return
        # Serialize jobs for the same FuncID; different FuncIDs run in parallel.
        with self._locks.acquire(f"funcid:{job.func_id}"):
            if not cancel.is_set():
                try:
                    self._job_runner(job_id, cancel)
                except Exception as exc:
                    log.exception("job %s runner raised; marking failed", job_id)
                    self._mark_failed(job_id, str(exc))
        self._finalize(job_id)

    def _mark_failed(self, job_id: str, message: str) -> None:
        from ..domain.errors import IllegalTransitionError

        jobs = JobRepository(self._store)
        try:
            jobs.transition_status(
                job_id, S.FAILED, event_type="worker_crashed", payload={"error": message[:500]}
            )
        except (IllegalTransitionError, Exception):  # pragma: no cover
            log.warning("could not mark job %s failed", job_id)

    def _finalize(self, job_id: str) -> None:
        self._cancels.release(job_id)
        with self._enqueued_guard:
            self._enqueued.discard(job_id)

    @property
    def is_idle(self) -> bool:
        return self._queue.unfinished_tasks == 0
