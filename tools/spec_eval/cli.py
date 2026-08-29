#!/usr/bin/env python3
"""Unified CLI for Function-level static evaluation."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_eval.config import EvaluationConfig
from spec_eval.discovery.changed_function_resolver import ChangedFunctionResolver
from spec_eval.discovery.function_locator import FunctionLocator
from spec_eval.errors import SpecEvalError
from spec_eval.function_analysis import (
    build_function_analysis_from_paths,
    write_function_analysis,
)
from spec_eval.function_report import build_function_report_from_paths, write_function_report
from spec_eval.orchestrator import EvaluationOrchestrator
from spec_eval.report.baseline_reporter import BaselineReporter
from spec_eval.report.performance_reporter import PerformanceReporter
from spec_eval.report.site_reporter import SiteReporter
from spec_eval.report.site_evaluation_reporter import (
    build_site_evaluation_report_from_paths,
    write_site_evaluation_report,
)
from spec_eval.report.site_evaluation_history import (
    build_site_evaluation_history_from_paths,
    write_site_evaluation_history,
)
from spec_eval.score import build_score_result_from_paths, write_score_result
from spec_eval.stability import build_stability_result_from_paths, write_stability_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate ArkUI specs by Function/FuncID")
    parser.add_argument("--output", type=Path, help="Output root; defaults to out/spec-evaluation")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--quiet", action="store_true", help="Print only errors and final status")
    parser.add_argument("--no-cache", action="store_true", help="Disable exact-input result cache")
    sub = parser.add_subparsers(dest="command", required=True)

    discover = sub.add_parser("discover", help="Resolve a FuncID or path to a complete Function context")
    group = discover.add_mutually_exclusive_group(required=True)
    group.add_argument("--func-id")
    group.add_argument("--path", type=Path)

    for name in ("check", "evidence"):
        command = sub.add_parser(name, help=f"Run Function {name}")
        command.add_argument("--func-id", required=True)

    scan = sub.add_parser("scan", help="Run all registered Functions")
    scan.add_argument("--all", action="store_true", required=True)
    scan.add_argument(
        "--report-only",
        action="store_true",
        help="record gate failures and per-Function errors without failing the full scan command",
    )

    changed = sub.add_parser("changed", help="Run all Functions affected by a file list")
    changed.add_argument("--files-from", type=Path, required=True)

    compare = sub.add_parser("compare", help="Compare current and baseline result roots")
    compare.add_argument("--current", type=Path, required=True)
    compare.add_argument("--baseline", type=Path, required=True)

    baseline = sub.add_parser("baseline", help="Freeze a complete scan as a stable Finding manifest")
    baseline.add_argument("--results", type=Path, required=True, help="Revision result root")
    baseline.add_argument("--site-report", type=Path, required=True, help="Complete scan site-report.json")
    baseline.add_argument("--write", type=Path, required=True, help="Destination baseline manifest")

    score = sub.add_parser("score", help="Build one deterministic Function score result")
    score.add_argument("--static-result", type=Path, required=True)
    score.add_argument("--evidence-manifest", type=Path, required=True)
    score.add_argument("--semantic-result", type=Path, required=True)
    score.add_argument("--write", type=Path, required=True, help="Destination score-result.json")
    score.add_argument(
        "--analysis-write",
        type=Path,
        help="Optional destination for deterministic function-analysis.json",
    )

    stability = sub.add_parser("stability", help="Analyze repeated semantic evaluation stability")
    stability.add_argument("--static-result", type=Path, required=True)
    stability.add_argument("--evidence-manifest", type=Path, required=True)
    stability.add_argument(
        "--semantic-result",
        type=Path,
        action="append",
        required=True,
        dest="semantic_results",
        help="Repeat once per independent semantic-result.json",
    )
    stability.add_argument("--selected-run-id", required=True)
    stability.add_argument("--write", type=Path, required=True, help="Destination stability-result.json")

    report = sub.add_parser("report", help="Assemble a Function JSON and Markdown report")
    report.add_argument("--static-result", type=Path, required=True)
    report.add_argument("--semantic-result", type=Path, required=True)
    report.add_argument("--score-result", type=Path, required=True)
    report.add_argument("--analysis-result", type=Path, required=True)
    report.add_argument("--stability-result", type=Path, required=True)
    report.add_argument(
        "--confidence-result",
        type=Path,
        help="Optional kernel confidence-result.json (report-reliability deductions) to render",
    )
    report.add_argument("--json-write", type=Path, required=True, help="Destination evaluation-report.json")
    report.add_argument("--markdown-write", type=Path, required=True, help="Destination function-report.md")

    site_evaluation = sub.add_parser(
        "site-evaluation", help="Export confirmed Review records for the semantic site view"
    )
    site_evaluation.add_argument("--reviews-root", type=Path, required=True)
    site_evaluation.add_argument("--site-report", type=Path, required=True)
    site_evaluation.add_argument("--write", type=Path, required=True, help="Destination site-evaluation-report.json")

    site_history = sub.add_parser(
        "site-evaluation-history", help="Update compact trend and Finding delta history"
    )
    site_history.add_argument("--site-evaluation-report", type=Path, required=True)
    site_history.add_argument("--history", type=Path, help="Existing site-evaluation-history.json")
    site_history.add_argument("--write", type=Path, required=True, help="Destination site-evaluation-history.json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = EvaluationConfig.discover(output_root=args.output)
    try:
        if args.command == "discover":
            locator = FunctionLocator(config)
            context = locator.locate(args.func_id) if args.func_id else locator.locate_by_path(args.path)
            return emit(context.to_dict(config.repo_root), args, gate="pass")
        if args.command == "compare":
            return emit(BaselineReporter().compare(args.current, args.baseline), args, gate="pass")
        if args.command == "baseline":
            reporter = BaselineReporter()
            manifest = reporter.build_manifest(args.results, args.site_report)
            if not manifest["complete"]:
                raise ValueError("baseline is incomplete; results and site report must cover the same error-free full scan")
            reporter.write_manifest(manifest, args.write)
            return emit(
                {
                    "gate": "pass",
                    "output_path": args.write.as_posix(),
                    "source_revision": manifest["source_revision"],
                    "function_count": manifest["scope"]["function_count"],
                    "finding_count": manifest["finding_count"],
                    "unique_finding_count": manifest["unique_finding_count"],
                },
                args,
                gate="pass",
            )
        if args.command == "score":
            result = build_score_result_from_paths(
                static_result_path=args.static_result,
                evidence_manifest_path=args.evidence_manifest,
                semantic_result_path=args.semantic_result,
                evaluation_root=config.rules_root,
            )
            analysis = None
            if args.analysis_write is not None:
                analysis = build_function_analysis_from_paths(
                    static_result_path=args.static_result,
                    evidence_manifest_path=args.evidence_manifest,
                    semantic_result_path=args.semantic_result,
                    score_result=result,
                )
            write_score_result(args.write, result)
            if analysis is not None:
                write_function_analysis(args.analysis_write, analysis)
            payload = {
                "func_id": result["func_id"],
                "output_path": args.write.as_posix(),
                "raw_score": result["raw_score"],
                "published_score": result["published_score"],
                "confidence": result["confidence"]["score"],
                "admission": result["admission"]["status"],
                "gate": result["gate"]["effective"],
            }
            if args.analysis_write is not None:
                payload["analysis_path"] = args.analysis_write.as_posix()
            return emit(payload, args, gate=result["gate"]["effective"])
        if args.command == "stability":
            result = build_stability_result_from_paths(
                static_result_path=args.static_result,
                evidence_manifest_path=args.evidence_manifest,
                semantic_result_paths=args.semantic_results,
                selected_run_id=args.selected_run_id,
                evaluation_root=config.rules_root,
            )
            write_stability_result(args.write, result)
            return emit(
                {
                    "func_id": result["func_id"],
                    "output_path": args.write.as_posix(),
                    "run_count": result["score_statistics"]["count"],
                    "raw_range": result["score_statistics"]["range"],
                    "population_stddev": result["score_statistics"]["population_stddev"],
                    "consensus_count": result["consensus_summary"]["consensus_count"],
                    "no_consensus_count": result["consensus_summary"]["no_consensus_count"],
                    "outlier_run_ids": result["outlier_run_ids"],
                    "selected_run_id": result["selected_run"]["run_id"],
                    "gate": "pass",
                },
                args,
                gate="pass",
            )
        if args.command == "report":
            report, markdown = build_function_report_from_paths(
                static_result_path=args.static_result,
                semantic_result_path=args.semantic_result,
                score_result_path=args.score_result,
                analysis_result_path=args.analysis_result,
                stability_result_path=args.stability_result,
                confidence_result_path=args.confidence_result,
                evaluation_root=config.rules_root,
            )
            write_function_report(
                json_path=args.json_write,
                markdown_path=args.markdown_write,
                report=report,
                markdown=markdown,
            )
            return emit(
                {
                    "func_id": report["func_id"],
                    "json_path": args.json_write.as_posix(),
                    "markdown_path": args.markdown_write.as_posix(),
                    "published_score": report["summary"]["published_score"],
                    "confidence": report["summary"]["confidence"],
                    "admission": report["summary"]["admission_status"],
                    "gate": report["summary"]["gate"],
                },
                args,
                gate=report["summary"]["gate"],
            )
        if args.command == "site-evaluation":
            result = build_site_evaluation_report_from_paths(
                reviews_root=args.reviews_root,
                site_report_path=args.site_report,
                schemas_root=config.rules_root / "schemas",
            )
            write_site_evaluation_report(args.write, result)
            return emit(
                {
                    "output_path": args.write.as_posix(),
                    "source_revision": result["sourceRevision"],
                    "function_count": result["summary"]["functionCount"],
                    "confirmed_function_count": result["summary"]["confirmedFunctionCount"],
                    "expired_function_count": result["summary"]["expiredFunctionCount"],
                    "finding_count": result["summary"]["findingCount"],
                    "expired_finding_count": result["summary"]["expiredFindingCount"],
                    "gate": "pass",
                },
                args,
                gate="pass",
            )
        if args.command == "site-evaluation-history":
            result = build_site_evaluation_history_from_paths(
                current_report_path=args.site_evaluation_report,
                previous_history_path=args.history,
                schemas_root=config.rules_root / "schemas",
            )
            write_site_evaluation_history(args.write, result)
            return emit(
                {
                    "output_path": args.write.as_posix(),
                    "source_revision": result["currentRevision"],
                    "snapshot_count": result["summary"]["snapshotCount"],
                    "comparison_status": result["summary"]["comparisonStatus"],
                    "added_finding_count": result["summary"]["addedFindingCount"],
                    "resolved_finding_count": result["summary"]["resolvedFindingCount"],
                    "gate": "pass",
                },
                args,
                gate="pass",
            )

        orchestrator = EvaluationOrchestrator(config)
        if args.command in ("check", "evidence"):
            result, cached, target = orchestrator.evaluate_and_write(
                args.func_id, args.output, use_cache=not args.no_cache
            )
            value = result["static"] if args.command == "check" else result["evidence"]
            value = dict(value)
            value["output_path"] = target.as_posix()
            value["cached"] = cached
            return emit(value, args, gate=result["static"]["gate"])
        if args.command == "scan":
            scan_started = time.perf_counter()
            results = []
            report_results = []
            exit_gate = "pass"
            func_ids = orchestrator.locator.all_func_ids()
            prepare = getattr(orchestrator, "prepare", None)
            fully_cached = False
            cache_probe = getattr(orchestrator, "batch_is_fully_cached", None)
            if not args.no_cache and callable(cache_probe):
                fully_cached = cache_probe(func_ids, config.output_root)
            preparation = (
                {
                    "total_ms": 0.0,
                    "function_count": len(func_ids),
                    "skipped": "all_results_cached",
                    "source_index": {},
                    "sdk_index": {},
                }
                if fully_cached
                else prepare(func_ids) if callable(prepare) else {}
            )
            for func_id in func_ids:
                context_value = {}
                locate = getattr(orchestrator.locator, "locate", None)
                if callable(locate):
                    try:
                        context_value = locate(func_id).to_dict(config.repo_root)
                    except Exception:
                        context_value = {}
                try:
                    result, cached, target = orchestrator.evaluate_and_write(
                        func_id, args.output, use_cache=not args.no_cache
                    )
                    result_gate = result["static"]["gate"]
                    results.append(
                        {
                            "func_id": func_id,
                            "gate": result_gate,
                            "cached": cached,
                            "output_path": target.as_posix(),
                            "performance": _performance_for(orchestrator, func_id),
                        }
                    )
                    report_results.append(
                        {
                            "func_id": func_id,
                            "context": result.get("context", context_value),
                            "result": result,
                            "cached": cached,
                            "output_path": target.as_posix(),
                            "performance": _performance_for(orchestrator, func_id),
                        }
                    )
                    if result_gate == "fail":
                        exit_gate = "fail"
                except Exception as error:  # keep full-repository scans progressing
                    results.append({"func_id": func_id, "gate": "error", "error": str(error)})
                    report_results.append(
                        {"func_id": func_id, "context": context_value, "error": str(error)}
                    )
                    exit_gate = "error"
            source_revision = config.git_revision()
            revision_root = config.output_root / source_revision
            static_paths = list(revision_root.glob("*/static-result.json")) if revision_root.is_dir() else []
            summary = BaselineReporter().aggregate(static_paths)
            revision_root.mkdir(parents=True, exist_ok=True)
            (revision_root / "baseline-summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            current_preparation = getattr(orchestrator, "preparation_metrics", None)
            if not fully_cached and callable(current_preparation):
                preparation = current_preparation()
            performance_reporter = PerformanceReporter()
            performance = performance_reporter.build(
                (_performance_for(orchestrator, func_id) for func_id in func_ids),
                source_revision=source_revision,
                total_ms=(time.perf_counter() - scan_started) * 1000,
                preparation=preparation,
            )
            site_reporter = SiteReporter()
            site_report = site_reporter.build(
                report_results,
                source_revision=source_revision,
                tool_version=config.tool_version,
                rule_version=getattr(getattr(orchestrator, "rule_configuration", None), "version", config.rule_version),
                report_only=args.report_only,
                performance=performance,
            )
            site_reporter.write_archive(config.output_root, source_revision, site_report)
            performance_reporter.write(revision_root / "performance-summary.json", performance)
            return emit(
                {"functions": results, "performance": performance},
                args,
                gate="pass" if args.report_only else exit_gate,
            )
        if args.command == "changed":
            paths = [line.strip() for line in args.files_from.read_text(encoding="utf-8").splitlines() if line.strip()]
            # Use HEAD as base_ref for CLI mode
            contexts = ChangedFunctionResolver(orchestrator.locator, base_ref="HEAD").resolve(paths)
            prepare_contexts = getattr(orchestrator, "prepare_contexts", None)
            cached_contexts = False
            cache_probe = getattr(orchestrator, "contexts_are_fully_cached", None)
            if not args.no_cache and callable(cache_probe):
                cached_contexts = cache_probe(contexts, config.output_root)
            if not cached_contexts and callable(prepare_contexts):
                prepare_contexts(contexts)
            results = []
            exit_gate = "pass"
            for context in contexts:
                result, cached, target = orchestrator.evaluate_and_write(
                    context.func_id, args.output, use_cache=not args.no_cache
                )
                result_gate = result["static"]["gate"]
                results.append(
                    {
                        "func_id": context.func_id,
                        "gate": result_gate,
                        "cached": cached,
                        "output_path": target.as_posix(),
                        "performance": _performance_for(orchestrator, context.func_id),
                    }
                )
                if result_gate == "fail":
                    exit_gate = "fail"
            return emit({"functions": results}, args, gate=exit_gate)
    except (OSError, SpecEvalError, ValueError) as error:
        if args.json:
            print(json.dumps({"gate": "error", "error": str(error)}, ensure_ascii=False))
        else:
            print(f"spec-eval error: {error}", file=sys.stderr)
        return 2
    return 2


def emit(value: dict, args, gate: str) -> int:
    if args.json:
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    elif not args.quiet:
        if "func_id" in value:
            print(f"Function {value['func_id']}: {gate}")
        elif "functions" in value and isinstance(value["functions"], list):
            for item in value["functions"]:
                print(f"{item.get('func_id', '-')}: {item.get('gate', '-')}")
        else:
            print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    if gate == "error":
        return 3
    if gate == "fail":
        return 1
    return 0


def _performance_for(orchestrator, func_id: str) -> dict:
    performance_for = getattr(orchestrator, "performance_for", None)
    return performance_for(func_id) if callable(performance_for) else {}


if __name__ == "__main__":
    raise SystemExit(main())
