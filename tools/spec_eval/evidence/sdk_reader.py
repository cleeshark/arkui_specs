"""Canonical SDK declaration locator."""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Iterable

from spec_eval.config import EvaluationConfig


class SdkReader:
    IDENTIFIER_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
    MAX_DECLARATIONS_PER_API = 20
    MAX_SUFFIX_CANDIDATES = 100

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.sdk_root = config.oh_root / "interface" / "sdk-js" / "api"
        self.ndk_root = config.oh_root / "interface" / "sdk_c"
        self.sdk_roots = (self.sdk_root, self.ndk_root)
        self._cache: dict[str, list[dict[str, object]]] = {}
        self._suffix_cache: dict[str, list[dict[str, object]]] = {}
        self._prepared_exact: set[str] = set()
        self._prepared_suffixes: set[str] = set()
        self._stats: dict[str, int | float] = {
            "duration_ms": 0.0,
            "scan_count": 0,
            "file_count": 0,
            "line_count": 0,
            "byte_count": 0,
            "exact_query_count": 0,
            "suffix_query_count": 0,
            "declaration_count": 0,
        }

    def prepare(self, api_names: Iterable[str], suffixes: Iterable[str] = ()) -> dict[str, int | float]:
        """Build a targeted process-level declaration index in one SDK pass."""

        exact = {name for name in api_names if name and name not in self._prepared_exact}
        suffix_values = {value for value in suffixes if value and value not in self._prepared_suffixes}
        if not exact and not suffix_values:
            return self.stats()
        started = time.perf_counter()
        for name in exact:
            self._cache[name] = []
        for suffix in suffix_values:
            self._suffix_cache[suffix] = []

        files = self._declaration_files()
        suffixes_by_last: dict[str, tuple[str, ...]] = {}
        for suffix in suffix_values:
            suffixes_by_last.setdefault(suffix[-1], tuple())
            suffixes_by_last[suffix[-1]] = (*suffixes_by_last[suffix[-1]], suffix)
        suffix_names: dict[str, set[str]] = {suffix: set() for suffix in suffix_values}
        line_count = 0
        byte_count = 0
        for path in files:
            raw = path.read_bytes()
            byte_count += len(raw)
            relative = path.resolve().relative_to(self.config.oh_root.resolve()).as_posix()
            for line_no, content in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
                line_count += 1
                identifiers = set(self.IDENTIFIER_RE.findall(content))
                for name in identifiers.intersection(exact):
                    matches = self._cache[name]
                    if len(matches) < self.MAX_DECLARATIONS_PER_API:
                        matches.append(self._match(relative, line_no, content))
                for identifier in identifiers:
                    for suffix in suffixes_by_last.get(identifier[-1], ()):
                        if identifier == suffix or not identifier.endswith(suffix):
                            continue
                        resolved = suffix_names[suffix]
                        if identifier in resolved or len(resolved) >= self.MAX_SUFFIX_CANDIDATES:
                            continue
                        resolved.add(identifier)
                        self._suffix_cache[suffix].append(
                            self._match(relative, line_no, content, resolved_api=identifier)
                        )

        self._prepared_exact.update(exact)
        self._prepared_suffixes.update(suffix_values)
        self._stats = {
            "duration_ms": round(float(self._stats["duration_ms"]) + (time.perf_counter() - started) * 1000, 3),
            "scan_count": int(self._stats["scan_count"]) + 1,
            "file_count": len(files),
            "line_count": line_count,
            "byte_count": byte_count,
            "exact_query_count": len(self._prepared_exact),
            "suffix_query_count": len(self._prepared_suffixes),
            "declaration_count": sum(len(values) for values in self._cache.values())
            + sum(len(values) for values in self._suffix_cache.values()),
        }
        return self.stats()

    def stats(self) -> dict[str, int | float]:
        return dict(self._stats)

    def locate(self, api_name: str, limit: int = 20) -> list[dict[str, object]]:
        if api_name in self._cache:
            return self._cache[api_name][:limit]
        search_specs = (
            (self.sdk_root, ("*.d.ts", "*.d.ets", "*.static.d.ets")),
            (self.ndk_root, ("*.h", "*.hpp")),
        )
        available_specs = [(root, globs) for root, globs in search_specs if root.is_dir()]
        if not available_specs:
            self._cache[api_name] = []
            return []
        output_lines: list[tuple[Path, str]] = []
        try:
            for root, globs in available_specs:
                command = ["rg", "-n", "-m", str(limit)]
                for glob in globs:
                    command.extend(["--glob", glob])
                command.extend(["--glob", "!zh-cn/**", "-F", api_name, "."])
                result = subprocess.run(
                    command,
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                output_lines.extend((root, line) for line in result.stdout.splitlines())
        except OSError:
            self._cache[api_name] = []
            return []
        identifier_boundary = r"[A-Za-z0-9_$]"
        word = re.compile(
            rf"(?<!{identifier_boundary}){re.escape(api_name)}(?!{identifier_boundary})"
        )
        matches: list[dict[str, object]] = []
        for root, line in output_lines:
            try:
                path_text, line_text, content = line.split(":", 2)
                line_no = int(line_text)
            except (ValueError, TypeError):
                continue
            if not word.search(content):
                continue
            path = root / path_text
            matches.append(
                {
                    "path": path.resolve().relative_to(self.config.oh_root.resolve()).as_posix(),
                    "line": line_no,
                    "declaration": content.strip(),
                }
            )
        self._cache[api_name] = matches[:limit]
        return self._cache[api_name]

    def locate_suffix(self, api_suffix: str, limit: int = 100) -> list[dict[str, object]]:
        if api_suffix in self._suffix_cache:
            return self._suffix_cache[api_suffix][:limit]
        search_specs = (
            (self.sdk_root, ("*.d.ts", "*.d.ets", "*.static.d.ets")),
            (self.ndk_root, ("*.h", "*.hpp")),
        )
        output_lines: list[tuple[Path, str]] = []
        try:
            for root, globs in search_specs:
                if not root.is_dir():
                    continue
                command = ["rg", "-n", "-m", str(limit)]
                for glob in globs:
                    command.extend(["--glob", glob])
                command.extend(["--glob", "!zh-cn/**", "-F", api_suffix, "."])
                result = subprocess.run(
                    command,
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                output_lines.extend((root, line) for line in result.stdout.splitlines())
        except OSError:
            self._suffix_cache[api_suffix] = []
            return []

        matches: list[dict[str, object]] = []
        for root, line in output_lines:
            try:
                path_text, line_text, content = line.split(":", 2)
                line_no = int(line_text)
            except (ValueError, TypeError):
                continue
            resolved_names = {
                identifier
                for identifier in self.IDENTIFIER_RE.findall(content)
                if identifier.endswith(api_suffix) and identifier != api_suffix
            }
            for resolved_name in resolved_names:
                path = root / path_text
                matches.append(
                    {
                        "path": path.resolve().relative_to(self.config.oh_root.resolve()).as_posix(),
                        "line": line_no,
                        "declaration": content.strip(),
                        "resolved_api": resolved_name,
                    }
                )
        unique_matches: list[dict[str, object]] = []
        seen_names: set[str] = set()
        for match in matches:
            resolved_name = str(match.get("resolved_api", ""))
            if not resolved_name or resolved_name in seen_names:
                continue
            seen_names.add(resolved_name)
            unique_matches.append(match)
            if len(unique_matches) >= limit:
                break
        self._suffix_cache[api_suffix] = unique_matches
        return unique_matches

    def _declaration_files(self) -> list[Path]:
        search_specs = (
            (self.sdk_root, (".static.d.ets", ".d.ets", ".d.ts")),
            (self.ndk_root, (".h", ".hpp")),
        )
        files: set[Path] = set()
        for root, suffixes in search_specs:
            if not root.is_dir():
                continue
            try:
                result = subprocess.run(
                    ["rg", "--files"],
                    cwd=root,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                candidates = (root / line for line in result.stdout.splitlines() if line.strip())
            except OSError:
                candidates = root.rglob("*")
            files.update(
                path.resolve()
                for path in candidates
                if path.is_file()
                and "zh-cn" not in path.relative_to(root).parts
                and path.name.endswith(suffixes)
            )
        return sorted(files, key=lambda path: path.as_posix())

    @staticmethod
    def _match(path: str, line: int, content: str, **extra: object) -> dict[str, object]:
        return {"path": path, "line": line, "declaration": content.strip(), **extra}
