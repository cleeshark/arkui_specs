"""Build deterministic remediation and per-Feature risk analysis for one Function."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable


FUNCTION_ANALYSIS_SCHEMA_VERSION = 1
FUNCTION_ANALYSIS_VERSION = "spec-eval-function-analysis@0.1.0"
_SEVERITIES = ("Critical", "Major", "Minor", "Info")
_SEVERITY_RANK = {"Info": 0, "Minor": 1, "Major": 2, "Critical": 3}
_PRIORITY = {"Critical": "P0", "Major": "P1", "Minor": "P2", "Info": "P2"}
_CLAIM_STATUSES = {"RESOLVED", "PARTIALLY_RESOLVED", "UNRESOLVED", "NO_EVIDENCE"}
_FEAT_PATTERN = re.compile(r"(?<![A-Za-z0-9])Feat-[0-9]+")


class FunctionAnalysisInputError(ValueError):
    """Raised when score inputs cannot produce a reproducible Function analysis."""


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FunctionAnalysisInputError(f"cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FunctionAnalysisInputError(f"{path}: expected a JSON object")
    return value


def _hash_file(path: Path) -> str:
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FunctionAnalysisInputError(f"cannot hash input {path}: {exc}") from exc
    return f"sha256:{digest}"


def _rounded_ratio(numerator: int, denominator: int) -> int | float:
    if denominator == 0:
        return 0
    value = (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal("0.000001"), rounding=ROUND_HALF_UP
    )
    normalized = value.normalize()
    return int(normalized) if normalized == normalized.to_integral() else float(normalized)


def _feat_ids(*values: Any) -> set[str]:
    result: set[str] = set()
    for value in values:
        if isinstance(value, str):
            result.update(_FEAT_PATTERN.findall(value))
        elif isinstance(value, list):
            result.update(_feat_ids(*value))
    return result


def _empty_counts() -> dict[str, int]:
    return {severity: 0 for severity in _SEVERITIES}


def _semantic_findings(
    semantic_result: dict[str, Any],
) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    complexity = semantic_result.get("complexity", {})
    for finding in complexity.get("normalization_findings", []):
        if isinstance(finding, dict):
            yield {}, finding
    for criterion in semantic_result.get("criterion_results", []):
        if not isinstance(criterion, dict):
            continue
        for finding in criterion.get("findings", []):
            if isinstance(finding, dict):
                yield criterion, finding


def _semantic_feat_ids(criterion: dict[str, Any], finding: dict[str, Any]) -> set[str]:
    result = _feat_ids(finding.get("claim_id"))
    evidence_by_id = {
        item.get("evidence_id"): item
        for item in criterion.get("evidence", [])
        if isinstance(item, dict)
    }
    for evidence_id in finding.get("evidence_ids", []):
        evidence = evidence_by_id.get(evidence_id, {})
        result.update(
            _feat_ids(
                evidence_id,
                evidence.get("claim_id"),
                evidence.get("path"),
                evidence.get("description"),
            )
        )
    if not result:
        result.update(_feat_ids(criterion.get("claim_ids", [])))
    return result


def _validate_identity(
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    semantic_result: dict[str, Any],
    score_result: dict[str, Any],
) -> tuple[str, str]:
    for key in ("func_id", "source_revision"):
        values = {
            "static": static_result.get(key),
            "evidence": evidence_manifest.get(key),
            "semantic": semantic_result.get(key),
            "score": score_result.get(key),
        }
        if len(set(values.values())) != 1:
            raise FunctionAnalysisInputError(f"{key} mismatch: {values}")
        if not isinstance(values["static"], str) or not values["static"]:
            raise FunctionAnalysisInputError(f"{key} must be a non-empty string")
    return str(static_result["func_id"]), str(static_result["source_revision"])


def _validate_versions(
    static_result: dict[str, Any], semantic_result: dict[str, Any], score_result: dict[str, Any]
) -> dict[str, str]:
    values = {
        "static_tool_version": static_result.get("tool_version"),
        "static_rule_version": static_result.get("rule_version"),
        "evaluator_protocol_version": semantic_result.get("evaluator_protocol_version"),
        "evaluator_version": semantic_result.get("evaluator_version"),
        "rubric_version": semantic_result.get("rubric_version"),
        "complexity_rules_version": semantic_result.get("complexity_rules_version"),
        "aggregator_protocol_version": score_result.get("aggregator_protocol_version"),
        "aggregator_version": score_result.get("aggregator_version"),
    }
    missing = [key for key, value in values.items() if not isinstance(value, str) or not value]
    if missing:
        raise FunctionAnalysisInputError(f"missing version fields: {', '.join(missing)}")
    for key in ("rubric_version", "complexity_rules_version"):
        if score_result.get(key) != semantic_result.get(key):
            raise FunctionAnalysisInputError(
                f"{key} mismatch: semantic={semantic_result.get(key)!r} "
                f"score={score_result.get(key)!r}"
            )
    return {key: str(value) for key, value in values.items()}


def _validate_artifacts(
    input_artifacts: dict[str, Any], expected_shards: set[str]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ("static_result", "evidence_manifest", "semantic_result"):
        item = input_artifacts.get(key)
        if not isinstance(item, dict):
            raise FunctionAnalysisInputError(f"input_artifacts.{key} must be an object")
        path = item.get("path")
        content_hash = item.get("content_hash")
        if not isinstance(path, str) or not path:
            raise FunctionAnalysisInputError(f"input_artifacts.{key}.path must be non-empty")
        if not isinstance(content_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", content_hash):
            raise FunctionAnalysisInputError(
                f"input_artifacts.{key}.content_hash must be a sha256 digest"
            )
        result[key] = {"path": path, "content_hash": content_hash}
    shard_artifacts = input_artifacts.get("evidence_shards")
    if not isinstance(shard_artifacts, list):
        raise FunctionAnalysisInputError("input_artifacts.evidence_shards must be a list")
    normalized_shards: list[dict[str, str]] = []
    for item in shard_artifacts:
        if not isinstance(item, dict):
            raise FunctionAnalysisInputError("evidence shard artifact must be an object")
        name = item.get("name")
        path = item.get("path")
        content_hash = item.get("content_hash")
        if not isinstance(name, str) or not name:
            raise FunctionAnalysisInputError("evidence shard artifact name must be non-empty")
        if not isinstance(path, str) or not path:
            raise FunctionAnalysisInputError(f"evidence shard artifact {name} path must be non-empty")
        if not isinstance(content_hash, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", content_hash):
            raise FunctionAnalysisInputError(
                f"evidence shard artifact {name} content_hash must be a sha256 digest"
            )
        normalized_shards.append({"name": name, "path": path, "content_hash": content_hash})
    actual_shards = {item["name"] for item in normalized_shards}
    if actual_shards != expected_shards or len(normalized_shards) != len(actual_shards):
        raise FunctionAnalysisInputError(
            f"evidence shard artifact set mismatch: expected={sorted(expected_shards)} "
            f"actual={sorted(actual_shards)}"
        )
    result["evidence_shards"] = sorted(normalized_shards, key=lambda item: item["name"])
    return result


def _validate_shards(
    func_id: str,
    source_revision: str,
    evidence_manifest: dict[str, Any],
    evidence_shards: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    claims_by_feat: dict[str, list[dict[str, Any]]] = {}
    expected_names = {
        item.get("name")
        for item in evidence_manifest.get("shards", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    if expected_names != set(evidence_shards):
        raise FunctionAnalysisInputError(
            f"evidence shard set mismatch: manifest={sorted(expected_names)} "
            f"loaded={sorted(evidence_shards)}"
        )
    total_claims = 0
    resolved_claims = 0
    manifest_by_name = {
        item["name"]: item
        for item in evidence_manifest.get("shards", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    for name in sorted(evidence_shards):
        shard = evidence_shards[name]
        if shard.get("func_id") != func_id:
            raise FunctionAnalysisInputError(f"evidence shard {name} func_id mismatch")
        if shard.get("source_revision") != source_revision:
            raise FunctionAnalysisInputError(f"evidence shard {name} source_revision mismatch")
        claims = shard.get("claims")
        if not isinstance(claims, list):
            raise FunctionAnalysisInputError(f"evidence shard {name}.claims must be a list")
        expected_count = manifest_by_name[name].get("claim_count")
        if isinstance(expected_count, int) and expected_count != len(claims):
            raise FunctionAnalysisInputError(
                f"evidence shard {name} claim_count mismatch: {expected_count} != {len(claims)}"
            )
        for claim in claims:
            if not isinstance(claim, dict):
                raise FunctionAnalysisInputError(f"evidence shard {name} contains a non-object claim")
            status = claim.get("evidence_status")
            if status not in _CLAIM_STATUSES:
                raise FunctionAnalysisInputError(
                    f"evidence shard {name} has invalid evidence_status {status!r}"
                )
            claim_feat_ids = _feat_ids(claim.get("feat_id"), claim.get("claim_id"))
            for feat_id in claim_feat_ids:
                claims_by_feat.setdefault(feat_id, []).append(claim)
            total_claims += 1
            if status == "RESOLVED":
                resolved_claims += 1
    metrics = evidence_manifest.get("metrics", {})
    if metrics.get("claim_count") != total_claims:
        raise FunctionAnalysisInputError(
            f"evidence claim_count mismatch: manifest={metrics.get('claim_count')} loaded={total_claims}"
        )
    if metrics.get("resolved_claim_count") != resolved_claims:
        raise FunctionAnalysisInputError(
            "evidence resolved_claim_count mismatch: "
            f"manifest={metrics.get('resolved_claim_count')} loaded={resolved_claims}"
        )
    return claims_by_feat


def _merge_group_value(group: dict[str, Any], key: str, values: Iterable[str]) -> None:
    group[key].update(value for value in values if isinstance(value, str) and value)


def _remediation_groups(
    static_result: dict[str, Any], semantic_result: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, set[str]], dict[str, tuple[str, set[str]]]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    static_locations: dict[str, set[str]] = {}
    semantic_locations: dict[str, tuple[str, set[str]]] = {}

    for finding in static_result.get("findings", []):
        if not isinstance(finding, dict):
            continue
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str):
            continue
        rule_id = str(finding.get("rule_id", ""))
        recommendation = str(finding.get("recommendation", "")).strip()
        key = ("static", rule_id, recommendation)
        group = groups.setdefault(
            key,
            {
                "source": "static",
                "severity": "Info",
                "message": str(finding.get("message", "")),
                "recommendation": recommendation or f"Resolve active {rule_id} findings.",
                "finding_ids": set(),
                "criterion_ids": set(),
                "rule_ids": set(),
                "feat_ids": set(),
                "claim_ids": set(),
                "evidence_ids": set(),
                "paths": set(),
            },
        )
        severity = str(finding.get("severity", "Info"))
        if _SEVERITY_RANK.get(severity, -1) > _SEVERITY_RANK[group["severity"]]:
            group["severity"] = severity
        feat_ids = _feat_ids(finding.get("feat_id"), finding.get("claim_id"), finding.get("path"))
        _merge_group_value(group, "finding_ids", [finding_id])
        _merge_group_value(group, "rule_ids", [rule_id])
        _merge_group_value(group, "feat_ids", feat_ids)
        _merge_group_value(group, "claim_ids", [finding.get("claim_id")])
        _merge_group_value(group, "paths", [finding.get("path")])
        static_locations[finding_id] = feat_ids

    for criterion, finding in _semantic_findings(semantic_result):
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str):
            continue
        message = str(finding.get("message", ""))
        recommendation = str(finding.get("recommendation", ""))
        key = ("semantic", message, recommendation)
        group = groups.setdefault(
            key,
            {
                "source": "semantic",
                "severity": "Info",
                "message": message,
                "recommendation": recommendation,
                "finding_ids": set(),
                "criterion_ids": set(),
                "rule_ids": set(),
                "feat_ids": set(),
                "claim_ids": set(),
                "evidence_ids": set(),
                "paths": set(),
            },
        )
        severity = str(finding.get("severity", "Info"))
        if _SEVERITY_RANK.get(severity, -1) > _SEVERITY_RANK[group["severity"]]:
            group["severity"] = severity
        feat_ids = _semantic_feat_ids(criterion, finding)
        evidence_ids = finding.get("evidence_ids", [])
        evidence_by_id = {
            item.get("evidence_id"): item
            for item in criterion.get("evidence", [])
            if isinstance(item, dict)
        }
        paths = [
            evidence_by_id[evidence_id].get("path")
            for evidence_id in evidence_ids
            if evidence_id in evidence_by_id
        ]
        claim_ids = [
            claim_id
            for claim_id in criterion.get("claim_ids", [])
            if not feat_ids or bool(_feat_ids(claim_id) & feat_ids)
        ]
        _merge_group_value(group, "finding_ids", [finding_id])
        _merge_group_value(group, "criterion_ids", [finding.get("criterion_id")])
        _merge_group_value(group, "feat_ids", feat_ids)
        _merge_group_value(group, "claim_ids", claim_ids)
        _merge_group_value(group, "evidence_ids", evidence_ids)
        _merge_group_value(group, "paths", paths)
        semantic_locations[finding_id] = (severity, feat_ids)

    serialized: list[dict[str, Any]] = []
    for group in groups.values():
        item = {
            "source": group["source"],
            "priority": _PRIORITY.get(group["severity"], "P2"),
            "severity": group["severity"],
            "message": group["message"],
            "recommendation": group["recommendation"],
        }
        for key in (
            "finding_ids",
            "criterion_ids",
            "rule_ids",
            "feat_ids",
            "claim_ids",
            "evidence_ids",
            "paths",
        ):
            item[key] = sorted(group[key])
        serialized.append(item)
    serialized.sort(
        key=lambda item: (
            -_SEVERITY_RANK.get(item["severity"], -1),
            -len(item["finding_ids"]),
            0 if item["source"] == "semantic" else 1,
            item["recommendation"],
            item["finding_ids"],
        )
    )
    for rank, item in enumerate(serialized[:5], 1):
        item["rank"] = rank
    return serialized[:5], static_locations, semantic_locations


def _feat_risks(
    static_result: dict[str, Any],
    claims_by_feat: dict[str, list[dict[str, Any]]],
    top_remediations: list[dict[str, Any]],
    static_locations: dict[str, set[str]],
    semantic_locations: dict[str, tuple[str, set[str]]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace_by_feat = (
        static_result.get("metrics", {}).get("traceability", {}).get("per_feat", {})
    )
    feature_ids = set(claims_by_feat) | set(trace_by_feat)
    feature_ids.update(feat_id for values in static_locations.values() for feat_id in values)
    feature_ids.update(
        feat_id for _, values in semantic_locations.values() for feat_id in values
    )
    static_by_id = {
        item.get("finding_id"): item
        for item in static_result.get("findings", [])
        if isinstance(item, dict)
    }
    result: list[dict[str, Any]] = []
    for feat_id in sorted(feature_ids):
        counts = _empty_counts()
        static_ids = sorted(
            finding_id for finding_id, values in static_locations.items() if feat_id in values
        )
        semantic_ids = sorted(
            finding_id for finding_id, (_, values) in semantic_locations.items() if feat_id in values
        )
        for finding_id in static_ids:
            severity = static_by_id.get(finding_id, {}).get("severity")
            if severity in counts:
                counts[severity] += 1
        for finding_id in semantic_ids:
            severity = semantic_locations[finding_id][0]
            if severity in counts:
                counts[severity] += 1
        active = [severity for severity in _SEVERITIES if counts[severity]]
        claims = claims_by_feat.get(feat_id, [])
        claim_counts = Counter(item.get("evidence_status") for item in claims)
        total_claims = len(claims)
        trace = trace_by_feat.get(feat_id, {})
        result.append(
            {
                "feat_id": feat_id,
                "risk_level": active[0] if active else "None",
                "finding_counts": counts,
                "static_finding_ids": static_ids,
                "semantic_finding_ids": semantic_ids,
                "claims": {
                    "total": total_claims,
                    "resolved": claim_counts["RESOLVED"],
                    "partially_resolved": claim_counts["PARTIALLY_RESOLVED"],
                    "unresolved": claim_counts["UNRESOLVED"],
                    "no_evidence": claim_counts["NO_EVIDENCE"],
                    "support_rate": _rounded_ratio(claim_counts["RESOLVED"], total_claims),
                },
                "traceability": {
                    "ac_count": int(trace.get("ac_count", 0)),
                    "closed_ac_count": int(trace.get("closed_ac_count", 0)),
                    "closure_rate": trace.get("closure_rate", 0),
                },
                "top_remediation_ranks": [
                    item["rank"]
                    for item in top_remediations
                    if feat_id in item["feat_ids"]
                ],
            }
        )
    shared_static = sorted(
        finding_id for finding_id, values in static_locations.items() if not values
    )
    shared_semantic = sorted(
        finding_id for finding_id, (_, values) in semantic_locations.items() if not values
    )
    shared_counts = _empty_counts()
    for finding_id in shared_static:
        severity = static_by_id.get(finding_id, {}).get("severity")
        if severity in shared_counts:
            shared_counts[severity] += 1
    for finding_id in shared_semantic:
        severity = semantic_locations[finding_id][0]
        if severity in shared_counts:
            shared_counts[severity] += 1
    shared_active = [severity for severity in _SEVERITIES if shared_counts[severity]]
    return result, {
        "risk_level": shared_active[0] if shared_active else "None",
        "finding_counts": shared_counts,
        "static_finding_ids": shared_static,
        "semantic_finding_ids": shared_semantic,
        "finding_count": len(shared_static) + len(shared_semantic),
        "top_remediation_ranks": [
            item["rank"] for item in top_remediations if not item["feat_ids"]
        ],
    }


def build_function_analysis(
    *,
    static_result: dict[str, Any],
    evidence_manifest: dict[str, Any],
    evidence_shards: dict[str, dict[str, Any]],
    semantic_result: dict[str, Any],
    score_result: dict[str, Any],
    input_artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic companion analysis without changing the frozen score protocol."""

    func_id, source_revision = _validate_identity(
        static_result, evidence_manifest, semantic_result, score_result
    )
    versions = _validate_versions(static_result, semantic_result, score_result)
    artifacts = _validate_artifacts(input_artifacts, set(evidence_shards))
    claims_by_feat = _validate_shards(
        func_id, source_revision, evidence_manifest, evidence_shards
    )
    top_remediations, static_locations, semantic_locations = _remediation_groups(
        static_result, semantic_result
    )
    feat_risks, function_shared = _feat_risks(
        static_result,
        claims_by_feat,
        top_remediations,
        static_locations,
        semantic_locations,
    )
    return {
        "schema_version": FUNCTION_ANALYSIS_SCHEMA_VERSION,
        "analysis_version": FUNCTION_ANALYSIS_VERSION,
        "func_id": func_id,
        "source_revision": source_revision,
        "versions": versions,
        "input_artifacts": artifacts,
        "score_summary": {
            "raw_score": score_result.get("raw_score"),
            "published_score": score_result.get("published_score"),
            "confidence": score_result.get("confidence", {}).get("score"),
            "gate": score_result.get("gate", {}).get("effective"),
            "admission": score_result.get("admission", {}).get("status"),
        },
        "top_remediations": top_remediations,
        "feat_risks": feat_risks,
        "function_shared_risk": function_shared,
    }


