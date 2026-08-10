#!/usr/bin/env python3
"""One-click deploy/upgrade for the spec_eval GitCode MR CI.

Clones ``ace_engine`` + nested ``specs`` + ``sdk-js`` + ``sdk_c`` into the
OpenHarmony tree layout mandated by ``spec_eval/config.py``
(``oh_root = repo_root.parents[2]``), so the CI Worker (``ci_worker.py``) and the
webhook receiver (``gitcode_webhook.py``) can run in place.

Self-contained (stdlib only). The repo table and frozen revisions are embedded so
the script can be ``curl``'d and run before any repo exists. Defaults to following
each repo's default branch; pass ``--frozen`` to pin the golden revisions that
match the frozen Finding baseline (``evaluation/baselines/current.json``).

Subcommands: ``deploy`` | ``upgrade`` | ``doctor`` | ``info``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_DEPLOY_ROOT = Path(os.environ.get("OH_ROOT", str(Path.home() / "ohos-spec-eval")))
DEFAULT_TOKEN_FILE = Path.home() / ".gitcode_webhook_token"

# Embedded repo table. Source of truth: specs/evaluation/golden/manifest.yaml
# (keep frozen SHAs in sync with that manifest when it is re-frozen).
REPO_TABLE = [
    {
        "name": "ace_engine",
        "url": "https://gitcode.com/openharmony/arkui_ace_engine",
        "rel": "foundation/arkui/ace_engine",
        "frozen": "d91b4e4990a990da2bfe809514e573e35852193e",
    },
    {
        "name": "specs",
        "url": "https://gitcode.com/arkui_architecture/arkui-specs",
        "rel": "foundation/arkui/ace_engine/specs",
        "frozen": "ca45d1f90c271fa7e58f9eb3eebb04a595e8b9ae",
    },
    {
        # GitCode repo name uses an underscore; the deploy DIR must be a hyphen
        # (sdk_reader.py reads oh_root/interface/sdk-js/api) -> clone explicitly.
        "name": "sdk-js",
        "url": "https://gitcode.com/openharmony/interface_sdk-js",
        "rel": "interface/sdk-js",
        "frozen": "224c0c10fde3910a473455eac6841614a162ce39",
    },
    {
        "name": "sdk_c",
        "url": "https://gitcode.com/openharmony/interface_sdk_c",
        "rel": "interface/sdk_c",
        "frozen": "62b5e3d0e63c2edd7e9073fece7a162b172f4ee4",
    },
]
REPO_ORDER = [r["name"] for r in REPO_TABLE]  # ace_engine first so specs can nest
FROZEN = "frozen"


@dataclass(frozen=True)
class RepoTarget:
    name: str
    url: str
    rel: str
    path: Path
    frozen: str


def repo_targets(deploy_root: Path, *, only: Iterable[str] | None = None) -> list[RepoTarget]:
    """Resolve the embedded repo table to absolute deploy paths (in clone order)."""
    only_set = set(_split_csv(only)) if only else None
    order = {name: i for i, name in enumerate(REPO_ORDER)}
    targets = [
        RepoTarget(name=r["name"], url=r["url"], rel=r["rel"],
                   path=deploy_root / r["rel"], frozen=r["frozen"])
        for r in REPO_TABLE
        if only_set is None or r["name"] in only_set
    ]
    return sorted(targets, key=lambda t: order.get(t.name, 99))


def target_revision(target: RepoTarget, *, frozen: bool) -> str | None:
    """``frozen`` -> the pinned SHA; otherwise None (track default branch)."""
    return target.frozen if frozen else None


def _split_csv(values: Iterable[str] | None) -> list[str]:
    if not values:
        return []
    out: list[str] = []
    for item in values:
        out.extend(part.strip() for part in item.split(",") if part.strip())
    return out


# --------------------------------------------------------------------------- #
# git wrapper + sync
# --------------------------------------------------------------------------- #
def _git(args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False)
    if check and proc.returncode != 0:
        message = (proc.stderr or proc.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed (exit {proc.returncode}): {message}")
    return proc


def _is_git_repo(path: Path) -> bool:
    return path.is_dir() and (path / ".git").exists()


def _origin_default_branch(path: Path) -> str:
    """Best-effort default branch of origin (master/main)."""
    _git(["remote", "set-head", "origin", "--auto"], cwd=path, check=False)
    head = _git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=path, check=False).stdout.strip()
    if head.startswith("origin/"):
        return head.split("origin/", 1)[1]
    return head or "master"


def sync_repo(target: RepoTarget, *, frozen: bool, shallow: bool) -> str:
    """Clone if absent, otherwise update in place. Returns a short human action."""
    rev = target_revision(target, frozen=frozen)
    if _is_git_repo(target.path):
        _git(["fetch", "origin", "--tags"], cwd=target.path)
        if rev is None:
            branch = _origin_default_branch(target.path)
            _git(["reset", "--hard", f"origin/{branch}"], cwd=target.path)
            return f"updated to origin/{branch}"
        _git(["checkout", rev], cwd=target.path)
        return f"checked out {rev[:7]}"
    target.path.parent.mkdir(parents=True, exist_ok=True)
    clone_cmd = ["clone"]
    if shallow:
        clone_cmd += ["--depth", "1", "--single-branch"]
    clone_cmd += [target.url, target.path.as_posix()]
    _git(clone_cmd, cwd=target.path.parent)
    if rev is not None:
        if shallow:  # the frozen SHA may lie outside the shallow slice
            _git(["fetch", "--depth", "1", "origin", rev], cwd=target.path, check=False)
        _git(["checkout", rev], cwd=target.path)
    tail = f" @ {rev[:7]}" if rev else ""
    return f"cloned{' (shallow)' if shallow else ''}{tail}"


def sync_all(deploy_root: Path, *, frozen: bool, shallow: bool, only: Iterable[str] | None) -> list[tuple[str, str, Path]]:
    actions: list[tuple[str, str, Path]] = []
    for target in repo_targets(deploy_root, only=only):
        action = sync_repo(target, frozen=frozen, shallow=shallow)
        actions.append((target.name, action, target.path))
    return actions


# --------------------------------------------------------------------------- #
# token
# --------------------------------------------------------------------------- #
def seed_token(token_file: Path) -> bool:
    """Write the webhook secret to ``token_file`` (0600) from $GITCODE_WEBHOOK_TOKEN.

    Returns True if a token was written or already present.
    """
    token_file = Path(token_file)
    if token_file.exists():
        print(f"[token] {token_file} already present, left unchanged")
        return True
    secret = os.environ.get("GITCODE_WEBHOOK_TOKEN")
    if not secret:
        print("[token] GITCODE_WEBHOOK_TOKEN not set; skip (set it later, or re-run deploy with it exported)")
        return False
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(secret.rstrip("\n"), encoding="utf-8")
    os.chmod(token_file, stat.S_IRUSR | stat.S_IWUSR)
    print(f"[token] wrote {token_file} (mode 0600)")
    return True


# --------------------------------------------------------------------------- #
# doctor
# --------------------------------------------------------------------------- #
def _check_prereqs() -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warns: list[str] = []
    py = shutil.which("python3")
    if not py:
        issues.append("python3 not found on PATH (require >= 3.10)")
    else:
        version = sys.version_info
        if version < (3, 10):
            issues.append(f"python3 is {version[0]}.{version[1]} (require >= 3.10)")
    if not shutil.which("git"):
        issues.append("git not found on PATH")
    if not shutil.which("rg"):
        warns.append("ripgrep (rg) not found -> evaluator falls back to slow rglob; install ripgrep")
    try:
        import yaml  # noqa: F401
    except ImportError:
        warns.append("PyYAML not importable -> pip install pyyaml (required by the evaluator)")
    if not shutil.which("oh-gc"):
        warns.append("oh-gc not found -> only needed for PR comment writeback: npm i -g @oh-gc/cli@0.7.5")
    return issues, warns


def _load_config(deploy_root: Path):
    """Import the deployed EvaluationConfig; None if specs not yet deployed."""
    spec_eval_dir = deploy_root / "foundation/arkui/ace_engine/specs/tools/spec_eval"
    if not (spec_eval_dir / "config.py").is_file():
        return None
    # `spec_eval` is a package under .../specs/tools ; import its parent.
    sys.path.insert(0, str(spec_eval_dir.parent))
    try:
        from spec_eval.config import EvaluationConfig  # type: ignore
        return EvaluationConfig.discover()
    except Exception as exc:  # noqa: BLE001
        return {"_import_error": str(exc)}


def doctor(deploy_root: Path) -> int:
    issues: list[str] = []
    warns: list[str] = []
    pre_issues, pre_warns = _check_prereqs()
    issues += pre_issues
    warns += pre_warns

    print(f"[doctor] deploy-root = {deploy_root}")
    for target in repo_targets(deploy_root):
        if not _is_git_repo(target.path):
            issues.append(f"{target.name}: not a git repo at {target.path}")
            print(f"  {target.name:11} MISSING  {target.path}")
            continue
        head = _git(["rev-parse", "--short", "HEAD"], cwd=target.path, check=False).stdout.strip() or "?"
        print(f"  {target.name:11} OK head={head:9} {target.path}")

    config = _load_config(deploy_root)
    if config is None:
        warns.append("specs not deployed yet -> config discovery skipped (run deploy first)")
    elif isinstance(config, dict) and config.get("_import_error"):
        issues.append(f"could not import spec_eval.config: {config['_import_error']}")
    else:
        if config.oh_root != deploy_root:
            issues.append(f"oh_root mismatch: config={config.oh_root} != deploy-root={deploy_root} "
                          "(ace_engine must live at <root>/foundation/arkui/ace_engine)")
        else:
            print(f"  config      OK oh_root={config.oh_root}")
        baseline = config.specs_root / "evaluation" / "baselines" / "current.json"
        if baseline.is_file():
            try:
                data = json.loads(baseline.read_text(encoding="utf-8"))
                rule = data.get("rule_version")
                src = (data.get("source_revision") or "")[:7]
                print(f"  baseline    OK source={src} rule=v{rule}")
                if rule is not None and rule != config.rule_version:
                    warns.append(
                        f"baseline rule_version v{rule} != orchestrator v{config.rule_version} "
                        "(baseline drift vs current specs; regenerate via a full scan if you follow master)"
                    )
            except (OSError, json.JSONDecodeError) as exc:
                warns.append(f"baseline unreadable at {baseline}: {exc}")
        else:
            warns.append(f"baseline not found at {baseline}")

    for w in warns:
        print(f"  WARN: {w}")
    if issues:
        for i in issues:
            print(f"  FAIL: {i}")
        print(f"\n[doctor] {len(issues)} blocking issue(s), {len(warns)} warning(s)")
        return 1
    print(f"\n[doctor] OK ({len(warns)} warning(s))")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deploy/upgrade the spec_eval GitCode MR CI environment")
    sub = parser.add_subparsers(dest="command", required=True)

    # --deploy-root is accepted on every subcommand (operator-natural: after the verb).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--deploy-root", type=Path, default=DEFAULT_DEPLOY_ROOT,
                        help=f"OpenHarmony aggregate root (default {DEFAULT_DEPLOY_ROOT}, or $OH_ROOT)")

    p_deploy = sub.add_parser("deploy", parents=[common], help="clone-or-update all repos into the tree layout")
    p_deploy.add_argument("--frozen", action="store_true", help="pin golden revisions (match the frozen baseline)")
    p_deploy.add_argument("--shallow", action="store_true", help="git clone --depth 1 --single-branch (smaller .git)")
    p_deploy.add_argument("--only", action="append", help="subset: comma list of ace_engine,specs,sdk-js,sdk_c")
    p_deploy.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN_FILE, help="webhook secret destination")
    p_deploy.add_argument("--no-token", action="store_true", help="skip seeding the webhook token")

    p_upgrade = sub.add_parser("upgrade", parents=[common], help="fetch + update already-deployed repos in place")
    p_upgrade.add_argument("--frozen", action="store_true", help="re-align to golden revisions")
    p_upgrade.add_argument("--shallow", action="store_true")
    p_upgrade.add_argument("--only", action="append")

    sub.add_parser("doctor", parents=[common], help="verify prerequisites, layout, config discovery and baseline")
    sub.add_parser("info", parents=[common], help="print each repo path + current HEAD")
    return parser


def cmd_deploy(args: argparse.Namespace) -> int:
    root = Path(args.deploy_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    print(f"[deploy] root={root} policy={'frozen' if args.frozen else 'follow-master'} "
          f"shallow={bool(args.shallow)} repos={[t.name for t in repo_targets(root, only=args.only)]}")
    for name, action, path in sync_all(root, frozen=args.frozen, shallow=args.shallow, only=args.only):
        print(f"  {name:11} {action:24} -> {path}")
    if not args.no_token:
        seed_token(Path(args.token_file))
    ace_engine = root / "foundation/arkui/ace_engine"
    print("\n[deploy] next steps:")
    print(f"  python3 {Path(__file__).name} doctor --deploy-root {root}")
    print(f"  cd {ace_engine} && ./specs/tools/spec_eval/ci_service.sh")
    return 0


def cmd_upgrade(args: argparse.Namespace) -> int:
    root = Path(args.deploy_root).resolve()
    print(f"[upgrade] root={root} policy={'frozen' if args.frozen else 'follow-master'}")
    for name, action, path in sync_all(root, frozen=args.frozen, shallow=args.shallow, only=args.only):
        print(f"  {name:11} {action:24} -> {path}")
    print("\n[upgrade] restart ci_service.sh to pick up changes.")
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    root = Path(args.deploy_root).resolve()
    print(f"[info] root={root}")
    for target in repo_targets(root):
        if _is_git_repo(target.path):
            head = _git(["rev-parse", "--short", "HEAD"], cwd=target.path, check=False).stdout.strip() or "?"
            branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=target.path, check=False).stdout.strip() or "?"
            print(f"  {target.name:11} {head:9} ({branch}) {target.path}")
        else:
            print(f"  {target.name:11} MISSING            {target.path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "deploy":
        return cmd_deploy(args)
    if args.command == "upgrade":
        return cmd_upgrade(args)
    if args.command == "doctor":
        return doctor(Path(args.deploy_root).resolve())
    if args.command == "info":
        return cmd_info(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
