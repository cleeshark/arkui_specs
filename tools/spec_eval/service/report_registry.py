"""Immutable report registration and Function current-pointer promotion."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .domain.errors import ReportConflictError, ReportPromotionError
from .domain.models import EvaluationReportRecord
from .freshness import calculate_freshness
from .settings import ServiceSettings
from .store.repositories import (
    EvaluationReportRepository,
    FreshnessPolicyRepository,
    FunctionReportHeadRepository,
)


@dataclass(frozen=True)
class ReportRegistrationResult:
    report: EvaluationReportRecord
    promotion_status: str  # PROMOTED | ALREADY_CURRENT | SUPERSEDED_ON_ARRIVAL
    previous_report_id: str | None


class ReportRegistry:
    """Register verified archives and atomically advance Function heads."""

    def __init__(
        self,
        settings: ServiceSettings,
        reports: EvaluationReportRepository,
        heads: FunctionReportHeadRepository,
        policies: FreshnessPolicyRepository,
    ) -> None:
        self.settings = settings
        self.reports = reports
        self.heads = heads
        self.policies = policies

    def register_and_promote(self, report: EvaluationReportRecord) -> ReportRegistrationResult:
        self._verify_archive(report)
        frozen = self.reports.insert(report)
        head = self.heads.ensure(report.func_id)
        previous_report_id = head.current_report_id
        if head.current_report_id == frozen.report_id:
            return ReportRegistrationResult(frozen, "ALREADY_CURRENT", None)
        policy = self.policies.effective_for(report.func_id) or self.policies.ensure_default()
        projection = calculate_freshness(head, frozen, policy)
        try:
            self.heads.promote(
                frozen,
                freshness=projection.status,
                warn_at=projection.warn_at or "",
                expires_at=projection.expires_at or "",
            )
        except ReportPromotionError as exc:
            if "SUPERSEDED_ON_ARRIVAL" not in str(exc):
                raise
            return ReportRegistrationResult(frozen, "SUPERSEDED_ON_ARRIVAL", previous_report_id)
        return ReportRegistrationResult(frozen, "PROMOTED", previous_report_id)

    def _verify_archive(self, report: EvaluationReportRecord) -> None:
        archive = Path(report.archive_path).resolve()
        root = self.settings.archives_root.resolve()
        if archive != root and root not in archive.parents:
            raise ReportConflictError(f"archive is outside automated root: {archive}")
        manifest_path = archive / "archive-manifest.json"
        if not manifest_path.is_file():
            raise ReportConflictError(f"archive manifest missing: {manifest_path}")
        data = manifest_path.read_bytes()
        actual = "sha256:" + hashlib.sha256(data).hexdigest()
        if actual != report.manifest_sha256:
            raise ReportConflictError(
                f"archive manifest hash mismatch: expected {report.manifest_sha256}, got {actual}"
            )
        try:
            manifest = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ReportConflictError(f"archive manifest is invalid JSON: {exc}") from exc
        expected = {
            "job_id": report.job_id,
            "func_id": report.func_id,
            "source_revision": report.source_revision,
        }
        actual_identity = {key: manifest.get(key) for key in expected}
        if actual_identity != expected:
            raise ReportConflictError(
                f"archive manifest identity mismatch: expected {expected}, got {actual_identity}"
            )
        files = manifest.get("files")
        if not isinstance(files, list):
            raise ReportConflictError("archive manifest files must be a list")
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise ReportConflictError("archive manifest contains an invalid file entry")
            path = archive / item["path"]
            if not path.is_file():
                raise ReportConflictError(f"archived file missing: {path}")
            file_data = path.read_bytes()
            digest = "sha256:" + hashlib.sha256(file_data).hexdigest()
            if digest != item.get("sha256") or len(file_data) != item.get("size"):
                raise ReportConflictError(f"archived file integrity mismatch: {path}")


def fingerprint_documents(paths: list[Path]) -> str:
    """Hash named file content into one stable sha256 fingerprint."""
    payload = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        data = path.read_bytes()
        payload.append(
            {
                "path": path.as_posix(),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        )
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def fingerprint_named_documents(
    documents: list[tuple[str, Path]], *, normalize_revision_fields: bool = False
) -> str:
    """Hash stable logical names and file bytes, excluding job-local absolute paths."""
    payload = []
    for name, path in sorted(documents, key=lambda item: item[0]):
        data = path.read_bytes()
        if normalize_revision_fields and path.suffix == ".json":
            try:
                document = json.loads(data)
                data = json.dumps(
                    _without_revision_identity(document),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            except json.JSONDecodeError:
                pass
        payload.append(
            {"name": name, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        )
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def _without_revision_identity(value):
    if isinstance(value, dict):
        return {
            key: _without_revision_identity(child)
            for key, child in value.items()
            if key not in {"source_revision", "observed_revision"}
        }
    if isinstance(value, list):
        return [_without_revision_identity(child) for child in value]
    return value
