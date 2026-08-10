#!/usr/bin/env python3
"""Async CI Worker for GitCode Merge Request webhook receipts.

Consumes the append-only receipt log written by ``gitcode_webhook.py`` and, for
each unprocessed delivery, runs the report-only static evaluation
(``ci_runner.py``) over the PR's changed specs files, archives the result
per-PR/per-delivery, and posts an updatable summary comment back to the PR via
``oh-gc``.

The Worker is report-only and non-blocking: it never passes ``--enforce`` or
``--delta-enforce`` and does not gate the PR. Semantic evaluation and blocking
gates are intentionally out of scope (see handoff NEXT-010). It is idempotent:
receipts are de-duplicated on ingest (``ReceiptStore``) and on processing
(``processed.ndjson`` keyed by ``delivery_id``), and the PR comment is edited in
place via a hidden marker rather than re-posted.
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LOGGER = logging.getLogger("spec_eval.ci_worker")

COMMENT_MARKER = "<!-- spec-eval-bot:updatable:v1 -->"
DEFAULT_BOT_LOGIN = "arkui_architecture"
DEFAULT_ALLOW_PROJECTS = ("arkui_architecture/arkui-specs",)

EXIT_OK = 0
EXIT_TOOL_ERROR = 2
EXIT_INCOMPLETE = 3

SEVERITY_EMOJI = {"Critical": "🔴", "Major": "🟠", "Minor": "🟡", "Info": "⚪"}


@dataclass
class WorkerContext:
    """Resolved configuration shared across receipt processing."""

    repo_root: Path
    specs_root: Path
    receipts: Path
    processed_ledger: Path
    baseline: Path
    output_root: Path
    ci_runner: Path
    repo: str
    allow_projects: tuple[str, ...]
    bot_login: str
    top: int
    no_cache: bool
    dry_run: bool
    no_comment: bool
    auto_checkout: bool
    oh_gc: str
    python: str


# --------------------------------------------------------------------------- #
# Receipt + ledger I/O
# --------------------------------------------------------------------------- #
def load_receipts(path: Path) -> list[dict[str, Any]]:
    """Load all receipts from an append-only NDJSON log."""
    if not path.is_file():
        return []
    receipts: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid receipt JSON at {path}:{lineno}: {exc.msg}") from exc
        if isinstance(value, dict):
            receipts.append(value)
    return receipts


def processed_set(path: Path) -> set[str]:
    """Return the set of delivery ids already handled by a prior Worker run."""
    if not path.is_file():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ids.add(json.loads(line)["delivery_id"])
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return ids


def mark_processed(path: Path, delivery_id: str, **info: Any) -> None:
    """Append a completion record for ``delivery_id`` (the idempotency boundary)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"delivery_id": delivery_id, **info, "finished_at": _now_iso()}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


# --------------------------------------------------------------------------- #
# Per-receipt steps (small, testable)
# --------------------------------------------------------------------------- #
def passes_whitelist(receipt: dict[str, Any], allowed: Iterable[str]) -> bool:
    project = (receipt.get("project") or {}).get("path_with_namespace")
    return project in set(allowed)


def resolve_shas(receipt: dict[str, Any]) -> tuple[str | None, str | None]:
    revisions = receipt.get("revisions") or {}
    return revisions.get("target"), revisions.get("tested")


