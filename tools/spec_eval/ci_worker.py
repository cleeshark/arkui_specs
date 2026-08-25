#!/usr/bin/env python3
"""Async CI Worker for GitCode Merge Request webhook receipts.

Consumes the append-only receipt log written by ``gitcode_webhook.py`` and, for
each unprocessed delivery, runs the report-only static evaluation
(``ci_runner.py``) over the PR's changed specs files, archives the result
per-PR/per-delivery, and posts a fresh summary comment to the PR via
``oh-gc``.

The Worker is report-only and non-blocking: it never passes ``--enforce`` or
``--delta-enforce`` and does not gate the PR. Semantic evaluation and blocking
gates are intentionally out of scope (see handoff NEXT-010). It is idempotent:
receipts are de-duplicated on ingest (``ReceiptStore``) and on processing
(``processed.ndjson`` keyed by ``delivery_id``); each delivery posts a fresh
PR comment (no in-place edit).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

LOGGER = logging.getLogger("spec_eval.ci_worker")

COMMENT_MARKER = "<!-- spec-eval-bot:updatable:v1 -->"
DEFAULT_BOT_LOGIN = "arkui_architecture"
DEFAULT_ALLOW_PROJECTS = ("arkui_architecture/arkui-specs",)

# GitCode MR webhook ``action`` values that signal a completed merge. A merge
# receipt does not represent a PR head to evaluate; instead it triggers a
# force-sync of every CI repo to its default-branch tip (see handle_merge_receipt).
MERGE_ACTIONS = {"merge", "merged"}

# Repositories that make up the CI environment, as (name, rel-path-below-oh_root,
# default-branch-fallback). The single source of truth is
# ``deploy_ci.REPO_TABLE`` / ``specs/evaluation/golden/manifest.yaml``; this inline
# copy keeps ci_worker self-contained and unit-testable. MirrorRepoTableTest
# guards against drift between the two.
CI_SYNC_REPOS = (
    ("ace_engine", "foundation/arkui/ace_engine", "master"),
    ("specs", "foundation/arkui/ace_engine/specs", "main"),
    ("sdk-js", "interface/sdk-js", "master"),
    ("sdk_c", "interface/sdk_c", "master"),
)

# The dependency snapshot is captured once per delivery.  The worker is
# intentionally single-flight, so this gives one immutable view of the
# ace_engine/specs/SDK tips for every step of that task while the next task
# observes whatever the repositories have advanced to in the meantime.

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
    test_on_pass: bool = False
    force_test: bool = False
    specs_checks_enabled: bool = True
    sync_on_merge: bool = True
    force_sync: bool = False
    rebuild_site_on_merge: bool = True
    site_base_url: str = "/arkui_specs/"
    site_mode: str = "static"


def capture_master_snapshot(oh_root: Path) -> list[dict[str, Any]]:
    """Capture the current default-branch tips of all CI dependency repos.

    This is metadata only: evaluation still runs against the checked-out tree
    (and the tested specs SHA).  Missing repositories or unavailable remote
    refs are recorded explicitly instead of being inferred.
    """
    snapshot: list[dict[str, Any]] = []
    for name, rel, fallback in CI_SYNC_REPOS:
        repo_path = oh_root / rel
        item: dict[str, Any] = {"name": name, "path": str(repo_path), "branch": fallback}
        if not (repo_path / ".git").exists():
            item.update({"status": "missing", "sha": None})
            snapshot.append(item)
            continue
        # Do not contact the network while processing a receipt.  Merge-sync
        # owns fetch/update; ordinary deliveries only snapshot the local
        # remote-tracking ref that was available at task start.
        candidates = [fallback] + [branch for branch in ("master", "main") if branch != fallback]
        ref = None
        branch = fallback
        for candidate in candidates:
            probe = _git_at(repo_path, "rev-parse", f"origin/{candidate}")
            if probe.returncode == 0 and probe.stdout.strip():
                ref = probe
                branch = candidate
                break
            ref = probe
        item["branch"] = branch
        if ref is not None and ref.returncode == 0 and ref.stdout.strip():
            item.update({"status": "ok", "sha": ref.stdout.strip()})
        else:
            head = _head_sha(repo_path)
            if head:
                item.update({"status": "head_fallback", "sha": head})
            else:
                item.update({"status": "error", "sha": None, "error": (ref.stderr or ref.stdout).strip() if ref else "unavailable"})
        snapshot.append(item)
    return snapshot


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


def _object_exists(specs_root: Path, sha: str) -> bool:
    """True iff ``sha`` resolves to a commit already in the local object store."""
    if not sha:
        return False
    return _git(specs_root, "cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def _fetch_into(specs_root: Path, sha: str, source_branch: str | None) -> str:
    """Fetch ``sha`` from origin; return the outcome.

    The webhook ``tested`` SHA comes from the PR source branch, which the worker
    checkout (parked on main) usually does not contain. Fetch the source branch
    first (precise, cheap); if that does not surface the commit, fall back to a
    full ``origin`` fetch. ``git fetch`` is idempotent and safe on a clean
    checkout. Returns ``"fetched_branch"`` / ``"fetched_origin"`` when the commit
    becomes available, ``"absent"`` when the fetch commands succeeded but the
    commit is still missing (force-pushed away — a real mismatch), or ``"error"``
    when every fetch command failed.
    """
    any_ok = False
    if source_branch:
        if _git(specs_root, "fetch", "origin", source_branch).returncode == 0:
            any_ok = True
            if _object_exists(specs_root, sha):
                return "fetched_branch"
    if _git(specs_root, "fetch", "origin").returncode == 0:
        any_ok = True
        if _object_exists(specs_root, sha):
            return "fetched_origin"
    return "absent" if any_ok else "error"


# --------------------------------------------------------------------------- #
# Repo tip-sync (triggered by action=merge receipts)
# --------------------------------------------------------------------------- #
def _git_at(repo_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in an arbitrary repo path (capture, never raise)."""
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _head_sha(repo_path: Path) -> str | None:
    result = _git_at(repo_path, "rev-parse", "HEAD")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _worktree_dirty(repo_path: Path) -> bool:
    """True iff the working tree has tracked-file modifications (uncommitted)."""
    result = _git_at(repo_path, "status", "--porcelain")
    return result.returncode == 0 and bool(result.stdout.strip())


