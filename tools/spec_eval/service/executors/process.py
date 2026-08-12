"""Subprocess helpers for executor backends.

Runs an external command, streams its stdout line-by-line (for JSONL progress),
captures stdout/stderr to files, and enforces timeout + cooperative
cancellation by terminating the whole process group. No token or environment
content is written to logs (see ``redaction.py`` for stdout filtering).
"""

from __future__ import annotations

import os
import queue
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

LineSink = Callable[[str], None]


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int | None
    timed_out: bool
    cancelled: bool
    elapsed_seconds: float
    stdout_log_path: str
    stderr_log_path: str


def _terminate_group(proc: subprocess.Popen) -> None:
    """Terminate the whole process group (SIGTERM then SIGKILL)."""
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        proc.terminate()
        return
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            proc.kill()
        proc.wait(timeout=5)


def run_subprocess(
    argv: list[str],
    *,
    cwd: str,
    stdin: str | None,
    timeout: float,
    stdout_log_path: str,
    stderr_log_path: str,
    cancel: threading.Event | None = None,
    line_sink: LineSink | None = None,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    """Run ``argv`` streaming stdout lines; honour timeout and cancellation.

    A new process group is created so the entire child tree can be terminated
    on timeout/cancel. stdout is read on a background thread and each line is
    passed to ``line_sink`` (after the caller redacts it) and appended to the
    stdout log; stderr goes straight to its log file.
    """
    started = time.monotonic()
    Path(stdout_log_path).parent.mkdir(parents=True, exist_ok=True)
    Path(stderr_log_path).parent.mkdir(parents=True, exist_ok=True)

    with open(stderr_log_path, "w", encoding="utf-8") as stderr_fh, \
            open(stdout_log_path, "w", encoding="utf-8") as stdout_fh:
        proc = subprocess.Popen(  # noqa: S603 - argv is built internally by the adapter
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE if stdin is not None else None,
            stdout=subprocess.PIPE,
            stderr=stderr_fh,
            text=True,
            encoding="utf-8",
            env=env,
            start_new_session=True,  # new process group for group termination
        )

        if stdin is not None:
            try:
                proc.stdin.write(stdin)
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        lines_q: queue.Queue[str | None] = queue.Queue()

        def reader() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                lines_q.put(line)
            lines_q.put(None)  # sentinel: EOF

        reader_thread = threading.Thread(target=reader, daemon=True)
        reader_thread.start()

        timed_out = False
        cancelled = False
        deadline = started + timeout if timeout > 0 else None

        while True:
            try:
                item = lines_q.get(timeout=0.2)
            except queue.Empty:
                item = None
            if item is None:
                # Either EOF or a poll timeout; distinguish below.
                if not reader_thread.is_alive() and lines_q.empty():
                    if proc.poll() is not None:
                        break
                # check cancellation / timeout while waiting for more output
            else:
                stdout_fh.write(item)
                stdout_fh.flush()
                if line_sink is not None:
                    line_sink(item.rstrip("\n"))

            if cancel is not None and cancel.is_set():
                cancelled = True
                _terminate_group(proc)
                break
            if deadline is not None and time.monotonic() >= deadline and proc.poll() is None:
                timed_out = True
                _terminate_group(proc)
                break
            if proc.poll() is not None and lines_q.empty() and not reader_thread.is_alive():
                break

        reader_thread.join(timeout=5)
        exit_code = proc.poll()
        if exit_code is None:
            _terminate_group(proc)
            exit_code = proc.wait()

    return ProcessResult(
        exit_code=exit_code,
        timed_out=timed_out,
        cancelled=cancelled,
        elapsed_seconds=time.monotonic() - started,
        stdout_log_path=stdout_log_path,
        stderr_log_path=stderr_log_path,
    )
