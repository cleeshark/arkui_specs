"""Deterministic report stage (TASK-011-07): score / stability / report.

Given validated ``semantic-result.json`` files (one per run) plus the frozen
evidence package, this stage runs the existing, deterministic ``spec_eval``
subcommands. It contains no model judgment: identical inputs always produce
identical bytes. Outputs land in the job-level ``aggregate/`` directory.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ._subprocess import Runner, default_runner, write_logs
from .context import RunContext


class ReportStageError(RuntimeError):
    """Raised when a deterministic score/stability/report command fails."""


def run_report(
    ctx: RunContext,
    *,
    semantic_results: dict[str, Path],
    selected_run_id: str,
    runner: Runner = default_runner,
    timeout: float = 600.0,
) -> dict[str, Path]:
    """Run score + stability + report. Returns the produced artifact paths."""
    if selected_run_id not in semantic_results:
        raise ReportStageError(
            f"selected run {selected_run_id!r} not in semantic_results {list(semantic_results)}"
        )
    ctx.aggregate_dir.mkdir(parents=True, exist_ok=True)
    static = ctx.input_dir / "static-result.json"
    evidence = ctx.input_dir / "evidence-manifest.json"
    selected_sr = semantic_results[selected_run_id]
    score_path = ctx.aggregate_dir / "score-result.json"
    analysis_path = ctx.aggregate_dir / "function-analysis.json"
    stability_path = ctx.aggregate_dir / "stability-result.json"
    report_json = ctx.aggregate_dir / "evaluation-report.json"
    report_md = ctx.aggregate_dir / "function-report.md"
    log_dir = ctx.job_root / "logs"

    _score(ctx, runner, log_dir, static, evidence, selected_sr, score_path, analysis_path, timeout)
    _stability(ctx, runner, log_dir, static, evidence, semantic_results, selected_run_id, stability_path, timeout)
    _report(ctx, runner, log_dir, static, selected_sr, score_path, analysis_path, stability_path, report_json, report_md, timeout)

    for name, path in (
        ("score", score_path), ("analysis", analysis_path), ("stability", stability_path),
        ("report_json", report_json), ("report_md", report_md),
    ):
        if not path.is_file():
            raise ReportStageError(f"{name} output missing after report stage: {path}")

    return {
        "score": score_path,
        "analysis": analysis_path,
        "stability": stability_path,
        "report_json": report_json,
        "report_md": report_md,
    }


def _score(ctx, runner, log_dir, static, evidence, semantic_result, score_path, analysis_path, timeout):
    argv = [
        "python3", str(ctx.cli_path), "score",
        "--static-result", str(static),
        "--evidence-manifest", str(evidence),
        "--semantic-result", str(semantic_result),
        "--write", str(score_path),
        "--analysis-write", str(analysis_path),
    ]
    _run(ctx, runner, log_dir, "score", argv, timeout)


def _stability(ctx, runner, log_dir, static, evidence, semantic_results, selected_run_id, stability_path, timeout):
    argv = [
        "python3", str(ctx.cli_path), "stability",
        "--static-result", str(static),
        "--evidence-manifest", str(evidence),
        "--selected-run-id", selected_run_id,
        "--write", str(stability_path),
    ]
    for sr in semantic_results.values():
        argv += ["--semantic-result", str(sr)]
    _run(ctx, runner, log_dir, "stability", argv, timeout)


def _report(ctx, runner, log_dir, static, semantic_result, score_path, analysis_path, stability_path, report_json, report_md, timeout):
    argv = [
        "python3", str(ctx.cli_path), "report",
        "--static-result", str(static),
        "--semantic-result", str(semantic_result),
        "--score-result", str(score_path),
        "--analysis-result", str(analysis_path),
        "--stability-result", str(stability_path),
        "--json-write", str(report_json),
        "--markdown-write", str(report_md),
    ]
    _run(ctx, runner, log_dir, "report", argv, timeout)


def _run(ctx, runner, log_dir, name, argv, timeout):
    try:
        cp = runner(argv, cwd=str(ctx.repo_root), timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ReportStageError(f"{name} timed out after {timeout:.0f}s") from exc
    write_logs(log_dir / f"{name}.stdout.log", log_dir / f"{name}.stderr.log", cp)
    # rc 1 from score/report means the *effective gate* is "fail" — the outputs
    # are still written and the job must continue to archive them. rc 2 is a
    # SpecEvalError, rc 3 is gate "error"; both abort. Output existence is
    # verified by the caller (run_report).
    if cp.returncode not in (0, 1):
        tail = (cp.stderr or "").strip().splitlines()[-4:] or (cp.stdout or "").strip().splitlines()[-4:]
        raise ReportStageError(f"{name} exited {cp.returncode}: {' | '.join(tail) or 'see logs'}")
