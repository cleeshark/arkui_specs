"""Shared subprocess runner for pipeline stages.

Stages call external Python scripts (the evaluator CLI and the staged-run skill
scripts). The runner is injectable so tests can drive stages with a fake instead
of spawning real processes. The default runner captures stdout/stderr as text.
"""

from __future__ import annotations

import subprocess
from typing import Callable

# A runner maps (argv, cwd, timeout) to a CompletedProcess with returncode,
# stdout and stderr text. Tests inject fakes conforming to this shape.
Runner = Callable[..., subprocess.CompletedProcess]


def default_runner(argv: list[str], *, cwd: str, timeout: float | None = None) -> subprocess.CompletedProcess:
    """Run ``argv`` capturing stdout/stderr as text."""
    return subprocess.run(  # noqa: S603 - argv is built by the pipeline stages
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def write_logs(stdout_path, stderr_path, cp: subprocess.CompletedProcess) -> None:
    """Persist a CompletedProcess's captured stdout/stderr to log files."""
    from pathlib import Path

    stdout_path = Path(stdout_path)
    stderr_path = Path(stderr_path)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(cp.stdout or "", encoding="utf-8")
    stderr_path.write_text(cp.stderr or "", encoding="utf-8")
