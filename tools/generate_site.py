#!/usr/bin/env python3
"""Generate the Docusaurus site inputs from the ArkUI spec registry."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
FUNCTIONS_FILE = ROOT / "registry" / "functions.yaml"
FEATURES_FILE = ROOT / "registry" / "features.yaml"
SITE_DIR = ROOT / "site"
DOCS_DIR = SITE_DIR / "docs"
SIDEBAR_FILE = SITE_DIR / "sidebars.js"
DATA_DIR = SITE_DIR / "src" / "data"
REGISTRY_JSON = DATA_DIR / "registry.json"
SPEC_EVAL_SUMMARY_JSON = DATA_DIR / "spec-evaluation-summary.json"
STATIC_DATA_DIR = SITE_DIR / "static" / "data"
# The built site Docusaurus serves; ``static/data`` is copied here at build time.
# A B-lite data-only refresh also mirrors into this dir so the served site
# reflects new reports on reload without a rebuild.
BUILD_DATA_DIR = SITE_DIR / "build" / "data"
SPEC_EVAL_STATIC_JSON = STATIC_DATA_DIR / "spec-evaluation.json"
SEMANTIC_EVAL_SUMMARY_JSON = DATA_DIR / "semantic-evaluation-summary.json"
SEMANTIC_EVAL_STATIC_JSON = STATIC_DATA_DIR / "semantic-evaluation.json"
SPEC_EVAL_HISTORY_JSON = DATA_DIR / "spec-evaluation-history.json"
SPEC_EVAL_ARCHIVE_DIR = ROOT / ".evaluator"

# Dynamic (B-lite) mode: the running CI service writes immutable, per-Function
# rolling reports under this archive root.  Dynamic mode reads the newest job
# per Function straight from the filesystem (bypassing the service SQLite DB) so
# a lightweight ``--data-only`` refresh can be triggered on each new archive.
AUTOMATED_ARCHIVE_DIR = ROOT / ".evaluator" / "service-data" / "archives" / "automated"
AUTOMATED_HISTORY_LOG = "site-history-automated.jsonl"

# Runtime-fetched copies of the summary/history documents.  In static mode these
# are imported at build time from ``src/data``; dynamic mode ALSO publishes them
# here so a data-only refresh is visible on browser reload without a rebuild.
SPEC_EVAL_SUMMARY_STATIC_JSON = STATIC_DATA_DIR / "spec-evaluation-summary.json"
SEMANTIC_EVAL_SUMMARY_STATIC_JSON = STATIC_DATA_DIR / "semantic-evaluation-summary.json"
SPEC_EVAL_HISTORY_STATIC_JSON = STATIC_DATA_DIR / "spec-evaluation-history.json"
SITE_RUNTIME_JSON = STATIC_DATA_DIR / "site-runtime.json"

# Reuse the CI service's report converters so dynamic and static site data share
# one contract.  ``tools/`` is the import root for the ``spec_eval`` package.
sys.path.insert(0, str(ROOT / "tools"))


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def doc_id(path: str) -> str:
    raw = Path(path)
    return str(raw.with_suffix(""))


def copy_markdown(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def sidebar_doc(path: str, label: str | None = None) -> dict[str, str]:
    item = {"type": "doc", "id": doc_id(path)}
    if label:
        item["label"] = label
    return item


def sort_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(features, key=lambda item: str(item["id"]))


def build_sidebar(
    top_levels: list[dict[str, Any]], functions: list[dict[str, Any]], features: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    features_by_func: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for feature in features:
        features_by_func[str(feature["func_id"])].append(feature)

    functions_by_l1_l2: defaultdict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for func in functions:
        func_id = str(func["id"])
        has_design = bool(func.get("design"))
        has_specs = any(feature.get("spec") for feature in features_by_func.get(func_id, []))
        if not has_design and not has_specs:
            continue
        key = (str(func["l1"]["id"]), str(func["l2"]["id"]), str(func["l2"]["title"]))
        functions_by_l1_l2[key].append(func)

    l1_lookup = {str(item["id"]): item for item in top_levels}
    docs_items: list[dict[str, Any]] = [
        {
            "type": "category",
            "label": "Overview",
            "collapsed": False,
            "items": [
                sidebar_doc("index.md", "Spec Index"),
                sidebar_doc("registry/README.md", "Registry Guide"),
            ],
        }
    ]

    for top in top_levels:
        l1_id = str(top["id"])
        l2_categories: list[dict[str, Any]] = []
        l2_keys = sorted(key for key in functions_by_l1_l2 if key[0] == l1_id)
        for _, l2_id, l2_title in l2_keys:
            func_items: list[dict[str, Any]] = []
            funcs = sorted(functions_by_l1_l2[(l1_id, l2_id, l2_title)], key=lambda item: str(item["id"]))
            for func in funcs:
                func_id = str(func["id"])
                items: list[dict[str, Any]] = []
                if func.get("design"):
                    items.append(sidebar_doc(str(func["design"]), "Design"))
                for feature in sort_features(features_by_func.get(func_id, [])):
                    if feature.get("spec"):
                        items.append(sidebar_doc(str(feature["spec"]), f"{feature['id']} {feature['title']}"))
                if items:
                    func_items.append(
                        {
                            "type": "category",
                            "label": f"{func_id} {func['l3']['title']}",
                            "collapsed": True,
                            "items": items,
                        }
                    )
            if func_items:
                l2_categories.append(
                    {
                        "type": "category",
                        "label": f"{l2_id} {l2_title}",
                        "collapsed": True,
                        "items": func_items,
                    }
                )
        if l2_categories:
            title = l1_lookup[l1_id]["title"]
            docs_items.append(
                {
                    "type": "category",
                    "label": f"{l1_id} {title}",
                    "collapsed": True,
                    "items": l2_categories,
                }
            )

    return {"docs": docs_items}


def build_registry_data(
    top_levels: list[dict[str, Any]], functions: list[dict[str, Any]], features: list[dict[str, Any]]
) -> dict[str, Any]:
    features_by_func: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for feature in features:
        features_by_func[str(feature["func_id"])].append(feature)

    function_cards: list[dict[str, Any]] = []
    for func in functions:
        func_id = str(func["id"])
        func_features = sort_features(features_by_func.get(func_id, []))
        has_docs = bool(func.get("design")) or any(item.get("spec") for item in func_features)
        status_counts = Counter(str(item.get("status", "unknown")) for item in func_features)
        function_cards.append(
            {
                "id": func_id,
                "l1": {"id": str(func["l1"]["id"]), "title": str(func["l1"]["title"])},
                "l2": {"id": str(func["l2"]["id"]), "title": str(func["l2"]["title"])},
                "l3": {"id": str(func["l3"]["id"]), "title": str(func["l3"]["title"])},
                "path": str(func["path"]),
                "design": str(func["design"]) if func.get("design") else None,
                "designDocId": doc_id(str(func["design"])) if func.get("design") else None,
                "status": str(func.get("status", "unknown")),
                "featureCount": len(func_features),
                "documentedFeatureCount": sum(1 for item in func_features if item.get("spec")),
                "statusCounts": dict(sorted(status_counts.items())),
                "hasDocs": has_docs,
                "features": [
                    {
                        "id": str(feature["id"]),
                        "title": str(feature["title"]),
                        "status": str(feature["status"]),
                        "spec": str(feature["spec"]) if feature.get("spec") else None,
                        "docId": doc_id(str(feature["spec"])) if feature.get("spec") else None,
                    }
                    for feature in func_features
                ],
            }
        )

    documented_functions = [item for item in function_cards if item["hasDocs"]]
    feature_status_counts = Counter(str(item.get("status", "unknown")) for item in features)
    return {
        "summary": {
            "topLevelCount": len(top_levels),
            "functionCount": len(functions),
            "documentedFunctionCount": len(documented_functions),
            "featureCount": len(features),
            "documentedFeatureCount": sum(1 for item in features if item.get("spec")),
            "functionWithDesignCount": sum(1 for item in functions if item.get("design")),
            "featureStatusCounts": dict(sorted(feature_status_counts.items())),
        },
        "topLevels": [
            {
                "id": str(item["id"]),
                "slug": str(item["slug"]),
                "title": str(item["title"]),
                "description": str(item["description"]),
                "functionCount": sum(1 for func in functions if str(func["l1"]["id"]) == str(item["id"])),
                "documentedFunctionCount": sum(
                    1 for func in documented_functions if str(func["l1"]["id"]) == str(item["id"])
                ),
            }
            for item in top_levels
        ],
        "functions": function_cards,
    }


def write_sidebar(sidebar: dict[str, Any]) -> None:
    SIDEBAR_FILE.write_text(
        "// This file is generated by tools/generate_site.py. Do not edit by hand.\n"
        "module.exports = "
        + json.dumps(sidebar, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def empty_spec_evaluation_data() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "available": False,
        "mode": "not-scanned",
        "generatedAt": None,
        "sourceRevision": None,
        "toolVersion": None,
        "ruleVersion": None,
        "summary": {
            "registeredFunctionCount": 0,
            "completedFunctionCount": 0,
            "errorCount": 0,
            "gateCounts": {"pass": 0, "warn": 0, "fail": 0, "error": 0},
            "findingCount": 0,
            "severityCounts": {"Critical": 0, "Major": 0, "Minor": 0, "Info": 0},
            "ruleCounts": {},
            "featureCount": 0,
            "documentCount": 0,
            "claimCount": 0,
            "resolvedClaimCount": 0,
            "evidenceCoverage": 0.0,
        },
        "functions": [],
    }


def load_archived_spec_evaluation(archive_root: Path = SPEC_EVAL_ARCHIVE_DIR) -> dict[str, Any]:
    pointer_path = archive_root / "latest.json"
    if not pointer_path.is_file():
        return empty_spec_evaluation_data()
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    report_value = pointer.get("siteReport")
    if not isinstance(report_value, str) or not report_value:
        raise ValueError(f"{pointer_path} must contain a non-empty siteReport path")
    report_path = (archive_root / report_value).resolve()
    try:
        report_path.relative_to(archive_root.resolve())
    except ValueError as error:
        raise ValueError(f"archived siteReport escapes {archive_root}: {report_value}") from error
    if not report_path.is_file():
        raise FileNotFoundError(f"archived spec evaluation report is missing: {report_path}")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or not isinstance(report.get("functions"), list):
        raise ValueError(f"invalid archived spec evaluation report: {report_path}")
    return report


def load_archived_semantic_evaluation(archive_root: Path = SPEC_EVAL_ARCHIVE_DIR) -> dict[str, Any]:
    report_path = archive_root / "site-evaluation-report.json"
    if not report_path.is_file():
        return {
            "schemaVersion": 1,
            "reportVersion": None,
            "available": False,
            "sourceRevision": None,
            "staticReport": {"path": "site-report.json", "sourceRevision": None},
            "summary": {
                "confirmedFunctionCount": 0,
                "expiredFunctionCount": 0,
                "functionCount": 0,
                "findingCount": 0,
                "expiredFindingCount": 0,
            },
            "functions": [],
        }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or not isinstance(report.get("functions"), list):
        raise ValueError(f"invalid archived semantic evaluation report: {report_path}")
    return report


def load_archived_evaluation_history(archive_root: Path = SPEC_EVAL_ARCHIVE_DIR) -> dict[str, Any]:
    report_path = archive_root / "site-evaluation-history.json"
    if not report_path.is_file():
        return {
            "schemaVersion": 1,
            "reportVersion": None,
            "available": False,
            "currentRevision": None,
            "summary": {
                "snapshotCount": 0,
                "comparisonStatus": "INITIAL",
                "baselineRevision": None,
                "currentFindingCount": 0,
                "addedFindingCount": 0,
                "resolvedFindingCount": 0,
                "persistentFindingCount": 0,
                "reclassifiedFindingCount": 0,
            },
            "snapshots": [],
            "recentDelta": {"summary": {}, "functions": [], "topAdded": [], "topResolved": [], "topReclassified": []},
            "activeFindings": [],
        }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or not isinstance(report.get("snapshots"), list):
        raise ValueError(f"invalid archived site evaluation history: {report_path}")
    return report


def site_history_data(report: dict[str, Any]) -> dict[str, Any]:
    """Exclude the active Finding index from the site JS bundle."""

    return {key: value for key, value in report.items() if key != "activeFindings"}


def spec_evaluation_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in report.items() if key != "functions"}


# --- dynamic (B-lite) mode: read the newest archived job per Function ---------


def _latest_jobs_by_func(archive_root: Path) -> dict[str, Path]:
    """Map each FuncID to its newest archived job directory.

    Ordering is taken from ``site-history-automated.jsonl`` (append-only, one
    line per archived job with ``func_id``/``job_id``/``created_at``); the DB is
    intentionally not consulted so a data-only refresh needs only the filesystem.
    Lines whose job directory is missing are skipped.
    """
    log_path = archive_root / AUTOMATED_HISTORY_LOG
    if not log_path.is_file():
        return {}
    latest: dict[str, tuple[str, Path]] = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        func_id = record.get("func_id")
        job_id = record.get("job_id")
        source_revision = record.get("source_revision")
        created_at = str(record.get("created_at", ""))
        if not (func_id and job_id and source_revision):
            continue
        job_dir = archive_root / source_revision / func_id / job_id
        if not (job_dir / "aggregate-report_json-evaluation-report.json").is_file():
            continue
        current = latest.get(func_id)
        if current is None or created_at >= current[0]:
            latest[func_id] = (created_at, job_dir)
    return {func_id: job_dir for func_id, (_, job_dir) in latest.items()}


def _observed_revision(latest_jobs: dict[str, Path]) -> str | None:
    """The most common source revision across the newest jobs, if any."""
    revisions = Counter(job_dir.parent.parent.name for job_dir in latest_jobs.values())
    if not revisions:
        return None
    return revisions.most_common(1)[0][0]


def build_dynamic_spec_evaluation(
    latest_jobs: dict[str, Path],
    functions: list[dict[str, Any]],
    features: list[dict[str, Any]],
    *,
    observed_revision: str | None,
) -> dict[str, Any]:
    """Build the static-scan ``spec-evaluation.json`` shape from archives.

    Reuses :class:`spec_eval.report.site_reporter.SiteReporter` by reconstructing
    its per-Function scan-result input from each archived evaluation report's
    ``static`` section plus the registry catalog (title/level/docs).
    """
    from spec_eval.report.site_reporter import SiteReporter

    features_by_func: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for feature in features:
        features_by_func[str(feature["func_id"])].append(feature)
    functions_by_id = {str(func["id"]): func for func in functions}

    tool_version = ""
    rule_version = ""
    scan_results: list[dict[str, Any]] = []
    for func_id, job_dir in sorted(latest_jobs.items()):
        report = _read_json(job_dir / "aggregate-report_json-evaluation-report.json")
        if report is None:
            continue
        static = report.get("static") if isinstance(report.get("static"), dict) else {}
        tool_version = tool_version or str(static.get("tool_version", ""))
        rule_version = rule_version or str(static.get("rule_version", ""))
        func_entry = functions_by_id.get(func_id, {"id": func_id})
        scan_results.append(
            {
                "func_id": func_id,
                "context": {
                    "function_registry_entry": func_entry,
                    "feature_registry_entries": sort_features(
                        features_by_func.get(func_id, [])
                    ),
                },
                "result": {
                    "static": static,
                    "evidence": {"metrics": static.get("metrics", {}).get("evidence", {})},
                },
            }
        )

    return SiteReporter().build(
        scan_results,
        source_revision=observed_revision or "",
        tool_version=tool_version,
        rule_version=rule_version,
        report_only=True,
    )


def build_dynamic_semantic_evaluation(
    latest_jobs: dict[str, Path],
    functions: list[dict[str, Any]],
    *,
    observed_revision: str | None,
) -> dict[str, Any]:
    """Build the confirmed-review ``semantic-evaluation.json`` shape from archives."""
    from spec_eval.service.site_export import _build_automated_site_evaluation

    functions_by_id = {str(func["id"]): func for func in functions}
    catalog_functions: list[dict[str, Any]] = []
    for func_id, job_dir in sorted(latest_jobs.items()):
        func_entry = functions_by_id.get(func_id, {})
        l3 = func_entry.get("l3") if isinstance(func_entry.get("l3"), dict) else {}
        catalog_functions.append(
            {
                "func_id": func_id,
                "title": str(l3.get("title") or func_id),
                "current_report": {"archive_path": str(job_dir)},
            }
        )
    # ``settings`` is unused by the builder; pass None to avoid the DB dependency.
    return _build_automated_site_evaluation(
        catalog_functions,
        settings=None,
        observed_revision=observed_revision or "",
    )


def build_dynamic_history(spec_evaluation: dict[str, Any]) -> dict[str, Any]:
    """Build the governance history document from the current dynamic snapshot.

    Dynamic mode has no confirmed-review chain, so history reduces to a single
    INITIAL snapshot derived from the current spec-evaluation document.
    """
    from spec_eval.report.site_evaluation_history import build_site_evaluation_history

    if not spec_evaluation.get("available"):
        return load_archived_evaluation_history(archive_root=Path("/nonexistent"))
    try:
        return build_site_evaluation_history(current_report=spec_evaluation)
    except Exception:  # noqa: BLE001 - history is best-effort in dynamic mode
        return load_archived_evaluation_history(archive_root=Path("/nonexistent"))


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_dynamic_evaluation(
    functions: list[dict[str, Any]],
    features: list[dict[str, Any]],
    *,
    archive_root: Path = AUTOMATED_ARCHIVE_DIR,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Return (spec_evaluation, semantic_evaluation, history) built from archives."""
    latest_jobs = _latest_jobs_by_func(archive_root)
    if not latest_jobs:
        return (
            empty_spec_evaluation_data(),
            load_archived_semantic_evaluation(archive_root=Path("/nonexistent")),
            load_archived_evaluation_history(archive_root=Path("/nonexistent")),
        )
    observed_revision = _observed_revision(latest_jobs)
    spec_evaluation = build_dynamic_spec_evaluation(
        latest_jobs, functions, features, observed_revision=observed_revision
    )
    semantic_evaluation = build_dynamic_semantic_evaluation(
        latest_jobs, functions, observed_revision=observed_revision
    )
    history = build_dynamic_history(spec_evaluation)
    return spec_evaluation, semantic_evaluation, history


