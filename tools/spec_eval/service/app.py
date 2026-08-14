"""Service assembly (TASK-011-06): wires Store + Executor + Dispatcher.

``SemanticServiceApp`` is the single object the HTTP layer and CLI talk to. It
exposes the operations the routes need (create/list/get/cancel/retry/events/
artifact) and owns the dispatcher lifecycle. Mutations only go through the
repositories and dispatcher; the HTTP layer never touches SQLite or subprocesses.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .domain.models import CreateJobCommand, FreshnessPolicy, Job
from .freshness import FreshnessManager
from .function_views import FunctionViewService
from .executors.base import SemanticExecutor
from .executors.codex_cli import CodexCliExecutor
from .pipeline.context import DEFAULT_SKILL_EVALUATOR_VERSION
from .manual_refresh import ManualRefreshService
from .scheduler.dispatcher import Dispatcher
from .scheduler.job_worker import build_runner
from .settings import ServiceSettings
from .store.repositories import (
    ArtifactRepository,
    EventRepository,
    FreshnessPolicyRepository,
    EvaluationReportRepository,
    FunctionReportHeadRepository,
    JobStatisticsRepository,
    JobRepository,
)
from .store.sqlite_store import SqliteStore, utc_now


class SemanticServiceApp:
    def __init__(
        self,
        settings: ServiceSettings,
        *,
        executor: SemanticExecutor | None = None,
        job_runner=None,
        max_workers: int = 2,
        token: str | None = None,
    ) -> None:
        self.settings = settings
        self.token = token
        self.store = SqliteStore(settings)
        FreshnessPolicyRepository(self.store).ensure_default()
        self.ui_dir = Path(__file__).resolve().parent / "ui"
        self._executor = executor or CodexCliExecutor(
            settings.default_executor_config, schemas_root=settings.schemas_root
        )
        runner = job_runner or build_runner(settings, self.store, self._executor)
        self.dispatcher = Dispatcher(self.store, job_runner=runner, max_workers=max_workers)
        self.manual_refresh = ManualRefreshService(self)

    # --- repositories (fresh handles are cheap; they only reference the store) -
    @property
    def jobs(self) -> JobRepository:
        return JobRepository(self.store)

    # --- operations used by HTTP routes -----------------------------------
    def default_source_revision(self) -> str:
        return _git_sha(self.settings.repo_root) or "unknown"

    def create_job(
        self,
        *,
        func_id: str,
        run_count: int,
        source_revision: str,
        job_id: str | None = None,
    ) -> Job:
        cmd = CreateJobCommand(
            func_id=func_id,
            source_revision=source_revision,
            run_count=run_count,
            job_id=job_id,
            executor_config=self.settings.default_executor_config,
        )
        job = self.jobs.create_job(
            cmd,
            evaluator_version=DEFAULT_SKILL_EVALUATOR_VERSION,
            executor_config=self.settings.default_executor_config,
        )
        EventRepository(self.store).append(job.job_id, "job_submitted", {})
        self.dispatcher.submit(job.job_id, job.func_id)
        return job

    def refresh_function(
        self, *, func_id: str, source_revision: str | None = None, run_count: int = 1
    ):
        return self.manual_refresh.request(
            func_id=func_id,
            source_revision=source_revision or self.default_source_revision(),
            run_count=run_count,
        )

    def list_functions(self):
        return FunctionViewService(self.settings, self.store).list_functions(
            observed_revision=self.default_source_revision()
        )

    def get_function(self, func_id: str):
        return FunctionViewService(self.settings, self.store).get_function(
            func_id, observed_revision=self.default_source_revision()
        )

    def function_history(self, func_id: str):
        return FunctionViewService(self.settings, self.store).history(func_id)

    def freshness_policies(self):
        return FreshnessPolicyRepository(self.store).list_all()

    def set_freshness_policy(
        self, *, scope_type: str, scope_key: str, max_age_days: int, warning_days: int
    ):
        policies = FreshnessPolicyRepository(self.store)
        existing = policies.get(scope_type, scope_key)
        policy = FreshnessPolicy(
            scope_type=scope_type,
            scope_key=scope_key,
            max_age_days=max_age_days,
            warning_days=warning_days,
            version=(existing.version + 1) if existing else 1,
            updated_at=utc_now(),
        )
        return FreshnessManager(
            EvaluationReportRepository(self.store),
            FunctionReportHeadRepository(self.store),
            policies,
        ).set_policy(policy)

    def export_site(self):
        from .site_export import export_automated_site

        return export_automated_site(
            self.settings, self.store, observed_revision=self.default_source_revision()
        )

    def list_jobs(self, status: str | None = None) -> list[Job]:
        return self.jobs.list_jobs(status=status)

    def get_job(self, job_id: str) -> Job:
        return self.jobs.get_job(job_id)

    def job_statistics(self, job_id: str):
        return JobStatisticsRepository(self.store).get(job_id)

    def list_events(self, job_id: str, since_seq: int = 0):
        self.jobs.get_job(job_id)  # raises JobNotFoundError if absent
        return EventRepository(self.store).list_for_job(job_id, since_seq=since_seq)

    def cancel(self, job_id: str) -> bool:
        return self.dispatcher.cancel(job_id)

    def retry(self, job_id: str) -> str:
        return self.dispatcher.retry(job_id)

    def artifact(self, job_id: str, kind: str):
        return ArtifactRepository(self.store).get(job_id, kind)

    def metrics(self) -> dict:
        from .metrics import collect_metrics

        return collect_metrics(self.store, archives_root=self.settings.archives_root)

    # --- lifecycle --------------------------------------------------------
    def start(self) -> None:
        self.dispatcher.start()

    def stop(self) -> None:
        self.dispatcher.shutdown()
        self.store.close()


def _git_sha(path: Path) -> str | None:
    try:
        cp = subprocess.run(  # noqa: S603,S607
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if cp.returncode != 0:
        return None
    return cp.stdout.strip() or None
