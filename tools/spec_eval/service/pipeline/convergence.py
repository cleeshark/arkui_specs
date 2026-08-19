"""Convergence metrics for evaluator protocol 0.2.1 (S5).

Computes convergence indicators from the Finding Ledger and writes
``convergence-result.json`` as a companion to the evaluation report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..store.repositories import FindingLedgerRepository
from ..store.sqlite_store import SqliteStore


def compute_convergence(
    store: SqliteStore,
    *,
    func_id: str,
    run_id: str,
    evaluator_version: str,
    rubric_version: str,
    source_revision: str,
) -> dict[str, Any]:
    """Compute convergence metrics from the Ledger for one FuncID."""
    ledger = FindingLedgerRepository(store)
    all_findings = ledger.get_all(func_id)
    active = [f for f in all_findings if f["status"] == "active"]
    resolved = [f for f in all_findings if f["status"] == "resolved"]
    refuted = [f for f in all_findings if f["status"] == "refuted"]
    superseded = [f for f in all_findings if f["status"] == "superseded"]

    total = len(all_findings) or 1  # avoid division by zero
    new_this_run = sum(1 for f in active if f["first_seen_run_id"] == run_id)
    resolved_this_run = sum(
        1 for f in resolved
        if _last_disposition_run(f) == run_id
    )
    change_count = new_this_run + resolved_this_run
    change_rate = round(change_count / total, 4) if len(all_findings) > 0 else 1.0

    max_confirmations = max(
        (f["confirmation_count"] for f in active), default=0,
    )

    if max_confirmations >= 3 and change_rate < 0.05:
        level = "stable"
    elif max_confirmations >= 2 or change_rate < 0.2:
        level = "converging"
    else:
        level = "volatile"

    epoch = f"{source_revision}:rubric-{rubric_version}:evaluator-{evaluator_version}"

    return {
        "epoch": epoch,
        "func_id": func_id,
        "run_id": run_id,
        "run_count": max_confirmations,
        "change_rate": change_rate,
        "convergence_level": level,
        "finding_summary": {
            "active": len(active),
            "resolved": len(resolved),
            "refuted": len(refuted),
            "superseded": len(superseded),
            "new_this_run": new_this_run,
            "resolved_this_run": resolved_this_run,
        },
    }


def write_convergence_result(
    store: SqliteStore,
    *,
    func_id: str,
    run_id: str,
    evaluator_version: str,
    rubric_version: str,
    source_revision: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Compute and write ``convergence-result.json``."""
    result = compute_convergence(
        store,
        func_id=func_id,
        run_id=run_id,
        evaluator_version=evaluator_version,
        rubric_version=rubric_version,
        source_revision=source_revision,
    )
    output_path = output_dir / "convergence-result.json"
    try:
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    return result


def _last_disposition_run(finding: dict[str, Any]) -> str | None:
    history = json.loads(finding.get("disposition_history") or "[]")
    if history and isinstance(history, list):
        last = history[-1]
        if isinstance(last, dict):
            return last.get("run_id")
    return None
