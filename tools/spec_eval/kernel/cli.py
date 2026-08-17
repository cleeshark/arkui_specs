"""Kernel self-check: schema/contract/registry consistency.

Usage (from the specs root):

    PYTHONPATH=tools python3 -m spec_eval.kernel.cli

Verifies that the generated strict schemas satisfy the local strict-subset
validator, that every contract enum appears in the generated schema, and that
every error code referenced by the validators is registered.
"""

from __future__ import annotations

import sys

from spec_eval.protocol_validator import validate_strict_output_schema

from . import contracts as K
from .errors import ERROR_REGISTRY, repairability_of
from .machine_contract import (
    build_aggregation_machine_contract,
    build_observation_machine_contract,
)
from .schema_gen import build_envelope_schema


def run_self_check() -> list[str]:
    problems: list[str] = []
    for kind in ("observation", "aggregation"):
        schema = build_envelope_schema(kind)
        strict_errors = validate_strict_output_schema(schema)
        problems.extend(f"{kind} schema: {error}" for error in strict_errors)
        defs = schema["$defs"]
        payload = defs.get(f"{kind}Payload", {})
        enum_sources = {
            "claimJudgment": {
                "local_outcome": K.LOCAL_OUTCOMES,
            },
            "unitJudgment": {
                "local_outcome": K.LOCAL_OUTCOMES,
                "facet_type": K.UNIT_FACET_TYPES,
            },
            "observationJudgment": {
                "local_outcome": K.LOCAL_OUTCOMES,
                "breadth": K.BREADTHS,
            },
            "evidenceDeclaration": {"type": K.EVIDENCE_TYPES},
            "criterionJudgment": {
                "conclusion": K.SEMANTIC_CONCLUSIONS,
                "applicability": K.APPLICABILITY_VALUES,
            },
            "findingJudgment": {"severity": K.FINDING_SEVERITIES},
            "policyBasis": {
                "content_status": K.POLICY_CONTENT_STATUSES,
                "evidence_status": K.POLICY_EVIDENCE_STATUSES,
                "conflict_scope": K.POLICY_CONFLICT_SCOPES,
            },
        }
        for def_name, expected_enums in enum_sources.items():
            node = defs.get(def_name)
            if node is None:
                continue  # not part of this payload kind
            properties = node.get("properties", {})
            for field, expected in expected_enums.items():
                actual = properties.get(field, {}).get("enum")
                if actual is not None and tuple(actual) != tuple(expected):
                    problems.append(
                        f"{kind}.{def_name}.{field}: schema enum {actual} != "
                        f"contract {list(expected)}"
                    )

    observation_contract = build_observation_machine_contract(
        expected_claim_ids=("Feat-01/AC-1",),
        required_checks=K.FEATURE_REQUIRED_CHECKS,
        valid_criterion_ids=("CORRECTNESS-SOURCE-SUPPORT",),
    )
    aggregation_contract = build_aggregation_machine_contract(
        valid_criterion_ids=("CORRECTNESS-SOURCE-SUPPORT",),
    )
    for name, contract in (
        ("observation", observation_contract),
        ("aggregation", aggregation_contract),
    ):
        if contract["payload_fields"] != (
            list(K.OBSERVATION_JUDGMENT_FIELDS)
            if name == "observation"
            else list(K.AGGREGATION_JUDGMENT_FIELDS)
        ):
            problems.append(f"{name} machine contract: payload fields drifted")

    for code in ERROR_REGISTRY:
        try:
            repairability_of(code)
        except ValueError as exc:
            problems.append(f"error registry: {exc}")
    return problems


def main() -> int:
    problems = run_self_check()
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    print(
        f"kernel self-check: protocol={K.EVALUATION_PROTOCOL_VERSION} "
        f"codes={len(ERROR_REGISTRY)} OK"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
