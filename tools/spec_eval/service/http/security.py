"""HTTP access security (TASK-011-06).

The primary boundary is loopback binding (the server defaults to 127.0.0.1).
When a token is configured (recommended for non-loopback binds), every API
request must carry it. Artifact/static downloads resolve the target and reject
any path that escapes its allowed root (path traversal defence).
"""

from __future__ import annotations

from pathlib import Path


def token_ok(headers: dict[str, str], expected: str | None) -> bool:
    """Return True if the request satisfies the optional bearer-token requirement."""
    if not expected:
        return True
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    candidate = auth.strip()
    if candidate.lower().startswith("bearer "):
        candidate = candidate[7:].strip()
    return candidate == expected


def safe_resolve(root: Path, candidate: Path) -> Path | None:
    """Return the resolved candidate if it lives strictly under ``root``, else None."""
    try:
        root_resolved = Path(root).resolve()
        cand_resolved = Path(candidate).resolve()
    except (OSError, RuntimeError):
        return None
    try:
        cand_resolved.relative_to(root_resolved)
    except ValueError:
        return None
    if not cand_resolved.is_file():
        return None
    return cand_resolved