def _origin_default_branch(repo_path: Path, fallback: str) -> str:
    """Best-effort default branch of origin (master/main); ``fallback`` on failure."""
    _git_at(repo_path, "remote", "set-head", "origin", "--auto")
    result = _git_at(repo_path, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    head = result.stdout.strip()
    if head.startswith("origin/"):
        return head.split("origin/", 1)[1]
    return head or fallback


@dataclass
class RepoSyncResult:
    """Outcome of force-syncing one CI repo to its default-branch tip."""

    name: str
    path: str
    action: str  # updated / skipped_dirty / error / missing
    branch: str | None
    before: str | None
    after: str | None
    error: str | None = None


def sync_repo_to_tip(
    name: str,
    repo_path: Path,
    *,
    fallback_branch: str,
    force: bool,
) -> RepoSyncResult:
    """Fetch + ``reset --hard origin/<default-branch>`` for one repo.

    Mirrors ``deploy_ci.sync_repo`` (follow-master mode) with two additions: a
    dirty-tree guard (skip unless ``force``) so uncommitted local work is never
    silently discarded, and per-repo error capture (never raises). A missing
    ``.git`` is reported as ``missing``; the CI environment is expected to be
    provisioned by ``deploy_ci.py``.
    """
    path_str = str(repo_path)
    before = _head_sha(repo_path)
    if not (repo_path / ".git").exists():
        return RepoSyncResult(name, path_str, "missing", None, before, None)
    if _worktree_dirty(repo_path) and not force:
        return RepoSyncResult(name, path_str, "skipped_dirty", None, before, before)
    branch = _origin_default_branch(repo_path, fallback_branch)
    fetch = _git_at(repo_path, "fetch", "origin", "--tags")
    if fetch.returncode != 0:
        return RepoSyncResult(
            name, path_str, "error", branch, before, before,
            error=(fetch.stderr or fetch.stdout).strip(),
        )
    reset = _git_at(repo_path, "reset", "--hard", f"origin/{branch}")
    if reset.returncode != 0:
        return RepoSyncResult(
            name, path_str, "error", branch, before, before,
            error=(reset.stderr or reset.stdout).strip(),
        )
    return RepoSyncResult(name, path_str, "updated", branch, before, _head_sha(repo_path))


def sync_ci_repos(oh_root: Path, *, force: bool) -> list[RepoSyncResult]:
    """Force-sync every CI repo to its default-branch tip (``oh_root`` layout).

    ``oh_root`` is the OpenHarmony aggregate root (``repo_root.parents[2]``,
    matching ``config.py``). A repo path without ``.git`` yields ``missing``;
    exceptions are captured as ``error`` so one broken repo never aborts the
    rest of the sync.
    """
    results: list[RepoSyncResult] = []
    for name, rel, fallback in CI_SYNC_REPOS:
        repo_path = oh_root / rel
        try:
            results.append(
                sync_repo_to_tip(name, repo_path, fallback_branch=fallback, force=force)
            )
        except Exception as exc:  # noqa: BLE001 - keep syncing the remaining repos
            results.append(
                RepoSyncResult(name, str(repo_path), "error", None, None, None, error=str(exc))
            )
    return results


def ensure_specs_at_sha(
    specs_root: Path,
    tested: str | None,
    *,
    auto_checkout: bool,
    source_branch: str | None = None,
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
    # The webhook's tested SHA comes from the PR source branch, which the worker
    # checkout (parked on main) usually does not contain. Fetch it before
    # detaching; a SHA still absent after fetch (force-pushed away) is the only
    # real mismatch.
    if not _object_exists(specs_root, tested):
        outcome = _fetch_into(specs_root, tested, source_branch)
        if outcome == "error":
            return current, False, "fetch_failed", None
        if outcome == "absent":
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


@dataclass
class SpecCheckResult:
    """One repo-level specs integrity check (generate_index / validate_specs).

    A non-zero ``exit_code`` records a failure rather than raising, so a broken
    specs tree gates the PR through the comment / test-status path instead of
    aborting the Worker.
    """

    name: str
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str
    elapsed_ms: float

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def specs_checks_passed(results: list[SpecCheckResult] | None) -> bool:
    """True iff every specs integrity check exited 0 (``None`` means not run)."""
    if not results:
        return True
    return all(result.passed for result in results)


def _specs_checks_summary(results: list[SpecCheckResult] | None) -> list[dict[str, Any]] | None:
    """Project ``SpecCheckResult`` list into a JSON-safe meta summary (no output bodies)."""
    if results is None:
        return None
    return [
        {"name": r.name, "exit_code": r.exit_code, "passed": r.passed, "elapsed_ms": r.elapsed_ms}
        for r in results
    ]


# Cap captured check output so a noisy failure cannot blow up the PR comment.
_SPECS_OUTPUT_MAX_LINES = 30
_SPECS_OUTPUT_MAX_CHARS = 4000


def _truncate_check_output(text: str) -> str:
    """Trim a check's stdout/stderr to a comment-safe size (lines then chars)."""
    if not text:
        return ""
    lines = text.splitlines()
    if len(lines) > _SPECS_OUTPUT_MAX_LINES:
        lines = lines[:_SPECS_OUTPUT_MAX_LINES]
        lines.append(f"... ({len(text.splitlines()) - _SPECS_OUTPUT_MAX_LINES} more line(s) truncated)")
    trimmed = "\n".join(lines)
    if len(trimmed) > _SPECS_OUTPUT_MAX_CHARS:
        trimmed = trimmed[:_SPECS_OUTPUT_MAX_CHARS] + "\n... (output truncated)"
    return trimmed


def _check_output_for_comment(result: SpecCheckResult) -> str:
    """Prefer stderr (generate_index writes ``error:`` there), fall back to stdout."""
    return _truncate_check_output(result.stderr or result.stdout)


def run_specs_checks(*, specs_root: Path, python: str = "python3") -> list[SpecCheckResult]:
    """Run the two repo-level specs integrity checks in a stable order.

    Both scripts locate ROOT via ``__file__`` (i.e. ``specs_root``), so the
    working directory does not change behavior; ``cwd=specs_root`` is set for
    clarity only. Never raises — failures are recorded as non-zero ``exit_code``
    so they gate the PR via the comment / test-status path.
    """
    targets = [
        ("generate_index", [python, str(specs_root / "tools" / "generate_index.py"), "--check"]),
        ("validate_specs", [python, str(specs_root / "tools" / "validate_specs.py")]),
    ]
    results: list[SpecCheckResult] = []
    for name, command in targets:
        started = time.perf_counter()
        proc = subprocess.run(command, cwd=str(specs_root), capture_output=True, text=True, check=False)
        elapsed = (time.perf_counter() - started) * 1000.0
        results.append(
            SpecCheckResult(
                name=name,
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                elapsed_ms=round(elapsed, 3),
            )
        )
    return results


def rebuild_site(
    specs_root: Path, *, base_url: str, python: str = "python3", site_mode: str = "static"
) -> dict[str, Any]:
    """Regenerate the Docusaurus site inputs and build static output.

    Runs ``tools/generate_site.py`` (registry → site/docs + data JSON) then
    ``npm run build`` with ``BASE_URL`` so asset URLs resolve under ``base_url``
    (must match the path the site is served at). ``site_mode`` selects the
    evaluation-data source: ``static`` bakes the single ``.evaluator`` snapshot;
    ``dynamic`` reads the newest archived job per Function (kept current
    afterwards by the data-only watcher). Best-effort: never raises — a step
    failure is recorded as a non-zero ``exit_code`` and short-circuits the
    remaining steps (build is skipped when generation failed). The merge-sync
    caller keeps its own status regardless of the site outcome.
    """
    steps: list[dict[str, Any]] = []
    plan: list[tuple[str, list[str], dict[str, Any]]] = [
        (
            "generate_site",
            [python, str(specs_root / "tools" / "generate_site.py"), "--mode", site_mode],
            {"cwd": str(specs_root)},
        ),
        (
            "build",
            ["npm", "run", "build"],
            {"cwd": str(specs_root / "site"), "env": {**os.environ, "BASE_URL": base_url}},
        ),
    ]
    overall_ok = True
    for name, command, run_kwargs in plan:
        started = time.perf_counter()
        proc = subprocess.run(command, capture_output=True, text=True, check=False, **run_kwargs)
        elapsed = round((time.perf_counter() - started) * 1000.0, 3)
        steps.append(
            {"name": name, "exit_code": proc.returncode, "elapsed_ms": elapsed, "stderr_tail": (proc.stderr or "").strip()[-500:]}
        )
        if proc.returncode != 0:
            overall_ok = False
            break
    error = None
    if not overall_ok:
        failed = next(step for step in steps if step["exit_code"] != 0)
        error = f"{failed['name']} failed (exit {failed['exit_code']})"
    return {"action": "rebuilt" if overall_ok else "error", "base_url": base_url, "steps": steps, "error": error}


def render_comment(
    ci_summary: dict[str, Any],
    receipt: dict[str, Any],
    *,
    shas: dict[str, str | None],
    ensure_action: str,
    exit_code: int = EXIT_OK,
    specs_checks: list[SpecCheckResult] | None = None,
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

    # When the specs integrity checks ran, surface a one-line header summary so
    # PR authors can confirm they executed (✅ pass / ❌ fail); a failure still
    # expands into the detailed block below.
    if specs_checks:
        marks = " · ".join(f"{'✅' if result.passed else '❌'} {result.name}" for result in specs_checks)
        lines.insert(len(lines) - 1, f"| **Specs checks** | {marks} |")

    specs_failed = not specs_checks_passed(specs_checks)
    if specs_failed:
        lines += [
            "**⛔ Specs 仓库完整性检查失败 · 已拦截 CI 通过**",
            "",
            "### ❌ Specs 完整性检查",
            "",
        ]
        for result in specs_checks or []:
            mark = "✅" if result.passed else "❌"
            lines.append(f"#### {mark} `{result.name}` (exit {result.exit_code}, {result.elapsed_ms:.0f} ms)")
            output = _check_output_for_comment(result)
            if output:
                lines += ["", "```", output, "```"]
            elif result.passed:
                lines += ["", "_检查通过。_"]
            lines.append("")
        lines += [
            "本地复现：",
            "",
            "```",
            "python3 tools/generate_index.py --check",
            "python3 tools/validate_specs.py",
            "```",
            "",
            "修复后重新推送即可；静态评估结果（report-only）见下，仅供参考。",
            "",
            "---",
            "",
            "### 静态评估 (report-only)",
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


def _gitcode_api_token() -> str:
    """Load the same token used by oh-gc, without exposing it in logs."""
    config_path = Path.home() / ".config/gitcode-cli/config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "GitCode API token unavailable; run `oh-gc auth login`"
        ) from exc
    token = config.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError(
            "GitCode API token unavailable; run `oh-gc auth login`"
        )
    return token


def _gitcode_api_json(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
) -> Any:
    """Call GitCode API v5 while keeping the access token out of error messages."""
    token = _gitcode_api_token()
    query = urllib.parse.urlencode({"access_token": token})
    url = f"https://api.gitcode.com/api/v5{path}?{query}"
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"GitCode API {method} {path} failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitCode API {method} {path} connection failed") from exc
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"GitCode API {method} {path} returned invalid JSON") from exc


def post_comment(
    repo: str,
    pr_iid: Any,
    body: str,
    *,
    dry_run: bool = False,
    oh_gc: str = "oh-gc",
) -> dict[str, Any]:
    """Post a fresh PR comment for every delivery (no in-place update)."""
    if dry_run:
        return {"action": "dry-run", "id": None, "url": None}
    created = _oh_gc_json(
        ["pr", "comment", str(pr_iid), "--repo", repo, "--body", body, "--json"],
        oh_gc=oh_gc,
    ) or {}
    return {"action": "created", "id": created.get("id"), "url": created.get("url")}


def decide_test_pass(ci_summary: dict[str, Any] | None, *, status: str, incomplete: bool) -> bool:
    """A run "passes" (no new errors) iff it completed cleanly with ``delta.added == 0``.

    Pre-existing baseline debt never blocks the CI test result (report-only is non-blocking);
    only *new* findings (``delta.added`` after exemptions) or an incomplete/tool-error
    run withhold it.
    """
    if ci_summary is None or status != "ok" or incomplete:
        return False
    delta = ci_summary.get("delta") or {}
    return int(delta.get("added", 0) or 0) == 0


def reset_pr_test(repo: str, pr_iid: Any, *, reset_all: bool = False) -> dict[str, Any]:
    """Reset the authenticated tester, or all testers in explicit force mode.

    GitCode documents ``PATCH /pulls/{number}/testers`` as the test-state reset
    endpoint. ``reset_all=false`` requires the caller to be an assigned tester;
    ``reset_all=true`` is admin-only and resets every tester, so it is coupled to
    the existing explicit ``--force-test`` opt-in.
    """
    owner, separator, name = repo.partition("/")
    if not separator or not owner or not name:
        raise ValueError(f"invalid GitCode repo: {repo!r}; expected OWNER/REPO")
    path = (
        f"/repos/{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(name, safe='')}"
        f"/pulls/{pr_iid}/testers"
    )
    detail = _gitcode_api_json("PATCH", path, body={"reset_all": reset_all}) or {}
    return {"action": "test_reset_all" if reset_all else "test_reset", "detail": detail}


def current_pr_head_sha(repo: str, pr_iid: Any, *, oh_gc: str = "oh-gc") -> str | None:
    """Read the current GitCode PR head immediately before writing a pass state."""
    detail = _oh_gc_json(
        ["pr", "view", str(pr_iid), "--repo", repo, "--json"],
        oh_gc=oh_gc,
    ) or {}
    head = detail.get("head") or {}
    sha = head.get("sha")
    return sha if isinstance(sha, str) and sha else None


def mark_pr_test_passed(
    repo: str,
    pr_iid: Any,
    *,
    oh_gc: str = "oh-gc",
    force: bool = False,
) -> dict[str, Any]:
    """Mark the PR's automated test as passed via ``oh-gc pr test``."""
    args = ["pr", "test", str(pr_iid), "--repo", repo]
    if force:
        args.append("--force")
    # ``oh-gc pr test --json`` prints ``undefined`` (oh-gc quirk, same as
    # ``pr comment-edit``), so success is the zero exit code from ``_oh_gc``;
    # we do not parse its stdout.
    _oh_gc(args, oh_gc=oh_gc)
    return {"action": "test_passed"}


# --------------------------------------------------------------------------- #
# Archive
# --------------------------------------------------------------------------- #
def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _archive_dir_for(output_root: Path, iid: Any, delivery_id: str) -> Path:
    safe_delivery = (delivery_id or "unknown").replace("/", "_")
    return output_root / f"pr-{iid}" / safe_delivery


def _last_processed_head_for(output_root: Path, iid: Any) -> str | None:
    """Return the tested SHA of the most recent successfully-processed delivery for ``iid``.

    Used to detect test-writeback echo: ``oh-gc pr test`` flips the merge-request
    test state, which GitCode re-delivers as another ``action=update`` webhook
    with the same head SHA. A delivery whose head was already processed
    successfully is that echo, not a new change.
    """
    pr_dir = output_root / f"pr-{iid}"
    if not pr_dir.is_dir():
        return None
    best: tuple[str, str] | None = None  # (finished_at, sha)
    for meta_path in pr_dir.glob("*/run-meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if meta.get("status") not in {"ok", "incomplete"}:
            continue
        finished = meta.get("finished_at") or ""
        sha = (meta.get("shas") or {}).get("tested")
        if isinstance(sha, str) and sha and (best is None or finished > best[0]):
            best = (finished, sha)
    return best[1] if best else None


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
    specs_checks: list[SpecCheckResult] | None = None,
    test_result: dict[str, Any] | None = None,
    repo_sync: list[dict[str, Any]] | None = None,
    site_build: dict[str, Any] | None = None,
    dependency_snapshot: list[dict[str, Any]] | None = None,
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
        "specs_checks": _specs_checks_summary(specs_checks),
        "comment": comment_result,
        "test": test_result,
        "repo_sync": repo_sync,
        "site_build": site_build,
        "dependency_snapshot": dependency_snapshot,
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
def handle_merge_receipt(receipt: dict[str, Any], ctx: WorkerContext) -> dict[str, Any]:
    """Handle an ``action=merge`` receipt by force-syncing the CI repos to tip.

    A merged PR has no head to evaluate and its target branch has already
    advanced, so the eval pipeline is skipped entirely (no ci_runner, comment,
    or test-status writeback). Instead every CI repo is reset to its
    default-branch tip so the next evaluation starts from a clean, current
    baseline. When sync is disabled the delivery is still consumed (recorded as
    ``merge_skipped_no_sync``) and never falls through to eval.
    """
    delivery = receipt.get("delivery_id")
    pull_request = receipt.get("pull_request") or {}
    iid = pull_request.get("iid")
    archive_dir = _archive_dir_for(ctx.output_root, iid, delivery)
    archive_dir.mkdir(parents=True, exist_ok=True)
    timing: dict[str, float] = {}

    repo_sync_dicts: list[dict[str, Any]] | None = None
    site_build_dict: dict[str, Any] | None = None
    dependency_snapshot: list[dict[str, Any]] | None = None
    if ctx.sync_on_merge:
        oh_root = ctx.repo_root.parents[2]
        started = time.perf_counter()
        results = sync_ci_repos(oh_root, force=ctx.force_sync)
        timing["repo_sync_ms"] = round((time.perf_counter() - started) * 1000.0, 3)
        repo_sync_dicts = [asdict(r) for r in results]
        dependency_snapshot = capture_master_snapshot(oh_root)
        _write_json(archive_dir / "repo-sync.json", repo_sync_dicts)
        status = "merge_synced" if all(r.action != "error" for r in results) else "merge_sync_partial"
        LOGGER.info(
            "delivery=%s pr=%s merge-sync status=%s repos=%s",
            delivery, iid, status,
            {r.name: r.action for r in results},
        )
        # Rebuild the Docusaurus site after sync so the served site reflects the
        # latest registry + site archives. Best-effort: a failure is recorded but
        # never changes the merge-sync status (repo sync is the primary outcome).
        if ctx.rebuild_site_on_merge:
            site_started = time.perf_counter()
            site_result = rebuild_site(
                ctx.specs_root,
                base_url=ctx.site_base_url,
                python=ctx.python,
                site_mode=ctx.site_mode,
            )
            timing["site_build_ms"] = round((time.perf_counter() - site_started) * 1000.0, 3)
            site_build_dict = site_result
            _write_json(archive_dir / "site-build.json", site_result)
            if site_result.get("action") == "rebuilt":
                LOGGER.info("delivery=%s pr=%s site rebuilt (%.0f ms)", delivery, iid, timing["site_build_ms"])
            else:
                LOGGER.warning("delivery=%s pr=%s site rebuild failed: %s", delivery, iid, site_result.get("error"))
    else:
        status = "merge_skipped_no_sync"
        dependency_snapshot = capture_master_snapshot(ctx.repo_root.parents[2])
        LOGGER.info("delivery=%s pr=%s merge-sync disabled (sync_on_merge=False)", delivery, iid)

    write_run_meta(
        archive_dir,
        receipt=receipt,
        ctx=ctx,
        shas={"tested": None, "target": None},
        specs_head_before=None,
        ensure_action="merge_sync",
        ci_summary=None,
        exit_code=None,
        incomplete=False,
        changed_files=[],
        comment_result=None,
        test_result=None,
        repo_sync=repo_sync_dicts,
        site_build=site_build_dict,
        dependency_snapshot=dependency_snapshot,
        timing=timing,
        status=status,
    )
    return {
        "delivery_id": delivery,
        "pr_iid": iid,
        "status": status,
        "archive_dir": archive_dir.as_posix(),
        "repo_sync": repo_sync_dicts,
        "site_build": site_build_dict,
        "dependency_snapshot": dependency_snapshot,
    }


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

    # A merge delivery does not represent a PR head to evaluate; force-sync the
    # CI repos to tip and consume it without entering the eval pipeline.
    if receipt.get("action") in MERGE_ACTIONS:
        return handle_merge_receipt(receipt, ctx)

    # Freeze the dependency view for this delivery before any specs checkout;
    # subsequent deliveries capture a fresh view after merge-sync/tip updates.
    dependency_snapshot = capture_master_snapshot(ctx.repo_root.parents[2])
    result["dependency_snapshot"] = dependency_snapshot

    target, tested = resolve_shas(receipt)
    shas = {"tested": tested, "target": target}
    archive_dir = _archive_dir_for(ctx.output_root, iid, delivery)
    result["archive_dir"] = archive_dir.as_posix()

    # When test writeback is on, break the echo loop: marking the PR test passed
    # flips the merge-request test state, which GitCode re-delivers as another
    # ``action=update`` webhook with the same head SHA. A delivery whose head was
    # already processed successfully is that echo, not a new change.
    if ctx.test_on_pass and tested is not None:
        last_head = _last_processed_head_for(ctx.output_root, iid)
        if last_head == tested:
            LOGGER.info(
                "delivery=%s pr=%s skipped (head %s already processed; test-writeback echo)",
                delivery, iid, _short(tested),
            )
            write_run_meta(
                archive_dir,
                receipt=receipt,
                ctx=ctx,
                shas=shas,
                specs_head_before=None,
                ensure_action="unchanged_head",
                ci_summary=None,
                exit_code=None,
                incomplete=False,
                changed_files=[],
                comment_result=None,
                test_result=None,
                timing=timing,
                status="skipped_unchanged_head",
                dependency_snapshot=dependency_snapshot,
                error=f"PR head {tested} already processed (test-writeback echo)",
            )
            result["status"] = "skipped_unchanged_head"
            return result

    # A pass belongs to one PR head. Reset this CI tester's prior state as soon
    # as a new delivery is consumed, before checkout/diff/evaluation can fail.
    test_result: dict[str, Any] | None = None
    if ctx.test_on_pass and not ctx.dry_run:
        test_result = {"reset": None, "pass": None}
        try:
            test_result["reset"] = reset_pr_test(ctx.repo, iid, reset_all=ctx.force_test)
        except Exception as exc:  # noqa: BLE001 - preserve the evaluation/report path
            LOGGER.exception("delivery=%s pr=%s test reset failed", delivery, iid)
            test_result["reset"] = {"action": "error", "error": str(exc)}
        archive_dir.mkdir(parents=True, exist_ok=True)
        _write_json(archive_dir / "test-result.json", test_result)
        result["test"] = test_result

    source_branch = (receipt.get("pull_request") or {}).get("source_branch")
    specs_checks: list[SpecCheckResult] | None = None
    specs_head_before, ok, action, restore_ref = ensure_specs_at_sha(
        ctx.specs_root, tested, auto_checkout=ctx.auto_checkout, source_branch=source_branch
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
                test_result=test_result,
                specs_checks=specs_checks,
                dependency_snapshot=dependency_snapshot,
                timing=timing,
                status=action,
                error=f"specs HEAD {specs_head_before} != tested {tested}",
            )
            result["status"] = action
            return result

        archive_dir.mkdir(parents=True, exist_ok=True)
        if ctx.specs_checks_enabled:
            specs_checks = run_specs_checks(specs_root=ctx.specs_root, python=ctx.python)
            timing["specs_checks_ms"] = round(sum(r.elapsed_ms for r in specs_checks), 3)
            _write_json(archive_dir / "specs-checks.json", [asdict(r) for r in specs_checks])

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
                changed_files=changed_files, comment_result=None, test_result=test_result,
                specs_checks=specs_checks, timing=timing, status=diff_status,
                dependency_snapshot=dependency_snapshot,
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
                changed_files=changed_files, comment_result=None, test_result=test_result,
                specs_checks=specs_checks, timing=timing, status="tool_error",
                dependency_snapshot=dependency_snapshot,
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
            specs_checks=specs_checks,
        )
        (archive_dir / "comment-body.md").write_text(comment_body, encoding="utf-8")
        try:
            comment_result = post_comment(
                ctx.repo, iid, comment_body,
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

        if not specs_checks_passed(specs_checks):
            final_status = "specs_check_failed"
        elif incomplete:
            final_status = "incomplete"
        else:
            final_status = "ok"
        if test_result is not None:
            reset_ok = (test_result.get("reset") or {}).get("action") in {"test_reset", "test_reset_all"}
            if not reset_ok:
                test_result["pass"] = {"action": "withheld", "reason": "test_reset_failed"}
            elif not specs_checks_passed(specs_checks):
                test_result["pass"] = {"action": "withheld", "reason": "specs_check_failed"}
            elif not decide_test_pass(summary, status=final_status, incomplete=incomplete):
                test_result["pass"] = {"action": "withheld", "reason": "evaluation_not_passed"}
            else:
                try:
                    current_head = current_pr_head_sha(ctx.repo, iid, oh_gc=ctx.oh_gc)
                    if current_head != tested:
                        test_result["pass"] = {
                            "action": "withheld",
                            "reason": "stale_head",
                            "tested": tested,
                            "current_head": current_head,
                        }
                    else:
                        test_result["pass"] = mark_pr_test_passed(
                            ctx.repo, iid, oh_gc=ctx.oh_gc, force=ctx.force_test,
                        )
                except Exception as exc:  # noqa: BLE001 - test writeback must not abort archiving
                    LOGGER.exception("delivery=%s pr=%s test writeback failed", delivery, iid)
                    test_result["pass"] = {"action": "error", "error": str(exc)}
            _write_json(archive_dir / "test-result.json", test_result)

        timing["total_ms"] = round((time.perf_counter() - started) * 1000.0, 3)
        write_run_meta(
            archive_dir, receipt=receipt, ctx=ctx, shas=shas, specs_head_before=specs_head_before,
            ensure_action=action, ci_summary=summary, exit_code=exit_code, incomplete=incomplete,
            changed_files=changed_files, comment_result=comment_result, test_result=test_result,
            specs_checks=specs_checks, timing=timing, status=final_status,
            dependency_snapshot=dependency_snapshot,
        )
        result.update(
            {
                "status": final_status,
                "affected_function_count": summary.get("affected_function_count"),
                "delta": summary.get("delta"),
                "exit_code": exit_code,
                "comment": comment_result,
                "test": test_result,
                "archive_dir": archive_dir.as_posix(),
            }
        )
        LOGGER.info(
            "delivery=%s pr=%s status=%s affected=%s exit=%s comment=%s test=%s",
            delivery, iid, result["status"], result.get("affected_function_count"),
            exit_code, comment_result.get("action"),
            (test_result.get("pass") or {}).get("action") if test_result else "off",
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
    parser.add_argument(
        "--no-auto-checkout",
        action="store_true",
        help="do NOT detached-HEAD checkout specs to the tested SHA (default: fetch + checkout so PR evaluation runs at the PR head)",
    )
    parser.add_argument(
        "--no-specs-check",
        action="store_true",
        help="skip repo-level specs integrity checks (generate_index --check, validate_specs)",
    )
    parser.add_argument(
        "--no-sync-on-merge",
        action="store_true",
        help="do NOT force-sync CI repos to tip on action=merge receipts (default: sync all 4 repos)",
    )
    parser.add_argument(
        "--force-sync",
        action="store_true",
        help="with merge-sync enabled, reset --hard even repos with uncommitted local changes",
    )
    parser.add_argument(
        "--no-rebuild-site",
        action="store_true",
        help="do NOT rebuild the Docusaurus site after a merge-sync (default: rebuild and serve at --site-base-url)",
    )
    parser.add_argument(
        "--site-base-url",
        default="/arkui_specs/",
        help="BASE_URL passed to `npm run build` so site assets resolve under the served path (default /arkui_specs/)",
    )
    parser.add_argument(
        "--site-mode",
        choices=["static", "dynamic"],
        default="static",
        help=(
            "evaluation-data source for the merge-time site rebuild: static bakes "
            "the .evaluator snapshot; dynamic reads the newest archived job per "
            "Function (kept current afterwards by the data-only watcher). Default static."
        ),
    )
    parser.add_argument(
        "--test-on-pass",
        action="store_true",
        help="on a passing run (delta.added == 0, not incomplete), mark GitCode PR test passed via `oh-gc pr test`",
    )
    parser.add_argument(
        "--force-test",
        action="store_true",
        help="with --test-on-pass, pass --force to `oh-gc pr test` (e.g. to re-submit the test result)",
    )
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
        auto_checkout=not args.no_auto_checkout,
        specs_checks_enabled=not args.no_specs_check,
        sync_on_merge=not args.no_sync_on_merge,
        force_sync=args.force_sync,
        rebuild_site_on_merge=not args.no_rebuild_site,
        site_base_url=args.site_base_url,
        site_mode=args.site_mode,
        oh_gc=args.oh_gc,
        python=args.python,
        test_on_pass=args.test_on_pass,
        force_test=args.force_test,
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
