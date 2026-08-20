"""Asynchronous projection (protocol 0.2.0 S3, design v3 R6/D2).

The synchronous critical path ends at the archive: once the immutable archive
is sealed the job is ``completed``. Everything that merely *publishes* the
completed evaluation — the automated site-history log append, rolling-report
registration/promotion, freshness updates and report deltas — runs through
this projector.

Guarantees:

- **Outbox**: one ``projection_requests`` row per completed job, enqueued
  right after completion; restarts sweep pending rows and retry them.
- **Idempotency**: ``report_id`` keys both the outbox and the site-history
  append guard, so a projection never executes twice for one report.
- **Isolation**: a projection failure is recorded on the request (status
  ``failed``) and emitted as a ``projection_failed`` event; the completed job
  is never regressed to ``failed``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..domain.models import Job
from ..settings import ServiceSettings
from ..store.repositories import (
    EventRepository,
    FindingLedgerRepository,
    ProjectionRepository,
    RefreshTargetRepository,
)
from ..store.sqlite_store import SqliteStore


def enqueue_projection(
    settings: ServiceSettings,
    *,
    job: Job,
    report_id: str,
    archive_dir: Path,
    aggregate_dir: Path,
    selected_run_id: str,
    pending_delta: Any = None,
    events: EventRepository | None = None,
) -> None:
    """Record one projection request (idempotent per job/report)."""
    del pending_delta  # the projector recomputes deltas from the store
    with SqliteStore(settings, run_recovery=False) as store:
        ProjectionRepository(store).enqueue(
            job_id=job.job_id,
            report_id=report_id,
            archive_dir=str(archive_dir),
            aggregate_dir=str(aggregate_dir),
            selected_run_id=selected_run_id,
        )
    if events is not None:
        events.append(job.job_id, "projection_enqueued", {"report_id": report_id})


def run_projection(
    settings: ServiceSettings,
    *,
    job: Job,
    events: EventRepository,
    runner: Any = None,
) -> bool:
    """Execute one job's projection; returns True on success.

    Failures are captured on the request and never propagate to the caller's
    job lifecycle.
    """
    del runner
    with SqliteStore(settings, run_recovery=False) as store:
        repository = ProjectionRepository(store)
        request = repository.get(job.job_id)
        if request is None or request.get("status") == "completed":
            return request is not None
        repository.mark_running(job.job_id)
        try:
            _project(settings, store, job=job, request=request, events=events)
        except Exception as exc:  # noqa: BLE001 - projection isolation boundary
            repository.mark_failed(job.job_id, str(exc))
            events.append(job.job_id, "projection_failed", {"error": str(exc)})
            return False
        repository.mark_completed(job.job_id)
        events.append(job.job_id, "projection_completed", {
            "report_id": request.get("report_id"),
        })
        return True


def run_pending_projections(settings: ServiceSettings) -> int:
    """Sweep and retry pending/failed projections (startup / dispatcher tick)."""
    from ..domain.models import Job as JobModel

    processed = 0
    with SqliteStore(settings, run_recovery=False) as store:
        repository = ProjectionRepository(store)
        pending_ids = [
            row["job_id"]
            for row in repository.list_by_status("pending")
        ] + [row["job_id"] for row in repository.list_by_status("failed")]
    for job_id in pending_ids:
        with SqliteStore(settings, run_recovery=False) as store:
            jobs = store  # JobRepository import below
            from ..store.repositories import JobRepository

            job = JobRepository(jobs).get_job(job_id)
            events = EventRepository(jobs)
            if job is None or job.status != "completed":
                continue
            if run_projection(settings, job=job, events=events):
                processed += 1
    del JobModel
    return processed


def _project(
    settings: ServiceSettings,
    store: SqliteStore,
    *,
    job: Job,
    request: dict[str, Any],
    events: EventRepository,
) -> None:
    from . import semantic_stage, site_history_stage

    aggregate_dir = Path(str(request.get("aggregate_dir", "")))
    # 1. automated site-history log append (report_id idempotent)
    snapshot_path = aggregate_dir / "site-history-snapshot.json"
    if snapshot_path.is_file():
        site_history_stage.append_automated_history(settings, snapshot_path)

    # 2. rolling report registration / promotion / freshness / delta
    refresh_targets = RefreshTargetRepository(store)
    target = refresh_targets.get(job.job_id)
    if target is not None:
        from ..store.repositories import EvaluationReportRepository

        pending_delta = None
        existing_report = EvaluationReportRepository(store).get_for_job(job.job_id)
        if existing_report is None:
            pending_delta = semantic_stage._prepare_report_delta(
                store,
                job.func_id,
                aggregate_dir / "evaluation-report.json",
                aggregate_dir,
            )
        else:
            pending_delta = semantic_stage._load_archived_delta(
                existing_report.archive_path
            )
        semantic_stage._register_rolling_report(
            settings=settings,
            job=job,
            target=target,
            archive_dir=Path(str(request.get("archive_dir", ""))),
            aggregate_dir=aggregate_dir,
            selected_run_id=str(request.get("selected_run_id", "")),
            refresh_targets=refresh_targets,
            events=events,
            pending_delta=pending_delta,
        )

    # 3. Finding Ledger update (0.2.1 S3)
    _update_finding_ledger(
        store, job=job, aggregate_dir=aggregate_dir,
        request=request, events=events,
    )

    # 4. Convergence metrics (0.2.1 S5)
    from .convergence import write_convergence_result

    write_convergence_result(
        store,
        func_id=job.func_id,
        run_id=str(request.get("selected_run_id", job.job_id)),
        evaluator_version=job.evaluator_version or "",
        rubric_version="0.3.0",
        source_revision=job.source_revision or "",
        output_dir=aggregate_dir,
    )


def _update_finding_ledger(
    store: SqliteStore,
    *,
    job: Job,
    aggregate_dir: Path,
    request: dict[str, Any],
    events: EventRepository,
) -> None:
    """Upsert findings from the completed run into the Ledger."""
    import json as _json

    semantic_path = aggregate_dir / "semantic-result.json"
    if not semantic_path.is_file():
        return
    try:
        semantic = _json.loads(semantic_path.read_text(encoding="utf-8"))
    except (OSError, _json.JSONDecodeError):
        return

    run_id = str(request.get("selected_run_id", job.job_id))
    executor = str(job.executor_config.get("type", "unknown")) if job.executor_config else "unknown"
    ledger = FindingLedgerRepository(store)

    current_finding_ids: set[str] = set()
    for criterion in semantic.get("criterion_results", []):
        criterion_id = criterion.get("criterion_id", "")
        for finding in criterion.get("findings", []):
            finding_id = finding.get("finding_id")
            if not isinstance(finding_id, str) or not finding_id:
                continue
            current_finding_ids.add(finding_id)
            ledger.upsert_finding(
                finding_id=finding_id,
                func_id=job.func_id,
                criterion_id=criterion_id,
                severity=finding.get("severity", "Major"),
                message=finding.get("message", ""),
                run_id=run_id,
                executor=executor,
            )

    resolved = ledger.mark_resolved(job.func_id, current_finding_ids, run_id)
    events.append(job.job_id, "finding_ledger_updated", {
        "func_id": job.func_id,
        "upserted": len(current_finding_ids),
        "resolved": resolved,
    })

    # Generate history-context.json for future aggregation runs (S4)
    _write_history_context(ledger, job.func_id, aggregate_dir)


def _write_history_context(
    ledger: FindingLedgerRepository,
    func_id: str,
    aggregate_dir: Path,
) -> None:
    """Write history-context.json from active Ledger entries (S4)."""
    import json as _json

    active = ledger.get_active(func_id)
    context = {
        "active_findings": [
            {
                "finding_id": row["finding_id"],
                "criterion_id": row["criterion_id"],
                "severity": row["severity"],
                "message": row["message"],
                "confirmation_count": row["confirmation_count"],
                "executor_set": _json.loads(row.get("executor_set") or "[]"),
                "first_seen_run_id": row["first_seen_run_id"],
                "last_confirmed_run_id": row.get("last_confirmed_run_id"),
            }
            for row in active
        ],
        "pending_questions": [],
    }
    context_path = aggregate_dir / "history-context.json"
    try:
        context_path.write_text(
            _json.dumps(context, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass
