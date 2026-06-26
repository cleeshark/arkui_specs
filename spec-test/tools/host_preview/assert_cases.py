#!/usr/bin/env python3

import argparse
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_inspector_response(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    marker = "Response:"
    if marker not in text:
        raise RuntimeError(f"Missing '{marker}' in {path}")
    response_obj = json.loads(text.split(marker, 1)[1].strip())
    result_str = response_obj.get("result")
    if not isinstance(result_str, str):
        raise RuntimeError("Inspector response result is not a string")
    return json.loads(result_str)


def find_node_by_attr_id(node: Any, target_id: str) -> Optional[Dict[str, Any]]:
    if isinstance(node, dict):
        attrs = node.get("$attrs")
        if isinstance(attrs, dict) and attrs.get("id") == target_id:
            return node
        children = node.get("$children")
        if isinstance(children, list):
            for child in children:
                found = find_node_by_attr_id(child, target_id)
                if found is not None:
                    return found
    return None


def parse_rect(rect_str: str) -> Dict[str, float]:
    parts = [float(x) for x in rect_str.split(",")]
    if len(parts) != 4:
        raise RuntimeError(f"Invalid rect format: {rect_str}")
    return {"x": parts[0], "y": parts[1], "width": parts[2], "height": parts[3]}


def load_cases_from_expected_file(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    suite_id = data.get("suiteId", "")
    cases = data.get("cases", [])
    if not isinstance(cases, list):
        return []
    loaded: List[Dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            continue
        copied = dict(case)
        copied["_suiteId"] = suite_id
        copied["_expectedFile"] = str(path)
        loaded.append(copied)
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspector-response", required=True)
    parser.add_argument("--screenshot-file", default="")
    parser.add_argument("--expected")
    parser.add_argument("--expected-root")
    parser.add_argument("--suite-id")
    parser.add_argument("--case-id")
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-md", required=True)
    args = parser.parse_args()

    if not args.expected and not args.expected_root:
        raise RuntimeError("Either --expected or --expected-root must be provided")
    if args.expected and args.expected_root:
        raise RuntimeError("Use only one of --expected or --expected-root")

    report_md_path = Path(args.report_md)
    screenshot_path = Path(args.screenshot_file) if args.screenshot_file else None
    screenshot_exists = bool(screenshot_path and screenshot_path.exists())
    screenshot_for_report = str(screenshot_path) if screenshot_exists and screenshot_path else ""
    screenshot_for_md = ""
    if screenshot_exists and screenshot_path:
        try:
            screenshot_for_md = str(screenshot_path.relative_to(report_md_path.parent))
        except ValueError:
            screenshot_for_md = screenshot_for_report

    tree = parse_inspector_response(Path(args.inspector_response))

    all_cases: List[Dict[str, Any]] = []
    if args.expected:
        all_cases.extend(load_cases_from_expected_file(Path(args.expected)))
    else:
        root = Path(args.expected_root)
        expected_files = sorted(root.rglob("expected.json"))
        for expected_file in expected_files:
            all_cases.extend(load_cases_from_expected_file(expected_file))

    selected_cases: List[Dict[str, Any]] = []
    for case in all_cases:
        if args.suite_id and case.get("_suiteId") != args.suite_id:
            continue
        if args.case_id and case.get("caseId") != args.case_id:
            continue
        selected_cases.append(case)

    if not selected_cases:
        raise RuntimeError("No cases selected. Check --suite-id/--case-id filters")

    case_results = []
    passed = 0

    for case in selected_cases:
        case_id = case["caseId"]
        target_id = case["targetNodeId"]
        tolerance = float(case.get("tolerancePx", 1.0))
        expected_rect = case["expectedRect"]

        node = find_node_by_attr_id(tree, target_id)
        if node is None:
            case_results.append(
                {
                    "caseId": case_id,
                    "status": "FAIL",
                    "reason": f"Target node not found: {target_id}",
                    "acRefs": case.get("acRefs", []),
                    "screenshotFile": screenshot_for_report,
                }
            )
            continue

        rect_raw = node.get("$rect")
        if not isinstance(rect_raw, str):
            case_results.append(
                {
                    "caseId": case_id,
                    "status": "FAIL",
                    "reason": f"Node has no $rect: {target_id}",
                    "acRefs": case.get("acRefs", []),
                    "screenshotFile": screenshot_for_report,
                }
            )
            continue

        actual_rect = parse_rect(rect_raw)
        width_diff = abs(actual_rect["width"] - float(expected_rect["width"]))
        height_diff = abs(actual_rect["height"] - float(expected_rect["height"]))
        ok = width_diff <= tolerance and height_diff <= tolerance
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        case_results.append(
            {
                "caseId": case_id,
                "status": status,
                "acRefs": case.get("acRefs", []),
                "suiteId": case.get("_suiteId", ""),
                "expectedFile": case.get("_expectedFile", ""),
                "targetNodeId": target_id,
                "expectedRect": expected_rect,
                "actualRect": actual_rect,
                "diff": {"width": width_diff, "height": height_diff},
                "tolerancePx": tolerance,
                "screenshotFile": screenshot_for_report,
            }
        )

    total = len(case_results)
    report = {
        "generatedAt": datetime.datetime.now().isoformat(timespec="seconds"),
        "filters": {
            "suiteId": args.suite_id or "",
            "caseId": args.case_id or "",
        },
        "artifacts": {
            "inspectorResponse": args.inspector_response,
            "screenshotFile": screenshot_for_report,
        },
        "summary": {"total": total, "passed": passed, "failed": total - passed},
        "results": case_results,
    }

    report_json_path = Path(args.report_json)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    md_lines = [
        "# HostPreview Test Report",
        "",
        f"- Total: {total}",
        f"- Passed: {passed}",
        f"- Failed: {total - passed}",
        "",
        f"- Suite filter: {args.suite_id or '(none)'}",
        f"- Case filter: {args.case_id or '(none)'}",
        f"- Inspector: {args.inspector_response}",
        f"- Screenshot: {screenshot_for_report or '(not captured)'}",
        "",
        "| Suite | Case | Status | AC | Note |",
        "|---|---|---|---|---|",
    ]
    for item in case_results:
        ac = ",".join(item.get("acRefs", []))
        if item["status"] == "PASS":
            note = "width/height within tolerance"
        else:
            note = item.get("reason", json.dumps(item.get("diff", {}), ensure_ascii=False))
        md_lines.append(
            f"| {item.get('suiteId','')} | {item['caseId']} | {item['status']} | {ac} | {note} |"
        )

    if screenshot_for_md:
        md_lines.extend(
            [
                "",
                "## Screenshot",
                "",
                f"![case screenshot]({screenshot_for_md})",
            ]
        )

    report_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if total - passed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
