"""Extract non-sensitive token counters from Codex CLI JSONL events.

Codex versions have emitted both ``turn.completed.usage`` and the older
``token_count.info.total_token_usage`` shape.  The adapter accepts either and
keeps the largest cumulative value observed during one ephemeral invocation.
Unknown event shapes are ignored instead of inventing usage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)

_ALIASES = {
    "input_tokens": ("input_tokens", "input"),
    "cached_input_tokens": ("cached_input_tokens", "cached_input"),
    "cache_write_input_tokens": ("cache_write_input_tokens", "cache_write_input"),
    "output_tokens": ("output_tokens", "output"),
    "reasoning_output_tokens": ("reasoning_output_tokens", "reasoning_output"),
    "total_tokens": ("total_tokens", "total"),
}


@dataclass
class TokenUsageAccumulator:
    """Collect the final cumulative usage snapshot for one Codex process."""

    values: dict[str, int] = field(
        default_factory=lambda: {name: 0 for name in TOKEN_FIELDS}
    )
    reported: bool = False

    def observe(self, line: str) -> None:
        usage = extract_token_usage(line)
        if usage is None:
            return
        self.reported = True
        for name in TOKEN_FIELDS:
            self.values[name] = max(self.values[name], usage[name])

    def snapshot(self) -> dict[str, int]:
        return dict(self.values)


def extract_token_usage(line: str) -> dict[str, int] | None:
    """Return normalized counters from one JSONL line, or ``None``."""
    try:
        document = json.loads(line)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(document, dict):
        return None

    candidates: list[Any] = []
    for container in (document, document.get("payload")):
        if not isinstance(container, dict):
            continue
        candidates.extend((container.get("usage"), container.get("token_usage")))
        info = container.get("info")
        if isinstance(info, dict):
            candidates.extend((info.get("total_token_usage"), info.get("last_token_usage")))

    for candidate in candidates:
        normalized = _normalize(candidate)
        if normalized is not None:
            return normalized
    return None


def _normalize(candidate: Any) -> dict[str, int] | None:
    if not isinstance(candidate, dict):
        return None
    values: dict[str, int] = {}
    found = False
    for canonical, aliases in _ALIASES.items():
        value = 0
        for alias in aliases:
            raw = candidate.get(alias)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0:
                value = raw
                found = True
                break
        values[canonical] = value
    if not found:
        return None
    if values["total_tokens"] == 0:
        values["total_tokens"] = values["input_tokens"] + values["output_tokens"]
    return values
