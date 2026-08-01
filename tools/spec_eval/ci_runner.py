#!/usr/bin/env python3
"""CI entry point for changed-Function report-only or enforcing evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_eval.config import EvaluationConfig
from spec_eval.discovery import ChangedFunctionResolver
from spec_eval.errors import SpecEvalError
from spec_eval.orchestrator import EvaluationOrchestrator


EXIT_OK = 0
EXIT_GATE_FAILED = 1
EXIT_TOOL_ERROR = 2
EXIT_INCOMPLETE = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate all complete Functions affected by a CI change")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--files-from", type=Path, help="newline-delimited changed file list")
    source.add_argument("--base", help="Git base revision used with --head")
    parser.add_argument("--head", default="HEAD", help="Git head revision; defaults to HEAD")
    parser.add_argument("--output", type=Path, help="artifact root; defaults to out/spec-evaluation")
    parser.add_argument("--enforce", action="store_true", help="return 1 when a Function quality gate fails")
    parser.add_argument("--no-cache", action="store_true", help="disable exact-input evaluator cache")
    parser.add_argument("--top", type=int, default=5, help="maximum findings shown per Function in the summary")
    parser.add_argument("--json", action="store_true", help="print the CI summary as JSON")
    parser.add_argument("--quiet", action="store_true", help="suppress human-readable output")
    return parser


def _changed_files(args: argparse.Namespace, config: EvaluationConfig) -> list[str]:
    if args.files_from is not None:
        if not args.files_from.is_file():
            raise OSError(f"changed-file list does not exist: {args.files_from}")
        values = args.files_from.read_text(encoding="utf-8").splitlines()
    else:
        result = subprocess.run(
            ["git", "diff", "--name-only", args.base, args.head, "--"],
            cwd=config.repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "git diff failed"
            raise OSError(message)
        values = result.stdout.splitlines()
    return sorted({value.strip() for value in values if value.strip()})


def _finding_sort_key(finding: dict[str, Any]) -> tuple[int, str, str, int, str]:
    rank = {"Critical": 0, "Major": 1, "Minor": 2, "Info": 3}
    return (
        rank.get(str(finding.get("severity", "Info")), 4),
        str(finding.get("rule_id", "")),
        str(finding.get("path", "")),
        int(finding.get("line", 0) or 0),
        str(finding.get("message", "")),
    )


def _function_summary(func_id: str, result: dict[str, Any], cached: bool, target: Path, top: int) -> dict[str, Any]:
    static = result["static"]
    metrics = static.get("metrics", {})
    findings = sorted(static.get("findings", []), key=_finding_sort_key)
    return {
        "func_id": func_id,
        "gate": static.get("gate", "error"),
        "cached": cached,
        "feature_count": metrics.get("feature_count", 0),
        "document_count": metrics.get("document_count", 0),
        "finding_count": len(findings),
        "severity_counts": metrics.get("severity_counts", {}),
        "top_findings": findings[: max(top, 0)],
        "output_path": target.as_posix(),
    }


def run(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    config = EvaluationConfig.discover(output_root=args.output)
    changed_files = _changed_files(args, config)
    orchestrator = EvaluationOrchestrator(config)
    contexts = ChangedFunctionResolver(orchestrator.locator).resolve(changed_files)
    functions: list[dict[str, Any]] = []
    has_gate_failure = False
    has_evaluation_error = False

    for context in contexts:
        try:
            result, cached, target = orchestrator.evaluate_and_write(
                context.func_id,
                config.output_root,
                use_cache=not args.no_cache,
            )
            item = _function_summary(context.func_id, result, cached, target, args.top)
            functions.append(item)
            has_gate_failure = has_gate_failure or item["gate"] == "fail"
        except Exception as error:  # preserve results for every other affected Function
            has_evaluation_error = True
            functions.append({"func_id": context.func_id, "gate": "error", "error": str(error)})

    functions.sort(key=lambda item: str(item.get("func_id", "")))
    summary: dict[str, Any] = {
        "mode": "enforce" if args.enforce else "report-only",
        "source_revision": config.git_revision(),
        "changed_files": changed_files,
        "affected_function_count": len(functions),
        "gate_failed_count": sum(1 for item in functions if item.get("gate") == "fail"),
        "error_count": sum(1 for item in functions if item.get("gate") == "error"),
        "functions": functions,
    }
    revision_root = config.output_root / summary["source_revision"]
    revision_root.mkdir(parents=True, exist_ok=True)
    summary_path = revision_root / "ci-summary.json"
    summary["summary_path"] = summary_path.as_posix()
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if has_evaluation_error:
        return summary, EXIT_INCOMPLETE
    if args.enforce and has_gate_failure:
        return summary, EXIT_GATE_FAILED
    return summary, EXIT_OK


def _emit(summary: dict[str, Any], args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if args.quiet:
        return
    print(
        f"spec-eval CI {summary['mode']}: "
        f"{summary['affected_function_count']} Function(s), "
        f"{summary['gate_failed_count']} gate failure(s), "
        f"{summary['error_count']} error(s)"
    )
    for item in summary["functions"]:
        print(f"{item['func_id']}: {item['gate']} ({item.get('finding_count', 0)} findings)")
    print(f"summary: {summary['summary_path']}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary, exit_code = run(args)
    except (OSError, SpecEvalError, ValueError, subprocess.SubprocessError) as error:
        if args.json:
            print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False))
        elif not args.quiet:
            print(f"spec-eval CI error: {error}", file=sys.stderr)
        return EXIT_TOOL_ERROR
    _emit(summary, args)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
