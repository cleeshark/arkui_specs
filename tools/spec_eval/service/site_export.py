"""Deterministic static export for automated rolling reports."""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .function_views import FunctionViewService
from .settings import ServiceSettings
from .store.sqlite_store import utc_now

from spec_eval.report.site_evaluation_reporter import (
    SITE_EVALUATION_SCHEMA_VERSION,
    SEVERITY_RANK,
    compact_finding,
    recommendations,
    semantic_data,
    static_data,
)

AUTOMATED_REPORT_VERSION = "spec-eval-site-evaluation-automated@0.1.0"


def export_automated_site(settings: ServiceSettings, store, *, observed_revision: str) -> dict[str, Path]:
    views = FunctionViewService(settings, store)
    functions = views.list_functions(observed_revision=observed_revision)
    generated_at = utc_now()
    index = {
        "schema_version": 1,
        "mode": "archive",
        "generated_at": generated_at,
        "semantic_revision": None,
        "functions": functions,
    }
    freshness = Counter(item["freshness"] for item in functions)
    report_revisions = sorted({
        item["current_report"]["source_revision"]
        for item in functions if item["current_report"] is not None
    })
    summary = {
        "schema_version": 1,
        "mode": "archive",
        "generated_at": generated_at,
        "function_count": len(functions),
        "evaluated_count": sum(1 for item in functions if item["current_report"] is not None),
        "freshness": dict(sorted(freshness.items())),
        "mixed_revisions": len(report_revisions) > 1,
        "report_revisions": report_revisions,
    }
    outputs = {
        "index": settings.exports_root / "automated-function-index.json",
        "summary": settings.exports_root / "automated-site-summary.json",
    }
    _write_atomic(outputs["index"], index)
    _write_atomic(outputs["summary"], summary)
    history_root = settings.exports_root / "automated-function-history"
    for item in functions:
        path = history_root / f"{item['func_id']}.json"
        _write_atomic(
            path,
            {
                "schema_version": 1,
                "mode": "archive",
                "generated_at": generated_at,
                "func_id": item["func_id"],
                "reports": views.history(item["func_id"]),
            },
        )
    # Generate site-evaluation-report-compatible document (#55)
    site_eval_path = settings.exports_root / "automated-site-evaluation-report.json"
    site_eval = _build_automated_site_evaluation(
        functions, settings=settings, observed_revision=observed_revision,
    )
    _write_atomic(site_eval_path, site_eval)
    outputs["site_evaluation"] = site_eval_path
    return outputs


