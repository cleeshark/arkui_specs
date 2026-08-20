"""Service runtime configuration.

Mirrors the frozen-dataclass + ``discover()`` style of
``spec_eval.config.EvaluationConfig``. Holds no tokens, model keys or full
environment variables (service plan §2, §6.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _default_executor_config() -> dict[str, Any]:
    """The Phase-1 fixed Codex CLI executor config (service plan §2.1)."""
    return {
        "type": "codex-cli",
        "command": "codex",
        "model": None,
        "sandbox": "read-only",
        "timeout_seconds": 3600,
        "max_parallel": 2,
        "output_schema": "executor-result.schema.json",
    }


def _claude_executor_config() -> dict[str, Any]:
    """Claude CLI executor config."""
    return {
        "type": "claude-cli",
        "command": "claude",
        "model": "claude-opus-4-6[1m]",
        "permission_mode": "bypassPermissions",
        "timeout_seconds": 3600,
        "max_parallel": 2,
        "max_output_tokens": 200_000,
        "output_schema": "executor-result.schema.json",
    }


_EXECUTOR_CONFIGS: dict[str, Any] = {
    "codex": _default_executor_config,
    "claude": _claude_executor_config,
}


def executor_config_for(name: str) -> dict[str, Any]:
    """Return the default config for the named executor."""
    factory = _EXECUTOR_CONFIGS.get(name)
    if factory is None:
        raise ValueError(f"unknown executor: {name!r}")
    return factory()


@dataclass(frozen=True)
class ServiceSettings:
    """Paths and immutable defaults for the local semantic service."""

    data_root: Path
    db_path: Path
    jobs_root: Path
    archives_root: Path
    locks_root: Path
    logs_root: Path
    backups_root: Path
    workspaces_root: Path
    exports_root: Path
    repo_root: Path
    specs_root: Path
    schemas_root: Path
    # service API version recorded on jobs (design v3 R5: independent from the
    # evaluator contract version and the executor envelope schema version)
    protocol_version: str = "0.2.0"
    service_version: str = "0.1.0"
    default_executor_config: dict[str, Any] = field(default_factory=_default_executor_config)

    def __post_init__(self) -> None:
        if self.protocol_version != "0.2.0":
            raise ValueError(
                "unsupported protocol_version: expected '0.2.0', "
                f"got {self.protocol_version!r}"
            )

    @classmethod
    def discover(cls, data_root: Path | str | None = None) -> "ServiceSettings":
        """Build settings from the repo layout, creating the data dir tree.

        ``settings.py`` lives at
        ``<ace_engine>/specs/tools/spec_eval/service/settings.py`` so
        ``parents[4]`` is the ace_engine repo root and ``parents[3]`` is specs.
        """
        repo_root = Path(__file__).resolve().parents[4]
        specs_root = repo_root / "specs"
        schemas_root = specs_root / "evaluation" / "schemas"

        if data_root is None:
            data_root = specs_root / ".evaluator" / "service-data"
        data_root = Path(data_root)

        db_path = data_root / "db" / "service.sqlite3"
        jobs_root = data_root / "jobs"
        archives_root = data_root / "archives" / "automated"
        locks_root = data_root / "locks"
        logs_root = data_root / "logs"
        backups_root = data_root / "backups"
        workspaces_root = data_root / "workspaces"
        exports_root = data_root / "exports"
        # db_path is a file, not a directory; create its parent plus the other roots.
        for path in (
            db_path.parent,
            jobs_root,
            archives_root,
            locks_root,
            logs_root,
            backups_root,
            workspaces_root,
            exports_root,
        ):
            path.mkdir(parents=True, exist_ok=True)

        return cls(
            data_root=data_root,
            db_path=db_path,
            jobs_root=jobs_root,
            archives_root=archives_root,
            locks_root=locks_root,
            logs_root=logs_root,
            backups_root=backups_root,
            workspaces_root=workspaces_root,
            exports_root=exports_root,
            repo_root=repo_root,
            specs_root=specs_root,
            schemas_root=schemas_root,
        )