def _load_evidence_shards(
    evidence_manifest_path: Path, evidence_manifest: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    result: dict[str, dict[str, Any]] = {}
    artifacts: list[dict[str, str]] = []
    evidence_root = evidence_manifest_path.parent / "evidence"
    for item in evidence_manifest.get("shards", []):
        if not isinstance(item, dict):
            raise FunctionAnalysisInputError("evidence manifest contains a non-object shard")
        name = item.get("name")
        relative = item.get("path")
        if not isinstance(name, str) or not name:
            raise FunctionAnalysisInputError("evidence shard name must be non-empty")
        if not isinstance(relative, str) or not relative:
            raise FunctionAnalysisInputError(f"evidence shard {name} path must be non-empty")
        relative_path = Path(relative)
        if relative_path.is_absolute() or relative_path.name != relative or ".." in relative_path.parts:
            raise FunctionAnalysisInputError(f"unsafe evidence shard path: {relative}")
        shard_path = evidence_root / relative_path
        result[name] = _load_json_object(shard_path)
        artifacts.append(
            {
                "name": name,
                "path": shard_path.as_posix(),
                "content_hash": _hash_file(shard_path),
            }
        )
    return result, artifacts


def build_function_analysis_from_paths(
    *,
    static_result_path: Path,
    evidence_manifest_path: Path,
    semantic_result_path: Path,
    score_result: dict[str, Any],
) -> dict[str, Any]:
    static_result = _load_json_object(static_result_path)
    evidence_manifest = _load_json_object(evidence_manifest_path)
    semantic_result = _load_json_object(semantic_result_path)
    evidence_shards, shard_artifacts = _load_evidence_shards(
        evidence_manifest_path, evidence_manifest
    )
    artifacts = {
        "static_result": {
            "path": static_result_path.as_posix(),
            "content_hash": _hash_file(static_result_path),
        },
        "evidence_manifest": {
            "path": evidence_manifest_path.as_posix(),
            "content_hash": _hash_file(evidence_manifest_path),
        },
        "semantic_result": {
            "path": semantic_result_path.as_posix(),
            "content_hash": _hash_file(semantic_result_path),
        },
        "evidence_shards": shard_artifacts,
    }
    return build_function_analysis(
        static_result=static_result,
        evidence_manifest=evidence_manifest,
        evidence_shards=evidence_shards,
        semantic_result=semantic_result,
        score_result=score_result,
        input_artifacts=artifacts,
    )


def write_function_analysis(path: Path, analysis: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
