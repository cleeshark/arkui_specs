"""JSON serializers for the HTTP API (TASK-011-06).

DTOs -> plain JSON-compatible dicts. Kept separate from routing so the shape is
easy to audit and adjust.
"""

from __future__ import annotations

from typing import Any

from ..domain.models import Artifact, Attempt, DependencySnapshot, Event, FreshnessPolicy, Job


def job_to_dict(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "func_id": job.func_id,
        "source_revision": job.source_revision,
        "run_count": job.run_count,
        "selected_run_ids": list(job.selected_run_ids),
        "status": job.status,
        "progress": job.progress,
        "executor_config": job.executor_config,
        "protocol_version": job.protocol_version,
        "evaluator_version": job.evaluator_version,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


def event_to_dict(event: Event) -> dict[str, Any]:
    return {
        "job_id": event.job_id,
        "seq": event.seq,
        "event_type": event.event_type,
        "payload": event.payload,
        "created_at": event.created_at,
    }


def artifact_to_dict(artifact: Artifact) -> dict[str, Any]:
    return {
        "artifact_id": artifact.artifact_id,
        "job_id": artifact.job_id,
        "kind": artifact.kind,
        "path": artifact.path,
        "sha256": artifact.sha256,
        "size": artifact.size,
        "created_at": artifact.created_at,
    }


def attempt_to_dict(attempt: Attempt) -> dict[str, Any]:
    return {
        "attempt_id": attempt.attempt_id,
        "job_id": attempt.job_id,
        "run_id": attempt.run_id,
        "feat_id": attempt.feat_id,
        "stage": attempt.stage,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "exit_code": attempt.exit_code,
        "artifact_dir": attempt.artifact_dir,
    }


def snapshot_to_dict(snap: DependencySnapshot) -> dict[str, Any]:
    return {
        "job_id": snap.job_id,
        "repo_name": snap.repo_name,
        "branch": snap.branch,
        "sha": snap.sha,
        "status": snap.status,
        "created_at": snap.created_at,
    }


def freshness_policy_to_dict(policy: FreshnessPolicy) -> dict[str, Any]:
    return {
        "scope_type": policy.scope_type,
        "scope_key": policy.scope_key,
        "max_age_days": policy.max_age_days,
        "warning_days": policy.warning_days,
        "version": policy.version,
        "updated_at": policy.updated_at,
    }
