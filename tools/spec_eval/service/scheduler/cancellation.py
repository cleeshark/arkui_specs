"""Cancellation registry (TASK-011-05).

Tracks one cooperative cancel flag per job. The dispatcher registers a flag
when a job starts and passes it down through ``run_job_pipeline`` so the
executor subprocess and the staged loop can terminate promptly. Cancellation is
strictly cooperative: setting the flag asks the worker to stop; it does not
forcibly kill anything outside the executor's own process group.
"""

from __future__ import annotations

import threading


class CancelRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, threading.Event] = {}

    def register(self, job_id: str) -> threading.Event:
        with self._lock:
            ev = self._events.get(job_id)
            if ev is None:
                ev = threading.Event()
                self._events[job_id] = ev
            return ev

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            ev = self._events.get(job_id)
        if ev is None:
            return False
        ev.set()
        return True

    def is_cancelled(self, job_id: str) -> bool:
        with self._lock:
            ev = self._events.get(job_id)
        return ev is not None and ev.is_set()

    def release(self, job_id: str) -> None:
        with self._lock:
            self._events.pop(job_id, None)

    def active(self) -> list[str]:
        with self._lock:
            return list(self._events)
