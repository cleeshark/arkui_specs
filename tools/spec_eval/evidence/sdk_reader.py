"""Canonical SDK declaration locator."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from spec_eval.config import EvaluationConfig


class SdkReader:
    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.sdk_root = config.oh_root / "interface" / "sdk-js" / "api"
        self.ndk_root = config.oh_root / "interface" / "sdk_c"
        self.sdk_roots = (self.sdk_root, self.ndk_root)
        self._cache: dict[str, list[dict[str, object]]] = {}

    def locate(self, api_name: str, limit: int = 20) -> list[dict[str, object]]:
        if api_name in self._cache:
            return self._cache[api_name]
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
        self._cache[api_name] = matches
        return matches
