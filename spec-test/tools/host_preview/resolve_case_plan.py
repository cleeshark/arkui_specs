#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_suite_pairs(spec_root: Path) -> List[Tuple[Path, Path]]:
    pairs: List[Tuple[Path, Path]] = []
    for suite_manifest in sorted(spec_root.rglob("suite.manifest.json")):
        suite_dir = suite_manifest.parent
        expected_json = suite_dir / "expected" / "expected.json"
        if expected_json.exists():
            pairs.append((suite_manifest, expected_json))
    return pairs


def build_case_records(
    spec_root: Path, main_pages_json: Path, suite_id_filter: str, case_id_filter: str
) -> List[Dict]:
    routes = set(load_json(main_pages_json).get("src", []))
    records: List[Dict] = []

    for suite_manifest_path, expected_json_path in discover_suite_pairs(spec_root):
        suite_manifest = load_json(suite_manifest_path)
        expected = load_json(expected_json_path)
        suite_id = suite_manifest.get("suiteId", "")
        if suite_id_filter and suite_id != suite_id_filter:
            continue

        manifest_cases = {
            c.get("caseId", ""): c for c in suite_manifest.get("cases", []) if isinstance(c, dict)
        }
        for case in expected.get("cases", []):
            if not isinstance(case, dict):
                continue
            case_id = case.get("caseId", "")
            if not case_id:
                continue
            if case_id_filter and case_id != case_id_filter:
                continue

            manifest_case = manifest_cases.get(case_id, {})
            url = (
                manifest_case.get("url")
                or case.get("url")
                or ""
            )
            if not url:
                raise RuntimeError(
                    f"Missing url for case '{case_id}' in {suite_manifest_path}"
                )
            if url not in routes:
                raise RuntimeError(
                    f"Route '{url}' for case '{case_id}' is not registered in {main_pages_json}"
                )

            operation_sequence = manifest_case.get("operationSequence")
            if operation_sequence is None:
                operation_sequence = manifest_case.get("operations")
            if operation_sequence is None:
                operation_sequence = []
            if not isinstance(operation_sequence, list):
                raise RuntimeError(
                    f"operationSequence for case '{case_id}' in {suite_manifest_path} must be a list"
                )
            for idx, op in enumerate(operation_sequence):
                if not isinstance(op, dict):
                    raise RuntimeError(
                        f"operationSequence[{idx}] for case '{case_id}' in {suite_manifest_path} must be an object"
                    )
                if not op.get("op"):
                    raise RuntimeError(
                        f"operationSequence[{idx}] for case '{case_id}' in {suite_manifest_path} missing 'op'"
                    )

            records.append(
                {
                    "suiteId": suite_id,
                    "caseId": case_id,
                    "url": url,
                    "expectedFile": str(expected_json_path),
                    "operationSequence": operation_sequence,
                }
            )

    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec-root", required=True)
    parser.add_argument("--main-pages-json", required=True)
    parser.add_argument("--suite-id", default="")
    parser.add_argument("--case-id", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    spec_root = Path(args.spec_root)
    main_pages_json = Path(args.main_pages_json)
    records = build_case_records(
        spec_root, main_pages_json, args.suite_id, args.case_id
    )
    if not records:
        raise RuntimeError("No cases selected. Check suite/case filters and manifests.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "summary": {
                    "totalCases": len(records),
                    "suiteFilter": args.suite_id,
                    "caseFilter": args.case_id,
                },
                "cases": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
