"""JSON serializers for the HTTP API (TASK-011-06).

DTOs -> plain JSON-compatible dicts. Kept separate from routing so the shape is
easy to audit and adjust.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..domain.models import (
    Artifact,
    Attempt,
    DependencySnapshot,
    Event,
    FreshnessPolicy,
    Job,
    JobStatistics,
)


def job_to_dict(job: Job, statistics: JobStatistics | None = None) -> dict[str, Any]:
    document = {
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
    if statistics is not None:
        document["timing"] = _timing_to_dict(job, statistics)
        document["usage"] = _usage_to_dict(statistics)
        document["executor_telemetry"] = _telemetry_to_dict(statistics)
    return document


def _timing_to_dict(job: Job, statistics: JobStatistics) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    created = _parse(job.created_at)
    started = _parse(statistics.started_at)
    finished = _parse(statistics.finished_at)
    queue_end = started or finished or now
    duration_end = finished or now
    queue_ms = max(0, int((queue_end - created).total_seconds() * 1000)) if created else 0
    duration_ms = (
        max(0, int((duration_end - started).total_seconds() * 1000)) if started else 0
    )
    return {
        "started_at": statistics.started_at,
        "finished_at": statistics.finished_at,
        "queue_duration_ms": queue_ms,
        "duration_ms": duration_ms,
        "executor_duration_ms": statistics.executor_elapsed_ms,
    }


def _usage_to_dict(statistics: JobStatistics) -> dict[str, Any]:
    return {
        "reported": statistics.usage_reported_invocations > 0,
        "complete": (
            statistics.executor_invocations > 0
            and statistics.usage_reported_invocations == statistics.executor_invocations
        ),
        "executor_invocations": statistics.executor_invocations,
        "reported_invocations": statistics.usage_reported_invocations,
        "input_tokens": statistics.input_tokens,
        "cached_input_tokens": statistics.cached_input_tokens,
        "cache_write_input_tokens": statistics.cache_write_input_tokens,
        "output_tokens": statistics.output_tokens,
        "reasoning_output_tokens": statistics.reasoning_output_tokens,
        "total_tokens": statistics.total_tokens,
    }


def _telemetry_to_dict(statistics: JobStatistics) -> dict[str, Any]:
    return {
        "reported": statistics.telemetry_reported_invocations > 0,
        "complete": (
            statistics.executor_invocations > 0
            and statistics.telemetry_reported_invocations == statistics.executor_invocations
        ),
        "reported_invocations": statistics.telemetry_reported_invocations,
        "tool_calls": statistics.executor_tool_calls,
        "command_calls": statistics.executor_command_calls,
        "input_paths_accessed": statistics.input_paths_accessed,
        "evidence_paths_accessed": statistics.evidence_paths_accessed,
    }


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


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
