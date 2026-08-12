"""Named resource locks for the scheduler (TASK-011-05).

Two concerns:

* **In-process correctness** — a per-name ``threading.Lock`` serializes workers
  that touch the same resource key (e.g. the same FuncID), while different keys
  run concurrently up to the worker cap.
* **Observability / recoverability** — each held lock is mirrored to a small
  JSON file under ``locks_root`` so an operator can see what is held and a
  later phase can reap stale locks left by a crashed process.

Phase 3 uses a single shared source tree (no per-revision worktree checkout);
worktree-per-revision isolation is Phase 5 (TASK-011-10). Parallel jobs are
already safe because each job writes its own ``run_dir`` and the evaluator
cache/output root is overridden per invocation. The lock here therefore
enforces a same-FuncID de-dup invariant and provides the framework for finer
resource isolation later.
"""

from __future__ import annotations

import json
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class NamedLockManager:
    """In-process named locks with file markers under ``locks_root``."""

    def __init__(self, locks_root: Path) -> None:
        self._locks_root = Path(locks_root)
        self._locks_root.mkdir(parents=True, exist_ok=True)
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}
        self._holders: dict[str, str] = {}  # name -> holder id

    def _lock_for(self, name: str) -> threading.Lock:
        with self._guard:
            if name not in self._locks:
                self._locks[name] = threading.Lock()
            return self._locks[name]

    @contextmanager
    def acquire(self, name: str) -> Iterator[str]:
        """Acquire the named lock; yield a holder id; release on exit."""
        holder = uuid.uuid4().hex
        lock = self._lock_for(name)
        lock.acquire()
        try:
            with self._guard:
                self._holders[name] = holder
            self._write_marker(name, holder)
            yield holder
        finally:
            self._clear_marker(name)
            with self._guard:
                self._holders.pop(name, None)
            lock.release()

    def held_names(self) -> list[str]:
        with self._guard:
            return list(self._holders)

    def _marker_path(self, name: str) -> Path:
        safe = name.replace("/", "_").replace(":", "_")
        return self._locks_root / f"{safe}.lock.json"

    def _write_marker(self, name: str, holder: str) -> None:
        from ..store.sqlite_store import utc_now

        try:
            self._marker_path(name).write_text(
                json.dumps({"name": name, "holder": holder, "acquired_at": utc_now()}),
                encoding="utf-8",
            )
        except OSError:
            pass  # markers are advisory; never block execution

    def _clear_marker(self, name: str) -> None:
        try:
            self._marker_path(name).unlink(missing_ok=True)
        except OSError:
            pass
