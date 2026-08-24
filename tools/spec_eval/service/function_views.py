"""Read models for Function rolling-report APIs and the live Site."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yaml

from .freshness import FreshnessManager
from .settings import ServiceSettings
from .store.repositories import (
    EvaluationReportRepository,
    FreshnessPolicyRepository,
    FunctionReportHeadRepository,
    ReportDeltaRepository,
)


class FunctionViewService:
    def __init__(self, settings: ServiceSettings, store) -> None:
        self.settings = settings
        self.reports = EvaluationReportRepository(store)
        self.heads = FunctionReportHeadRepository(store)
        self.policies = FreshnessPolicyRepository(store)
        self.deltas = ReportDeltaRepository(store)
        self.freshness = FreshnessManager(self.reports, self.heads, self.policies)

    def list_functions(self, *, observed_revision: str) -> list[dict[str, Any]]:
        return [
            self.get_function(item["func_id"], observed_revision=observed_revision, catalog=item)
            for item in self._catalog()
        ]

    def get_function(
        self,
        func_id: str,
        *,
        observed_revision: str,
        catalog: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        catalog = catalog or next(
            (item for item in self._catalog() if item["func_id"] == func_id),
            {"func_id": func_id, "title": func_id, "l1": None, "path": None},
        )
        head = self.freshness.refresh(func_id)
        report = self.reports.get(head.current_report_id) if head.current_report_id else None
        return {
            **catalog,
            "observed_revision": observed_revision,
            "current_report": _report_summary(report),
            "freshness": head.freshness,
            "stale_reasons": list(head.stale_reasons),
            "warn_at": head.warn_at,
            "expires_at": head.expires_at,
            "remaining_days": _remaining_days(head.expires_at),
            "refresh_status": head.refresh_status,
            "active_job_id": head.active_job_id,
            "last_refresh_error": head.last_refresh_error,
            "desired_generation": head.desired_generation,
            "desired_revision": head.desired_revision,
            "history_count": len(self.reports.list_for_func(func_id, limit=10_000)),
        }

    def history(self, func_id: str) -> list[dict[str, Any]]:
        result = []
        for report in self.reports.list_for_func(func_id):
            item = _report_summary(report)
            delta = self.deltas.get(report.report_id)
            if item is not None:
                item["delta"] = (
                    {
                        "previous_report_id": delta.previous_report_id,
                        "summary": delta.summary,
                        "details_path": delta.details_path,
                    }
                    if delta else None
                )
                result.append(item)
        return result

    def _catalog(self) -> list[dict[str, Any]]:
        document = yaml.safe_load(
            (self.settings.specs_root / "registry" / "functions.yaml").read_text(encoding="utf-8")
        )
        result = []
        for entry in document.get("functions", []):
            if not isinstance(entry, dict) or not entry.get("id"):
                continue
            path = entry.get("path")
            if isinstance(path, str) and path:
                feat_dir = self.settings.specs_root / path
                # A Function is reportable only when its registered directory
                # exists and contains at least one Feat spec.  Missing paths
                # must be filtered too; otherwise stale registry entries leak
                # back into the UI catalog.
                if not feat_dir.is_dir() or not any(feat_dir.glob("Feat-*")):
                    continue
            l1 = entry.get("l1") if isinstance(entry.get("l1"), dict) else {}
            l3 = entry.get("l3") if isinstance(entry.get("l3"), dict) else {}
            result.append(
                {
                    "func_id": str(entry["id"]),
                    "title": str(l3.get("title") or entry["id"]),
                    "l1": {"id": l1.get("id"), "title": l1.get("title")},
                    "path": entry.get("path"),
                    "status": entry.get("status"),
                }
            )
        return result


def _report_summary(report) -> dict[str, Any] | None:
    if report is None:
        return None
    return {
        "report_id": report.report_id,
        "job_id": report.job_id,
        "source_revision": report.source_revision,
        "revision_set": report.revision_set,
        "input_fingerprint": report.input_fingerprint,
        "evidence_fingerprint": report.evidence_fingerprint,
        "evaluator_version": report.evaluator_version,
        "protocol_version": report.protocol_version,
        "rubric_version": report.rubric_version,
        "selected_run_id": report.selected_run_id,
        "run_count": report.run_count,
        "completed_at": report.completed_at,
        "archive_path": report.archive_path,
        "manifest_sha256": report.manifest_sha256,
        "summary": report.summary,
    }


def _remaining_days(expires_at: str | None) -> int | None:
    if not expires_at:
        return None
    expires = datetime.fromisoformat(expires_at)
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return (expires.date() - datetime.now(timezone.utc).date()).days
