#!/usr/bin/env python3

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence


ACTION_CONNECT_RETRY_COUNT = 20
ACTION_CONNECT_RETRY_INTERVAL_SEC = 0.1


def load_operations(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise RuntimeError(f"operations file is not a list: {path}")
    ops: List[Dict[str, Any]] = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise RuntimeError(f"operation[{i}] is not an object")
        if not item.get("op"):
            raise RuntimeError(f"operation[{i}] missing 'op'")
        ops.append(item)
    return ops


def to_int(v: Any, name: str) -> int:
    if isinstance(v, bool):
        raise RuntimeError(f"{name} must be int, got bool")
    try:
        return int(v)
    except Exception as exc:
        raise RuntimeError(f"{name} must be int, got {v!r}") from exc


def build_args_pairs(args_obj: Dict[str, Any]) -> List[str]:
    cli_args: List[str] = []
    for k, v in args_obj.items():
        key = f"-{k}" if len(k) == 1 else f"--{k}"
        cli_args.extend([key, str(v)])
    return cli_args


def call_action(
    previewer_bin: Path,
    previewer_name: str,
    command: str,
    args_pairs: Sequence[str],
    op_log: Path,
    timeout_sec: int,
) -> None:
    cli = previewer_bin / "PreviewerCLI"
    cmd = [
        str(cli),
        "--name",
        previewer_name,
        "--",
        "--type",
        "action",
        "--command",
        command,
        "--version",
        "1.0.1",
    ]
    if args_pairs:
        cmd.append("--args")
        cmd.extend(args_pairs)

    def is_socket_not_ready(output: str) -> bool:
        text = output.lower()
        return "connect socket failed" in text or "unable to connect to server socket" in text

    last_rc = 0
    for attempt in range(1, ACTION_CONNECT_RETRY_COUNT + 1):
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout_sec,
            check=False,
        )

        with op_log.open("a", encoding="utf-8") as f:
            f.write(f"### COMMAND {command}")
            if ACTION_CONNECT_RETRY_COUNT > 1:
                f.write(f" (attempt {attempt}/{ACTION_CONNECT_RETRY_COUNT})")
            f.write("\n")
            f.write("ARGS: " + (" ".join(args_pairs) if args_pairs else "(none)") + "\n")
            f.write(proc.stdout or "")
            if proc.stdout and not proc.stdout.endswith("\n"):
                f.write("\n")
            f.write("\n")

        if proc.returncode == 0:
            return

        last_rc = proc.returncode
        output = proc.stdout or ""
        if attempt < ACTION_CONNECT_RETRY_COUNT and is_socket_not_ready(output):
            time.sleep(ACTION_CONNECT_RETRY_INTERVAL_SEC)
            continue
        raise RuntimeError(f"PreviewerCLI command failed: {command} rc={proc.returncode}")

    raise RuntimeError(f"PreviewerCLI command failed after retries: {command} rc={last_rc}")


def execute_click(
    previewer_bin: Path,
    previewer_name: str,
    op: Dict[str, Any],
    op_log: Path,
    timeout_sec: int,
) -> None:
    inject = str(op.get("inject", "touch")).lower()
    x = to_int(op.get("x"), "click.x")
    y = to_int(op.get("y"), "click.y")
    hold_ms = to_int(op.get("holdMs", 40), "click.holdMs")
    if hold_ms < 0:
        raise RuntimeError("click.holdMs must be >= 0")

    if inject == "touch":
        press_cmd, release_cmd = "TouchPress", "TouchRelease"
    elif inject == "mouse":
        press_cmd, release_cmd = "MousePress", "MouseRelease"
    else:
        raise RuntimeError(f"unsupported click.inject: {inject}")

    args_pairs = ["-x", str(x), "-y", str(y)]
    call_action(previewer_bin, previewer_name, press_cmd, args_pairs, op_log, timeout_sec)
    if hold_ms > 0:
        time.sleep(hold_ms / 1000.0)
    call_action(previewer_bin, previewer_name, release_cmd, args_pairs, op_log, timeout_sec)


def extract_swipe_coords(op: Dict[str, Any]) -> Dict[str, int]:
    if isinstance(op.get("from"), dict) and isinstance(op.get("to"), dict):
        start = op["from"]
        end = op["to"]
        return {
            "start_x": to_int(start.get("x"), "swipe.from.x"),
            "start_y": to_int(start.get("y"), "swipe.from.y"),
            "end_x": to_int(end.get("x"), "swipe.to.x"),
            "end_y": to_int(end.get("y"), "swipe.to.y"),
        }
    return {
        "start_x": to_int(op.get("startX"), "swipe.startX"),
        "start_y": to_int(op.get("startY"), "swipe.startY"),
        "end_x": to_int(op.get("endX"), "swipe.endX"),
        "end_y": to_int(op.get("endY"), "swipe.endY"),
    }