def _build_automated_site_evaluation(
    functions: list[dict[str, Any]],
    *,
    settings: ServiceSettings,
    observed_revision: str,
) -> dict[str, Any]:
    """Build a site-evaluation-report-compatible document from automated reports."""
    entries: list[dict[str, Any]] = []
    for item in functions:
        report_meta = item.get("current_report")
        if report_meta is None:
            continue
        archive_path = report_meta.get("archive_path")
        if not archive_path:
            continue
        eval_report_path = Path(archive_path) / "aggregate-report_json-evaluation-report.json"
        if not eval_report_path.is_file():
            continue
        try:
            eval_report = json.loads(eval_report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        created_at = report_meta.get("completed_at") or _archive_created_at(Path(archive_path))
        entry = _convert_function_entry(
            eval_report, catalog=item,
            observed_revision=observed_revision,
            created_at=created_at,
        )
        if entry is not None:
            entries.append(entry)

    confirmed = [e for e in entries if e["status"] == "CONFIRMED"]
    expired = [e for e in entries if e["status"] == "EXPIRED"]
    return {
        "schemaVersion": SITE_EVALUATION_SCHEMA_VERSION,
        "reportVersion": AUTOMATED_REPORT_VERSION,
        "available": bool(entries),
        "sourceRevision": observed_revision,
        "staticReport": {
            "path": "automated-site-summary.json",
            "sourceRevision": observed_revision,
        },
        "summary": {
            "confirmedFunctionCount": len(confirmed),
            "expiredFunctionCount": len(expired),
            "functionCount": len(entries),
            "findingCount": sum(len(e["findings"]) for e in confirmed),
            "expiredFindingCount": sum(len(e["findings"]) for e in expired),
        },
        "functions": entries,
    }


def _convert_function_entry(
    eval_report: dict[str, Any],
    *,
    catalog: dict[str, Any],
    observed_revision: str,
    created_at: str | None = None,
) -> dict[str, Any] | None:
    """Convert one evaluation-report.json to a site-evaluation-report function entry."""
    func_id = str(eval_report.get("func_id", ""))
    source_revision = str(eval_report.get("source_revision", ""))
    if not func_id or not source_revision:
        return None

    # semantic data → criterion_summaries + findings
    semantic = eval_report.get("semantic", {})
    semantic_as_review = {"semantic_result": semantic}
    criteria, semantic_findings, semantic_paths = semantic_data(semantic_as_review)

    # static data → findings
    static = eval_report.get("static", {})
    static_findings, static_paths = static_data(static, func_id=func_id)

    all_findings = static_findings + semantic_findings

    # scores: convert from score-result format to site format
    score = eval_report.get("score", {})
    scores = _convert_scores(score)

    # Freshness is time-based (report age), NOT revision equality. Under rolling
    # per-Function evaluation each Function legitimately sits at its own revision,
    # so a byte-equal "source == observed" check would flip most reports to
    # EXPIRED whenever the observed-revision majority shifts (issue: #73 unfroze
    # ace_engine, exposing this). We keep the report CONFIRMED and publishable at
    # its own revision, expose a time-based freshness signal, and surface any
    # revision drift as informational metadata for a display-layer badge.
    freshness, expires_at = _report_freshness(created_at)
    revision_current = source_revision == observed_revision
    status = "EXPIRED" if freshness == "EXPIRED" else "CONFIRMED"
    entry: dict[str, Any] = {
        "func_id": func_id,
        "title": str(catalog.get("title", func_id)),
        "source_revision": source_revision,
        "observed_revision": observed_revision,
        "revision_current": revision_current,
        "status": status,
        "freshness": freshness,
        "evaluated_at": created_at or "",
        "expires_at": expires_at or "",
        "scores": scores,
        "criterion_summaries": sorted(criteria, key=lambda c: str(c.get("criterion_id", ""))),
        "findings": all_findings,
        "recommendations": recommendations(all_findings),
        "evidence_paths": sorted(set(semantic_paths + static_paths)),
        "confirmation": {
            "confirmed_by": "automated-evaluator",
            "confirmed_at": created_at or "",
            "conclusion": "",
            "notes": [],
        },
        "static_report_reference": {
            "path": "automated-site-summary.json",
            "func_id": func_id,
            "source_revision": observed_revision,
            "available": bool(static.get("findings")),
            "gate": static.get("gate", "error"),
            "finding_count": len(static_findings),
        },
    }
    if freshness == "EXPIRED":
        entry["staleness"] = {
            "reason": "report_age_exceeded",
            "evaluated_at": created_at or "",
            "expires_at": expires_at or "",
        }
    return entry


# Mirror the service default freshness policy (repositories.ensure_default):
# reports expire 30 days after evaluation, warning 7 days before that.
FRESHNESS_MAX_AGE_DAYS = 30
FRESHNESS_WARNING_DAYS = 7


def _archive_created_at(archive_path: Path) -> str | None:
    """Read ``created_at`` from an archive manifest, or None if unavailable."""
    manifest_path = archive_path / "archive-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = manifest.get("created_at")
    return value if isinstance(value, str) and value else None


def _report_freshness(
    created_at: str | None, *, now: datetime | None = None
) -> tuple[str, str | None]:
    """Classify a report by age → (FRESH | EXPIRING | EXPIRED, expires_at).

    Mirrors the time-based half of ``service.freshness.calculate_freshness``
    without the DB dependency, so the static export and the live service agree
    on what "stale" means. Returns FRESH with no expiry when the timestamp is
    absent or unparseable, so a missing time never hides a report.
    """
    if not created_at:
        return "FRESH", None
    try:
        completed = datetime.fromisoformat(created_at)
    except ValueError:
        return "FRESH", None
    if completed.tzinfo is None:
        completed = completed.replace(tzinfo=timezone.utc)
    expires = completed + timedelta(days=FRESHNESS_MAX_AGE_DAYS)
    warns = expires - timedelta(days=FRESHNESS_WARNING_DAYS)
    expires_at = expires.astimezone(timezone.utc).isoformat(timespec="seconds")
    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    if instant >= expires:
        return "EXPIRED", expires_at
    if instant >= warns:
        return "EXPIRING", expires_at
    return "FRESH", expires_at


def _convert_scores(score: dict[str, Any]) -> dict[str, Any]:
    """Convert score-result.json format to site scores format."""
    dimensions = {}
    for dim in score.get("dimensions", []):
        # The evaluation report and score-result.json key dimensions by
        # ``dimension_id``; tolerate a legacy ``id`` as a fallback.
        dim_id = dim.get("dimension_id") or dim.get("id")
        if isinstance(dim_id, str):
            dimensions[dim_id] = dim.get("score", 0)
    confidence = score.get("confidence", {})
    admission = score.get("admission", {})
    return {
        "dimensions": dimensions,
        "raw_score": score.get("raw_score", 0),
        "published_score": score.get("published_score", 0),
        "confidence": confidence.get("score", 0) if isinstance(confidence, dict) else 0,
        "admission": admission.get("status", "") if isinstance(admission, dict) else "",
    }


def _write_atomic(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
