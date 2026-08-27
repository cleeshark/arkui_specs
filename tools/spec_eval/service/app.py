"""Service assembly (TASK-011-06): wires Store + Executor + Dispatcher.

``SemanticServiceApp`` is the single object the HTTP layer and CLI talk to. It
exposes the operations the routes need (create/list/get/cancel/retry/events/
artifact) and owns the dispatcher lifecycle. Mutations only go through the
repositories and dispatcher; the HTTP layer never touches SQLite or subprocesses.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from .domain import states as S
from .domain.errors import IllegalTransitionError
from .domain.models import CreateJobCommand, DependencySnapshot, FreshnessPolicy, Job
from .freshness import FreshnessManager
from .function_views import FunctionViewService
from .executors.base import SemanticExecutor
from .executors.registry import create, create_default as _create_default_executor
from .pipeline.context import DEFAULT_SKILL_EVALUATOR_VERSION
from .manual_refresh import ManualRefreshService
from .report_registry import OrphanReconcileResult, ReportRegistry
from .scheduler.dispatcher import CancelResult, Dispatcher
from .scheduler.job_worker import build_runner
from .settings import ServiceSettings, executor_config_for, executor_profiles
from .store.repositories import (
    ArtifactRepository,
    EventRepository,
    FreshnessPolicyRepository,
    EvaluationReportRepository,
    FunctionReportHeadRepository,
    JobStatisticsRepository,
    JobRepository,
    DependencySnapshotRepository,
    RefreshTargetRepository,
)
from .workspace.manager import RevisionWorkspaceManager, WorkspaceError
from .store.sqlite_store import SqliteStore, utc_now

LOGGER = logging.getLogger(__name__)


class SemanticServiceApp:
    def __init__(
        self,
        settings: ServiceSettings,
        *,
        executor: SemanticExecutor | None = None,
        executor_config: dict | None = None,
        job_runner=None,
        max_workers: int = 2,
        token: str | None = None,
        default_agent: str | None = None,
    ) -> None:
        self.settings = settings
        self.token = token
        supplied_config = executor_config or settings.default_executor_config
        self._default_agent = default_agent or supplied_config.get("agent_id", "codex")
        self._executor_config = supplied_config
        if "agent_id" not in self._executor_config:
            self._executor_config = executor_config_for(self._default_agent)
        self._injected_executor = executor
        self.store = SqliteStore(settings)
        policies = FreshnessPolicyRepository(self.store)
        policies.ensure_default()
        try:
            self.startup_reconcile_result = ReportRegistry(
                settings,
                EvaluationReportRepository(self.store),
                FunctionReportHeadRepository(self.store),
                policies,
                JobRepository(self.store),
            ).reconcile_orphan_reports()
            if self.startup_reconcile_result.repaired:
                LOGGER.info(
                    "startup orphan report reconciliation repaired %d report(s)",
                    self.startup_reconcile_result.repaired,
                )
        except Exception:  # noqa: BLE001 - reconciliation must not block service startup
            LOGGER.exception("startup orphan report reconciliation failed")
            self.startup_reconcile_result = OrphanReconcileResult()
        self.ui_dir = Path(__file__).resolve().parent / "ui"
        self._executor = executor or _create_default_executor(
            self._executor_config, schemas_root=settings.schemas_root
        )
        runner = job_runner or build_runner(
            settings,
            self.store,
            self._executor,
            executor_resolver=self.executor_for_job,
        )
        self.dispatcher = Dispatcher(self.store, job_runner=runner, max_workers=max_workers)
        self.manual_refresh = ManualRefreshService(self)

    @property
    def executor_config(self) -> dict:
        return self._executor_config

    @property
    def default_agent(self) -> str:
        return self._default_agent

    def list_agents(self) -> list[dict]:
        profiles = executor_profiles()
        for profile in profiles:
            profile["default"] = profile["id"] == self._default_agent
        return profiles

    def resolve_executor_config(
        self, agent_id: str | None = None, agent_params: dict | None = None
    ) -> dict:
        name = agent_id or self._default_agent
        return executor_config_for(name, agent_params or {})

    def executor_for_job(self, config: dict) -> SemanticExecutor:
        """Create the executor selected by an immutable job config."""
        legacy_type = {"codex-cli": "codex", "claude-cli": "claude"}.get(
            str(config.get("type", ""))
        )
        name = str(config.get("agent_id") or legacy_type or self._default_agent)
        if (
            name == self._default_agent
            and self._injected_executor is not None
            and config == self._executor_config
        ):
            return self._injected_executor
        return create(name, config, schemas_root=self.settings.schemas_root)

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
        config = self._executor_config
        cmd = CreateJobCommand(
            func_id=func_id,
            source_revision=source_revision,
            run_count=run_count,
            job_id=job_id,
            executor_config=config,
        )
        job = self.jobs.create_job(
            cmd,
            evaluator_version=DEFAULT_SKILL_EVALUATOR_VERSION,
            executor_config=config,
        )
        EventRepository(self.store).append(job.job_id, "job_submitted", {})
        self.dispatcher.submit(job.job_id, job.func_id)
        return job

    def refresh_function(
        self,
        *,
        func_id: str,
        source_revision: str | None = None,
        run_count: int = 1,
        agent_id: str | None = None,
        agent_params: dict | None = None,
    ):
        return self.manual_refresh.request(
            func_id=func_id,
            source_revision=source_revision or self.default_source_revision(),
            run_count=run_count,
            agent_id=agent_id,
            agent_params=agent_params,
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

    def list_events(
        self,
        job_id: str,
        since_seq: int = 0,
        limit: int | None = None,
        *,
        tail: bool = False,
    ):
        self.jobs.get_job(job_id)  # raises JobNotFoundError if absent
        return EventRepository(self.store).list_for_job(
            job_id, since_seq=since_seq, limit=limit, tail=tail
        )

    def cancel(self, job_id: str) -> CancelResult:
        return self.dispatcher.cancel(job_id)

    def retry(self, job_id: str) -> str:
        return self.dispatcher.retry(job_id)

    def retry_latest_specs(self, job_id: str) -> tuple[str, str]:
        """Retry using the current specs revision while reusing checkpoints.

        Only aggregation failures are eligible: refreshing specs
        before observations would make the existing observation evidence stale.
        """
        job = self.jobs.get_job(job_id)
        if job.status not in {S.FAILED, S.CANCELLED}:
            raise IllegalTransitionError(job.status, S.QUEUED)
        if job.stage != S.STAGE_AGGREGATION:
            raise WorkspaceError(
                "latest specs retry is only available for aggregation failures"
            )
        workspace = RevisionWorkspaceManager(self.settings).refresh_specs_revision(job)
        # Keep the persisted execution envelope and eventual report metadata
        # aligned with the refreshed workspace before the worker is queued.
        snapshots = DependencySnapshotRepository(self.store)
        previous_snapshot = snapshots.get(job_id, "specs")
        snapshots.refresh(
            DependencySnapshot(
                job_id=job_id,
                repo_name="specs",
                branch="detached",
                sha=workspace.revisions["specs"],
                status="frozen",
                created_at=utc_now(),
            )
        )
        targets = RefreshTargetRepository(self.store)
        target = targets.get(job_id)
        if target is not None:
            targets.update_revision_set(job_id, workspace.revisions)
        # Clear any stale CORRECTION_PENDING states that would block retry
        # when the specs revision refresh causes a fingerprint mismatch.
        run_state_path = (
            self.settings.jobs_root / job_id / "runs" / "run-1" / "staged" / "run-state.json"
        )
        if run_state_path.is_file():
            import json
            run_state = json.loads(run_state_path.read_text(encoding="utf-8"))
            pseudo = run_state.get("pseudo_work_item_states", {})
            if isinstance(pseudo, dict):
                cleared = {k: v for k, v in pseudo.items() if v != "CORRECTION_PENDING"}
                if cleared != pseudo:
                    run_state["pseudo_work_item_states"] = cleared
                    run_state_path.write_text(
                        json.dumps(run_state, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
        EventRepository(self.store).append(
            job_id,
            "workspace_revision_refreshed",
            {
                "repository": "specs",
                "previous_specs_revision": (
                    previous_snapshot.sha if previous_snapshot is not None else None
                ),
                "specs_revision": workspace.revisions["specs"],
            },
        )
        status = self.dispatcher.retry(
            job_id, reason="retry with latest specs revision"
        )
        return status, workspace.revisions["specs"]

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
