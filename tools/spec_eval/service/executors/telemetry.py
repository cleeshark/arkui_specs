"""Conservative, non-sensitive telemetry for Codex/Claude JSONL executor events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract import WorkItemInput


_KNOWN_EVENT_TYPES = {
    # Codex JSONL event types
    "thread.started",
    "turn.started",
    "turn.completed",
    "turn.failed",
    "item.started",
    "item.updated",
    "item.completed",
    "error",
    # Claude stream-json event types
    "system",
    "assistant",
    "result",
}
_COMMAND_ITEM_TYPES = {"command_execution"}
_TOOL_ITEM_TYPES = {
    "command_execution",
    "mcp_tool_call",
    "tool_call",
    "file_search",
}
_CLAUDE_COMMAND_TOOLS = {"Bash"}


class ExecutionTelemetryAccumulator:
    """Count stable tool events and distinct declared input-path hits.

    Unknown JSONL shapes are ignored and leave ``reported`` false. Paths are
    never returned; only aggregate counts cross the executor boundary.
    """

    def __init__(self, work: WorkItemInput) -> None:
        self._work = work
        self._reported = False
        self._tool_calls = 0
        self._command_calls = 0
        self._input_hits: set[str] = set()
        self._evidence_hits: set[str] = set()

    @property
    def reported(self) -> bool:
        return self._reported

    def observe(self, line: str) -> None:
        try:
            event = json.loads(line)
        except (TypeError, json.JSONDecodeError):
            return
        if not isinstance(event, dict):
            return
        event_type = event.get("type")
        if event_type not in _KNOWN_EVENT_TYPES:
            return
        self._reported = True

        # Codex: tool calls via item.completed
        if event_type == "item.completed":
            item = event.get("item")
            if not isinstance(item, dict):
                return
            item_type = item.get("type")
            if item_type in _TOOL_ITEM_TYPES:
                self._tool_calls += 1
            if item_type in _COMMAND_ITEM_TYPES:
                self._command_calls += 1
            if item_type in _TOOL_ITEM_TYPES:
                self._record_input_hits(_flatten_strings(item))
            return

        # Claude: tool calls via assistant message content blocks
        if event_type == "assistant":
            message = event.get("message")
            if not isinstance(message, dict):
                return
            content = message.get("content")
            if not isinstance(content, list):
                return
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    self._tool_calls += 1
                    tool_name = block.get("name", "")
                    if tool_name in _CLAUDE_COMMAND_TOOLS:
                        self._command_calls += 1
                    tool_input = block.get("input")
                    if isinstance(tool_input, dict):
                        self._record_input_hits(_flatten_strings(tool_input))
            return

    def snapshot(self) -> dict[str, int]:
        return {
            "tool_calls": self._tool_calls,
            "command_calls": self._command_calls,
            "input_paths_accessed": len(self._input_hits),
            "evidence_paths_accessed": len(self._evidence_hits),
        }

    def _record_input_hits(self, texts: list[str]) -> None:
        haystack = "\n".join(texts)
        if not haystack:
            return
        repo_root = Path(self._work.repo_root)
        run_dir = Path(self._work.run_dir)
        for raw_path in self._work.input_paths:
            path = Path(raw_path)
            candidates = {str(path)}
            for root in (repo_root, run_dir):
                try:
                    candidates.add(str(path.relative_to(root)))
                except ValueError:
                    pass
            if not any(candidate and candidate in haystack for candidate in candidates):
                continue
            self._input_hits.add(str(path))
            normalized = path.as_posix()
            if (
                "/evidence/" in normalized
                or path.name in {
                    "evidence-manifest.json",
                    "function-context.json",
                    "static-result.json",
                }
            ):
                self._evidence_hits.add(str(path))


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for nested in value.values() for text in _flatten_strings(nested)]
    if isinstance(value, list):
        return [text for nested in value for text in _flatten_strings(nested)]
    return []
