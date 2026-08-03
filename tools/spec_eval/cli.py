#!/usr/bin/env python3
"""Unified CLI for Function-level static evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spec_eval.config import EvaluationConfig
from spec_eval.discovery import ChangedFunctionResolver, FunctionLocator
from spec_eval.errors import SpecEvalError
from spec_eval.orchestrator import EvaluationOrchestrator
from spec_eval.report import BaselineReporter, SiteReporter


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
            results = []
            report_results = []
            exit_gate = "pass"
            for func_id in orchestrator.locator.all_func_ids():
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
                        {"func_id": func_id, "gate": result_gate, "cached": cached, "output_path": target.as_posix()}
                    )
                    report_results.append(
                        {
                            "func_id": func_id,
                            "context": result.get("context", context_value),
                            "result": result,
                            "cached": cached,
                            "output_path": target.as_posix(),
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
            revision_root = config.output_root / config.git_revision()
            static_paths = list(revision_root.glob("*/static-result.json")) if revision_root.is_dir() else []
            summary = BaselineReporter().aggregate(static_paths)
            revision_root.mkdir(parents=True, exist_ok=True)
            (revision_root / "baseline-summary.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            site_reporter = SiteReporter()
            site_report = site_reporter.build(
                report_results,
                source_revision=config.git_revision(),
                tool_version=config.tool_version,
                rule_version=getattr(getattr(orchestrator, "rule_configuration", None), "version", config.rule_version),
                report_only=args.report_only,
            )
            site_reporter.write_archive(config.output_root, config.git_revision(), site_report)
            return emit({"functions": results}, args, gate="pass" if args.report_only else exit_gate)
        if args.command == "changed":
            paths = [line.strip() for line in args.files_from.read_text(encoding="utf-8").splitlines() if line.strip()]
            contexts = ChangedFunctionResolver(orchestrator.locator).resolve(paths)
            results = []
            exit_gate = "pass"
            for context in contexts:
                result, cached, target = orchestrator.evaluate_and_write(
                    context.func_id, args.output, use_cache=not args.no_cache
                )
                result_gate = result["static"]["gate"]
                results.append(
                    {"func_id": context.func_id, "gate": result_gate, "cached": cached, "output_path": target.as_posix()}
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


if __name__ == "__main__":
    raise SystemExit(main())
