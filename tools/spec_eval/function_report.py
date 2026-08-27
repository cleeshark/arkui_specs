"""Assemble the frozen Function evaluation JSON and a human-readable companion report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from spec_eval.protocol_validator import validate_evaluation_report, validate_protocol, raise_for_errors


REPORT_VERSION = "spec-eval-function-report@0.1.0"

# Evidence type mismatch is a bounded data-quality gap that score/assemble stages
# already degrade to a confidence warning. Filter it here so report assembly does
# not re-block a report that passed score with reduced confidence.
EVIDENCE_TYPE_WARNING_MARKER = "evidence must include one of"


class FunctionReportInputError(ValueError):
    """Raised when report inputs are incomplete or refer to different artifacts."""


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FunctionReportInputError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FunctionReportInputError(f"{label} must be a JSON object: {path}")
    return value


def _identity(documents: dict[str, dict[str, Any]]) -> tuple[str, str]:
    values = {
        key: {label: document.get(key) for label, document in documents.items()}
        for key in ("func_id", "source_revision")
    }
    for key, items in values.items():
        if len(set(items.values())) != 1:
            raise FunctionReportInputError(f"{key} mismatch: {items}")
        value = next(iter(items.values()))
        if not isinstance(value, str) or not value:
            raise FunctionReportInputError(f"{key} must be a non-empty string")
    return str(next(iter(values["func_id"].values()))), str(next(iter(values["source_revision"].values())))


def _validate_companions(
    score: dict[str, Any], analysis: dict[str, Any], stability: dict[str, Any], semantic: dict[str, Any]
) -> None:
    for label, document in (("analysis", analysis), ("stability", stability)):
        if document.get("func_id") != score.get("func_id"):
            raise FunctionReportInputError(f"{label}.func_id mismatch")
        if document.get("source_revision") != score.get("source_revision"):
            raise FunctionReportInputError(f"{label}.source_revision mismatch")
    selected = stability.get("selected_run", {})
    selected_run_id = selected.get("run_id")
    if selected_run_id != semantic.get("run_id"):
        raise FunctionReportInputError(
            "selected semantic run must match stability.selected_run.run_id: "
            f"{semantic.get('run_id')!r} != {selected_run_id!r}"
        )
    score_summary = analysis.get("score_summary", {})
    expected = {
        "raw_score": score.get("raw_score"),
        "published_score": score.get("published_score"),
        "confidence": score.get("confidence", {}).get("score"),
        "gate": score.get("gate", {}).get("effective"),
        "admission": score.get("admission", {}).get("status"),
    }
    if score_summary != expected:
        raise FunctionReportInputError("analysis.score_summary must mirror score-result")
    versions = analysis.get("versions", {})
    expected_versions = {
        "rubric_version": semantic.get("rubric_version"),
        "complexity_rules_version": semantic.get("complexity_rules_version"),
        "evaluator_protocol_version": semantic.get("evaluator_protocol_version"),
        "evaluator_version": semantic.get("evaluator_version"),
        "aggregator_protocol_version": score.get("aggregator_protocol_version"),
        "aggregator_version": score.get("aggregator_version"),
    }
    for key, value in expected_versions.items():
        if versions.get(key) != value:
            raise FunctionReportInputError(f"analysis.versions.{key} mismatch")


def build_function_report(
    *,
    static_result: dict[str, Any],
    semantic_result: dict[str, Any],
    score_result: dict[str, Any],
    analysis_result: dict[str, Any],
    stability_result: dict[str, Any],
    rubric: dict[str, Any],
    complexity_rules: dict[str, Any],
    schemas_root: Path,
) -> tuple[dict[str, Any], str]:
    """Return a schema-valid core JSON report and deterministic Markdown companion."""

    func_id, source_revision = _identity(
        {"static": static_result, "semantic": semantic_result, "score": score_result}
    )
    _validate_companions(score_result, analysis_result, stability_result, semantic_result)
    report = {
        "schema_version": 1,
        "func_id": func_id,
        "source_revision": source_revision,
        "protocol": {
            "rubric_version": semantic_result["rubric_version"],
            "complexity_rules_version": semantic_result["complexity_rules_version"],
            "evaluator_protocol_version": semantic_result["evaluator_protocol_version"],
            "aggregator_protocol_version": score_result["aggregator_protocol_version"],
        },
        "static": static_result,
        "semantic": semantic_result,
        "score": score_result,
        "summary": {
            "gate": score_result["gate"]["effective"],
            "raw_score": score_result["raw_score"],
            "published_score": score_result["published_score"],
            "confidence": score_result["confidence"]["score"],
            "admission_status": score_result["admission"]["status"],
        },
    }
    errors = validate_evaluation_report(report, rubric, complexity_rules, schemas_root)
    # Filter evidence type warnings that score/assemble stages already degraded
    blocking = [e for e in errors if EVIDENCE_TYPE_WARNING_MARKER not in e]
    raise_for_errors(blocking)
    return report, render_markdown_report(
        report=report, analysis=analysis_result, stability=stability_result
    )


def render_markdown_report(
    *, report: dict[str, Any], analysis: dict[str, Any], stability: dict[str, Any]
) -> str:
    score = report["score"]
    summary = report["summary"]
    lines = [
        f"# Function Evaluation Report: {report['func_id']}",
        "",
        f"- Source revision: `{report['source_revision']}`",
        f"- Report generator: `{REPORT_VERSION}`",
        f"- Gate: **{summary['gate']}**",
        f"- Score: **{summary['published_score']} / 100** (raw {summary['raw_score']})",
        f"- Confidence: **{summary['confidence']}**",
        f"- Admission: **{summary['admission_status']}**",
        "",
        "## Dimension scores",
        "",
        "| Dimension | Score | Applicable max | Verifiability |",
        "| --- | ---: | ---: | --- |",
    ]
    for dimension in score["dimensions"]:
        lines.append(
            f"| `{dimension['dimension_id']}` | {dimension['score']} / {dimension['max_score']} "
            f"| {dimension['applicable_max_score']} | {dimension['verifiability']} |"
        )
    lines.extend(["", "## Selected semantic run", "", f"- Run ID: `{report['semantic']['run_id']}`"])
    lines.append(f"- Evaluator: `{report['semantic']['evaluator_version']}`")
    lines.append(
        "- Selection is explicit; stability consensus is informational and does not rewrite the formal score."
    )
    lines.extend(["", "## Top remediation items", "", "| Rank | Priority | Severity | Recommendation | Feats | Findings |", "| ---: | --- | --- | --- | --- | ---: |"])
    for item in analysis.get("top_remediations", [])[:5]:
        feats = ", ".join(item.get("feat_ids", [])) or "Function-shared"
        recommendation = str(item.get("recommendation", "")).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {item.get('rank', '')} | {item.get('priority', '')} | {item.get('severity', '')} "
            f"| {recommendation} | {feats} | {len(item.get('finding_ids', []))} |"
        )
    lines.extend(["", "## Feat risk distribution", "", "| Feat | Risk | Critical | Major | Minor | Claims support | AC closure |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"])
    for item in analysis.get("feat_risks", []):
        counts = item.get("finding_counts", {})
        claims = item.get("claims", {})
        trace = item.get("traceability", {})
        lines.append(
            f"| `{item['feat_id']}` | {item.get('risk_level', 'None')} | {counts.get('Critical', 0)} "
            f"| {counts.get('Major', 0)} | {counts.get('Minor', 0)} | {claims.get('support_rate', 0)} "
            f"| {trace.get('closure_rate', 0)} |"
        )
    shared = analysis.get("function_shared_risk", {})
    lines.extend(["", "### Function-shared risk", "", f"- Risk level: **{shared.get('risk_level', 'None')}**", f"- Findings: {shared.get('finding_count', 0)}"])
    if stability.get("status") == "insufficient_runs":
        lines.extend([
            "",
            "## Stability",
            "",
            "- Status: **N/A — insufficient runs**",
            f"- Runs provided: {stability.get('provided_run_count', 0)}",
            f"- Runs required: {stability.get('required_run_count', 0)}",
            "- Raw score range: N/A",
            "- Population standard deviation: N/A",
            "- Criterion consensus: N/A",
            "- Outlier runs: N/A",
        ])
    else:
        lines.extend([
            "",
            "## Stability",
            "",
            f"- Runs: {stability.get('score_statistics', {}).get('count', 0)}",
            f"- Raw score range: {stability.get('score_statistics', {}).get('range', 0)}",
            "- Population standard deviation: "
            f"{stability.get('score_statistics', {}).get('population_stddev', 0)}",
            "- Criterion consensus: "
            f"{stability.get('consensus_summary', {}).get('consensus_count', 0)}/"
            f"{stability.get('consensus_summary', {}).get('criterion_count', 0)}",
            f"- Outlier runs: {', '.join(stability.get('outlier_run_ids', [])) or 'none'}",
        ])
    lines.extend(["", "## Protocol and traceability", "", f"- Rubric: `{report['protocol']['rubric_version']}`", f"- Complexity rules: `{report['protocol']['complexity_rules_version']}`", f"- Aggregator: `{score['aggregator_version']}`"])
    lines.append("- Machine-readable analysis and stability inputs remain companion artifacts; they are intentionally outside the frozen JSON report schema.")
    return "\n".join(lines) + "\n"


def build_function_report_from_paths(
    *,
    static_result_path: Path,
    semantic_result_path: Path,
    score_result_path: Path,
    analysis_result_path: Path,
    stability_result_path: Path,
    evaluation_root: Path,
) -> tuple[dict[str, Any], str]:
    rubric, complexity, errors = validate_protocol(evaluation_root)
    raise_for_errors(errors)
    static = _load(static_result_path, "static-result.json")
    semantic = _load(semantic_result_path, "semantic-result.json")
    score = _load(score_result_path, "score-result.json")
    analysis = _load(analysis_result_path, "function-analysis.json")
    stability = _load(stability_result_path, "stability-result.json")
    return build_function_report(
        static_result=static,
        semantic_result=semantic,
        score_result=score,
        analysis_result=analysis,
        stability_result=stability,
        rubric=rubric,
        complexity_rules=complexity,
        schemas_root=evaluation_root / "schemas",
    )


def write_function_report(
    *, json_path: Path, markdown_path: Path, report: dict[str, Any], markdown: str
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
