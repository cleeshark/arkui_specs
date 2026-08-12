"""Evidence stage: build the Function evidence package (the staged-run input-dir).

Runs ``spec_eval evidence --func-id <FID>`` against the current working tree
(revision freezing/worktree isolation arrives in Phase 3). The produced package
— ``function-context.json``, ``static-result.json``, ``evidence-manifest.json``
and the ``evidence/`` shards — is exactly what ``initialize_staged_run.py``
consumes as ``--input-dir``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ._subprocess import Runner, default_runner, write_logs
from .context import RunContext

DEFAULT_EVIDENCE_TIMEOUT = 1800.0


class EvidenceStageError(RuntimeError):
    """Raised when the evidence package cannot be built or is incomplete."""


def prepare_evidence(
    ctx: RunContext,
    *,
    runner: Runner = default_runner,
    timeout: float = DEFAULT_EVIDENCE_TIMEOUT,
) -> Path:
    """Build the evidence package and return the input-dir path.

    Raises :class:`EvidenceStageError` if the command fails or any required
    artifact is missing.
    """
    ctx.evidence_output_root.mkdir(parents=True, exist_ok=True)
    argv = [
        "python3",
        str(ctx.cli_path),
        "--output",
        str(ctx.evidence_output_root),
        "--no-cache",
        "--quiet",
        "evidence",
        "--func-id",
        ctx.func_id,
    ]
    log_dir = ctx.evidence_output_root / ".logs"
    try:
        cp = runner(argv, cwd=str(ctx.repo_root), timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise EvidenceStageError(f"evidence command timed out after {timeout:.0f}s") from exc
    write_logs(log_dir / "evidence.stdout.log", log_dir / "evidence.stderr.log", cp)
    if cp.returncode != 0:
        tail = (cp.stderr or "").strip().splitlines()[-5:]
        raise EvidenceStageError(
            f"spec_eval evidence exited {cp.returncode}: {' | '.join(tail) or 'see logs'}"
        )

    _require(ctx.input_dir / "function-context.json")
    _require(ctx.input_dir / "static-result.json")
    _require(ctx.input_dir / "evidence-manifest.json")
    return ctx.input_dir


def _require(path: Path) -> None:
    if not path.is_file():
        raise EvidenceStageError(f"evidence package missing required file: {path}")
