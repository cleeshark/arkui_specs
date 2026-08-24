"""Immutable report registration and Function current-pointer promotion."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .domain import states as S
from .domain.errors import ReportConflictError, ReportPromotionError
from .domain.models import EvaluationReportRecord
from .freshness import calculate_freshness
from .settings import ServiceSettings
from .store.repositories import (
    EventRepository,
    EvaluationReportRepository,
    FreshnessPolicyRepository,
    FunctionReportHeadRepository,
    JobRepository,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReportRegistrationResult:
    report: EvaluationReportRecord
    promotion_status: str  # PROMOTED | ALREADY_CURRENT | SUPERSEDED_ON_ARRIVAL
    previous_report_id: str | None


@dataclass(frozen=True)
class OrphanReconcileResult:
    """Counters from one startup orphan-report reconciliation sweep."""

    scanned: int = 0
    repaired: int = 0
    skipped_stale: int = 0
    skipped_active: int = 0
    skipped_invalid: int = 0


class ReportRegistry:
    """Register verified archives and atomically advance Function heads."""

    def __init__(
        self,
        settings: ServiceSettings,
        reports: EvaluationReportRepository,
        heads: FunctionReportHeadRepository,
        policies: FreshnessPolicyRepository,
        jobs: JobRepository | None = None,
    ) -> None:
        self.settings = settings
        self.reports = reports
        self.heads = heads
        self.policies = policies
        self.jobs = jobs or JobRepository(reports.store)

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

    def reconcile_orphan_reports(self) -> OrphanReconcileResult:
        """Repair only safe, unclaimed Function report pointers.

        A report is considered repairable only when it belongs to the current
        desired generation/fingerprint, its producing Job is completed, and no
        different refresh Job currently owns the head.  The final promotion is
        a conditional compare-and-set in the repository, so a concurrent
        refresh cannot be overwritten by this startup sweep.
        """
        scanned = repaired = skipped_stale = skipped_active = skipped_invalid = 0
        events = EventRepository(self.reports.store)
        for head in self.heads.list_all():
            if head.current_report_id is not None:
                continue
            scanned += 1
            fingerprint = head.desired_input_fingerprint
            if not fingerprint:
                skipped_stale += 1
                continue
            report = self.reports.latest_for_target(
                head.func_id,
                target_generation=head.desired_generation,
                input_fingerprint=fingerprint,
            )
            if report is None:
                continue
            if head.active_job_id not in (None, report.job_id):
                skipped_active += 1
                continue
            try:
                job = self.jobs.get_job(report.job_id)
            except Exception as exc:  # pragma: no cover - FK normally prevents this
                skipped_invalid += 1
                LOGGER.warning(
                    "orphan reconcile skipped report %s: producing job unavailable: %s",
                    report.report_id,
                    exc,
                )
                continue
            if job.status != S.COMPLETED:
                skipped_invalid += 1
                continue
            try:
                self._verify_archive(report)
            except (OSError, ReportConflictError, ValueError) as exc:
                skipped_invalid += 1
                LOGGER.warning(
                    "orphan reconcile skipped invalid report %s: %s",
                    report.report_id,
                    exc,
                )
                continue

            policy = self.policies.effective_for(report.func_id) or self.policies.ensure_default()
            projection = calculate_freshness(head, report, policy)
            promoted = self.heads.promote_orphan(
                report,
                freshness=projection.status,
                warn_at=projection.warn_at or "",
                expires_at=projection.expires_at or "",
            )
            if promoted is None:
                # A concurrent refresh/current-pointer update won the CAS.
                continue
            repaired += 1
            try:
                events.append(
                    report.job_id,
                    "orphan_report_reconciled",
                    {
                        "report_id": report.report_id,
                        "func_id": report.func_id,
                        "target_generation": report.target_generation,
                    },
                )
            except Exception as exc:  # pragma: no cover - audit must not undo repair
                LOGGER.warning(
                    "orphan report %s repaired but audit event failed: %s",
                    report.report_id,
                    exc,
                )
        return OrphanReconcileResult(
            scanned=scanned,
            repaired=repaired,
            skipped_stale=skipped_stale,
            skipped_active=skipped_active,
            skipped_invalid=skipped_invalid,
        )

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
