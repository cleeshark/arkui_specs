"""Validate the NEXT-005 rubric, complexity rules, schemas, and result instances.

The repository intentionally does not depend on the third-party ``jsonschema``
package. This module implements the small Draft 2020-12 keyword subset used by
the spec-evaluation schemas and adds cross-document scoring invariants that JSON
Schema cannot express, such as score normalization and publishing caps.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable

import yaml


class ProtocolValidationError(ValueError):
    """Raised when a protocol document or result violates the frozen contract."""


# Criterion-level adverse conclusions must carry at least one actionable,
# evidence-backed Finding. Keep this set shared by the protocol validator and
# the staged aggregation contract so model-facing and machine-facing rules
# cannot drift apart.
FINDING_REQUIRED_CONCLUSIONS = frozenset(
    {"PARTIALLY_SUPPORTED", "CONTRADICTED", "MISSING"}
)


def _number(value: Any) -> Decimal:
    return Decimal(str(value))


def _rounded(value: Any, precision: int = 2) -> Decimal:
    quantum = Decimal(1).scaleb(-precision)
    return _number(value).quantize(quantum, rounding=ROUND_HALF_UP)


def _load_yaml(path: Path) -> dict[str, Any]:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ProtocolValidationError(f"{path}: expected a YAML mapping")
    return document


def _load_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ProtocolValidationError(f"{path}: expected a JSON object")
    return document


def _rubric_index(rubric: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    criteria: dict[str, dict[str, Any]] = {}
    dimensions: dict[str, str] = {}
    for dimension in rubric.get("dimensions", []):
        dimension_id = dimension.get("id")
        for criterion in dimension.get("criteria", []):
            criterion_id = criterion.get("id")
            if isinstance(criterion_id, str):
                criteria[criterion_id] = criterion
                dimensions[criterion_id] = dimension_id
    return criteria, dimensions


def validate_rubric(rubric: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    conclusions = rubric.get("semantic_conclusions", [])
    expected_conclusions = {
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONTRADICTED",
        "MISSING",
        "NOT_APPLICABLE",
        "NOT_VERIFIABLE",
    }
    if set(conclusions) != expected_conclusions or len(conclusions) != len(expected_conclusions):
        errors.append("rubric.semantic_conclusions must contain the six unique frozen conclusions")

    dimensions = rubric.get("dimensions", [])
    dimension_ids = [item.get("id") for item in dimensions]
    if len(dimension_ids) != len(set(dimension_ids)):
        errors.append("rubric dimension IDs must be unique")
    total_weight = sum((_number(item.get("weight", 0)) for item in dimensions), Decimal(0))
    expected_total = _number(rubric.get("score_model", {}).get("total_score", 0))
    if total_weight != expected_total or expected_total != Decimal(100):
        errors.append(f"rubric dimension weights must sum to 100, got {total_weight}")

    seen_criteria: set[str] = set()
    for dimension in dimensions:
        dimension_id = dimension.get("id", "<missing>")
        weight = _number(dimension.get("weight", 0))
        criterion_total = Decimal(0)
        for criterion in dimension.get("criteria", []):
            criterion_id = criterion.get("id")
            if not isinstance(criterion_id, str) or not criterion_id:
                errors.append(f"{dimension_id}: criterion ID is missing")
                continue
            if criterion_id in seen_criteria:
                errors.append(f"duplicate criterion ID: {criterion_id}")
            seen_criteria.add(criterion_id)
            maximum = _number(criterion.get("max_score", 0))
            criterion_total += maximum
            if maximum <= 0:
                errors.append(f"{criterion_id}: max_score must be positive")
            if criterion.get("evaluator") not in {"static", "semantic", "hybrid"}:
                errors.append(f"{criterion_id}: evaluator must be static, semantic, or hybrid")
            outcomes = criterion.get("outcomes", {})
            if set(outcomes) != expected_conclusions:
                errors.append(f"{criterion_id}: outcomes must define every frozen conclusion")
            for conclusion, outcome in outcomes.items():
                deduction = _number(outcome.get("deduction", -1))
                if deduction < 0 or deduction > maximum:
                    errors.append(
                        f"{criterion_id}/{conclusion}: deduction {deduction} is outside [0, {maximum}]"
                    )
            if outcomes.get("NOT_APPLICABLE", {}).get("exclude_from_denominator") is not True:
                errors.append(f"{criterion_id}: NOT_APPLICABLE must be excluded from the denominator")
            if outcomes.get("NOT_VERIFIABLE", {}).get("confidence_penalty") is not True:
                errors.append(f"{criterion_id}: NOT_VERIFIABLE must reduce confidence")
        if criterion_total != weight:
            errors.append(
                f"{dimension_id}: criterion maxima must sum to dimension weight {weight}, got {criterion_total}"
            )

    if rubric.get("rubric_version") in {"0.2.0", "0.3.0"}:
        expected_design_criteria = [
            "DESIGN-IMPLEMENTATION-PATH",
            "DESIGN-FEAT-RUNTIME-COVERAGE",
            "DESIGN-ALGORITHM-DATA-STATE",
            "DESIGN-DECISION-QUALITY",
            "DESIGN-IMPACT-COVERAGE",
            "DESIGN-VERIFICATION-PLAN",
        ]
        design_dimension = next(
            (item for item in dimensions if item.get("id") == "design_quality"), None
        )
        actual_design_criteria = [
            item.get("id") for item in (design_dimension or {}).get("criteria", [])
        ]
        if actual_design_criteria != expected_design_criteria:
            errors.append(
                "rubric 0.2+ design criteria must cover architecture, per-Feat runtime, "
                "algorithm/data/state, ADR, build/deployment, and verification in order"
            )
        for criterion in (design_dimension or {}).get("criteria", []):
            criterion_id = criterion.get("id", "<missing>")
            if criterion.get("coverage_scope") not in {
                "function",
                "per_registered_feature",
                "function_and_feature",
            }:
                errors.append(f"{criterion_id}: rubric 0.2+ requires a valid coverage_scope")
            checks = criterion.get("required_checks", [])
            if not checks or len(checks) != len(set(checks)):
                errors.append(f"{criterion_id}: required_checks must be non-empty and unique")
            outcome_policy = criterion.get("outcome_policy", {})
            expected_policy = {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "MISSING"}
            if set(outcome_policy) != expected_policy:
                errors.append(
                    f"{criterion_id}: outcome_policy must define SUPPORTED, "
                    "PARTIALLY_SUPPORTED, CONTRADICTED, and MISSING"
                )

    if rubric.get("rubric_version") == "0.3.0":
        if rubric.get("status") != "frozen":
            errors.append("rubric 0.3 must be frozen after the reference Pilot is confirmed")
        approval = rubric.get("approval", {})
        if approval.get("freeze_state") != "frozen":
            errors.append("rubric 0.3 approval.freeze_state must be frozen")
        if approval.get("confirmation_mode") != "single":
            errors.append("rubric 0.3 uses the single-confirmation workflow")
        if not approval.get("confirmed_by") or not approval.get("confirmed_at"):
            errors.append("rubric 0.3 freeze requires confirmed_by and confirmed_at")
        function_dimension = next(
            (item for item in dimensions if item.get("id") == "function_modeling"), None
        )
        expected_function_criteria = [
            "FUNCTION-FEAT-COVERAGE",
            "FUNCTION-FEAT-DECOMPOSITION",
            "FUNCTION-FEAT-BOUNDARY",
        ]
        actual_function_criteria = [
            item.get("id") for item in (function_dimension or {}).get("criteria", [])
        ]
        if actual_function_criteria != expected_function_criteria:
            errors.append(
                "rubric 0.3 function modeling criteria must cover Feat coverage, "
                "decomposition, and boundary in order"
            )
        for criterion in (function_dimension or {}).get("criteria", []):
            criterion_id = criterion.get("id", "<missing>")
            if criterion.get("evaluator") != "semantic":
                errors.append(f"{criterion_id}: function modeling must be evaluated by Skill")
            if criterion.get("coverage_scope") != "function":
                errors.append(f"{criterion_id}: function modeling must use Function scope")
            outcome_policy = criterion.get("outcome_policy", {})
            expected_policy = {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "MISSING"}
            if set(outcome_policy) != expected_policy:
                errors.append(
                    f"{criterion_id}: outcome_policy must define SUPPORTED, "
                    "PARTIALLY_SUPPORTED, CONTRADICTED, and MISSING"
                )

    caps = rubric.get("publishing_caps", {}).get("caps", {})
    if caps != {"Critical": 39, "Major": 59, "Minor": 79, "None": 100}:
        errors.append("publishing caps must be Critical=39, Major=59, Minor=79, None=100")

    confidence = rubric.get("confidence", {}).get("components", {})
    expected_components = {
        "evidence_verification_coverage": Decimal("0.4"),
        "human_confirmation": Decimal("0.3"),
        "source_revision_reproducibility": Decimal("0.2"),
        "tool_execution_completeness": Decimal("0.1"),
    }
    actual_components = {key: _number(value.get("weight", 0)) for key, value in confidence.items()}
    if actual_components != expected_components:
        errors.append("confidence component weights must remain 0.4/0.3/0.2/0.1")
    if sum(actual_components.values(), Decimal(0)) != Decimal(1):
        errors.append("confidence component weights must sum to 1")

    forbidden = set(rubric.get("score_model", {}).get("forbidden_positive_factors", []))
    expected_forbidden = {
        "document_length",
        "table_count",
        "diagram_count",
        "citation_count",
        "checked_self_audit_boxes",
    }
    if forbidden != expected_forbidden:
        errors.append("forbidden positive factors must remain complete and exact")

    admission = rubric.get("admission", {})
    expected_admission = {
        "BASELINED": (Decimal(80), Decimal("0.8")),
        "HIGH_QUALITY": (Decimal(90), Decimal("0.85")),
    }
    for status, (score, confidence_score) in expected_admission.items():
        rule = admission.get(status, {})
        if _number(rule.get("minimum_published_score", -1)) != score:
            errors.append(f"{status}: unexpected minimum_published_score")
        if _number(rule.get("minimum_confidence", -1)) != confidence_score:
            errors.append(f"{status}: unexpected minimum_confidence")
        if rule.get("all_gates_pass") is not True:
            errors.append(f"{status}: all_gates_pass must be true")

    compatibility = rubric.get("protocol_compatibility", {})
    if compatibility.get("complexity_rules_version") != "0.2.0":
        errors.append("rubric 0.2+ must bind complexity_rules_version 0.2.0")
    return errors


def validate_complexity_rules(complexity: dict[str, Any], rubric: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if complexity.get("rubric_version") != rubric.get("rubric_version"):
        errors.append("complexity_rules.rubric_version must match rubric.rubric_version")
    if complexity.get("complexity_rules_version") != rubric.get("protocol_compatibility", {}).get(
        "complexity_rules_version"
    ):
        errors.append("complexity_rules version does not match rubric compatibility declaration")

    levels = complexity.get("canonical_levels", [])
    level_ids = [item.get("id") for item in levels]
    if level_ids != ["simple", "standard", "complex", "critical"]:
        errors.append("canonical complexity levels must be simple/standard/complex/critical in rank order")
    ranks = [item.get("rank") for item in levels]
    if ranks != [1, 2, 3, 4]:
        errors.append("canonical complexity ranks must be 1,2,3,4")

    if complexity.get("function_aggregation", {}).get("input_scope") != (
        "all_registered_non_deprecated_features"
    ):
        errors.append("complexity aggregation must cover all registered non-deprecated Features")
    critical_depth = complexity.get("review_depth", {}).get("critical", {})
    for requirement in (
        "require_function_architecture_context",
        "require_per_feature_runtime_coverage",
        "require_algorithm_data_state_review",
        "require_build_deployment_review",
    ):
        if critical_depth.get(requirement) is not True:
            errors.append(f"critical review depth must enable {requirement}")

    aliases: dict[str, str] = {}
    for level in levels:
        level_id = level.get("id", "<missing>")
        for alias in level.get("exact_aliases", []):
            normalized = unicodedata.normalize("NFKC", str(alias)).strip().casefold()
            previous = aliases.get(normalized)
            if previous is not None and previous != level_id:
                errors.append(f"complexity alias {alias!r} belongs to both {previous} and {level_id}")
            aliases[normalized] = level_id
        for pattern in level.get("match_patterns", []):
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as exc:
                errors.append(f"{level_id}: invalid complexity regex {pattern!r}: {exc}")

    criteria, _ = _rubric_index(rubric)
    correctness = {
        criterion_id
        for criterion_id in criteria
        if criterion_id.startswith("CORRECTNESS-")
    }
    invariant_correctness = set(
        complexity.get("invariants", {}).get("correctness_criteria_always_applicable", [])
    )
    if correctness != invariant_correctness:
        errors.append("all and only correctness criteria must be always applicable")

    allowed_na = complexity.get("not_applicable_policy", {}).get("allowed", {})
    valid_levels = set(level_ids)
    for criterion_id, policy in allowed_na.items():
        if criterion_id not in criteria:
            errors.append(f"N/A policy references unknown criterion {criterion_id}")
            continue
        if criteria[criterion_id].get("allow_not_applicable") is not True:
            errors.append(f"N/A policy allows criterion forbidden by rubric: {criterion_id}")
        unknown_levels = set(policy.get("levels", [])) - valid_levels
        if unknown_levels:
            errors.append(f"{criterion_id}: N/A policy contains unknown levels {sorted(unknown_levels)}")
        if not str(policy.get("requires_statement", "")).strip():
            errors.append(f"{criterion_id}: N/A policy needs an explicit statement")

    for criterion_id, criterion in criteria.items():
        if criterion.get("allow_not_applicable") is True and criterion_id not in allowed_na:
            errors.append(f"rubric allows N/A but complexity policy is missing: {criterion_id}")
    return errors


def validate_design_completeness_rules(
    rules: dict[str, Any], rubric: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if rules.get("rubric_version") != rubric.get("rubric_version"):
        errors.append("design completeness rubric_version must match rubric.rubric_version")
    expected_version = rubric.get("protocol_compatibility", {}).get(
        "design_completeness_rules_version"
    )
    if rules.get("design_completeness_rules_version") != expected_version:
        errors.append("design completeness rules version does not match rubric compatibility")
    coverage_policy = rules.get("coverage_policy", {})
    expected_coverage_policy = {
        "registered_feature_scope": "all_non_deprecated_features",
        "function_supported_requires": "all_applicable_checks_covered",
        "per_feature_supported_requires": "every_registered_feature_all_applicable_checks_covered",
        "partial_policy": "at_least_one_applicable_check_partial_or_missing_with_main_design_present",
        "missing_policy": "core_design_absent_or_registered_feature_has_only_title_or_summary",
        "contradicted_policy": "design_claim_conflicts_with_frozen_implementation_or_contract",
    }
    for field, expected in expected_coverage_policy.items():
        if coverage_policy.get(field) != expected:
            errors.append(f"design completeness coverage_policy.{field} must be {expected}")
    expected_forbidden = {
        "heading_presence_only",
        "table_presence_only",
        "diagram_presence_only",
        "document_length",
        "checked_self_audit_boxes",
    }
    if set(coverage_policy.get("forbidden_positive_factors", [])) != expected_forbidden:
        errors.append("design completeness forbidden positive factors must remain complete and exact")
    rubric_design = next(
        (item for item in rubric.get("dimensions", []) if item.get("id") == "design_quality"),
        {},
    )
    rubric_criteria = {item.get("id"): item for item in rubric_design.get("criteria", [])}
    rule_criteria = rules.get("criteria", {})
    if list(rule_criteria) != list(rubric_criteria):
        errors.append("design completeness criteria must match rubric design criteria in order")
    seen_checks: set[str] = set()
    for criterion_id, criterion_rules in rule_criteria.items():
        rubric_criterion = rubric_criteria.get(criterion_id, {})
        if criterion_rules.get("coverage_scope") != rubric_criterion.get("coverage_scope"):
            errors.append(f"{criterion_id}: coverage_scope does not match rubric")
        checks = criterion_rules.get("checks", [])
        check_ids = [item.get("check_id") for item in checks]
        if check_ids != rubric_criterion.get("required_checks", []):
            errors.append(f"{criterion_id}: check IDs do not match rubric required_checks")
        for check in checks:
            check_id = check.get("check_id")
            if check_id in seen_checks:
                errors.append(f"duplicate design completeness check ID: {check_id}")
            seen_checks.add(check_id)
            if check.get("evaluator") not in {"script", "semantic_skill", "hybrid"}:
                errors.append(f"{check_id}: invalid evaluator")
            if check.get("evaluator") in {"script", "hybrid"} and not str(
                check.get("script_signal", "")
            ).strip():
                errors.append(f"{check_id}: script or hybrid check requires script_signal")
            if not str(check.get("semantic_requirement", "")).strip():
                errors.append(f"{check_id}: semantic_requirement is required")
    return errors


def normalize_complexity_value(value: str | None, complexity: dict[str, Any]) -> tuple[str, str]:
    """Return ``(canonical_level, state)`` for one Feature complexity value."""

    policy = complexity["normalization"]
    if value is None or not str(value).strip():
        return policy["missing_value"]["normalized_level"], "missing"
    normalized = unicodedata.normalize(policy.get("unicode_normalization", "NFKC"), str(value))
    if policy.get("trim_whitespace", True):
        normalized = normalized.strip()
    comparable = normalized if policy.get("case_sensitive", False) else normalized.casefold()
    exact_matches: list[tuple[int, str]] = []
    regex_matches: list[tuple[int, str]] = []
    flags = 0 if policy.get("case_sensitive", False) else re.IGNORECASE
    for level in complexity["canonical_levels"]:
        aliases = [
            unicodedata.normalize(policy.get("unicode_normalization", "NFKC"), str(alias)).strip()
            for alias in level.get("exact_aliases", [])
        ]
        aliases = aliases if policy.get("case_sensitive", False) else [item.casefold() for item in aliases]
        if comparable in aliases:
            exact_matches.append((level["rank"], level["id"]))
        if any(re.fullmatch(pattern, normalized, flags=flags) for pattern in level.get("match_patterns", [])):
            regex_matches.append((level["rank"], level["id"]))
    matches = exact_matches or regex_matches
    if matches:
        return max(matches)[1], "matched"
    return policy["unknown_value"]["normalized_level"], "unknown"


def aggregate_function_complexity(
    raw_feature_values: dict[str, str | None], complexity: dict[str, Any]
) -> dict[str, Any]:
    """Normalize all Features and select the highest canonical Function level."""

    normalized: dict[str, str] = {}
    events: list[dict[str, Any]] = []
    ranks = {item["id"]: item["rank"] for item in complexity["canonical_levels"]}
    for feat_id, raw_value in sorted(raw_feature_values.items()):
        level, state = normalize_complexity_value(raw_value, complexity)
        normalized[feat_id] = level
        if state != "matched":
            policy = complexity["normalization"][f"{state}_value"]
            events.append(
                {
                    "feat_id": feat_id,
                    "raw_value": raw_value,
                    "normalized_level": level,
                    "state": state,
                    "finding": policy["finding"],
                }
            )
    if normalized:
        function_level = max(normalized.values(), key=lambda item: (ranks[item], item))
    else:
        function_level = complexity["normalization"]["missing_value"]["normalized_level"]
        events.append(
            {
                "feat_id": None,
                "raw_value": None,
                "normalized_level": function_level,
                "state": "missing",
                "finding": complexity["normalization"]["missing_value"]["finding"],
            }
        )
    return {
        "raw_feature_values": dict(sorted(raw_feature_values.items())),
        "normalized_feature_levels": normalized,
        "function_level": function_level,
        "normalization_findings": events,
    }


class JsonSchemaSubsetValidator:
    """Validate the keyword subset used by the repository-owned schemas."""

    def __init__(self, schemas_root: Path):
        self.schemas_root = schemas_root
        self._documents: dict[Path, dict[str, Any]] = {}

    def validate_file(self, instance: Any, schema_path: Path) -> list[str]:
        schema_path = schema_path.resolve()
        document = self._document(schema_path)
        return self._validate(instance, document, document, schema_path, "$")

    def _document(self, path: Path) -> dict[str, Any]:
        path = path.resolve()
        if path not in self._documents:
            self._documents[path] = _load_json(path)
        return self._documents[path]

    def _resolve_ref(
        self,
        reference: str,
        current_document: dict[str, Any],
        current_path: Path,
    ) -> tuple[dict[str, Any], dict[str, Any], Path]:
        file_part, _, pointer = reference.partition("#")
        if file_part:
            target_path = (current_path.parent / file_part).resolve()
            target_document = self._document(target_path)
        else:
            target_path = current_path
            target_document = current_document
        target: Any = target_document
        if pointer:
            for token in pointer.lstrip("/").split("/"):
                token = token.replace("~1", "/").replace("~0", "~")
                target = target[token]
        if not isinstance(target, dict):
            raise ProtocolValidationError(f"schema reference {reference} does not resolve to an object")
        return target, target_document, target_path

    @staticmethod
    def _matches_type(instance: Any, expected: str) -> bool:
        if expected == "null":
            return instance is None
        if expected == "object":
            return isinstance(instance, dict)
        if expected == "array":
            return isinstance(instance, list)
        if expected == "string":
            return isinstance(instance, str)
        if expected == "boolean":
            return isinstance(instance, bool)
        if expected == "integer":
            return isinstance(instance, int) and not isinstance(instance, bool)
        if expected == "number":
            return isinstance(instance, (int, float)) and not isinstance(instance, bool)
        return False

    def _validate(
        self,
        instance: Any,
        schema: dict[str, Any],
        current_document: dict[str, Any],
        current_path: Path,
        instance_path: str,
    ) -> list[str]:
        errors: list[str] = []
        if "$ref" in schema:
            target, target_document, target_path = self._resolve_ref(
                schema["$ref"], current_document, current_path
            )
            errors.extend(self._validate(instance, target, target_document, target_path, instance_path))
            return errors

        expected_type = schema.get("type")
        if expected_type is not None:
            expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
            if not any(self._matches_type(instance, item) for item in expected_types):
                errors.append(f"{instance_path}: expected type {expected_types}, got {type(instance).__name__}")
                return errors

        if "const" in schema and instance != schema["const"]:
            errors.append(f"{instance_path}: expected constant {schema['const']!r}")
        if "enum" in schema and instance not in schema["enum"]:
            errors.append(f"{instance_path}: value {instance!r} is not in enum {schema['enum']!r}")

        if isinstance(instance, dict):
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    errors.append(f"{instance_path}: missing required property {key!r}")
            properties = schema.get("properties", {})
            for key, value in instance.items():
                child_path = f"{instance_path}.{key}"
                if key in properties:
                    errors.extend(
                        self._validate(value, properties[key], current_document, current_path, child_path)
                    )
                else:
                    additional = schema.get("additionalProperties", True)
                    if additional is False:
                        errors.append(f"{child_path}: additional property is not allowed")
                    elif isinstance(additional, dict):
                        errors.extend(
                            self._validate(value, additional, current_document, current_path, child_path)
                        )

        if isinstance(instance, list):
            if len(instance) < schema.get("minItems", 0):
                errors.append(f"{instance_path}: expected at least {schema['minItems']} items")
            if "maxItems" in schema and len(instance) > schema["maxItems"]:
                errors.append(f"{instance_path}: expected at most {schema['maxItems']} items")
            if schema.get("uniqueItems"):
                serialized = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in instance]
                if len(serialized) != len(set(serialized)):
                    errors.append(f"{instance_path}: items must be unique")
            item_schema = schema.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(instance):
                    errors.extend(
                        self._validate(
                            item,
                            item_schema,
                            current_document,
                            current_path,
                            f"{instance_path}[{index}]",
                        )
                    )

        if isinstance(instance, str):
            if len(instance) < schema.get("minLength", 0):
                errors.append(f"{instance_path}: string is shorter than {schema['minLength']}")
            if "pattern" in schema and re.search(schema["pattern"], instance) is None:
                errors.append(f"{instance_path}: value {instance!r} does not match {schema['pattern']!r}")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            value = _number(instance)
            if "minimum" in schema and value < _number(schema["minimum"]):
                errors.append(f"{instance_path}: value is below minimum {schema['minimum']}")
            if "maximum" in schema and value > _number(schema["maximum"]):
                errors.append(f"{instance_path}: value is above maximum {schema['maximum']}")
            if "exclusiveMinimum" in schema and value <= _number(schema["exclusiveMinimum"]):
                errors.append(f"{instance_path}: value must be greater than {schema['exclusiveMinimum']}")

        for sub_schema in schema.get("allOf", []):
            errors.extend(self._validate(instance, sub_schema, current_document, current_path, instance_path))
        if "anyOf" in schema:
            candidates = [
                self._validate(instance, item, current_document, current_path, instance_path)
                for item in schema["anyOf"]
            ]
            if not any(not candidate for candidate in candidates):
                errors.append(f"{instance_path}: no anyOf branch matched")
        if "oneOf" in schema:
            matched = sum(
                not self._validate(instance, item, current_document, current_path, instance_path)
                for item in schema["oneOf"]
            )
            if matched != 1:
                errors.append(f"{instance_path}: expected exactly one matching oneOf branch, got {matched}")
        if "not" in schema and not self._validate(
            instance, schema["not"], current_document, current_path, instance_path
        ):
            errors.append(f"{instance_path}: matched a forbidden schema")
        if "if" in schema:
            condition_errors = self._validate(
                instance, schema["if"], current_document, current_path, instance_path
            )
            branch = schema.get("then") if not condition_errors else schema.get("else")
            if isinstance(branch, dict):
                errors.extend(self._validate(instance, branch, current_document, current_path, instance_path))
        return errors


def validate_strict_output_schema(schema: dict[str, Any]) -> list[str]:
    """Check the JSON Schema subset required by strict structured outputs.

    Every object node must be closed and every declared property must be
    required. Optional values are represented by nullable types, not by
    omitting their property from ``required``.
    """

    errors: list[str] = []

    def walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        declared_type = node.get("type")
        is_object = declared_type == "object" or (
            isinstance(declared_type, list) and "object" in declared_type
        )
        if is_object:
            if node.get("additionalProperties") is not False:
                errors.append(f"{path}.additionalProperties: must be false")
            properties = node.get("properties")
            if not isinstance(properties, dict):
                errors.append(f"{path}.properties: expected an object")
                properties = {}
            required = node.get("required")
            if not isinstance(required, list) or any(
                not isinstance(item, str) for item in required
            ):
                errors.append(f"{path}.required: expected a list of property names")
                required = []
            elif len(required) != len(set(required)):
                errors.append(f"{path}.required: duplicate property names are not allowed")
            missing = sorted(set(properties) - set(required))
            extra = sorted(set(required) - set(properties))
            if missing or extra:
                errors.append(
                    f"{path}.required: must contain every property exactly once; "
                    f"missing={missing} extra={extra}"
                )
            for key, child in properties.items():
                walk(child, f"{path}.properties.{key}")

        items = node.get("items")
        if isinstance(items, dict):
            walk(items, f"{path}.items")
        prefix_items = node.get("prefixItems")
        if isinstance(prefix_items, list):
            for index, child in enumerate(prefix_items):
                walk(child, f"{path}.prefixItems[{index}]")
        for keyword in ("anyOf", "oneOf", "allOf"):
            branches = node.get(keyword)
            if isinstance(branches, list):
                for index, child in enumerate(branches):
                    walk(child, f"{path}.{keyword}[{index}]")
        for keyword in ("$defs", "definitions"):
            definitions = node.get(keyword)
            if isinstance(definitions, dict):
                for key, child in definitions.items():
                    walk(child, f"{path}.{keyword}.{key}")

    walk(schema, "$")
    return errors


def validate_schema_contracts(schemas_root: Path, rubric: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "semantic-result.schema.json": "semantic_result_schema_version",
        "score-result.schema.json": "score_result_schema_version",
        "evaluation-report.schema.json": "evaluation_report_schema_version",
    }
    compatibility = rubric.get("protocol_compatibility", {})
    for filename, compatibility_key in expected.items():
        path = schemas_root / filename
        if not path.is_file():
            errors.append(f"missing schema: {filename}")
            continue
        schema = _load_json(path)
        if schema.get("type") != "object" or not schema.get("required"):
            errors.append(f"{filename}: root must be an object with required fields")
        declared = schema.get("properties", {}).get("schema_version", {}).get("const")
        if declared != compatibility.get(compatibility_key):
            errors.append(f"{filename}: schema_version const does not match rubric compatibility")
    executor_schema_path = schemas_root / "executor-result.schema.json"
    if not executor_schema_path.is_file():
        errors.append("missing schema: executor-result.schema.json")
    else:
        executor_schema = _load_json(executor_schema_path)
        errors.extend(
            f"executor-result.schema.json: {error}"
            for error in validate_strict_output_schema(executor_schema)
        )
    return errors


def validate_protocol(evaluation_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    rubric = _load_yaml(evaluation_root / "rubric.yaml")
    complexity = _load_yaml(evaluation_root / "complexity_rules.yaml")
    design_completeness = _load_yaml(evaluation_root / "design_completeness_rules.yaml")
    errors = validate_rubric(rubric)
    errors.extend(validate_complexity_rules(complexity, rubric))
    errors.extend(validate_design_completeness_rules(design_completeness, rubric))
    errors.extend(validate_schema_contracts(evaluation_root / "schemas", rubric))
    return rubric, complexity, errors


def _expected_criterion_ids(rubric: dict[str, Any]) -> list[str]:
    return [
        criterion["id"]
        for dimension in rubric["dimensions"]
        for criterion in dimension["criteria"]
    ]


def validate_semantic_result(
    instance: dict[str, Any],
    rubric: dict[str, Any],
    complexity: dict[str, Any],
    schemas_root: Path,
) -> list[str]:
    errors = JsonSchemaSubsetValidator(schemas_root).validate_file(
        instance, schemas_root / "semantic-result.schema.json"
    )
    criteria, dimensions = _rubric_index(rubric)
    results = instance.get("criterion_results", [])
    result_ids = [item.get("criterion_id") for item in results]
    expected_ids = _expected_criterion_ids(rubric)
    if result_ids != expected_ids:
        errors.append("semantic criterion_results must contain every rubric criterion once in rubric order")

    all_finding_ids: set[str] = set()
    level = instance.get("complexity", {}).get("function_level")
    na_policy = complexity.get("not_applicable_policy", {}).get("allowed", {})
    per_dimension: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        criterion_id = result.get("criterion_id")
        if criterion_id not in criteria:
            continue
        per_dimension.setdefault(dimensions[criterion_id], []).append(result)
        if result.get("dimension_id") != dimensions[criterion_id]:
            errors.append(f"{criterion_id}: dimension_id does not match rubric")
        conclusion = result.get("conclusion")
        if conclusion not in criteria[criterion_id].get("outcomes", {}):
            errors.append(f"{criterion_id}: unknown conclusion {conclusion!r}")
        evidence = result.get("evidence", [])
        evidence_ids = {item.get("evidence_id") for item in evidence}
        if len(evidence_ids) != len(evidence):
            errors.append(f"{criterion_id}: evidence IDs must be unique within the criterion")
        for item in evidence:
            if item.get("source_revision") != instance.get("source_revision"):
                errors.append(f"{criterion_id}/{item.get('evidence_id')}: evidence revision mismatch")
            if item.get("line_start") and item.get("line_end") and item["line_end"] < item["line_start"]:
                errors.append(f"{criterion_id}/{item.get('evidence_id')}: line_end precedes line_start")
        if conclusion in {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONTRADICTED", "MISSING"}:
            if not evidence:
                errors.append(f"{criterion_id}: {conclusion} requires reproducible evidence")
            required_types = set(criteria[criterion_id].get("required_evidence_types", []))
            actual_types = {item.get("type") for item in evidence}
            if evidence and required_types.isdisjoint(actual_types):
                errors.append(
                    f"{criterion_id}: evidence must include one of {sorted(required_types)}, "
                    f"got {sorted(actual_types)}"
                )
        findings = result.get("findings", [])
        if conclusion in FINDING_REQUIRED_CONCLUSIONS and not findings:
            errors.append(f"{criterion_id}: {conclusion} requires an evidence-backed finding")
        if conclusion in {"SUPPORTED", "NOT_APPLICABLE"} and findings:
            errors.append(f"{criterion_id}: {conclusion} must not contain defect findings")
        if conclusion == "NOT_APPLICABLE":
            policy = na_policy.get(criterion_id)
            if not criteria[criterion_id].get("allow_not_applicable") or policy is None:
                errors.append(f"{criterion_id}: N/A is not allowed")
            elif level not in policy.get("levels", []):
                errors.append(f"{criterion_id}: N/A is not allowed for complexity {level}")
            if not str(result.get("applicability_reason", "")).strip() or not evidence:
                errors.append(f"{criterion_id}: N/A requires a reason and reproducible evidence")
        if conclusion == "NOT_VERIFIABLE" and not str(result.get("missing_evidence", "")).strip():
            errors.append(f"{criterion_id}: NOT_VERIFIABLE requires missing_evidence")
        severity_rank = {"Info": 0, "Minor": 1, "Major": 2, "Critical": 3}
        expected_severity = criteria[criterion_id].get("outcomes", {}).get(conclusion, {}).get("severity")
        for finding in findings:
            finding_id = finding.get("finding_id")
            if finding_id in all_finding_ids:
                errors.append(f"duplicate semantic finding ID: {finding_id}")
            all_finding_ids.add(finding_id)
            if finding.get("criterion_id") != criterion_id:
                errors.append(f"{finding_id}: finding criterion_id does not match its result")
            if finding.get("conclusion") != conclusion:
                errors.append(f"{finding_id}: finding conclusion does not match its criterion result")
            if conclusion in FINDING_REQUIRED_CONCLUSIONS and not finding.get("evidence_ids"):
                errors.append(f"{finding_id}: {conclusion} finding requires evidence_ids")
            missing_refs = set(finding.get("evidence_ids", [])) - evidence_ids
            if missing_refs:
                errors.append(f"{finding_id}: unresolved evidence IDs {sorted(missing_refs)}")
            if finding.get("severity") in {"Major", "Critical"} and not finding.get("evidence_ids"):
                errors.append(f"{finding_id}: Critical/Major finding requires evidence")
            if expected_severity and severity_rank.get(finding.get("severity"), -1) < severity_rank[expected_severity]:
                errors.append(
                    f"{finding_id}: severity may not be lower than rubric outcome severity {expected_severity}"
                )

    minimum_ratio = _number(
        rubric.get("score_model", {}).get("not_applicable", {}).get(
            "minimum_applicable_criterion_ratio", 0
        )
    )
    for dimension_id, dimension_results in per_dimension.items():
        applicable = [item for item in dimension_results if item.get("conclusion") != "NOT_APPLICABLE"]
        ratio = Decimal(len(applicable)) / Decimal(len(dimension_results))
        if ratio < minimum_ratio and not any(
            item.get("conclusion") == "NOT_VERIFIABLE" for item in applicable
        ):
            errors.append(
                f"{dimension_id}: applicable criterion ratio {ratio} is below {minimum_ratio}; "
                "dimension must be marked NOT_VERIFIABLE"
            )

    coverage = instance.get("coverage", {})
    counts = {
        "expected_criteria": len(expected_ids),
        "evaluated_criteria": len(results),
        "applicable_criteria": sum(item.get("conclusion") != "NOT_APPLICABLE" for item in results),
        "not_applicable_criteria": sum(item.get("conclusion") == "NOT_APPLICABLE" for item in results),
        "not_verifiable_criteria": sum(item.get("conclusion") == "NOT_VERIFIABLE" for item in results),
    }
    for key, expected in counts.items():
        if coverage.get(key) != expected:
            errors.append(f"semantic coverage.{key} must be {expected}, got {coverage.get(key)!r}")
    return errors


def _gate_rank(value: str) -> int:
    return {"pass": 0, "warn": 1, "fail": 2, "error": 3}.get(value, -1)


def validate_score_result(
    instance: dict[str, Any],
    rubric: dict[str, Any],
    schemas_root: Path,
) -> list[str]:
    errors = JsonSchemaSubsetValidator(schemas_root).validate_file(
        instance, schemas_root / "score-result.schema.json"
    )
    criteria, dimensions = _rubric_index(rubric)
    expected_dimension_ids = [item["id"] for item in rubric["dimensions"]]
    actual_dimension_ids = [item.get("dimension_id") for item in instance.get("dimensions", [])]
    if actual_dimension_ids != expected_dimension_ids:
        errors.append("score dimensions must appear once in rubric order")

    dimension_scores: list[Decimal] = []
    minimum_ratio = _number(
        rubric.get("score_model", {}).get("not_applicable", {}).get(
            "minimum_applicable_criterion_ratio", 0
        )
    )
    for dimension_result in instance.get("dimensions", []):
        dimension_id = dimension_result.get("dimension_id")
        rubric_dimension = next(
            (item for item in rubric["dimensions"] if item["id"] == dimension_id), None
        )
        if rubric_dimension is None:
            continue
        expected_ids = [item["id"] for item in rubric_dimension["criteria"]]
        actual_ids = [item.get("criterion_id") for item in dimension_result.get("criteria", [])]
        if actual_ids != expected_ids:
            errors.append(f"{dimension_id}: criterion scores must appear once in rubric order")
        applicable_max = Decimal(0)
        earned = Decimal(0)
        for criterion_result in dimension_result.get("criteria", []):
            criterion_id = criterion_result.get("criterion_id")
            criterion = criteria.get(criterion_id)
            if criterion is None:
                continue
            maximum = _number(criterion["max_score"])
            conclusion = criterion_result.get("conclusion")
            expected_applicable = conclusion != "NOT_APPLICABLE"
            if criterion_result.get("applicable") is not expected_applicable:
                errors.append(f"{criterion_id}: applicable flag conflicts with conclusion")
            if _number(criterion_result.get("max_score", -1)) != maximum:
                errors.append(f"{criterion_id}: max_score does not match rubric")
            expected_deduction = _number(criterion.get("outcomes", {}).get(conclusion, {}).get("deduction", -1))
            actual_deduction = _number(criterion_result.get("deduction", -1))
            if actual_deduction != expected_deduction:
                errors.append(
                    f"{criterion_id}: deduction must be {expected_deduction} for {conclusion}, "
                    f"got {actual_deduction}"
                )
            if expected_applicable:
                applicable_max += maximum
                expected_score = _rounded(max(Decimal(0), maximum - expected_deduction))
                if criterion_result.get("score") is None or _number(criterion_result["score"]) != expected_score:
                    errors.append(f"{criterion_id}: score must be {expected_score}")
                earned += expected_score
            elif criterion_result.get("score") is not None:
                errors.append(f"{criterion_id}: N/A score must be null")
        maximum = _number(rubric_dimension["weight"])
        expected_dimension_score = (
            _rounded(earned / applicable_max * maximum) if applicable_max else Decimal(0)
        )
        if _number(dimension_result.get("max_score", -1)) != maximum:
            errors.append(f"{dimension_id}: max_score does not match rubric")
        if _number(dimension_result.get("applicable_max_score", -1)) != applicable_max:
            errors.append(f"{dimension_id}: applicable_max_score must be {applicable_max}")
        if _number(dimension_result.get("earned_score", -1)) != _rounded(earned):
            errors.append(f"{dimension_id}: earned_score must be {_rounded(earned)}")
        if _number(dimension_result.get("score", -1)) != expected_dimension_score:
            errors.append(f"{dimension_id}: normalized score must be {expected_dimension_score}")
        criterion_count = len(rubric_dimension["criteria"])
        applicable_count = sum(item.get("applicable") is True for item in dimension_result.get("criteria", []))
        ratio = Decimal(applicable_count) / Decimal(criterion_count)
        expected_verifiability = "NOT_VERIFIABLE" if ratio < minimum_ratio else "VERIFIABLE"
        if dimension_result.get("verifiability") != expected_verifiability:
            errors.append(f"{dimension_id}: verifiability must be {expected_verifiability}")
        dimension_scores.append(expected_dimension_score)

    expected_raw = _rounded(sum(dimension_scores, Decimal(0)))
    if _number(instance.get("raw_score", -1)) != expected_raw:
        errors.append(f"raw_score must equal dimension sum {expected_raw}")

    active = set(instance.get("caps", {}).get("active_severities", []))
    if "Critical" in active:
        expected_severity = "Critical"
    elif "Major" in active:
        expected_severity = "Major"
    elif "Minor" in active:
        expected_severity = "Minor"
    else:
        expected_severity = "None"
    caps = rubric["publishing_caps"]["caps"]
    expected_cap = _number(caps[expected_severity])
    applied = instance.get("caps", {}).get("applied", {})
    if applied.get("severity") != expected_severity or _number(applied.get("limit", -1)) != expected_cap:
        errors.append(f"applied cap must be {expected_severity}/{expected_cap}")
    expected_published = min(expected_raw, expected_cap)
    if _number(instance.get("published_score", -1)) != expected_published:
        errors.append(f"published_score must be min(raw_score, cap) = {expected_published}")

    gate = instance.get("gate", {})
    expected_effective = max((gate.get("static"), gate.get("semantic")), key=_gate_rank)
    if gate.get("effective") != expected_effective:
        errors.append(f"effective gate must preserve the stricter static/semantic gate: {expected_effective}")

    execution = instance.get("execution", {})
    completion = Decimal(sum(value is True for value in execution.values())) / Decimal(4)
    components = instance.get("confidence", {}).get("components", {})
    if _number(components.get("tool_execution_completeness", -1)) != completion:
        errors.append(f"tool_execution_completeness must be {completion}")
    weights = {
        key: _number(value["weight"])
        for key, value in rubric["confidence"]["components"].items()
    }
    expected_confidence = _rounded(
        sum((_number(components.get(key, 0)) * weight for key, weight in weights.items()), Decimal(0))
    )
    confidence = instance.get("confidence", {})
    if _number(confidence.get("score", -1)) != expected_confidence:
        errors.append(f"confidence.score must be weighted and rounded to {expected_confidence}")
    expected_publishable = all(value is True for value in execution.values())
    if confidence.get("publishable") is not expected_publishable:
        errors.append("confidence.publishable must equal all required stages complete")

    if not expected_publishable or gate.get("effective") != "pass":
        expected_admission = "NOT_READY"
    elif expected_published >= Decimal(90) and expected_confidence >= Decimal("0.85"):
        expected_admission = "HIGH_QUALITY"
    elif expected_published >= Decimal(80) and expected_confidence >= Decimal("0.8"):
        expected_admission = "BASELINED"
    else:
        expected_admission = "NOT_READY"
    if any(item.get("verifiability") == "NOT_VERIFIABLE" for item in instance.get("dimensions", [])):
        expected_admission = "NOT_READY"
    if instance.get("admission", {}).get("status") != expected_admission:
        errors.append(f"admission.status must be {expected_admission}")
    return errors


def validate_evaluation_report(
    instance: dict[str, Any],
    rubric: dict[str, Any],
    complexity: dict[str, Any],
    schemas_root: Path,
) -> list[str]:
    errors = JsonSchemaSubsetValidator(schemas_root).validate_file(
        instance, schemas_root / "evaluation-report.schema.json"
    )
    semantic = instance.get("semantic", {})
    score = instance.get("score", {})
    errors.extend(validate_semantic_result(semantic, rubric, complexity, schemas_root))
    errors.extend(validate_score_result(score, rubric, schemas_root))
    for child_name, child in (("static", instance.get("static", {})), ("semantic", semantic), ("score", score)):
        if child.get("func_id") != instance.get("func_id"):
            errors.append(f"evaluation report {child_name}.func_id mismatch")
        if child.get("source_revision") != instance.get("source_revision"):
            errors.append(f"evaluation report {child_name}.source_revision mismatch")
    protocol = instance.get("protocol", {})
    if protocol.get("rubric_version") != rubric.get("rubric_version"):
        errors.append("evaluation report rubric version mismatch")
    if protocol.get("complexity_rules_version") != complexity.get("complexity_rules_version"):
        errors.append("evaluation report complexity version mismatch")
    summary = instance.get("summary", {})
    expected_summary = {
        "gate": score.get("gate", {}).get("effective"),
        "raw_score": score.get("raw_score"),
        "published_score": score.get("published_score"),
        "confidence": score.get("confidence", {}).get("score"),
        "admission_status": score.get("admission", {}).get("status"),
    }
    if summary != expected_summary:
        errors.append("evaluation report summary must exactly mirror score-result")
    return errors


def raise_for_errors(errors: Iterable[str]) -> None:
    errors = list(errors)
    if errors:
        raise ProtocolValidationError("\n".join(f"- {item}" for item in errors))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate spec_eval semantic protocol v0.2")
    parser.add_argument(
        "--evaluation-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "evaluation",
        help="Path containing rubric.yaml, complexity_rules.yaml, and schemas/",
    )
    parser.add_argument(
        "--examples-dir",
        type=Path,
        help="Optional directory containing semantic-result.json, score-result.json, and evaluation-report.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rubric, complexity, errors = validate_protocol(args.evaluation_root)
    schemas_root = args.evaluation_root / "schemas"
    if args.examples_dir:
        validators = {
            "semantic-result.json": lambda value: validate_semantic_result(
                value, rubric, complexity, schemas_root
            ),
            "score-result.json": lambda value: validate_score_result(value, rubric, schemas_root),
            "evaluation-report.json": lambda value: validate_evaluation_report(
                value, rubric, complexity, schemas_root
            ),
        }
        for filename, validator in validators.items():
            path = args.examples_dir / filename
            if not path.is_file():
                errors.append(f"missing example: {path}")
                continue
            errors.extend(f"{filename}: {item}" for item in validator(_load_json(path)))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"protocol valid: rubric={rubric['rubric_version']} "
        f"complexity={complexity['complexity_rules_version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
