#!/usr/bin/env python3

import argparse
import datetime
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel_or_abs(path_str: str, base: Path) -> str:
    if not path_str:
        return ""
    path = Path(path_str)
    if not path.is_absolute():
        path = (base / path).resolve()
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def pick_case_result(report: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    results = report.get("results", [])
    if not isinstance(results, list):
        return {}
    for item in results:
        if isinstance(item, dict) and item.get("caseId") == case_id:
            return item
    for item in results:
        if isinstance(item, dict):
            return item
    return {}


def parse_note(result: Dict[str, Any]) -> str:
    reason = result.get("reason")
    if isinstance(reason, str) and reason:
        return reason
    diff = result.get("diff")
    if isinstance(diff, dict):
        return json.dumps(diff, ensure_ascii=False)
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    run_root = Path(args.run_root)
    plan = load_json(Path(args.plan_json))
    plan_cases = plan.get("cases", [])
    if not isinstance(plan_cases, list) or not plan_cases:
        raise RuntimeError("No cases in plan json")

    case_rows: List[Dict[str, Any]] = []
    suite_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "passed": 0, "failed": 0, "missing": 0}
    )

    passed_cases = 0
    failed_cases = 0
    missing_reports = 0

    for plan_case in plan_cases:
        if not isinstance(plan_case, dict):
            continue
        suite_id = str(plan_case.get("suiteId", ""))
        case_id = str(plan_case.get("caseId", ""))
        url = str(plan_case.get("url", ""))

        suite_stats[suite_id]["total"] += 1

        case_dir = run_root / suite_id / case_id
        report_json_path = case_dir / "report.json"
        report_md_path = case_dir / "report.md"

        report_json_rel = str(report_json_path.relative_to(run_root)) if report_json_path.exists() else ""
        report_md_rel = str(report_md_path.relative_to(run_root)) if report_md_path.exists() else ""

        if not report_json_path.exists():
            status = "MISSING"
            note = "report.json missing"
            screenshot_rel = ""
            missing_reports += 1
            suite_stats[suite_id]["missing"] += 1
        else:
            report = load_json(report_json_path)
            result = pick_case_result(report, case_id)
            status = str(result.get("status", "UNKNOWN"))
            note = "width/height within tolerance" if status == "PASS" else parse_note(result)
            screenshot = str(
                result.get("screenshotFile")
                or report.get("artifacts", {}).get("screenshotFile", "")
            )
            screenshot_rel = rel_or_abs(screenshot, run_root)

            if status == "PASS":
                passed_cases += 1
                suite_stats[suite_id]["passed"] += 1
            else:
                failed_cases += 1
                suite_stats[suite_id]["failed"] += 1

        case_rows.append(
            {
                "suiteId": suite_id,
                "caseId": case_id,
                "url": url,
                "status": status,
                "note": note,
                "reportJson": report_json_rel,
                "reportMd": report_md_rel,
                "screenshot": screenshot_rel,
            }
        )

    planned_cases = len(case_rows)
    executed_cases = planned_cases - missing_reports
    pass_rate = (passed_cases / planned_cases * 100.0) if planned_cases > 0 else 0.0

    summary_json = {
        "generatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "runRoot": str(run_root),
        "filters": plan.get("summary", {}),
        "summary": {
            "plannedCases": planned_cases,
            "executedCases": executed_cases,
            "passedCases": passed_cases,
            "failedCases": failed_cases,
            "missingReports": missing_reports,
            "passRate": round(pass_rate, 2),
        },
        "suiteSummary": [
            {"suiteId": suite_id, **stats}
            for suite_id, stats in sorted(suite_stats.items(), key=lambda x: x[0])
        ],
        "cases": sorted(case_rows, key=lambda x: (x["suiteId"], x["caseId"])),
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# HostPreview Summary Report",
        "",
        f"- Generated At: {summary_json['generatedAt']}",
        f"- Run Root: {summary_json['runRoot']}",
        f"- Planned Cases: {planned_cases}",
        f"- Executed Cases: {executed_cases}",
        f"- Passed Cases: {passed_cases}",
        f"- Failed Cases: {failed_cases}",
        f"- Missing Reports: {missing_reports}",
        f"- Pass Rate: {summary_json['summary']['passRate']}%",
        "",
        f"- Suite filter: {plan.get('summary', {}).get('suiteFilter', '') or '(none)'}",
        f"- Case filter: {plan.get('summary', {}).get('caseFilter', '') or '(none)'}",
        "",
        "## Suite Summary",
        "",
        "| Suite | Total | Passed | Failed | Missing |",
        "|---|---:|---:|---:|---:|",
    ]

    for suite in summary_json["suiteSummary"]:
        md_lines.append(
            f"| {suite['suiteId']} | {suite['total']} | {suite['passed']} | {suite['failed']} | {suite['missing']} |"
        )

    md_lines.extend(
        [
            "",
            "## Case Details",
            "",
            "| Suite | Case | Status | Report | Screenshot | Note |",
            "|---|---|---|---|---|---|",
        ]
    )

    for case in summary_json["cases"]:
        report_cell = f"[report]({case['reportMd']})" if case["reportMd"] else "(missing)"
        screenshot_cell = f"[image]({case['screenshot']})" if case["screenshot"] else "(none)"
        note = case.get("note", "").replace("|", "/")
        md_lines.append(
            f"| {case['suiteId']} | {case['caseId']} | {case['status']} | {report_cell} | {screenshot_cell} | {note} |"
        )

    Path(args.out_md).write_text("\n".join(md_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
