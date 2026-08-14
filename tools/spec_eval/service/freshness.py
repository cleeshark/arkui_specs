"""Deterministic Function report freshness calculation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .domain.models import EvaluationReportRecord, FreshnessPolicy, FunctionReportHead
from .store.repositories import (
    EvaluationReportRepository,
    FreshnessPolicyRepository,
    FunctionReportHeadRepository,
)

FRESH = "FRESH"
EXPIRING = "EXPIRING"
EXPIRED_TIME = "EXPIRED_TIME"
STALE_INPUT = "STALE_INPUT"
MISSING = "MISSING"

SPEC_CHANGED = "SPEC_CHANGED"
SOURCE_EVIDENCE_CHANGED = "SOURCE_EVIDENCE_CHANGED"
SDK_CHANGED = "SDK_CHANGED"
PROTOCOL_CHANGED = "PROTOCOL_CHANGED"
DEPENDENCY_SNAPSHOT_CHANGED = "DEPENDENCY_SNAPSHOT_CHANGED"


@dataclass(frozen=True)
class FreshnessProjection:
    status: str
    stale_reasons: tuple[str, ...]
    warn_at: str | None
    expires_at: str | None


class FreshnessManager:
    """Persist policies and refresh FunctionHead projections."""

    def __init__(
        self,
        reports: EvaluationReportRepository,
        heads: FunctionReportHeadRepository,
        policies: FreshnessPolicyRepository,
    ) -> None:
        self.reports = reports
        self.heads = heads
        self.policies = policies

    def set_policy(self, policy: FreshnessPolicy, *, now: datetime | None = None) -> FreshnessPolicy:
        stored = self.policies.set(policy)
        for head in self.heads.list_all():
            if policy.scope_type == "func" and head.func_id != policy.scope_key:
                continue
            self.refresh(head.func_id, now=now)
        return stored

    def refresh(self, func_id: str, *, now: datetime | None = None) -> FunctionReportHead:
        head = self.heads.ensure(func_id)
        report = self.reports.get(head.current_report_id) if head.current_report_id else None
        policy = self.policies.effective_for(func_id) or self.policies.ensure_default()
        projection = calculate_freshness(head, report, policy, now=now)
        return self.heads.update_freshness(
            func_id,
            freshness=projection.status,
            stale_reasons=projection.stale_reasons,
            warn_at=projection.warn_at,
            expires_at=projection.expires_at,
        )

    def refresh_all(self, *, now: datetime | None = None) -> list[FunctionReportHead]:
        return [self.refresh(head.func_id, now=now) for head in self.heads.list_all()]


def calculate_freshness(
    head: FunctionReportHead,
    current_report: EvaluationReportRecord | None,
    policy: FreshnessPolicy,
    *,
    now: datetime | None = None,
) -> FreshnessProjection:
    """Calculate freshness using input drift before time-based expiry."""
    if current_report is None:
        return FreshnessProjection(MISSING, (), None, None)

    completed_at = _parse_time(current_report.completed_at)
    expires = completed_at + timedelta(days=policy.max_age_days)
    warns = expires - timedelta(days=policy.warning_days)
    warn_at = _format_time(warns)
    expires_at = _format_time(expires)

    desired = head.desired_input_fingerprint
    if desired and desired != current_report.input_fingerprint:
        reasons = head.stale_reasons or (DEPENDENCY_SNAPSHOT_CHANGED,)
        return FreshnessProjection(STALE_INPUT, reasons, warn_at, expires_at)

    instant = now or datetime.now(timezone.utc)
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=timezone.utc)
    if instant >= expires:
        return FreshnessProjection(EXPIRED_TIME, (), warn_at, expires_at)
    if instant >= warns:
        return FreshnessProjection(EXPIRING, (), warn_at, expires_at)
    return FreshnessProjection(FRESH, (), warn_at, expires_at)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")
