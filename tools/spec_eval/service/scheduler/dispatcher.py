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
from dataclasses import dataclass
from typing import Callable, Optional

from ..domain import states as S
from ..domain.errors import IllegalTransitionError, JobNotFoundError
from ..store.repositories import EventRepository, JobRepository
from ..store.sqlite_store import SqliteStore
from .cancellation import CancelRegistry
from .resource_lock import NamedLockManager

log = logging.getLogger(__name__)

# A job runner executes one job id, honouring a cooperative cancel flag.
JobRunner = Callable[[str, threading.Event], None]


@dataclass(frozen=True)
class CancelResult:
    """State-aware result of a cancellation command."""

    accepted: bool
    outcome: str
    status: str | None
    message: str


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

    def cancel(self, job_id: str) -> CancelResult:
        jobs = JobRepository(self._store)
        try:
            job = jobs.get_job(job_id)
        except JobNotFoundError:
            return CancelResult(False, "not_found", None, "job not found")

        if job.status in S.TERMINAL_STATES:
            return CancelResult(
                False,
                "already_terminal",
                job.status,
                f"job is already {job.status}",
            )

        if job.status in S.IMMEDIATE_CANCEL_STATES:
            # A queued item may already be present in the dispatch queue. Set its
            # event first so a racing worker observes the request, then persist
            # the terminal state. _run_one skips terminal queue entries.
            self._cancels.cancel(job_id)
            try:
                cancelled = jobs.cancel(job_id, reason=f"cancelled while {job.status}")
            except IllegalTransitionError:
                return self._cancel_race_result(job_id)
            return CancelResult(True, "cancelled", cancelled.status, "job cancelled")

        if job.status in S.CANCELLABLE_WORKER_STATES:
            already_requested = self._cancels.is_cancelled(job_id)
            if self._cancels.cancel(job_id):
                if not already_requested:
                    EventRepository(self._store).append(
                        job_id, "cancel_requested", {"status": job.status}
                    )
                return CancelResult(
                    True,
                    (
                        "cancellation_already_requested"
                        if already_requested
                        else "cancellation_requested"
                    ),
                    job.status,
                    (
                        "cancellation already requested"
                        if already_requested
                        else "cancellation requested"
                    ),
                )

            # An active DB state without a registered worker is an orphan. There
            # is no process left to observe a cooperative flag, so close it
            # deterministically instead of returning the old misleading 409.
            try:
                cancelled = jobs.cancel(job_id, reason="active job has no registered worker")
            except IllegalTransitionError:
                return self._cancel_race_result(job_id)
            EventRepository(self._store).append(
                job_id, "orphaned_job_cancelled", {"prior_status": job.status}
            )
            return CancelResult(True, "cancelled", cancelled.status, "orphaned job cancelled")

        return CancelResult(
            False,
            "stage_not_cancellable",
            job.status,
            f"job cannot be cancelled while {job.status}",
        )

    def _cancel_race_result(self, job_id: str) -> CancelResult:
        try:
            current = JobRepository(self._store).get_job(job_id)
        except JobNotFoundError:
            return CancelResult(False, "not_found", None, "job not found")
        if current.status in S.TERMINAL_STATES:
            return CancelResult(
                current.status == S.CANCELLED,
                "cancelled" if current.status == S.CANCELLED else "already_terminal",
                current.status,
                f"job is already {current.status}",
            )
        return CancelResult(
            False,
            "state_changed",
            current.status,
            f"job state changed to {current.status}; retry the command",
        )

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
        try:
            if job.status in S.QUIESCENT_STATES:
                return
            if cancel.is_set():
                self._mark_cancelled(job_id, "cancelled before worker start")
                return
            # Serialize jobs for the same FuncID; different FuncIDs run in parallel.
            with self._locks.acquire(f"funcid:{job.func_id}"):
                job = JobRepository(self._store).get_job(job_id)
                if job.status in S.QUIESCENT_STATES:
                    return
                if cancel.is_set():
                    self._mark_cancelled(job_id, "cancelled while waiting for resource lock")
                    return
                try:
                    self._job_runner(job_id, cancel)
                except Exception as exc:
                    log.exception("job %s runner raised; marking failed", job_id)
                    self._mark_failed(job_id, str(exc))
                self._reconcile_runner_exit(job_id, cancel)
        finally:
            self._finalize(job_id)

    def _reconcile_runner_exit(self, job_id: str, cancel: threading.Event) -> None:
        job = JobRepository(self._store).get_job(job_id)
        if job.status in S.QUIESCENT_STATES:
            return
        if cancel.is_set():
            self._mark_cancelled(job_id, "worker stopped after cancellation request")
            return
        self._mark_failed(job_id, "worker returned without reaching a quiescent state")

    def _mark_cancelled(self, job_id: str, reason: str) -> None:
        jobs = JobRepository(self._store)
        try:
            current = jobs.get_job(job_id)
            if current.status in S.TERMINAL_STATES:
                return
            jobs.cancel(job_id, reason=reason)
        except IllegalTransitionError:
            current = jobs.get_job(job_id)
            if current.status not in S.TERMINAL_STATES:
                log.exception("could not mark job %s cancelled from %s", job_id, current.status)

    def _mark_failed(self, job_id: str, message: str) -> None:
        jobs = JobRepository(self._store)
        try:
            jobs.transition_status(
                job_id,
                S.FAILED,
                event_type=(
                    "worker_returned_nonterminal"
                    if message == "worker returned without reaching a quiescent state"
                    else "worker_crashed"
                ),
                payload={"error": message[:500]},
            )
        except IllegalTransitionError:
            current = jobs.get_job(job_id)
            if current.status not in S.TERMINAL_STATES:
                log.exception("could not mark job %s failed from %s", job_id, current.status)
        except Exception:  # pragma: no cover - store failure
            log.exception("could not persist failed status for job %s", job_id)

    def _finalize(self, job_id: str) -> None:
        try:
            status = JobRepository(self._store).get_job(job_id).status
        except JobNotFoundError:  # pragma: no cover - defensive
            status = None
        if status not in S.QUIESCENT_STATES:
            log.error(
                "job %s worker finalized in non-quiescent state %s; keeping cancellation registration",
                job_id,
                status,
            )
            return
        self._cancels.release(job_id)
        with self._enqueued_guard:
            self._enqueued.discard(job_id)

    @property
    def is_idle(self) -> bool:
        return self._queue.unfinished_tasks == 0
