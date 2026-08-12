"""Job worker: binds the dispatcher to the real pipeline (TASK-011-05).

``build_runner`` returns a closure the dispatcher calls per job. It constructs
fresh repository handles (cheap; they only hold a back-reference to the shared,
thread-safe store) and delegates to :func:`run_job_pipeline`. Status
transitions on success/awaiting/failure happen inside the pipeline; any
unexpected exception is caught by the dispatcher and marked ``failed``.
"""

from __future__ import annotations

import threading
from typing import Callable

from ..executors.base import SemanticExecutor
from ..pipeline._subprocess import Runner, default_runner
from ..pipeline.semantic_stage import run_job_pipeline
from ..settings import ServiceSettings
from ..store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EventRepository,
    JobRepository,
)
from ..store.sqlite_store import SqliteStore


def build_runner(
    settings: ServiceSettings,
    store: SqliteStore,
    executor: SemanticExecutor,
    *,
    runner: Runner = default_runner,
) -> Callable[[str, threading.Event], None]:
    """Return a ``run_job(job_id, cancel)`` closure for the dispatcher."""

    def run_job(job_id: str, cancel: threading.Event) -> None:
        run_job_pipeline(
            job_id,
            settings=settings,
            jobs=JobRepository(store),
            attempts=AttemptRepository(store),
            events=EventRepository(store),
            artifacts=ArtifactRepository(store),
            snapshots=DependencySnapshotRepository(store),
            executor=executor,
            cancel=cancel,
            runner=runner,
        )

    return run_job
