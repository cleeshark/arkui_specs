"""Operational metrics for the semantic service (TASK-011-09).

Aggregates job/event/artifact/archive state into a JSON-serializable report and
a flat CSV. Everything is derived from the DB and the automated-history log;
only non-sensitive token counts are included, never credentials or prompts.
Designed to be cheap enough to expose at ``GET /api/metrics`` and to export on
a schedule.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .domain import states as S
from .store.repositories import (
    ArtifactRepository,
    EventRepository,
    JobRepository,
    JobStatisticsRepository,
)
from .store.sqlite_store import SqliteStore

TERMINAL_STATES = S.TERMINAL_STATES
_ERROR_EVENT_TYPES = {
    "semantic_failed", "aggregation_failed", "report_failed", "worker_crashed",
    "executor_error",
}


def collect_metrics(store: SqliteStore, *, archives_root: Path) -> dict[str, Any]:
    """Build the full metrics report from the store + automated archives."""
    jobs_repo = JobRepository(store)
    events_repo = EventRepository(store)
    artifacts_repo = ArtifactRepository(store)
    jobs = jobs_repo.list_jobs(limit=100_000)
    statistics = {item.job_id: item for item in JobStatisticsRepository(store).list_all()}

    status_counts: Counter[str] = Counter(j.status for j in jobs)
    durations: list[dict[str, Any]] = []
    executor_errors = 0
    cancelled = status_counts.get(S.CANCELLED, 0)

    for job in jobs:
        events = events_repo.list_for_job(job.job_id, limit=10_000)
        executor_errors += sum(1 for e in events if e.event_type in _ERROR_EVENT_TYPES)
        stat = statistics.get(job.job_id)
        if stat and stat.started_at:
            queue_ms = _ms_between(job.created_at, stat.started_at)
            run_ms = _ms_between(stat.started_at, stat.finished_at or _now())
            if queue_ms is not None and run_ms is not None:
                durations.append({
                    "job_id": job.job_id,
                    "func_id": job.func_id,
                    "status": job.status,
                    "queue_ms": queue_ms,
                    "run_ms": run_ms,
                    "executor_ms": stat.executor_elapsed_ms,
                    "total_tokens": stat.total_tokens,
                })

    artifact_bytes = 0
    for job in jobs:
        for art in artifacts_repo.list_for_job(job.job_id):
            artifact_bytes += art.size

    archive_bytes, archive_job_count = _archive_bytes(archives_root)
    finding_deltas = _finding_deltas(archives_root)
    token_usage = _token_usage_summary(statistics.values())
    executor_invocations = sum(item.executor_invocations for item in statistics.values())

    return {
        "job_total": len(jobs),
        "status_counts": dict(status_counts),
        "cancelled_total": cancelled,
        "executor_errors": executor_errors,
        "failed_total": status_counts.get(S.FAILED, 0),
        "artifact_bytes": artifact_bytes,
        "archive_bytes": archive_bytes,
        "archive_job_count": archive_job_count,
        "durations": durations,
        "duration_summary": _summarize([d["run_ms"] for d in durations]),
        "queue_summary": _summarize([d["queue_ms"] for d in durations]),
        "executor_duration_summary": _summarize(
            [item.executor_elapsed_ms for item in statistics.values() if item.executor_invocations]
        ),
        "executor_invocations": executor_invocations,
        "token_usage": token_usage,
        "finding_deltas": finding_deltas,
    }


def write_metrics_json(metrics: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_metrics_csv(metrics: dict[str, Any], path: Path) -> Path:
    """Write a flat key,value CSV (lists/dicts are serialized as JSON)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["metric", "value"])
    for key, value in _flatten(metrics).items():
        writer.writerow([key, value])
    path.write_text(buf.getvalue(), encoding="utf-8")
    return path


# --- helpers ----------------------------------------------------------------

