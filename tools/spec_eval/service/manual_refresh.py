"""Manual Function refresh submission built on the existing Dispatcher."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass

from .domain.models import CreateJobCommand, Job, RefreshTarget, make_job_id
from .freshness import DEPENDENCY_SNAPSHOT_CHANGED
from .pipeline.context import DEFAULT_SKILL_EVALUATOR_VERSION
from .settings import ServiceSettings
from .store.repositories import JobRepository, RefreshTargetRepository
from .workspace.manager import RevisionWorkspaceManager


@dataclass(frozen=True)
class ManualRefreshResult:
    job: Job
    target: RefreshTarget
    deduplicated: bool


class ManualRefreshService:
    """Resolve, deduplicate, reserve, and enqueue one explicit refresh."""

    def __init__(self, app) -> None:
        self.app = app
        self.settings: ServiceSettings = app.settings
        self._lock = threading.Lock()
        self._workspace_manager = RevisionWorkspaceManager(self.settings)

    def request(
        self,
        *,
        func_id: str,
        source_revision: str,
        run_count: int,
        agent_id: str | None = None,
        agent_params: dict | None = None,
    ) -> ManualRefreshResult:
        executor_config = self.app.resolve_executor_config(agent_id, agent_params)
        revisions = self._workspace_manager.resolve_revisions(source_revision)
        resolved_revision = revisions["ace_engine"]
        provisional = _fingerprint(
            {
                "func_id": func_id,
                "revision_set": revisions,
                "evaluator_version": DEFAULT_SKILL_EVALUATOR_VERSION,
                "protocol_version": self.settings.protocol_version,
                "executor_config": executor_config,
            }
        )
        dedupe_key = _fingerprint(
            {
                "func_id": func_id,
                "revision_set": revisions,
                "evaluator_version": DEFAULT_SKILL_EVALUATOR_VERSION,
                "protocol_version": self.settings.protocol_version,
                "run_count": run_count,
                "executor_config": executor_config,
            }
        )

        with self._lock:
            targets = RefreshTargetRepository(self.app.store)
            existing = targets.get_active_by_dedupe(dedupe_key)
            if existing is not None:
                return ManualRefreshResult(
                    JobRepository(self.app.store).get_job(existing.job_id), existing, True
                )

            job_id = make_job_id()
            jobs = JobRepository(self.app.store)
            job = jobs.create_job(
                CreateJobCommand(
                    func_id=func_id,
                    source_revision=resolved_revision,
                    run_count=run_count,
                    job_id=job_id,
                    executor_config=executor_config,
                ),
                evaluator_version=DEFAULT_SKILL_EVALUATOR_VERSION,
                executor_config=executor_config,
            )
            target, created = targets.create_active(
                job_id=job.job_id,
                func_id=func_id,
                desired_revision=resolved_revision,
                revision_set=revisions,
                provisional_fingerprint=provisional,
                dedupe_key=dedupe_key,
                stale_reasons=(DEPENDENCY_SNAPSHOT_CHANGED,),
            )
            if not created:  # guarded above; retained as a DB-level race backstop
                return ManualRefreshResult(jobs.get_job(target.job_id), target, True)
            try:
                self._workspace_manager.prepare(job, reserved_revisions=revisions)
            except Exception as exc:
                targets.finish(job.job_id, status="FAILED")
                from .domain import states as S
                from .store.repositories import FunctionReportHeadRepository

                jobs.transition_status(
                    job.job_id, S.FAILED, event_type="workspace_prepare_failed",
                    payload={"error": str(exc)[:500]},
                )
                FunctionReportHeadRepository(self.app.store).mark_refresh_failed(
                    func_id, job.job_id, str(exc)
                )
                raise
            self.app.dispatcher.submit(job.job_id, job.func_id)
            return ManualRefreshResult(job, target, False)


def _fingerprint(value: dict) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(data).hexdigest()
