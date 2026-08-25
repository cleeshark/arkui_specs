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

from ..domain import states as S
from ..executors import contract as C
from ..executors.base import SemanticExecutor
from ..pipeline._subprocess import Runner, default_runner
from ..pipeline.semantic_stage import run_job_pipeline
from ..settings import ServiceSettings
from ..store.repositories import (
    ArtifactRepository,
    AttemptRepository,
    DependencySnapshotRepository,
    EventRepository,
    FunctionReportHeadRepository,
    ExecutorCallRepository,
    JobStatisticsRepository,
    JobRepository,
    RefreshTargetRepository,
)
from ..store.sqlite_store import SqliteStore
from ..workspace.manager import RevisionWorkspaceManager


def build_runner(
    settings: ServiceSettings,
    store: SqliteStore,
    executor: SemanticExecutor,
    *,
    executor_resolver: Callable[[dict], SemanticExecutor] | None = None,
    runner: Runner = default_runner,
) -> Callable[[str, threading.Event], None]:
    """Return a ``run_job(job_id, cancel)`` closure for the dispatcher."""

    def run_job(job_id: str, cancel: threading.Event) -> None:
        workspace_manager = RevisionWorkspaceManager(settings)
        targets = RefreshTargetRepository(store)
        jobs = JobRepository(store)
        raised = False
        try:
            # Retry normally restores refresh ownership in Dispatcher.retry.
            # Repeat the idempotent repair here so a process crash between the
            # queued transition and enqueue cannot strand the target again.
            targets.reactivate_for_retry(job_id)
            job = jobs.get_job(job_id)
            selected_executor = (
                executor_resolver(job.executor_config)
                if executor_resolver is not None
                else executor
            )
            result = run_job_pipeline(
                job_id,
                settings=settings,
                jobs=jobs,
                attempts=AttemptRepository(store),
                events=EventRepository(store),
                artifacts=ArtifactRepository(store),
                snapshots=DependencySnapshotRepository(store),
                executor=selected_executor,
                workspace_provider=workspace_manager.prepare,
                refresh_targets=targets,
                statistics=JobStatisticsRepository(store),
                invocations=ExecutorCallRepository(store),
                cancel=cancel,
                runner=runner,
            )
            if result.outcome == C.STATUS_CANCELLED:
                current = jobs.get_job(job_id)
                if current.status not in S.TERMINAL_STATES:
                    jobs.cancel(job_id, reason=result.error or "cancelled by user")
        except Exception as exc:
            raised = True
            _mark_refresh_failed(store, targets, job_id, str(exc))
            raise
        finally:
            job = jobs.get_job(job_id)
            if job.status in {"failed", "cancelled"}:
                _mark_refresh_failed(store, targets, job_id, job.status)
            if raised or job.status in {"completed", "failed", "cancelled"}:
                workspace_manager.release(job_id)

    return run_job


def _mark_refresh_failed(
    store: SqliteStore, targets: RefreshTargetRepository, job_id: str, error: str
) -> None:
    target = targets.get(job_id)
    if target is None or target.status != "ACTIVE":
        return
    targets.finish(job_id, status="FAILED")
    FunctionReportHeadRepository(store).mark_refresh_failed(target.func_id, job_id, error)
