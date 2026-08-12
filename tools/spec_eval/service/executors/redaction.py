"""Sensitive-field redaction for executor logs (service plan §2 / §2.1).

The service must not write tokens, model keys or full environment variables to
logs. Codex JSONL events are filtered through :func:`redact_jsonl` before they
reach the event log. Patterns are deliberately conservative: they target common
secret shapes rather than arbitrary content.
"""

from __future__ import annotations

import json
import re
from typing import Any

# Conservative secret-like patterns. Matched case-insensitively.
_SECRET_PATTERNS = [
    # Bearer / Authorization headers
    re.compile(r"(?i)\b(authorization|bearer)\b[:=]?\s*\S+"),
    # Generic api_key / secret / token assignments
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd)\b['\"]?\s*[:=]\s*\S+"),
    # sk-... style API keys (OpenAI/Anthropic-style)
    re.compile(r"\bsk-[A-Za-z0-9_\-]{8,}"),
    # hex/base64 blobs >= 32 chars that look like keys (not file hashes)
    re.compile(r"(?i)\b[A-Fa-f0-9]{64}\b"),
]

_REDACTED = "<redacted>"


def redact_text(value: str) -> str:
    """Redact secret-like substrings in free text."""
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_REDACTED, redacted)
    return redacted


def redact_jsonl(line: str) -> str:
    """Redact a Codex JSONL line, preserving its JSON structure when possible.

    Falls back to :func:`redact_text` if the line is not valid JSON. Within a
    valid JSON object, secret-named keys are blanked and any secret-like
    substring inside a string value is regex-redacted.
    """
    stripped = line.strip()
    if not stripped:
        return line
    try:
        obj: Any = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return redact_text(line)
    return json.dumps(_redact_obj(obj), ensure_ascii=False, sort_keys=True)


def _redact_obj(obj: Any) -> Any:
    if isinstance(obj, dict):
        redacted: dict[Any, Any] = {}
        for key, value in obj.items():
            lowered = str(key).lower()
            if any(s in lowered for s in ("token", "secret", "key", "password", "auth")):
                redacted[key] = _REDACTED
            else:
                redacted[key] = _redact_obj(value)
        return redacted
    if isinstance(obj, list):
        return [_redact_obj(item) for item in obj]
    if isinstance(obj, str):
        return redact_text(obj)
    return obj
