"""Process-level immutable file indexes for source citation resolution."""

from __future__ import annotations

import subprocess
import time
from collections import defaultdict
from pathlib import Path

from spec_eval.config import EvaluationConfig


class RepositoryFileIndex:
    """Index repository and SDK files once instead of running ``rg --files`` per citation."""

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.repo_root = config.repo_root.resolve()
        self.sdk_root = (config.oh_root / "interface" / "sdk-js").resolve()
        self._repo_by_basename: dict[str, tuple[Path, ...]] = {}
        self._sdk_by_basename: dict[str, tuple[Path, ...]] = {}
        self._prepared = False
        self._stats: dict[str, int | float] = {
            "duration_ms": 0.0,
            "repository_file_count": 0,
            "sdk_file_count": 0,
            "basename_count": 0,
        }

    def prepare(self) -> dict[str, int | float]:
        if self._prepared:
            return self.stats()
        started = time.perf_counter()
        repo_paths = self._scan(self.repo_root)
        sdk_paths = (
            self._scan(
                self.sdk_root,
                excluded_parts={"zh-cn"},
                included_suffixes=(".static.d.ets", ".d.ets", ".d.ts"),
            )
            if self.sdk_root.is_dir()
            else []
        )
        self._repo_by_basename = self._group(repo_paths)
        self._sdk_by_basename = self._group(sdk_paths)
        self._prepared = True
        self._stats = {
            "duration_ms": round((time.perf_counter() - started) * 1000, 3),
            "repository_file_count": len(repo_paths),
            "sdk_file_count": len(sdk_paths),
            "basename_count": len(set(self._repo_by_basename) | set(self._sdk_by_basename)),
        }
        return self.stats()

    def basename_matches(self, name: str, *, include_sdk: bool = False) -> tuple[Path, ...]:
        self.prepare()
        matches = set(self._repo_by_basename.get(name, ()))
        if include_sdk:
            matches.update(self._sdk_by_basename.get(name, ()))
        return tuple(sorted(matches, key=lambda path: path.as_posix()))

    def suffix_matches(self, suffix: str) -> tuple[Path, ...]:
        self.prepare()
        normalized = suffix.replace("\\", "/")
        name = Path(normalized).name
        return tuple(
            path
            for path in self._repo_by_basename.get(name, ())
            if path.as_posix().endswith(normalized)
        )

    def stats(self) -> dict[str, int | float]:
        return dict(self._stats)

    @staticmethod
    def _group(paths: list[Path]) -> dict[str, tuple[Path, ...]]:
        grouped: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            grouped[path.name].append(path)
        return {
            name: tuple(sorted(values, key=lambda path: path.as_posix()))
            for name, values in grouped.items()
        }

    @staticmethod
    def _scan(
        root: Path,
        excluded_parts: set[str] | None = None,
        included_suffixes: tuple[str, ...] | None = None,
    ) -> list[Path]:
        if not root.is_dir():
            return []
        excluded_parts = excluded_parts or set()
        try:
            result = subprocess.run(
                ["rg", "--files", "--hidden", "--no-ignore-vcs"],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            relative_paths = [Path(line) for line in result.stdout.splitlines() if line.strip()]
        except OSError:
            relative_paths = [path.relative_to(root) for path in root.rglob("*") if path.is_file()]
        paths = {
            (root / relative).resolve()
            for relative in relative_paths
            if not excluded_parts.intersection(relative.parts)
            and (included_suffixes is None or relative.name.endswith(included_suffixes))
            and (root / relative).is_file()
        }
        return sorted(paths, key=lambda path: path.as_posix())
