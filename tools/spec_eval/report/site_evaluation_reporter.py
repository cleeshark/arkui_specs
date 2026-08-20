"""Build the compact, confirmed-review-only semantic site archive."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from spec_eval.models.finding import enrich_finding_identity
from spec_eval.protocol_validator import JsonSchemaSubsetValidator


SITE_EVALUATION_SCHEMA_VERSION = 1
SITE_EVALUATION_VERSION = "spec-eval-site-evaluation@0.2.0"
SEVERITIES = ("Critical", "Major", "Minor", "Info")
SEVERITY_RANK = {value: len(SEVERITIES) - index for index, value in enumerate(SEVERITIES)}


class SiteEvaluationInputError(ValueError):
    """Raised when confirmed reviews cannot be safely joined to static results."""


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SiteEvaluationInputError(f"cannot read review {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SiteEvaluationInputError(f"review must be a YAML object: {path}")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SiteEvaluationInputError(f"cannot read site report {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SiteEvaluationInputError(f"site report must be a JSON object: {path}")
    return value


def compact_finding(finding: dict[str, Any], *, source: str) -> dict[str, Any]:
    fields = (
        "finding_id", "criterion_id", "rule_id", "severity", "conclusion", "message",
        "recommendation", "path", "line", "feat_id", "claim_id", "evidence_ids",
    )
    result = {key: finding[key] for key in fields if finding.get(key) not in (None, "", [])}
    result["source"] = source
    return result


def semantic_data(review: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    semantic = review.get("semantic_result", {})
    criteria: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    evidence_paths: set[str] = set()
    for item in semantic.get("criterion_results", []):
        if not isinstance(item, dict):
            continue
        item_findings = [
            compact_finding(finding, source="semantic")
            for finding in item.get("findings", [])
            if isinstance(finding, dict)
        ]
        findings.extend(item_findings)
        evidence = item.get("evidence", [])
        compact_evidence = []
        for value in evidence:
            if not isinstance(value, dict):
                continue
            if isinstance(value.get("path"), str):
                evidence_paths.add(value["path"])
            compact_evidence.append({
                key: value[key]
                for key in ("evidence_id", "type", "path", "line_start", "line_end", "description")
                if value.get(key) not in (None, "")
            })
        criterion = {
            "criterion_id": item.get("criterion_id"),
            "dimension_id": item.get("dimension_id"),
            "conclusion": item.get("conclusion"),
            "reason": item.get("reason", ""),
            "finding_ids": sorted(
                finding.get("finding_id") for finding in item_findings
                if isinstance(finding.get("finding_id"), str)
            ),
            "findings": item_findings,
            "evidence": compact_evidence,
        }
        criteria.append(criterion)
    return criteria, findings, sorted(evidence_paths)


def static_data(static: dict[str, Any], *, func_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    findings = [
        compact_finding(enrich_finding_identity(finding, default_func_id=func_id), source="static")
        for finding in static.get("findings", [])
        if isinstance(finding, dict)
    ]
    paths = sorted({finding["path"] for finding in findings if isinstance(finding.get("path"), str)})
    return findings, paths


def recommendations(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for finding in findings:
        recommendation = finding.get("recommendation")
        if not recommendation:
            continue
        result.append({
            "finding_id": finding.get("finding_id"),
            "source": finding.get("source"),
            "severity": finding.get("severity", "Info"),
            "recommendation": recommendation,
            "feat_id": finding.get("feat_id"),
        })
    return sorted(
        result,
        key=lambda item: (
            -SEVERITY_RANK.get(item["severity"], 0),
            str(item.get("finding_id", "")),
        ),
    )


def _function_entry(
    review: dict[str, Any], static: dict[str, Any] | None, site_revision: str, static_report_name: str
) -> dict[str, Any]:
    func_id = str(review.get("func_id", ""))
    review_revision = str(review.get("source_revision", ""))
    criteria, semantic_findings, semantic_paths = semantic_data(review)
    static_findings, static_paths = static_data(static or {}, func_id=func_id)
    all_findings = static_findings + semantic_findings
    confirmation = review.get("confirmation", {})
    status = "CONFIRMED" if review_revision == site_revision and static is not None else "EXPIRED"
    entry = {
        "func_id": func_id,
        "title": str((static or {}).get("title", "")),
        "source_revision": review_revision,
        "status": status,
        "scores": review.get("scores", {}),
        "criterion_summaries": sorted(criteria, key=lambda item: str(item.get("criterion_id", ""))),
        "findings": all_findings,
        "recommendations": recommendations(all_findings),
        "evidence_paths": sorted(set(semantic_paths + static_paths)),
        "confirmation": {
            "confirmed_by": confirmation.get("confirmed_by", ""),
            "confirmed_at": confirmation.get("confirmed_at", ""),
            "conclusion": confirmation.get("conclusion", ""),
            "notes": confirmation.get("notes", []),
        },
        "static_report_reference": {
            "path": static_report_name,
            "func_id": func_id,
            "source_revision": site_revision,
            "available": static is not None,
            "gate": (static or {}).get("gate", "error"),
            "finding_count": len(static_findings),
        },
    }
    if status == "EXPIRED":
        entry["staleness"] = {
            "reason": "review_source_revision_mismatch" if review_revision != site_revision else "static_function_missing",
            "review_source_revision": review_revision,
            "static_source_revision": site_revision,
        }
    return entry


def build_site_evaluation_report(
    *, reviews_root: Path, site_report: dict[str, Any], static_report_name: str = "site-report.json"
) -> dict[str, Any]:
    """Export confirmed Review records without scanning source or SDK repositories."""

    site_revision = site_report.get("sourceRevision")
    if not isinstance(site_revision, str) or not site_revision:
        raise SiteEvaluationInputError("site report sourceRevision must be non-empty")
    function_values = site_report.get("functions", [])
    if not isinstance(function_values, list):
        raise SiteEvaluationInputError("site report functions must be a list")
    static_by_id = {
        str(item.get("funcId")): item for item in function_values if isinstance(item, dict) and item.get("funcId")
    }
    reviews: list[dict[str, Any]] = []
    review_func_ids: set[str] = set()
    for path in sorted(reviews_root.glob("*.yaml")):
        review = _load_yaml(path)
        if review.get("status") != "confirmed":
            continue
        if not isinstance(review.get("func_id"), str) or not review["func_id"]:
            raise SiteEvaluationInputError(f"confirmed review missing func_id: {path}")
        if not isinstance(review.get("source_revision"), str) or not review["source_revision"]:
            raise SiteEvaluationInputError(f"confirmed review missing source_revision: {path}")
        if review["func_id"] in review_func_ids:
            raise SiteEvaluationInputError(f"duplicate confirmed review func_id: {review['func_id']}")
        review_func_ids.add(review["func_id"])
        reviews.append(review)
    entries = [
        _function_entry(review, static_by_id.get(review["func_id"]), site_revision, static_report_name)
        for review in sorted(reviews, key=lambda item: item["func_id"])
    ]
    counts = Counter(item["status"] for item in entries)
    return {
        "schemaVersion": SITE_EVALUATION_SCHEMA_VERSION,
        "reportVersion": SITE_EVALUATION_VERSION,
        "available": True,
        "sourceRevision": site_revision,
        "staticReport": {
            "path": static_report_name,
            "sourceRevision": site_revision,
        },
        "summary": {
            "confirmedFunctionCount": counts["CONFIRMED"],
            "expiredFunctionCount": counts["EXPIRED"],
            "functionCount": len(entries),
            "findingCount": sum(len(item["findings"]) for item in entries if item["status"] == "CONFIRMED"),
            "expiredFindingCount": sum(len(item["findings"]) for item in entries if item["status"] == "EXPIRED"),
        },
        "functions": entries,
    }


def validate_site_evaluation_report(instance: dict[str, Any], schemas_root: Path) -> list[str]:
    return JsonSchemaSubsetValidator(schemas_root).validate_file(
        instance, schemas_root / "site-evaluation-report.schema.json"
    )


def build_site_evaluation_report_from_paths(
    *, reviews_root: Path, site_report_path: Path, schemas_root: Path
) -> dict[str, Any]:
    site_report = _load_json(site_report_path)
    result = build_site_evaluation_report(
        reviews_root=reviews_root,
        site_report=site_report,
        static_report_name=site_report_path.name,
    )
    errors = validate_site_evaluation_report(result, schemas_root)
    if errors:
        raise SiteEvaluationInputError("generated site-evaluation-report is invalid:\n" + "\n".join(errors))
    return result


def write_site_evaluation_report(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
