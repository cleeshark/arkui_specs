#!/usr/bin/env python3
"""CI entry point for changed-Function report-only or enforcing evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_eval.config import EvaluationConfig
from spec_eval.discovery.changed_function_resolver import ChangedFunctionResolver
from spec_eval.errors import SpecEvalError
from spec_eval.orchestrator import EvaluationOrchestrator
from spec_eval.report.baseline_reporter import BaselineReporter
from spec_eval.report.performance_reporter import PerformanceReporter
from spec_eval.rules.delta_gate_engine import DeltaGateEngine


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
    parser.add_argument(
        "--registry-base",
        help=(
            "Git base revision for registry (features.yaml/functions.yaml) diff analysis; "
            "used with --files-from where the working tree is checked out to the tested commit "
            "so HEAD-based diffs would be empty. Defaults to --base or HEAD."
        ),
    )
    parser.add_argument("--output", type=Path, help="artifact root; defaults to out/spec-evaluation")
    gate = parser.add_mutually_exclusive_group()
    gate.add_argument("--enforce", action="store_true", help="return 1 when an absolute Function gate fails")
    gate.add_argument(
        "--delta-enforce",
        action="store_true",
        help="return 1 only for new or worsened findings relative to --baseline",
    )
    parser.add_argument("--baseline", type=Path, help="complete Finding baseline manifest or result root")
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


def _delta_count(values: list[dict[str, Any]]) -> int:
    return sum(int(item.get("count", 1) or 1) for item in values)


def _reclassified_sort_key(finding: dict[str, Any]) -> tuple[int, str, str, str]:
    after = finding.get("after", {})
    rank = {"Critical": 0, "Major": 1, "Minor": 2, "Info": 3}
    return (
        rank.get(str(after.get("severity", "Info")), 4),
        str(finding.get("rule_id", "")),
        str(finding.get("path", "")),
        str(finding.get("finding_id", "")),
    )


def _attach_delta(
    item: dict[str, Any],
    function_delta: dict[str, Any],
    delta_gate: dict[str, Any],
    top: int,
) -> None:
    added = sorted(function_delta.get("added", []), key=_finding_sort_key)
    resolved = sorted(function_delta.get("resolved", []), key=_finding_sort_key)
    reclassified = sorted(function_delta.get("reclassified", []), key=_reclassified_sort_key)
    item["absolute_gate"] = item["gate"]
    item["delta_gate"] = delta_gate["gate"]
    item["baseline_status"] = delta_gate["baseline_status"]
    item["delta"] = {
        "added": _delta_count(added),
        "resolved": _delta_count(resolved),
        "reclassified": _delta_count(reclassified),
        "unchanged": int(function_delta.get("unchanged", 0) or 0),
        "added_counts": delta_gate["added_counts"],
        "exempted_added_count": delta_gate["exempted_added_count"],
        "reason_codes": delta_gate["reason_codes"],
    }
    limit = max(top, 0)
    item["top_added_findings"] = added[:limit]
    item["top_resolved_findings"] = resolved[:limit]
    item["top_reclassified_findings"] = reclassified[:limit]
    item["delta_reasons"] = delta_gate["reasons"]


def run(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    run_started = time.perf_counter()
    if args.delta_enforce and args.baseline is None:
        raise ValueError("--delta-enforce requires --baseline")
    config = EvaluationConfig.discover(output_root=args.output)
    changed_files = _changed_files(args, config)
    orchestrator = EvaluationOrchestrator(config)
    baseline_reporter = BaselineReporter()
    baseline = (
        baseline_reporter.load_baseline(
            args.baseline,
            expected_rule_version=orchestrator.rule_configuration.version,
        )
        if args.baseline is not None
        else None
    )
    # Determine base_ref for registry diff analysis. Prefer an explicit
    # --registry-base (CI passes the target SHA here because the specs repo is
    # checked out to the tested commit, making HEAD-based diffs empty), then
    # fall back to --base, then HEAD for local/interactive use.
    base_ref = args.registry_base or args.base or "HEAD"
    contexts = ChangedFunctionResolver(orchestrator.locator, base_ref=base_ref).resolve(changed_files)
    prepare_contexts = getattr(orchestrator, "prepare_contexts", None)
    cache_probe = getattr(orchestrator, "contexts_are_fully_cached", None)
    fully_cached = not args.no_cache and callable(cache_probe) and cache_probe(contexts, config.output_root)
    preparation = (
        {
            "total_ms": 0.0,
            "function_count": len(contexts),
            "skipped": "all_results_cached",
            "source_index": {},
            "sdk_index": {},
        }
        if fully_cached
        else prepare_contexts(contexts) if callable(prepare_contexts) else {}
    )
    functions: list[dict[str, Any]] = []
    evaluated_results: dict[str, dict[str, Any]] = {}
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
            item["performance"] = _performance_for(orchestrator, context.func_id)
            functions.append(item)
            evaluated_results[context.func_id] = result
            has_gate_failure = has_gate_failure or item["gate"] == "fail"
        except Exception as error:  # preserve results for every other affected Function
            has_evaluation_error = True
            functions.append({"func_id": context.func_id, "gate": "error", "error": str(error)})

    functions.sort(key=lambda item: str(item.get("func_id", "")))
    delta_document = None
    has_delta_failure = False
    delta_reasons: list[dict[str, Any]] = []
    if baseline is not None and evaluated_results:
        delta_document = baseline_reporter.compare_results(evaluated_results.values(), baseline)
        delta_engine = DeltaGateEngine(orchestrator.rule_configuration)
        for item in functions:
            func_id = str(item.get("func_id", ""))
            if item.get("gate") == "error":
                item["absolute_gate"] = "error"
                item["delta_gate"] = "error"
                continue
            function_delta = delta_document["functions"][func_id]
            delta_gate = delta_engine.evaluate(func_id, str(item["gate"]), function_delta).to_dict()
            _attach_delta(item, function_delta, delta_gate, args.top)
            has_delta_failure = has_delta_failure or delta_gate["gate"] == "fail"
            delta_reasons.extend(delta_gate["reasons"])
    elif baseline is not None:
        delta_document = {
            "summary": {"added": 0, "reclassified": 0, "resolved": 0, "unchanged": 0},
            "functions": {},
        }

    mode = "delta-enforce" if args.delta_enforce else "enforce" if args.enforce else "report-only"
    summary: dict[str, Any] = {
        "mode": mode,
        "source_revision": config.git_revision(),
        "changed_files": changed_files,
        "affected_function_count": len(functions),
        "gate_failed_count": sum(1 for item in functions if item.get("gate") == "fail"),
        "absolute_gate_failed_count": sum(1 for item in functions if item.get("gate") == "fail"),
        "delta_gate_failed_count": sum(1 for item in functions if item.get("delta_gate") == "fail"),
        "delta_warn_count": sum(1 for item in functions if item.get("delta_gate") == "warn"),
        "new_function_count": sum(1 for item in functions if item.get("baseline_status") == "new"),
        "error_count": sum(1 for item in functions if item.get("gate") == "error"),
        "functions": functions,
    }
    current_preparation = getattr(orchestrator, "preparation_metrics", None)
    if not fully_cached and callable(current_preparation):
        preparation = current_preparation()
    performance_reporter = PerformanceReporter()
    performance = performance_reporter.build(
        (_performance_for(orchestrator, context.func_id) for context in contexts),
        source_revision=config.git_revision(),
        total_ms=(time.perf_counter() - run_started) * 1000,
        preparation=preparation,
    )
    summary["performance"] = {key: value for key, value in performance.items() if key != "functions"}
    if baseline is not None:
        summary["baseline"] = {
            "path": args.baseline.as_posix(),
            "source_revision": baseline.get("source_revision"),
            "identity_version": baseline.get("identity_version"),
            "rule_version": baseline.get("rule_version"),
        }
        summary["delta"] = delta_document["summary"] if delta_document is not None else {}
        summary["delta_reasons"] = delta_reasons
    if has_evaluation_error:
        summary["exit_reasons"] = [
            {
                "code": "FUNCTION_EVALUATION_INCOMPLETE",
                "func_id": str(item.get("func_id", "")),
                "count": 1,
                "gate": "error",
            }
            for item in functions
            if item.get("gate") == "error"
        ]
    elif args.delta_enforce:
        summary["exit_reasons"] = [item for item in delta_reasons if item.get("gate") == "fail"]
    elif args.enforce:
        summary["exit_reasons"] = [
            {
                "code": "ABSOLUTE_GATE_FAILED",
                "func_id": str(item.get("func_id", "")),
                "count": 1,
                "gate": "fail",
            }
            for item in functions
            if item.get("gate") == "fail"
        ]
    else:
        summary["exit_reasons"] = []
    revision_root = config.output_root / summary["source_revision"]
    revision_root.mkdir(parents=True, exist_ok=True)
    summary_path = revision_root / "ci-summary.json"
    summary["summary_path"] = summary_path.as_posix()
    performance["total_ms"] = round((time.perf_counter() - run_started) * 1000, 3)
    summary["performance"]["total_ms"] = performance["total_ms"]
    performance_reporter.write(revision_root / "performance-summary.json", performance)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if has_evaluation_error:
        return summary, EXIT_INCOMPLETE
    if args.delta_enforce and has_delta_failure:
        return summary, EXIT_GATE_FAILED
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
        f"{summary['absolute_gate_failed_count']} absolute failure(s), "
        f"{summary['delta_gate_failed_count']} delta failure(s), "
        f"{summary['error_count']} error(s)"
    )
    for item in summary["functions"]:
        delta_gate = item.get("delta_gate")
        delta_text = f", delta={delta_gate}" if delta_gate else ""
        print(f"{item['func_id']}: absolute={item['gate']}{delta_text} ({item.get('finding_count', 0)} findings)")
    print(f"summary: {summary['summary_path']}")


def _performance_for(orchestrator, func_id: str) -> dict[str, Any]:
    performance_for = getattr(orchestrator, "performance_for", None)
    return performance_for(func_id) if callable(performance_for) else {}


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
