"""Deterministic static export for automated rolling reports."""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

from .function_views import FunctionViewService
from .settings import ServiceSettings
from .store.sqlite_store import utc_now


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
    return outputs


def _write_atomic(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)
