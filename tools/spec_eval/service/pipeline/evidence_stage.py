"""Evidence stage: build the Function evidence package (the staged-run input-dir).

Runs ``spec_eval evidence --func-id <FID>`` against the Job's detached revision
workspace. The produced package
— ``function-context.json``, ``static-result.json``, ``evidence-manifest.json``
and the ``evidence/`` shards — is exactly what ``initialize_staged_run.py``
consumes as ``--input-dir``.
"""

from __future__ import annotations

import json
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
    # The CLI exits 1 when the *static gate* is "fail" — findings exist, which is
    # exactly what the semantic evaluation is meant to judge. The evidence
    # package is written before the gate is checked, so rc 0/1 both mean the
    # run succeeded; rc 2 is a SpecEvalError and rc 3 is gate "error".
    if cp.returncode not in (0, 1):
        tail = (cp.stderr or "").strip().splitlines()[-5:] or (cp.stdout or "").strip().splitlines()[-5:]
        raise EvidenceStageError(
            f"spec_eval evidence exited {cp.returncode}: {' | '.join(tail) or 'see logs'}"
        )

    return validate_evidence_package(ctx)


def validate_evidence_package(ctx: RunContext) -> Path:
    """Validate the exact evidence path and its FuncID/revision envelope."""
    package_dir = ctx.input_dir
    for name in ("function-context.json", "static-result.json", "evidence-manifest.json"):
        _require(package_dir / name)
    _validate_revision_envelope(package_dir, ctx.func_id, ctx.source_revision)
    return package_dir


def _require(path: Path) -> None:
    if not path.is_file():
        raise EvidenceStageError(f"evidence package missing required file: {path}")


def _validate_revision_envelope(package_dir: Path, func_id: str, source_revision: str) -> None:
    for name in ("function-context.json", "static-result.json", "evidence-manifest.json"):
        path = package_dir / name
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise EvidenceStageError(f"cannot validate revision envelope in {path}: {exc}") from exc
        if not isinstance(document, dict):
            raise EvidenceStageError(f"{name}: expected a JSON object")
        if document.get("func_id") != func_id:
            raise EvidenceStageError(
                f"{name}: FuncID mismatch, expected {func_id}, got {document.get('func_id')!r}"
            )
        if document.get("source_revision") != source_revision:
            raise EvidenceStageError(
                f"{name}: source revision mismatch, expected {source_revision}, "
                f"got {document.get('source_revision')!r}"
            )