def _write_json(path: Path, document: dict[str, Any], *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(document, ensure_ascii=False, indent=2)
    path.write_text(text + "\n", encoding="utf-8")


def write_evaluation_data(
    spec_evaluation: dict[str, Any],
    semantic_evaluation: dict[str, Any],
    evaluation_history: dict[str, Any],
    *,
    mode: str,
) -> list[Path]:
    """Write the five evaluation documents the site consumes.

    The full spec/semantic reports go to ``static/data`` (runtime-fetched). The
    summary/history documents go to ``src/data`` (build-time import) and, in
    dynamic mode, are ALSO mirrored into ``static/data`` so a data-only refresh
    is visible on browser reload without a webpack rebuild.
    """
    spec_summary = spec_evaluation_summary(spec_evaluation)
    semantic_summary = spec_evaluation_summary(semantic_evaluation)
    history_document = site_history_data(evaluation_history)

    written: list[Path] = []
    _write_json(SPEC_EVAL_SUMMARY_JSON, spec_summary)
    _write_json(SPEC_EVAL_STATIC_JSON, spec_evaluation, compact=True)
    _write_json(SEMANTIC_EVAL_SUMMARY_JSON, semantic_summary)
    _write_json(SEMANTIC_EVAL_STATIC_JSON, semantic_evaluation, compact=True)
    _write_json(SPEC_EVAL_HISTORY_JSON, history_document)
    written += [
        SPEC_EVAL_SUMMARY_JSON,
        SPEC_EVAL_STATIC_JSON,
        SEMANTIC_EVAL_SUMMARY_JSON,
        SEMANTIC_EVAL_STATIC_JSON,
        SPEC_EVAL_HISTORY_JSON,
    ]

    # Runtime-fetched mirrors + runtime descriptor so the page can pick its
    # data source without a rebuild.
    _write_json(SPEC_EVAL_SUMMARY_STATIC_JSON, spec_summary)
    _write_json(SEMANTIC_EVAL_SUMMARY_STATIC_JSON, semantic_summary)
    _write_json(SPEC_EVAL_HISTORY_STATIC_JSON, history_document)
    _write_json(SITE_RUNTIME_JSON, {"schemaVersion": 1, "mode": mode})
    written += [
        SPEC_EVAL_SUMMARY_STATIC_JSON,
        SEMANTIC_EVAL_SUMMARY_STATIC_JSON,
        SPEC_EVAL_HISTORY_STATIC_JSON,
        SITE_RUNTIME_JSON,
    ]
    return written


def load_static_evaluation() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Load the single-snapshot archived documents used by static mode."""
    spec_evaluation = load_archived_spec_evaluation()
    semantic_evaluation = load_archived_semantic_evaluation()
    evaluation_history = load_archived_evaluation_history()
    if (
        semantic_evaluation.get("available")
        and semantic_evaluation.get("sourceRevision") != spec_evaluation.get("sourceRevision")
    ):
        raise ValueError(
            "semantic and static site archives use different source revisions: "
            f"{semantic_evaluation.get('sourceRevision')} != {spec_evaluation.get('sourceRevision')}"
        )
    if (
        evaluation_history.get("available")
        and evaluation_history.get("currentRevision") != semantic_evaluation.get("sourceRevision")
    ):
        raise ValueError(
            "history and semantic site archives use different source revisions: "
            f"{evaluation_history.get('currentRevision')} != {semantic_evaluation.get('sourceRevision')}"
        )
    return spec_evaluation, semantic_evaluation, evaluation_history


def generate_data_only(mode: str) -> None:
    """Regenerate only the evaluation data files (no docs/sidebar/registry).

    This is the B-lite refresh entry point: on each new archive the CI hook can
    rebuild just ``static/data`` (and mirror into the served ``build/data``) so
    the site reflects the latest reports on browser reload, with no rebuild.
    """
    functions_data = load_yaml(FUNCTIONS_FILE)
    features_data = load_yaml(FEATURES_FILE)
    functions = functions_data.get("functions", [])
    features = features_data.get("features", [])
    STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if mode == "dynamic":
        spec_evaluation, semantic_evaluation, evaluation_history = load_dynamic_evaluation(
            functions, features
        )
    else:
        spec_evaluation, semantic_evaluation, evaluation_history = load_static_evaluation()

    written = write_evaluation_data(
        spec_evaluation, semantic_evaluation, evaluation_history, mode=mode
    )
    for path in written:
        print(f"generated {path.relative_to(ROOT)}")

    # Mirror the runtime-fetched files into the already-built site so the served
    # site reflects the refresh on reload without a Docusaurus rebuild. Only the
    # files Docusaurus copies from ``static/data`` are mirrored (not the
    # ``src/data`` build-time imports, which require a rebuild to take effect).
    if BUILD_DATA_DIR.is_dir():
        for path in written:
            try:
                relative = path.relative_to(STATIC_DATA_DIR)
            except ValueError:
                continue
            destination = BUILD_DATA_DIR / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            print(f"mirrored {destination.relative_to(ROOT)}")


def watch_data_only(mode: str, poll_interval: float) -> None:
    """Refresh the evaluation data files whenever the archive log changes.

    Watches the append-only ``site-history-automated.jsonl`` the CI service
    writes on each new archive; on any change (mtime/size) it re-runs the
    data-only refresh. Runs an initial refresh immediately, then polls. Only
    meaningful with ``--mode dynamic``.
    """
    import time

    log_path = AUTOMATED_ARCHIVE_DIR / AUTOMATED_HISTORY_LOG
    print(f"[watch] refreshing on changes to {log_path} every {poll_interval}s (mode={mode})")
    last_signature: tuple[int, int] | None = None
    while True:
        try:
            stat = log_path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            signature = None
        if signature != last_signature:
            last_signature = signature
            try:
                generate_data_only(mode)
            except Exception as error:  # noqa: BLE001 - a watch loop must not die
                print(f"[watch] refresh failed: {error}", file=sys.stderr)
        try:
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("[watch] stopped")
            return


def generate(mode: str = "static") -> None:
    functions_data = load_yaml(FUNCTIONS_FILE)
    features_data = load_yaml(FEATURES_FILE)
    top_levels = functions_data.get("top_levels", [])
    functions = functions_data.get("functions", [])
    features = features_data.get("features", [])

    shutil.rmtree(DOCS_DIR, ignore_errors=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

    docs_to_copy = {"index.md", "registry/README.md"}
    for func in functions:
        if func.get("design"):
            docs_to_copy.add(str(func["design"]))
    for feature in features:
        if feature.get("spec"):
            docs_to_copy.add(str(feature["spec"]))

    missing: list[str] = []
    for rel_path in sorted(docs_to_copy):
        source = ROOT / rel_path
        if not source.is_file():
            missing.append(rel_path)
            continue
        copy_markdown(source, DOCS_DIR / rel_path)
    if missing:
        raise FileNotFoundError("registered docs are missing: " + ", ".join(missing))

    write_sidebar(build_sidebar(top_levels, functions, features))
    REGISTRY_JSON.write_text(
        json.dumps(build_registry_data(top_levels, functions, features), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if mode == "dynamic":
        spec_evaluation, semantic_evaluation, evaluation_history = load_dynamic_evaluation(
            functions, features
        )
    else:
        spec_evaluation, semantic_evaluation, evaluation_history = load_static_evaluation()

    write_evaluation_data(
        spec_evaluation, semantic_evaluation, evaluation_history, mode=mode
    )

    print(f"generated {DOCS_DIR.relative_to(ROOT)}")
    print(f"generated {SIDEBAR_FILE.relative_to(ROOT)}")
    print(f"generated {REGISTRY_JSON.relative_to(ROOT)}")
    print(f"generated {SPEC_EVAL_SUMMARY_JSON.relative_to(ROOT)}")
    print(f"generated {SPEC_EVAL_STATIC_JSON.relative_to(ROOT)}")
    print(f"generated {SEMANTIC_EVAL_SUMMARY_JSON.relative_to(ROOT)}")
    print(f"generated {SEMANTIC_EVAL_STATIC_JSON.relative_to(ROOT)}")
    print(f"generated {SPEC_EVAL_HISTORY_JSON.relative_to(ROOT)}")
    print(f"generated {SITE_RUNTIME_JSON.relative_to(ROOT)} (mode={mode})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["static", "dynamic"],
        default="static",
        help=(
            "static: bake the single archived snapshot from .evaluator/ (default). "
            "dynamic: read the newest archived job per Function from the CI "
            "service archives for a B-lite refresh."
        ),
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help=(
            "regenerate only the evaluation data files under site/static/data "
            "(no docs/sidebar/registry rebuild); intended for the per-archive "
            "refresh hook."
        ),
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help=(
            "keep running and re-refresh the data files whenever the archive log "
            "changes (implies --data-only). Use with --mode dynamic to keep the "
            "served site current without a rebuild."
        ),
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=60.0,
        help="seconds between archive-log checks in --watch mode (default 60).",
    )
    args = parser.parse_args()
    if args.watch:
        watch_data_only(args.mode, args.poll_interval)
    elif args.data_only:
        generate_data_only(args.mode)
    else:
        generate(args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
