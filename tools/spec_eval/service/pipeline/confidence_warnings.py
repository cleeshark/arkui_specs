"""Persist run-local post-Correction warnings for report-first publication."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from spec_eval.kernel.errors import TypedError, is_post_correction_warning


WARNING_FILE_NAME = "post-correction-warnings.json"
WARNING_SCHEMA_VERSION = 1


def record_post_correction_warnings(
    run_dir: Path,
    work_item_id: str,
    errors: list[TypedError],
) -> None:
    """Idempotently retain eligible residuals from one published work item."""
    eligible = [error for error in errors if is_post_correction_warning(error)]
    if not eligible:
        return
    path = run_dir / WARNING_FILE_NAME
    records = _load_records(path)
    identities = {_record_identity(record) for record in records}
    for error in eligible:
        record = {
            "work_item_id": work_item_id,
            "error": error.to_dict(),
        }
        identity = _record_identity(record)
        if identity in identities:
            continue
        identities.add(identity)
        records.append(record)
    document = {
        "schema_version": WARNING_SCHEMA_VERSION,
        "warnings": records,
    }
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError:
        # Confidence warnings are advisory.  A persistence failure must not
        # undo an otherwise usable report-first publication.
        return


def load_post_correction_warning_records(run_dir: Path) -> list[dict[str, Any]]:
    """Load valid warning records, ignoring a missing or damaged sidecar."""
    return _load_records(run_dir / WARNING_FILE_NAME)


def load_post_correction_warnings(run_dir: Path) -> list[TypedError]:
    """Return typed residuals recorded by observation-stage degradation."""
    return [
        TypedError.from_dict(record["error"])
        for record in load_post_correction_warning_records(run_dir)
    ]


def _load_records(path: Path) -> list[dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(document, dict):
        return []
    warnings = document.get("warnings")
    if not isinstance(warnings, list):
        return []
    records: list[dict[str, Any]] = []
    for record in warnings:
        if not isinstance(record, dict):
            continue
        work_item_id = record.get("work_item_id")
        error = record.get("error")
        if not isinstance(work_item_id, str) or not work_item_id:
            continue
        if not isinstance(error, dict):
            continue
        typed = TypedError.from_dict(error)
        if not is_post_correction_warning(typed):
            continue
        records.append({
            "work_item_id": work_item_id,
            "error": typed.to_dict(),
        })
    return records


def _record_identity(record: dict[str, Any]) -> tuple[str, str, str, str, str]:
    error = record.get("error", {})
    return (
        str(record.get("work_item_id", "")),
        str(error.get("code", "")),
        str(error.get("path", "")),
        str(error.get("entity_type", "")),
        str(error.get("entity_id", "")),
    )