def _git(specs_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(specs_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def ensure_specs_at_sha(
    specs_root: Path,
    tested: str | None,
    *,
    auto_checkout: bool,
) -> tuple[str | None, bool, str, str | None]:
    """Ensure ``ace_engine/specs`` is at ``tested``.

    Returns ``(current_sha, ok, action, restore_ref)``. ``restore_ref`` is the
    original branch/SHA to checkout back, set only when the Worker detached HEAD
    (``--auto-checkout``). The evaluator must run in place because
    ``config.py`` hard-codes ``specs_root = parents[3]/specs``; a separate
    worktree breaks that path math, so we never use one.
    """
    rev = _git(specs_root, "rev-parse", "HEAD")
    if rev.returncode != 0:
        return None, False, "git_error", None
    current = rev.stdout.strip()
    if tested is None:
        return current, False, "missing_tested_sha", None
    if current == tested:
        return current, True, "matched", None
    if not auto_checkout:
        return current, False, "skipped_mismatch", None
    symbolic = _git(specs_root, "symbolic-ref", "--short", "HEAD")
    restore = symbolic.stdout.strip() if (symbolic.returncode == 0 and symbolic.stdout.strip()) else current
    checkout = _git(specs_root, "checkout", "--detach", tested)
    if checkout.returncode != 0:
        return current, False, "checkout_failed", None
    return current, True, "checked_out", restore


def compute_changed_files(specs_root: Path, target: str | None, tested: str | None) -> tuple[list[str], str]:
    """Diff ``target..tested`` and return ``specs/``-prefixed paths.

    ``git -C specs diff`` emits specs-root-relative paths (no ``specs/`` prefix),
    but ``ChangedFunctionResolver`` joins candidates onto ``repo_root`` and the
    registry stores specs-root-relative ``path:`` values resolved under
    ``specs_root``. The prefix is therefore load-bearing: without it, real spec
    changes silently map to zero affected Functions.
    """
    if not target or not tested:
        return [], "missing_target_sha"
    result = _git(specs_root, "diff", "--name-only", target, tested)
    if result.returncode != 0:
        return [], "diff_failed"
    bare = sorted({line.strip() for line in result.stdout.splitlines() if line.strip()})
    prefixed = [f"specs/{path}" for path in bare]
    return prefixed, "ok"


def run_ci_runner(
    *,
    runner: Path,
    files_from: Path,
    baseline: Path,
    output_dir: Path,
    repo_root: Path,
    top: int = 5,
    no_cache: bool = False,
    python: str = "python3",
) -> tuple[dict[str, Any] | None, int, float, str]:
    """Invoke ``ci_runner.py`` report-only; return ``(summary, exit_code, elapsed_ms, stderr)``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        python,
        str(runner),
        "--files-from",
        str(files_from),
        "--baseline",
        str(baseline),
        "--output",
        str(output_dir),
        "--top",
        str(top),
        "--json",
        "--quiet",
    ]
    if no_cache:
        command.append("--no-cache")
    started = time.perf_counter()
    proc = subprocess.run(command, cwd=str(repo_root), capture_output=True, text=True, check=False)
    elapsed = (time.perf_counter() - started) * 1000.0
    summary: dict[str, Any] | None = None
    stdout = proc.stdout.strip()
    if stdout:
        try:
            summary = json.loads(stdout)
        except json.JSONDecodeError:
            summary = None
    return summary, proc.returncode, elapsed, proc.stderr.strip()


def render_comment(
    ci_summary: dict[str, Any],
    receipt: dict[str, Any],
    *,
    shas: dict[str, str | None],
    ensure_action: str,
    exit_code: int = EXIT_OK,
) -> str:
    """Render the updatable PR comment markdown from a ci-summary.

    Pure function: no I/O. ``ci_summary`` follows the schema written by
    ``ci_runner.run`` (see ``ci_runner.py``).
    """
    pull_request = receipt.get("pull_request") or {}
    iid = pull_request.get("iid")
    source_branch = pull_request.get("source_branch", "")
    target_branch = pull_request.get("target_branch", "")
    delivery = receipt.get("delivery_id", "")
    delivery_short = _short(delivery, 18)

    affected = int(ci_summary.get("affected_function_count", 0) or 0)
    delta = ci_summary.get("delta") or {}
    added = int(delta.get("added", 0) or 0)
    resolved = int(delta.get("resolved", 0) or 0)
    reclassified = int(delta.get("reclassified", 0) or 0)
    error_count = int(ci_summary.get("error_count", 0) or 0)
    functions = ci_summary.get("functions") or []
    baseline = ci_summary.get("baseline") or {}
    changed_files = ci_summary.get("changed_files") or []
    src_rev = ci_summary.get("source_revision", "")
    tested = shas.get("tested")
    target = shas.get("target")

    lines: list[str] = [COMMENT_MARKER, "## 🤖 spec-evaluator (report-only)", ""]
    lines += [
        "| | |",
        "|---|---|",
        f"| **PR** | !{iid} ({source_branch} → {target_branch}) |",
        f"| **Delivery** | `{delivery_short}` |",
        f"| **Specs head** | `{_short(tested)}` · **Target** `{_short(target)}` |",
        f"| **ace_engine** | `{_short(src_rev)}` |",
        "| **Mode** | report-only (non-blocking) |",
        f"| **Baseline** | {Path(baseline.get('path', 'current.json')).name} @ `{_short(baseline.get('source_revision'))}`"
        f" (rule v{baseline.get('rule_version', '?')}, identity v{baseline.get('identity_version', '?')}) |",
        "",
    ]

    if error_count > 0:
        lines.append(f"**⚠️ evaluation incomplete for {error_count} Function(s) — see below.**")
    elif affected == 0:
        lines.append(
            f"**Result:** 0 affected Functions · {len(changed_files)} changed file(s) · no new errors ✅"
        )
        lines.append("")
        lines.append(
            "> No spec-bearing Function paths matched this change (tooling/non-spec files); "
            "no evaluation was needed."
        )
    elif added == 0:
        lines.append(
            f"**Result:** {affected} affected Function(s) · {len(changed_files)} changed file(s) · "
            "**no new errors** ✅"
        )
    else:
        lines.append(
            f"**Result:** {affected} affected Function(s) · **⚠️ {added} new error(s)**"
        )
    lines.append("")
    lines.append(
        f"**Delta vs baseline:** ➕ added {added} · ➖ resolved {resolved} · 🔄 reclassified {reclassified}"
    )
    lines.append("")

    if affected > 0 and added > 0:
        lines += ["### New findings", "", "| Function | Rule | Severity | Location | Message |", "|---|---|---|---|---|"]
        rows = 0
        for function in functions:
            for finding in function.get("top_added_findings") or []:
                severity = finding.get("severity", "Info")
                location = finding.get("path", "")
                line_no = finding.get("line")
                if line_no:
                    location = f"{location}:{line_no}"
                message = (finding.get("message", "") or "").replace("|", "\\|").replace("\n", " ")
                rule_id = finding.get("rule_id", "")
                lines.append(
                    f"| {function.get('func_id', '')} | {rule_id} | {SEVERITY_EMOJI.get(severity, '')} {severity} "
                    f"| `{location}` | {message} |"
                )
                rows += 1
        if rows == 0:
            lines.append("| _(no top added findings surfaced; see full report)_ | | | | |")
        lines.append("")

    if error_count > 0:
        lines += ["### Incomplete evaluations", ""]
        for function in functions:
            if function.get("gate") == "error":
                lines.append(f"- `{function.get('func_id', '')}`: {function.get('error', 'evaluation error')}")
        lines.append("")

    lines += [
        "<details><summary>How this was computed</summary>",
        "",
        f"- Specs head verified at `{_short(tested)}` (ensure action: `{ensure_action}`).",
        f"- Changed files: `git -C specs diff --name-only {_short(target)} {_short(tested)}` "
        f"({len(changed_files)} path(s)), each prefixed `specs/` and resolved against `functions.yaml`.",
        "- Evaluation: `ci_runner.py --files-from … --baseline current.json` "
        f"(report-only, exit {exit_code}).",
        "- \"No new errors\" means `delta.added == 0` after exemptions; pre-existing baseline findings "
        "are unchanged debt, not claimed resolved.",
        "- This comment is updatable: re-runs edit it in place.",
        "",
        "</details>",
        "",
    ]
    return "\n".join(lines)


def _oh_gc(args: list[str], *, oh_gc: str) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([oh_gc, *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"oh-gc failed (exit {proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc


def _oh_gc_json(args: list[str], *, oh_gc: str) -> Any:
    """Run an oh-gc command and parse its JSON stdout."""
    proc = _oh_gc(args, oh_gc=oh_gc)
    stdout = proc.stdout.strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"oh-gc returned non-JSON output: {stdout[:160]!r}") from exc


def post_or_update_comment(
    repo: str,
    pr_iid: Any,
    body: str,
    *,
    bot_login: str = DEFAULT_BOT_LOGIN,
    dry_run: bool = False,
    oh_gc: str = "oh-gc",
) -> dict[str, Any]:
    """Create or edit-in-place the bot's updatable PR comment."""
    if dry_run:
        return {"action": "dry-run", "id": None, "url": None}
    comments = _oh_gc_json(
        ["pr", "comments", str(pr_iid), "--repo", repo, "--json", "--comment-type", "pr_comment"],
        oh_gc=oh_gc,
    ) or []
    own = [c for c in comments if isinstance(c, dict) and COMMENT_MARKER in (c.get("body") or "")]
    if own:
        target = max(own, key=lambda c: int(c.get("id") or 0))
        comment_id = target.get("id")
        # ``pr comment-edit --json`` prints ``undefined`` (oh-gc quirk), so we do
        # not parse its stdout; success is the zero exit code from ``_oh_gc``.
        _oh_gc(
            ["pr", "comment-edit", str(comment_id), "--repo", repo, "--body", body],
            oh_gc=oh_gc,
        )
        return {"action": "updated", "id": comment_id, "url": target.get("url")}
    created = _oh_gc_json(
        ["pr", "comment", str(pr_iid), "--repo", repo, "--body", body, "--json"],
        oh_gc=oh_gc,
    ) or {}
    return {"action": "created", "id": created.get("id"), "url": created.get("url")}


# --------------------------------------------------------------------------- #
# Archive
# --------------------------------------------------------------------------- #
def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _archive_dir_for(output_root: Path, iid: Any, delivery_id: str) -> Path:
    safe_delivery = (delivery_id or "unknown").replace("/", "_")
    return output_root / f"pr-{iid}" / safe_delivery


def write_run_meta(
    archive_dir: Path,
    *,
    receipt: dict[str, Any],
    ctx: WorkerContext,
    shas: dict[str, str | None],
    specs_head_before: str | None,
    ensure_action: str,
    ci_summary: dict[str, Any] | None,
    exit_code: int | None,
    incomplete: bool,
    changed_files: list[str],
    comment_result: dict[str, Any] | None,
    timing: dict[str, float],
    status: str,
    error: str | None = None,
) -> dict[str, Any]:
    pull_request = receipt.get("pull_request") or {}
    baseline_meta = (ci_summary or {}).get("baseline") or {}
    meta = {
        "delivery_id": receipt.get("delivery_id"),
        "pr_iid": pull_request.get("iid"),
        "repo": ctx.repo,
        "received_at": receipt.get("received_at"),
        "action": receipt.get("action"),
        "state": receipt.get("state"),
        "source_branch": pull_request.get("source_branch"),
        "target_branch": pull_request.get("target_branch"),
        "shas": {
            "tested": shas.get("tested"),
            "target": shas.get("target"),
            "specs_head_before": specs_head_before,
            "ensure_action": ensure_action,
        },
        "ace_engine_revision": (ci_summary or {}).get("source_revision"),
        "baseline": {
            "path": str(ctx.baseline),
            "source_revision": baseline_meta.get("source_revision"),
            "rule_version": baseline_meta.get("rule_version"),
            "identity_version": baseline_meta.get("identity_version"),
        },
        "mode": (ci_summary or {}).get("mode", "report-only"),
        "changed_file_count": len(changed_files),
        "affected_function_count": (ci_summary or {}).get("affected_function_count"),
        "delta": (ci_summary or {}).get("delta"),
        "exit_code": exit_code,
        "incomplete": incomplete,
        "gate": {
            "absolute_failed": (ci_summary or {}).get("absolute_gate_failed_count"),
            "delta_failed": (ci_summary or {}).get("delta_gate_failed_count"),
            "delta_warn": (ci_summary or {}).get("delta_warn_count"),
            "errors": (ci_summary or {}).get("error_count"),
        },
        "comment": comment_result,
        "timing_ms": timing,
        "status": status,
        "started_at": None,
        "finished_at": _now_iso(),
        "error": error,
    }
    _write_json(archive_dir / "run-meta.json", meta)
    return meta


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
def process_receipt(receipt: dict[str, Any], ctx: WorkerContext) -> dict[str, Any]:
    """Process one receipt end-to-end. Always idempotent (caller marks processed)."""
    delivery = receipt.get("delivery_id")
    pull_request = receipt.get("pull_request") or {}
    iid = pull_request.get("iid")
    started = time.perf_counter()
    timing: dict[str, float] = {}
    result: dict[str, Any] = {"delivery_id": delivery, "pr_iid": iid}

    if not passes_whitelist(receipt, ctx.allow_projects):
        result["status"] = "skipped_whitelist"
        LOGGER.info("delivery=%s skipped (project not whitelisted)", delivery)
        return result

    target, tested = resolve_shas(receipt)
    shas = {"tested": tested, "target": target}
    archive_dir = _archive_dir_for(ctx.output_root, iid, delivery)
    result["archive_dir"] = archive_dir.as_posix()

    specs_head_before, ok, action, restore_ref = ensure_specs_at_sha(
        ctx.specs_root, tested, auto_checkout=ctx.auto_checkout
    )
    try:
        if not ok:
            LOGGER.warning("delivery=%s ensure_specs action=%s (tested=%s head=%s)", delivery, action, tested, specs_head_before)
            write_run_meta(
                archive_dir,
                receipt=receipt,
                ctx=ctx,
                shas=shas,
                specs_head_before=specs_head_before,
                ensure_action=action,
                ci_summary=None,
                exit_code=None,
                incomplete=False,
                changed_files=[],
                comment_result=None,
                timing=timing,
                status=action,
                error=f"specs HEAD {specs_head_before} != tested {tested}",
            )
            result["status"] = action
            return result

        archive_dir.mkdir(parents=True, exist_ok=True)
        changed_files, diff_status = compute_changed_files(ctx.specs_root, target, tested)
        (archive_dir / "changed-files.txt").write_text(
            "\n".join(changed_files) + ("\n" if changed_files else ""), encoding="utf-8"
        )
        files_from = archive_dir / "files-from.txt"
        files_from.write_text("\n".join(changed_files) + ("\n" if changed_files else ""), encoding="utf-8")
        if diff_status != "ok":
            result["status"] = diff_status
            write_run_meta(
                archive_dir, receipt=receipt, ctx=ctx, shas=shas, specs_head_before=specs_head_before,
                ensure_action=action, ci_summary=None, exit_code=None, incomplete=False,
                changed_files=changed_files, comment_result=None, timing=timing, status=diff_status,
            )
            return result

        summary, exit_code, ci_elapsed, stderr = run_ci_runner(
            runner=ctx.ci_runner,
            files_from=files_from,
            baseline=ctx.baseline,
            output_dir=archive_dir / "out",
            repo_root=ctx.repo_root,
            top=ctx.top,
            no_cache=ctx.no_cache,
            python=ctx.python,
        )
        timing["ci_runner_ms"] = round(ci_elapsed, 3)

        if exit_code == EXIT_TOOL_ERROR or summary is None:
            error = "ci_runner tool error"
            if summary and summary.get("error"):
                error = str(summary.get("error"))
            elif stderr:
                error = stderr[:500]
            write_run_meta(
                archive_dir, receipt=receipt, ctx=ctx, shas=shas, specs_head_before=specs_head_before,
                ensure_action=action, ci_summary=summary, exit_code=exit_code, incomplete=False,
                changed_files=changed_files, comment_result=None, timing=timing, status="tool_error",
                error=error,
            )
            (archive_dir / "ci-runner-stderr.log").write_text(stderr, encoding="utf-8")
            result["status"] = "tool_error"
            result["affected_function_count"] = None
            return result

        incomplete = exit_code == EXIT_INCOMPLETE
        comment_body = render_comment(
            summary,
            receipt,
            shas=shas,
            ensure_action=action,
            exit_code=exit_code,
        )
        (archive_dir / "comment-body.md").write_text(comment_body, encoding="utf-8")
        try:
            comment_result = post_or_update_comment(
                ctx.repo, iid, comment_body,
                bot_login=ctx.bot_login,
                dry_run=ctx.dry_run or ctx.no_comment,
                oh_gc=ctx.oh_gc,
            )
        except Exception as exc:  # noqa: BLE001 - posting must not abort archiving
            LOGGER.exception("delivery=%s comment post failed", delivery)
            comment_result = {"action": "error", "error": str(exc)}
        (archive_dir / "comment.json").write_text(
            json.dumps(comment_result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _write_json(archive_dir / "ci-summary.json", summary)

        timing["total_ms"] = round((time.perf_counter() - started) * 1000.0, 3)
        write_run_meta(
            archive_dir, receipt=receipt, ctx=ctx, shas=shas, specs_head_before=specs_head_before,
            ensure_action=action, ci_summary=summary, exit_code=exit_code, incomplete=incomplete,
            changed_files=changed_files, comment_result=comment_result, timing=timing,
            status="incomplete" if incomplete else "ok",
        )
        result.update(
            {
                "status": "incomplete" if incomplete else "ok",
                "affected_function_count": summary.get("affected_function_count"),
                "delta": summary.get("delta"),
                "exit_code": exit_code,
                "comment": comment_result,
                "archive_dir": archive_dir.as_posix(),
            }
        )
        LOGGER.info(
            "delivery=%s pr=%s status=%s affected=%s exit=%s comment=%s",
            delivery, iid, result["status"], result.get("affected_function_count"),
            exit_code, comment_result.get("action"),
        )
        return result
    finally:
        if restore_ref is not None:
            _git(ctx.specs_root, "checkout", restore_ref)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short(value: str | None, length: int = 7) -> str:
    if not value:
        return "—"
    return value if len(value) <= length else value[:length]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Process GitCode MR webhook receipts into report-only CI evaluations")
    parser.add_argument("--receipts", type=Path, default=Path("specs/.evaluator/webhook/receipts.ndjson"))
    parser.add_argument("--processed-ledger", type=Path, default=Path("specs/.evaluator/ci/processed.ndjson"))
    parser.add_argument("--baseline", type=Path, default=Path("specs/evaluation/baselines/current.json"))
    parser.add_argument("--output-root", type=Path, default=Path("specs/.evaluator/ci"))
    parser.add_argument("--specs-root", type=Path, help="specs checkout root (default: <ci_worker>/parents[2])")
    parser.add_argument("--ci-runner", type=Path, default=Path("specs/tools/spec_eval/ci_runner.py"))
    parser.add_argument("--repo", default="arkui_architecture/arkui-specs", help="GitCode owner/repo for comment writeback")
    parser.add_argument("--allow-project", action="append", dest="allow_projects", help="whitelisted project path (repeatable)")
    parser.add_argument("--bot-login", default=DEFAULT_BOT_LOGIN)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--no-cache", action="store_true", help="disable ci_runner exact-input cache")
    parser.add_argument("--dry-run", action="store_true", help="do everything except post the PR comment")
    parser.add_argument("--no-comment", action="store_true", help="skip oh-gc comment posting (archive still written)")
    parser.add_argument("--auto-checkout", action="store_true", help="detached-HEAD checkout specs to tested SHA on mismatch")
    parser.add_argument("--process-limit", type=int, default=0, help="process at most N unprocessed receipts (0=all)")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="stay resident: poll the receipts file and process new deliveries as they arrive",
    )
    parser.add_argument("--poll-interval", type=int, default=10, help="--watch poll interval in seconds (default 10)")
    parser.add_argument("--oh-gc", default="oh-gc")
    parser.add_argument("--python", default="python3")
    parser.add_argument("--json", action="store_true", help="print one JSON line per processed receipt")
    return parser


def _resolve(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else (root / path).resolve()


def build_context(args: argparse.Namespace) -> WorkerContext:
    specs_root = (args.specs_root or Path(__file__).resolve().parents[2]).resolve()
    repo_root = specs_root.parent.resolve()
    return WorkerContext(
        repo_root=repo_root,
        specs_root=specs_root,
        receipts=_resolve(args.receipts, repo_root),
        processed_ledger=_resolve(args.processed_ledger, repo_root),
        baseline=_resolve(args.baseline, repo_root),
        output_root=_resolve(args.output_root, repo_root),
        ci_runner=_resolve(args.ci_runner, repo_root),
        repo=args.repo,
        allow_projects=tuple(args.allow_projects or DEFAULT_ALLOW_PROJECTS),
        bot_login=args.bot_login,
        top=args.top,
        no_cache=args.no_cache,
        dry_run=args.dry_run,
        no_comment=args.no_comment,
        auto_checkout=args.auto_checkout,
        oh_gc=args.oh_gc,
        python=args.python,
    )


def run_once(ctx: WorkerContext, *, process_limit: int, emit_json: bool) -> int:
    """Process all currently-pending receipts once. Returns the count processed."""
    done = processed_set(ctx.processed_ledger)
    receipts = load_receipts(ctx.receipts)
    processed = 0
    for receipt in receipts:
        delivery = receipt.get("delivery_id")
        if delivery in done:
            continue
        if process_limit and processed >= process_limit:
            break
        result = process_receipt(receipt, ctx)
        mark_processed(
            ctx.processed_ledger,
            delivery,
            status=result.get("status"),
            archive=result.get("archive_dir"),
        )
        processed += 1
        if emit_json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    return processed


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    ctx = build_context(args)
    if args.watch:
        # In watch mode every tick drains all pending receipts; --process-limit
        # is a one-shot batch control and does not apply per tick.
        LOGGER.info(
            "watch mode: polling %s every %ds (ledger=%s)",
            ctx.receipts, args.poll_interval, ctx.processed_ledger,
        )
        try:
            while True:
                processed = run_once(ctx, process_limit=0, emit_json=args.json)
                if processed:
                    LOGGER.info("watch tick: processed %d receipt(s)", processed)
                time.sleep(args.poll_interval)
        except KeyboardInterrupt:
            LOGGER.info("watch interrupted, exiting")
        return EXIT_OK
    processed = run_once(ctx, process_limit=args.process_limit, emit_json=args.json)
    already = len(processed_set(ctx.processed_ledger))
    LOGGER.info("processed %d receipt(s) (%d already done)", processed, already)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
