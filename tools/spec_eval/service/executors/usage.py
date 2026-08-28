"""Extract and normalize token counters from executor JSONL events.

Supports both Codex and Claude CLI output formats, normalizing to a unified schema:
    - input_tokens = fresh input + cache creation
    - cached_input_tokens = cache read
    - output_tokens = output tokens
    - total_tokens = input_tokens + output_tokens

Codex emits ``turn.completed.usage`` or legacy ``token_count.info.total_token_usage``.
Claude emits usage in the final ``result`` event.

The adapter accepts either format and keeps the largest cumulative value observed
during one ephemeral invocation. Unknown event shapes are ignored.
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
    "cached_input_tokens": ("cached_input_tokens", "cached_input", "cache_read_input_tokens"),
    "cache_write_input_tokens": ("cache_write_input_tokens", "cache_write_input", "cache_creation_input_tokens"),
    "output_tokens": ("output_tokens", "output"),
    "reasoning_output_tokens": ("reasoning_output_tokens", "reasoning_output"),
    "total_tokens": ("total_tokens", "total"),
}


@dataclass
class TokenUsageAccumulator:
    """Collect the final cumulative usage snapshot for one executor process.

    Accumulates usage from both Codex and Claude CLI output, normalizing to
    a unified schema where input_tokens includes cache creation.
    """

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
    """Normalize usage counters to a unified schema.

    Unified schema:
        input_tokens = fresh_input + cache_creation
        cached_input_tokens = cache_read
        output_tokens = output
        total_tokens = input_tokens + output_tokens

    Handles both Codex and Claude raw formats:
        - Codex: input_tokens, cache_write_input_tokens, cached_input_tokens
        - Claude: input_tokens, cache_creation_input_tokens, cache_read_input_tokens
    """
    if not isinstance(candidate, dict):
        return None

    # Extract raw values using aliases
    raw_values: dict[str, int] = {}
    found = False
    for canonical, aliases in _ALIASES.items():
        value = 0
        for alias in aliases:
            raw = candidate.get(alias)
            if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0:
                value = raw
                found = True
                break
        raw_values[canonical] = value

    if not found:
        return None

    # Normalize to unified schema:
    # input_tokens should include cache_creation/cache_write
    # For Codex: input_tokens already includes fresh input, add cache_write if separate
    # For Claude: input_tokens is fresh only, add cache_creation
    values: dict[str, int] = {}
    values["input_tokens"] = raw_values["input_tokens"] + raw_values["cache_write_input_tokens"]
    values["cached_input_tokens"] = raw_values["cached_input_tokens"]
    values["cache_write_input_tokens"] = raw_values["cache_write_input_tokens"]
    values["output_tokens"] = raw_values["output_tokens"]
    values["reasoning_output_tokens"] = raw_values["reasoning_output_tokens"]

    # Calculate total_tokens
    if raw_values["total_tokens"] > 0:
        values["total_tokens"] = raw_values["total_tokens"]
    else:
        values["total_tokens"] = values["input_tokens"] + values["output_tokens"]

    return values
