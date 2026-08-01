"""Render a stable human-readable Function static report."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from spec_eval.models import EvaluationRun


class MarkdownReporter:
    def write(self, run: EvaluationRun, target: Path) -> Path:
        path = target / "report.md"
        findings = sorted(
            run.static_result.findings,
            key=lambda item: (-int(item.severity), item.rule_id, item.path, item.line or 0),
        )
        per_feat = Counter(item.feat_id or "design/function" for item in findings)
        lines = [
            f"# Function {run.context.func_id} 静态评价报告",
            "",
            f"- Gate: **{run.static_result.gate.upper()}**",
            f"- Source revision: `{run.context.source_revision}`",
            f"- Tool/Rule: `{run.context.tool_version}` / `{run.context.rule_version}`",
            f"- Feature 数: {len(run.context.feature_specs)}",
            f"- Finding 数: {len(findings)}",
            f"- Claim 数: {run.evidence.metrics.get('claim_count', 0)}",
            f"- Evidence coverage: {run.evidence.metrics.get('evidence_coverage', 0):.2%}",
            "",
            "## 严重度统计",
            "",
            "| Severity | Count |",
            "|---|---:|",
        ]
        for label in ("Critical", "Major", "Minor", "Info"):
            lines.append(f"| {label} | {run.static_result.metrics.get('severity_counts', {}).get(label, 0)} |")
        lines.extend(["", "## Feat/Design 分布", "", "| Scope | Findings |", "|---|---:|"])
        for scope, count in sorted(per_feat.items()):
            lines.append(f"| {scope} | {count} |")
        lines.extend(["", "## Findings", ""])
        if not findings:
            lines.append("无确定性问题。")
        for finding in findings:
            location = f"{finding.path}:{finding.line}" if finding.line else finding.path
            lines.extend(
                [
                    f"### {finding.severity.label()} · {finding.rule_id}",
                    "",
                    f"- 位置：`{location}`",
                    f"- 问题：{finding.message}",
                ]
            )
            if finding.recommendation:
                lines.append(f"- 建议：{finding.recommendation}")
            lines.append("")
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return path

