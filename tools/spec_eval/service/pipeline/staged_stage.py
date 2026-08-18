"""Staged-run stage: thin wrappers around the staged-run skill scripts.

Each function maps to one skill script call:

* :func:`init_staged_run`      -> ``initialize_staged_run.py``
* :func:`next_work_item`       -> ``show_next_work_item.py`` (one pending item)
* :func:`validate_work_item`   -> ``validate_staged_run.py --work-item --update-state``
* :func:`build_aggregation_context` -> ``build_aggregation_context.py``
* :func:`assemble_semantic`    -> ``assemble_semantic_result.py``

The wrappers never decide completeness on their own: they forward the script's
exit code and error lines. A non-zero validator means the checkpoint is not
complete (service plan §7 anti-fake-completion).
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._subprocess import Runner, default_runner, write_logs
from .context import RunContext

DEFAULT_SCRIPT_TIMEOUT = 300.0


class StagedStageError(RuntimeError):
    """Raised when a staged-run script fails fatally (not a validation failure)."""


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...]


def init_staged_run(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = DEFAULT_SCRIPT_TIMEOUT,
) -> None:
    """Initialize a staged run. ``ctx.run_dir`` must not exist or be empty."""
    ctx.run_dir.parent.mkdir(parents=True, exist_ok=True)
    argv = [
        "python3",
        str(ctx.initialize_script),
        "--func-id",
        ctx.func_id,
        "--input-dir",
        str(ctx.input_dir),
        "--run-id",
        ctx.run_id,
        "--run-dir",
        str(ctx.run_dir),
        "--evaluation-mode",
        "automated",
        "--source-revision",
        ctx.source_revision,
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(argv, cwd=str(ctx.repo_root), runner=runner, timeout=timeout, log_dir=log_dir, name="init")
    if cp.returncode != 0:
        raise StagedStageError(_format_failure("initialize_staged_run", cp))


def next_work_item(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = 60.0,
) -> dict[str, Any] | None:
    """Return the next pending work item, or ``None`` if none remain.

    ``None`` means the run has no more observation work items (the script then
    advises completing aggregation — Phase 4 territory).
    """
    argv = ["python3", str(ctx.show_next_script), "--run-dir", str(ctx.run_dir)]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(argv, cwd=str(ctx.repo_root), runner=runner, timeout=timeout, log_dir=log_dir, name="show_next")
    if cp.returncode != 0:
        raise StagedStageError(_format_failure("show_next_work_item", cp))
    try:
        payload = json.loads(cp.stdout)
    except (json.JSONDecodeError, ValueError) as exc:
        raise StagedStageError(f"show_next_work_item produced non-JSON output: {exc}") from exc
    item = payload.get("work_item")
    return item if isinstance(item, dict) else None


def validate_work_item(
    ctx: RunContext,
    work_item_id: str,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> ValidationResult:
    """Validate and checkpoint one work item. Returns the validator verdict."""
    argv = [
        "python3",
        str(ctx.validate_script),
        "--run-dir",
        str(ctx.run_dir),
        "--work-item",
        work_item_id,
        "--update-state",
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(
        argv,
        cwd=str(ctx.repo_root),
        runner=runner,
        timeout=timeout,
        log_dir=log_dir,
        name=f"validate-{work_item_id}",
    )
    return _validation_result(cp, "validate work item")


def validate_work_item_candidate(
    ctx: RunContext,
    work_item_id: str,
    candidate_path: Path,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> ValidationResult:
    """Validate one candidate observation without replacing the initialized template."""
    argv = [
        "python3",
        str(ctx.validate_script),
        "--run-dir",
        str(ctx.run_dir),
        "--work-item",
        work_item_id,
        "--candidate",
        str(candidate_path),
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(
        argv,
        cwd=str(ctx.repo_root),
        runner=runner,
        timeout=timeout,
        log_dir=log_dir,
        name=f"validate-candidate-{work_item_id}",
    )
    return _validation_result(cp, "validate observation candidate")


def validate_observation_checkpoints(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> ValidationResult:
    """Recheck every persisted observation before starting aggregation.

    This is a read-only, cheap defense against stale or externally modified
    observation artifacts.  It intentionally does not update staged state.
    """
    argv = [
        "python3",
        str(ctx.validate_script),
        "--run-dir",
        str(ctx.run_dir),
        "--stage",
        "observations",
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(
        argv,
        cwd=str(ctx.repo_root),
        runner=runner,
        timeout=timeout,
        log_dir=log_dir,
        name="validate-observation-checkpoints",
    )
    return _validation_result(cp, "validate observation checkpoints")


def validate_aggregation_candidate(
    ctx: RunContext,
    candidate_path: Path,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> ValidationResult:
    """Validate aggregation against every checkpoint before publishing it."""
    argv = [
        "python3",
        str(ctx.validate_script),
        "--run-dir",
        str(ctx.run_dir),
        "--stage",
        "aggregation",
        "--candidate",
        str(candidate_path),
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(
        argv,
        cwd=str(ctx.repo_root),
        runner=runner,
        timeout=timeout,
        log_dir=log_dir,
        name="validate-aggregation-candidate",
    )
    return _validation_result(cp, "validate aggregation candidate")


def build_aggregation_context(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> Path:
    """Build the Skill-owned run-derived mapping used by aggregation."""
    output = ctx.run_dir / "aggregation-context.json"
    argv = [
        "python3",
        str(ctx.build_aggregation_context_script),
        "--run-dir",
        str(ctx.run_dir),
        "--output",
        str(output),
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(
        argv,
        cwd=str(ctx.repo_root),
        runner=runner,
        timeout=timeout,
        log_dir=log_dir,
        name="build-aggregation-context",
    )
    if cp.returncode != 0:
        raise StagedStageError(_format_failure("build_aggregation_context", cp))
    if not output.is_file():
        raise StagedStageError(f"build_aggregation_context produced no file at {output}")
    return output


def assemble_semantic(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> Path:
    """Assemble ``semantic-result.json`` from completed observations + aggregation.

    Phase 2 stops at completed observations; this is exercised once aggregation
    (Phase 4 / TASK-011-07) has written ``aggregation.json``.
    """
    argv = ["python3", str(ctx.assemble_script), "--run-dir", str(ctx.run_dir)]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(argv, cwd=str(ctx.repo_root), runner=runner, timeout=timeout, log_dir=log_dir, name="assemble")
    if cp.returncode != 0:
        raise StagedStageError(_format_failure("assemble_semantic_result", cp))
    return ctx.run_dir / "semantic-result.json"


def validate_final(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = 120.0,
) -> ValidationResult:
    """Validate and checkpoint the ``final`` stage after assembly."""
    argv = [
        "python3",
        str(ctx.validate_script),
        "--run-dir",
        str(ctx.run_dir),
        "--stage",
        "final",
        "--update-state",
    ]
    log_dir = ctx.jobs_run_root / "logs"
    cp = _run(
        argv,
        cwd=str(ctx.repo_root),
        runner=runner,
        timeout=timeout,
        log_dir=log_dir,
        name="validate-final",
    )
    return _validation_result(cp, "validate final result")


def _run(
    argv: list[str],
    *,
    cwd: str,
    runner: Runner,
    timeout: float,
    log_dir: Path,
    name: str,
) -> subprocess.CompletedProcess:
    try:
        cp = runner(argv, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise StagedStageError(f"{name} timed out after {timeout:.0f}s") from exc
    write_logs(log_dir / f"{name}.stdout.log", log_dir / f"{name}.stderr.log", cp)
    return cp


def _format_failure(name: str, cp: subprocess.CompletedProcess) -> str:
    tail = (cp.stderr or "").strip().splitlines()[-4:]
    return f"{name} exited {cp.returncode}: {' | '.join(tail) or 'see logs'}"


def _validation_result(cp: subprocess.CompletedProcess, name: str) -> ValidationResult:
    errors = tuple(
        line[len("ERROR:"):].strip()
        for line in (cp.stderr or "").splitlines()
        if line.startswith("ERROR:")
    )
    if cp.returncode != 0 and not errors:
        tail = (cp.stderr or cp.stdout or "").strip().splitlines()[-4:]
        errors = (f"{name} exited {cp.returncode}: {' | '.join(tail) or 'see logs'}",)
    return ValidationResult(ok=cp.returncode == 0 and not errors, errors=errors)