def _flatten(obj: Any, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        out[prefix] = json.dumps(obj, ensure_ascii=False, sort_keys=True)
    else:
        out[prefix] = "" if obj is None else str(obj)
    return out


def _summarize(values: Iterable[float]) -> dict[str, float]:
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {"count": 0, "min_ms": 0, "avg_ms": 0, "max_ms": 0, "p90_ms": 0}
    avg = sum(vals) / len(vals)
    p90 = vals[min(len(vals) - 1, int(0.9 * len(vals)))]
    return {"count": len(vals), "min_ms": vals[0], "avg_ms": avg, "max_ms": vals[-1], "p90_ms": p90}


def _ms_between(start_ts: str, end_ts: str) -> float | None:
    start = _parse(start_ts)
    end = _parse(end_ts)
    if start is None or end is None:
        return None
    return (end - start).total_seconds() * 1000.0


def _parse(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _token_usage_summary(statistics: Iterable[Any]) -> dict[str, Any]:
    items = list(statistics)
    with_executor = [item for item in items if item.executor_invocations > 0]
    reported = [item for item in with_executor if item.usage_reported_invocations > 0]
    complete = [
        item for item in with_executor
        if item.usage_reported_invocations == item.executor_invocations
    ]
    executor_invocations = sum(item.executor_invocations for item in items)
    reported_invocations = sum(item.usage_reported_invocations for item in items)
    fields = (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    )
    summary = {name: sum(getattr(item, name) for item in items) for name in fields}
    summary.update({
        "reported_jobs": len(reported),
        "complete_jobs": len(complete),
        "unreported_jobs_with_executor": len(with_executor) - len(reported),
        "reported_invocations": reported_invocations,
        "unreported_invocations": executor_invocations - reported_invocations,
        "reporting_coverage": (
            reported_invocations / executor_invocations if executor_invocations else 0.0
        ),
    })
    return summary


def _archive_bytes(archives_root: Path) -> tuple[int, int]:
    total = 0
    count = 0
    if not archives_root.is_dir():
        return 0, 0
    for manifest_path in archives_root.rglob("archive-manifest.json"):
        count += 1
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in manifest.get("files", []):
                total += int(entry.get("size", 0))
        except (OSError, json.JSONDecodeError):
            continue
    return total, count


def _finding_deltas(archives_root: Path) -> dict[str, Any]:
    """Approximate added/resolved/reclassified from the automated history log.

    Compares consecutive snapshots per func_id using severity buckets: a total
    increase counts as added, a decrease as resolved, and an unchanged total
    with shifted buckets counts as reclassified.
    """
    log = archives_root / "site-history-automated.jsonl"
    if not log.is_file():
        return {"added": 0, "resolved": 0, "reclassified": 0}
    by_func: dict[str, list[dict]] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        by_func.setdefault(rec.get("func_id", "?"), []).append(rec)

    added = resolved = reclassified = 0
    for records in by_func.values():
        for prev, cur in zip(records, records[1:]):
            delta = _delta(prev.get("finding_summary", {}), cur.get("finding_summary", {}))
            added += delta["added"]
            resolved += delta["resolved"]
            reclassified += delta["reclassified"]
    return {"added": added, "resolved": resolved, "reclassified": reclassified}


def _delta(prev: dict, cur: dict) -> dict[str, int]:
    prev_total = int(prev.get("total", 0))
    cur_total = int(cur.get("total", 0))
    prev_sev = prev.get("by_severity", {}) or {}
    cur_sev = cur.get("by_severity", {}) or {}
    if cur_total > prev_total:
        return {"added": cur_total - prev_total, "resolved": 0, "reclassified": 0}
    if cur_total < prev_total:
        return {"added": 0, "resolved": prev_total - cur_total, "reclassified": 0}
    # total unchanged: count findings that moved out of their severity bucket
    moved = sum(max(0, prev_sev.get(sev, 0) - cur_sev.get(sev, 0)) for sev in set(prev_sev) | set(cur_sev))
    return {"added": 0, "resolved": 0, "reclassified": moved}
