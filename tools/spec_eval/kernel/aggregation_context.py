"""Accessors for the normalized Aggregation context.

The context stores each Observation/Claim/Unit/Evidence once in global tables;
Criterion rows contain only references into those tables.
"""

from __future__ import annotations

from typing import Any, Iterable


def criteria(context: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(context, dict):
        return []
    return [row for row in context.get("criteria", []) if isinstance(row, dict)]


def criteria_by_id(context: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("criterion_id")): row
        for row in criteria(context)
        if isinstance(row.get("criterion_id"), str)
    }


def table(context: dict[str, Any] | None, name: str) -> dict[str, dict[str, Any]]:
    if not isinstance(context, dict):
        return {}
    value = context.get(name, {})
    if not isinstance(value, dict):
        return {}
    return {
        str(key): row for key, row in value.items()
        if isinstance(key, str) and isinstance(row, dict)
    }


def refs(row: dict[str, Any], field: str) -> list[str]:
    value = row.get(field, [])
    return [item for item in value if isinstance(item, str) and item]


def mapped_claim_ids(
    context: dict[str, Any] | None, criterion: dict[str, Any]
) -> list[str]:
    claims = table(context, "claims")
    result: list[str] = []
    for ref in refs(criterion, "claim_refs"):
        claim_id = claims.get(ref, {}).get("claim_id")
        if isinstance(claim_id, str) and claim_id not in result:
            result.append(claim_id)
    return result


def criterion_evidence_catalog(
    context: dict[str, Any] | None, criterion: dict[str, Any]
) -> list[dict[str, Any]]:
    catalog = table(context, "evidence_catalog")
    return [catalog[evidence_id] for evidence_id in refs(criterion, "evidence_ids")
            if evidence_id in catalog]


def all_evidence(context: dict[str, Any] | None) -> Iterable[dict[str, Any]]:
    return table(context, "evidence_catalog").values()
