"""Aggregation-specific context for the single bounded Correction turn.

The normal Aggregation input is intentionally comprehensive because the model
must review every Criterion.  A Correction turn is different: typed errors
already identify the affected semantic objects, so loading the complete
``aggregation-context.json`` repeats hundreds of kilobytes of unrelated
Observation tables.  This module projects the frozen context to the affected
Criteria and their referenced rows while preserving the same authoritative
IDs and allowlists.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Iterable


_CRITERION_SELECTOR = re.compile(r"criterion_results\[([^\]]+)\]")
_EVIDENCE_ONLY_ERROR_CODES = frozenset({
    "CRITERION_EVIDENCE_UNKNOWN",
    "FINDING_EVIDENCE_UNKNOWN",
    "EVIDENCE_TYPE_MISSING",
    "EVIDENCE_REQUIRED_MISSING",
})
_EVIDENCE_CRITERION_FIELDS = (
    "criterion_id", "evidence_ids", "evidence_ids_by_type",
    "required_evidence_types",
)


def _rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _criterion_ids_from_finding(
    candidate: dict[str, Any], identity: str,
) -> list[str]:
    result: list[str] = []
    for criterion in _rows(candidate.get("criterion_results")):
        criterion_id = criterion.get("criterion_id")
        if not isinstance(criterion_id, str):
            continue
        for finding in _rows(criterion.get("findings")):
            if identity in {finding.get("finding_id"), finding.get("key")}:
                result.append(criterion_id)
                break
    return result


def target_criterion_ids(
    candidate: dict[str, Any], typed_errors: Iterable[dict[str, Any]],
) -> list[str]:
    """Return stable Criterion IDs implicated by Aggregation typed errors."""
    criteria = _rows(candidate.get("criterion_results"))
    valid_ids = [
        row.get("criterion_id") for row in criteria
        if isinstance(row.get("criterion_id"), str)
    ]
    valid_set = set(valid_ids)
    result: list[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value in valid_set and value not in result:
            result.append(value)

    for error in typed_errors:
        entity_type = str(error.get("entity_type", ""))
        entity_id = str(error.get("entity_id", ""))
        if entity_type in {"criterion", "policy_basis"}:
            add(entity_id)
        if entity_type == "finding" and entity_id:
            for criterion_id in _criterion_ids_from_finding(candidate, entity_id):
                add(criterion_id)

        path = str(error.get("path", ""))
        for selector in _CRITERION_SELECTOR.findall(path):
            if selector.isdigit():
                index = int(selector)
                if 0 <= index < len(criteria):
                    add(criteria[index].get("criterion_id"))
            else:
                add(selector)

        if entity_type == "defect" and entity_id:
            for owner in _rows(candidate.get("defect_ownership")):
                if owner.get("defect_key") == entity_id:
                    add(owner.get("primary_criterion_id"))
                    finding_identities = set(
                        _strings(owner.get("finding_ids"))
                        + _strings(owner.get("finding_keys"))
                    )
                    for finding_identity in finding_identities:
                        for criterion_id in _criterion_ids_from_finding(
                            candidate, finding_identity,
                        ):
                            add(criterion_id)
    return result


def build_aggregation_correction_context(
    aggregation_context: dict[str, Any],
    candidate: dict[str, Any],
    typed_errors: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Project Aggregation context to the Criteria named by typed errors."""
    errors = [dict(error) for error in typed_errors]
    error_codes = {
        str(error.get("code", "")) for error in errors if error.get("code")
    }
    target_ids = target_criterion_ids(candidate, errors)
    criteria = [
        copy.deepcopy(row)
        for row in _rows(aggregation_context.get("criteria"))
        if row.get("criterion_id") in target_ids
    ]

    evidence_only = bool(error_codes) and error_codes.issubset(
        _EVIDENCE_ONLY_ERROR_CODES
    )
    if evidence_only:
        criteria = [{
            field: copy.deepcopy(row.get(field))
            for field in _EVIDENCE_CRITERION_FIELDS if field in row
        } for row in criteria]

    refs_by_table = {
        "observations": {
            ref for row in criteria for ref in _strings(row.get("observation_refs"))
        },
        "claims": {
            ref for row in criteria for ref in _strings(row.get("claim_refs"))
        },
        "units": {
            ref for row in criteria for ref in _strings(row.get("unit_refs"))
        },
    }
    projected_tables: dict[str, dict[str, Any]] = {}
    for table_name, selected_refs in refs_by_table.items():
        source = aggregation_context.get(table_name, {})
        if not isinstance(source, dict):
            source = {}
        projected_tables[table_name] = {
            ref: copy.deepcopy(source[ref])
            for ref in selected_refs if ref in source
        }

    evidence_ids = {
        evidence_id
        for row in criteria for evidence_id in _strings(row.get("evidence_ids"))
    }
    for table_rows in projected_tables.values():
        for row in table_rows.values():
            evidence_ids.update(_strings(row.get("evidence_ids")))
    evidence_catalog = aggregation_context.get("evidence_catalog", {})
    if not isinstance(evidence_catalog, dict):
        evidence_catalog = {}

    metadata_fields = (
        "schema_version", "staged_schema_version", "evaluator_version",
        "func_id", "source_revision", "run_id",
    )
    return {
        **{
            field: copy.deepcopy(aggregation_context.get(field))
            for field in metadata_fields if field in aggregation_context
        },
        "correction_scope": "aggregation",
        "target_criterion_ids": target_ids,
        "typed_error_codes": list(dict.fromkeys(
            str(error.get("code", "")) for error in errors
            if error.get("code")
        )),
        "projection_profile": (
            "criterion_evidence" if evidence_only else "criterion_semantic"
        ),
        "criteria": criteria,
        **projected_tables,
        "evidence_catalog": {
            evidence_id: copy.deepcopy(evidence_catalog[evidence_id])
            for evidence_id in evidence_ids if evidence_id in evidence_catalog
        },
        # The whitelist is compact and may be required by ownership errors
        # even when no single Criterion can be inferred from the error path.
        "valid_defect_keys": copy.deepcopy(
            aggregation_context.get("valid_defect_keys", [])
        ),
    }


def correction_evidence_catalog(
    correction_context: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return the projected canonical Evidence rows for prompt embedding."""
    catalog = correction_context.get("evidence_catalog", {})
    if not isinstance(catalog, dict):
        return []
    return [copy.deepcopy(row) for row in catalog.values() if isinstance(row, dict)]
