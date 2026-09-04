"""Shared converters for the semantic site archive.

These helpers turn a semantic evaluation body (a Review's ``semantic_result`` or
an automated report's ``semantic`` block) and a static result into the compact
Finding/criterion shapes the site consumes. They are reused by the automated
publish path (``spec_eval.service.site_export``) and by
``tools/generate_site.py``; the former reviews-based ``site-evaluation`` export
has been retired in favour of publishing directly from real CI runtime archives.
"""

from __future__ import annotations

from typing import Any

from spec_eval.models.finding import enrich_finding_identity


SITE_EVALUATION_SCHEMA_VERSION = 1
SEVERITIES = ("Critical", "Major", "Minor", "Info")
SEVERITY_RANK = {value: len(SEVERITIES) - index for index, value in enumerate(SEVERITIES)}


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
