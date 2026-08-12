"""Automated site-history snapshot (TASK-011-08): isolated from confirmed reviews.

Writes a self-contained snapshot of one automated run (score + evaluation
report + finding summary) into the ``automated`` namespace and appends a
compact record to an append-only automated history log under ``data_root``.

It never writes to ``specs/evaluation/reviews/**`` or to the confirmed site
archive (``specs/.evaluator/site-evaluation-history.json``). The confirmed
namespace stays byte-for-byte unchanged; automated results are queryable
separately for status / score / stability / finding diffs.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from ..domain.models import Job
from ..settings import ServiceSettings
from ..store.sqlite_store import utc_now

SNAPSHOT_SCHEMA_VERSION = 1
_AUTOMATED_HISTORY_REL = Path("archives") / "automated" / "site-history-automated.jsonl"


def automated_history_path(settings: ServiceSettings) -> Path:
    return settings.data_root / _AUTOMATED_HISTORY_REL


def write_site_history_snapshot(
    settings: ServiceSettings,
    job: Job,
    aggregate_dir: Path,
    *,
    selected_run_id: str,
    run_ids: list[str],
) -> Path:
    """Write the snapshot into ``aggregate_dir`` and append to the automated log.

    Returns the snapshot path (consumed by the archive stage).
    """
    score = _load_json(aggregate_dir / "score-result.json")
    report = _load_json(aggregate_dir / "evaluation-report.json")

    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "namespace": "automated",
        "job_id": job.job_id,
        "func_id": job.func_id,
        "source_revision": job.source_revision,
        "evaluator_version": job.evaluator_version,
        "protocol_version": job.protocol_version,
        "run_count": job.run_count,
        "run_ids": run_ids,
        "selected_run_id": selected_run_id,
        "status": "completed",
        "created_at": utc_now(),
        "score": score,
        "evaluation_report": report,
        "finding_summary": _finding_summary(report),
    }

    snapshot_path = aggregate_dir / "site-history-snapshot.json"
    _write_atomic(snapshot_path, snapshot)

    _append_automated_history(settings, snapshot)
    return snapshot_path


def _append_automated_history(settings: ServiceSettings, snapshot: dict) -> None:
    """Append one compact record to the automated history log (never the confirmed one)."""
    record = {
        "namespace": "automated",
        "job_id": snapshot["job_id"],
        "func_id": snapshot["func_id"],
        "source_revision": snapshot["source_revision"],
        "selected_run_id": snapshot["selected_run_id"],
        "created_at": snapshot["created_at"],
        "finding_summary": snapshot["finding_summary"],
    }
    history_path = automated_history_path(settings)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with open(history_path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def _finding_summary(report: dict) -> dict:
    """Defensively count findings by severity from an evaluation report."""
    counts: dict[str, int] = {}
    total = 0

    def walk(obj) -> None:
        nonlocal total
        if isinstance(obj, dict):
            if "finding_id" in obj and "severity" in obj:
                total += 1
                sev = str(obj.get("severity"))
                counts[sev] = counts.get(sev, 0) + 1
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(report)
    return {"total": total, "by_severity": counts}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_atomic(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