def execute_swipe(
    previewer_bin: Path,
    previewer_name: str,
    op: Dict[str, Any],
    op_log: Path,
    timeout_sec: int,
) -> None:
    inject = str(op.get("inject", "touch")).lower()
    if inject == "touch":
        press_cmd, move_cmd, release_cmd = "TouchPress", "TouchMove", "TouchRelease"
    elif inject == "mouse":
        press_cmd, move_cmd, release_cmd = "MousePress", "MouseMove", "MouseRelease"
    else:
        raise RuntimeError(f"unsupported swipe.inject: {inject}")

    coords = extract_swipe_coords(op)
    steps = to_int(op.get("steps", 6), "swipe.steps")
    duration_ms = to_int(op.get("durationMs", 300), "swipe.durationMs")
    if steps <= 0:
        raise RuntimeError("swipe.steps must be > 0")
    if duration_ms < 0:
        raise RuntimeError("swipe.durationMs must be >= 0")

    step_sleep = duration_ms / steps / 1000.0 if steps > 0 else 0.0

    call_action(
        previewer_bin,
        previewer_name,
        press_cmd,
        ["-x", str(coords["start_x"]), "-y", str(coords["start_y"])],
        op_log,
        timeout_sec,
    )

    for i in range(1, steps + 1):
        x = round(coords["start_x"] + (coords["end_x"] - coords["start_x"]) * i / steps)
        y = round(coords["start_y"] + (coords["end_y"] - coords["start_y"]) * i / steps)
        call_action(previewer_bin, previewer_name, move_cmd, ["-x", str(x), "-y", str(y)], op_log, timeout_sec)
        if step_sleep > 0:
            time.sleep(step_sleep)

    call_action(
        previewer_bin,
        previewer_name,
        release_cmd,
        ["-x", str(coords["end_x"]), "-y", str(coords["end_y"])],
        op_log,
        timeout_sec,
    )


def execute_wait(op: Dict[str, Any]) -> None:
    duration_ms = to_int(op.get("durationMs"), "wait.durationMs")
    if duration_ms < 0:
        raise RuntimeError("wait.durationMs must be >= 0")
    time.sleep(duration_ms / 1000.0)


def execute_custom_action(
    previewer_bin: Path,
    previewer_name: str,
    op: Dict[str, Any],
    op_log: Path,
    timeout_sec: int,
) -> None:
    command = str(op.get("command", "")).strip()
    if not command:
        raise RuntimeError("action.command is required")
    args_obj = op.get("args", {})
    if args_obj is None:
        args_obj = {}
    if not isinstance(args_obj, dict):
        raise RuntimeError("action.args must be an object")
    call_action(previewer_bin, previewer_name, command, build_args_pairs(args_obj), op_log, timeout_sec)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previewer-bin", required=True)
    parser.add_argument("--previewer-name", default="previewer")
    parser.add_argument("--operations-file", required=True)
    parser.add_argument("--output-log", required=True)
    parser.add_argument("--timeout-sec", type=int, default=8)
    args = parser.parse_args()

    previewer_bin = Path(args.previewer_bin)
    previewer_name = str(args.previewer_name)
    operations_file = Path(args.operations_file)
    output_log = Path(args.output_log)
    output_log.parent.mkdir(parents=True, exist_ok=True)
    output_log.write_text("", encoding="utf-8")

    operations = load_operations(operations_file)
    if not operations:
        with output_log.open("a", encoding="utf-8") as f:
            f.write("No operations to execute.\n")
        return

    with output_log.open("a", encoding="utf-8") as f:
        f.write(f"Operation count: {len(operations)}\n\n")

    for idx, op in enumerate(operations):
        op_name = str(op.get("op", "")).strip().lower()
        with output_log.open("a", encoding="utf-8") as f:
            f.write(f"== OP[{idx}] {op_name} ==\n")
            f.write(json.dumps(op, ensure_ascii=False) + "\n")

        if op_name == "wait":
            execute_wait(op)
        elif op_name == "click":
            execute_click(previewer_bin, previewer_name, op, output_log, args.timeout_sec)
        elif op_name == "swipe":
            execute_swipe(previewer_bin, previewer_name, op, output_log, args.timeout_sec)
        elif op_name == "action":
            execute_custom_action(previewer_bin, previewer_name, op, output_log, args.timeout_sec)
        else:
            raise RuntimeError(f"unsupported op: {op_name}")

        with output_log.open("a", encoding="utf-8") as f:
            f.write(f"== OP[{idx}] DONE ==\n\n")


if __name__ == "__main__":
    main()
