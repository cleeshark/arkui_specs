"""Strict structured-output schemas for evaluator protocol 0.2.0.

Schemas are generated at runtime from :mod:`.contracts` (never committed as
hand-maintained artifacts) and passed to the executor's ``--output-schema``.
They follow the strict subset proven by the S0 spike:

- every object node declares ``additionalProperties: false`` and requires
  every declared property (optionality is expressed as a nullable type union,
  never by omitting a property);
- cross-field couplings (verification gap required iff NOT_VERIFIABLE,
  applicability_reason required iff NOT_APPLICABLE) are intentionally NOT
  encoded as anyOf branches — they would conflict with closed objects — and
  are enforced by the typed validator instead.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import contracts as K
from .errors import SERVICE_NORMALIZATION  # noqa: F401  (re-export convenience)
from .contracts import ENVELOPE_SCHEMA_VERSION


def _enum(*values: str) -> dict:
    return {"enum": list(values)}


def _non_empty_string() -> dict:
    return {"type": "string", "minLength": 1}


def _verification_gap_def() -> dict:
    return {
        "type": ["object", "null"],
        "properties": {
            "checked_scope": {
                "type": "array", "items": {"type": "string"}, "minItems": 1,
            },
            "missing_evidence": {
                "type": "array", "items": {"type": "string"}, "minItems": 1,
            },
            "consequence": _non_empty_string(),
        },
        "required": list(K.VERIFICATION_GAP_FIELDS),
        "additionalProperties": False,
    }


def _evidence_key_ref() -> dict:
    return {"type": "string", "pattern": "^e[0-9]+$"}


def _evidence_declaration_def() -> dict:
    return {
        "type": "object",
        "properties": {
            "key": _evidence_key_ref(),
            "type": _enum(*K.EVIDENCE_TYPES),
            "path": _non_empty_string(),
            "lines": {"type": ["string", "null"]},
            "description": _non_empty_string(),
        },
        "required": list(K.EVIDENCE_DECLARATION_FIELDS),
        "additionalProperties": False,
    }


def _observation_defs() -> dict:
    outcome = _enum(*K.LOCAL_OUTCOMES)
    unit = {
        "type": "object",
        "properties": {
            "unit_id": _non_empty_string(),
            "facet_type": _enum(*K.UNIT_FACET_TYPES),
            "local_outcome": outcome,
            "evidence_refs": {"type": "array", "items": _evidence_key_ref()},
            "fact": {"type": "string"},
            "verification_gap": {"$ref": "#/$defs/verificationGap"},
        },
        "required": list(K.UNIT_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    claim = {
        "type": "object",
        "properties": {
            "claim_id": _non_empty_string(),
            "local_outcome": outcome,
            "evidence_refs": {"type": "array", "items": _evidence_key_ref()},
            "reason": {"type": "string"},
            "verification_gap": {"$ref": "#/$defs/verificationGap"},
            "defect_keys": {"type": "array", "items": {"type": "string", "pattern": K.DEFECT_KEY_PATTERN}},
            "unit_reviews": {"type": "array", "items": {"$ref": "#/$defs/unitJudgment"}},
        },
        "required": list(K.CLAIM_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    observation = {
        "type": "object",
        "properties": {
            "criterion_ids": {
                "type": "array", "items": _non_empty_string(), "minItems": 1,
            },
            "check_ids": {"type": "array", "items": _non_empty_string()},
            "claim_ids": {"type": "array", "items": _non_empty_string()},
            "local_outcome": outcome,
            "breadth": _enum(*K.BREADTHS),
            "contract_family": _non_empty_string(),
            "fact": _non_empty_string(),
            "defect_key": {"type": ["string", "null"], "pattern": K.DEFECT_KEY_PATTERN},
            "primary_criterion_id": {"type": ["string", "null"]},
            "evidence_refs": {
                "type": "array", "items": _evidence_key_ref(), "minItems": 1,
            },
        },
        "required": list(K.OBSERVATION_JUDGMENT_ENTRY_FIELDS),
        "additionalProperties": False,
    }
    payload = {
        "type": ["object", "null"],
        "properties": {
            "evidence_declarations": {
                "type": "array",
                "items": {"$ref": "#/$defs/evidenceDeclaration"},
            },
            "claim_reviews": {
                "type": "array", "items": {"$ref": "#/$defs/claimJudgment"},
            },
            "observations": {
                "type": "array",
                "items": {"$ref": "#/$defs/observationJudgment"},
            },
            "open_questions": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": list(K.OBSERVATION_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    return {
        "verificationGap": _verification_gap_def(),
        "evidenceDeclaration": _evidence_declaration_def(),
        "unitJudgment": unit,
        "claimJudgment": claim,
        "observationJudgment": observation,
        "observationPayload": payload,
    }


def _aggregation_defs() -> dict:
    finding = {
        "type": "object",
        "properties": {
            "key": _non_empty_string(),
            "criterion_id": _non_empty_string(),
            "claim_id": {"type": ["string", "null"]},
            "severity": _enum(*K.FINDING_SEVERITIES),
            "message": _non_empty_string(),
            "evidence_ids": {"type": "array", "items": _non_empty_string()},
            "recommendation": _non_empty_string(),
        },
        "required": list(K.FINDING_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    criterion = {
        "type": "object",
        "properties": {
            "criterion_id": _non_empty_string(),
            "conclusion": _enum(*K.SEMANTIC_CONCLUSIONS),
            "applicability": _enum(*K.APPLICABILITY_VALUES),
            "reason": _non_empty_string(),
            "applicability_reason": {"type": ["string", "null"]},
            "missing_evidence": {"type": ["string", "null"]},
            "claim_ids": {
                "type": "array", "items": _non_empty_string(),
            },
            "evidence_ids": {
                "type": "array", "items": _non_empty_string(),
            },
            "findings": {"type": "array", "items": {"$ref": "#/$defs/findingJudgment"}},
        },
        "required": list(K.CRITERION_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    ownership = {
        "type": "object",
        "properties": {
            "defect_key": {**_non_empty_string(), "pattern": K.DEFECT_KEY_PATTERN},
            "primary_criterion_id": _non_empty_string(),
            "finding_keys": {
                "type": "array", "items": _non_empty_string(), "minItems": 1,
            },
            "rationale": _non_empty_string(),
        },
        "required": list(K.DEFECT_OWNERSHIP_FIELDS),
        "additionalProperties": False,
    }
    contradiction = {
        "type": "object",
        "properties": {
            "statement": _non_empty_string(),
            "left_assertion": _non_empty_string(),
            "right_assertion": _non_empty_string(),
            "affected_feat_ids": {
                "type": "array", "items": _non_empty_string(), "minItems": 1,
            },
            "correction_scope": _enum("replace_core"),
            "function_shared_assertion": {"type": "boolean"},
            "primary_defect_key": {**_non_empty_string(), "pattern": K.DEFECT_KEY_PATTERN},
        },
        "required": list(K.CONTRADICTION_BASIS_FIELDS),
        "additionalProperties": False,
    }
    policy = {
        "type": "object",
        "properties": {
            "criterion_id": _non_empty_string(),
            "content_status": _enum(*K.POLICY_CONTENT_STATUSES),
            "evidence_status": _enum(*K.POLICY_EVIDENCE_STATUSES),
            "conflict_scope": _enum(*K.POLICY_CONFLICT_SCOPES),
            "reason": _non_empty_string(),
        },
        "required": list(K.POLICY_BASIS_FIELDS),
        "additionalProperties": False,
    }
    payload = {
        "type": ["object", "null"],
        "properties": {
            "cross_feat_contracts_reviewed": {"type": "boolean"},
            "contradiction_bases": {
                "type": "array", "items": {"$ref": "#/$defs/contradictionBasis"},
            },
            "defect_ownership": {
                "type": "array", "items": {"$ref": "#/$defs/defectOwnership"},
            },
            "outcome_policy_bases": {
                "type": "array", "items": {"$ref": "#/$defs/policyBasis"},
            },
            "criterion_results": {
                "type": "array", "items": {"$ref": "#/$defs/criterionJudgment"},
            },
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": list(K.AGGREGATION_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    return {
        "findingJudgment": finding,
        "criterionJudgment": criterion,
        "defectOwnership": ownership,
        "contradictionBasis": contradiction,
        "policyBasis": policy,
        "aggregationPayload": payload,
    }


def _correction_defs() -> dict:
    """Strict envelope payload for a bounded JSON Patch correction."""
    patch = {
        "type": "object",
        "properties": {
            "op": _enum("add", "remove", "replace"),
            "path": _non_empty_string(),
            # The executor's strict JSON-schema subset cannot express an
            # arbitrary JSON value union.  Transport the RFC-6902 value as a
            # JSON-encoded string; the service decodes it before applying the
            # operation (use "null" for remove).
            "value": _non_empty_string(),
        },
        "required": ["op", "path", "value"],
        "additionalProperties": False,
    }
    payload = {
        "type": ["object", "null"],
        "properties": {
            "patches": {"type": "array", "items": {"$ref": "#/$defs/jsonPatch"}},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": list(K.CORRECTION_JUDGMENT_FIELDS),
        "additionalProperties": False,
    }
    return {
        "jsonPatch": patch,
        "correctionPayload": payload,
    }


def build_envelope_schema(payload_kind: str) -> dict:
    """Build the executor envelope v3 schema for one payload kind.

    ``payload_kind`` is ``"observation"`` or ``"aggregation"``; the envelope is
    identical for both, only the nested payload definition differs.
    """
    if payload_kind == "observation":
        defs = _observation_defs()
        payload_ref = {"$ref": "#/$defs/observationPayload"}
    elif payload_kind == "aggregation":
        defs = _aggregation_defs()
        payload_ref = {"$ref": "#/$defs/aggregationPayload"}
    elif payload_kind == "correction":
        defs = _correction_defs()
        payload_ref = {"$ref": "#/$defs/correctionPayload"}
    else:
        raise ValueError(f"unknown payload kind: {payload_kind!r}")
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "schema_version": {"type": "integer", "const": ENVELOPE_SCHEMA_VERSION},
            "work_item_id": _non_empty_string(),
            "status": _enum("completed", "failed"),
            "payload": payload_ref,
            "notes": {"type": "array", "items": {"type": "string"}},
            "error": {"type": ["string", "null"]},
        },
        "required": [
            "schema_version", "work_item_id", "status", "payload", "notes", "error",
        ],
        "additionalProperties": False,
        "$defs": defs,
    }


def write_envelope_schema(payload_kind: str, path: Path) -> Path:
    """Write one generated schema; callers pass it to ``--output-schema``."""
    schema = build_envelope_schema(payload_kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path
