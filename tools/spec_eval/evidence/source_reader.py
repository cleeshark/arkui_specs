"""Resolve and read repository source citations reproducibly."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from spec_eval.config import EvaluationConfig


class SourceReader:
    SDK_DECLARATION_SUFFIXES = (".static.d.ets", ".d.ets", ".d.ts")

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self._basename_cache: dict[str, tuple[Path | None, str]] = {}

    def resolve(self, raw_path: str, document_directory: Path) -> tuple[Path | None, str]:
        normalized = raw_path.strip().strip("`'")
        candidate = Path(normalized)
        if candidate.is_absolute() or (len(normalized) > 2 and normalized[1:3] == ":\\"):
            return None, "absolute"

        direct_candidates: list[Path] = []
        if normalized.startswith(("frameworks/", "interfaces/", "adapter/", "test/", "specs/")):
            direct_candidates.append(self.config.repo_root / normalized)
        elif normalized.startswith("interface/sdk-js/"):
            direct_candidates.append(self.config.oh_root / normalized)
        elif normalized.startswith("interface_sdk-js/"):
            suffix = normalized[len("interface_sdk-js/") :]
            direct_candidates.append(self.config.oh_root / "interface" / "sdk-js" / suffix)
        elif normalized.startswith("api/") and self.is_sdk_declaration_basename(Path(normalized).name):
            direct_candidates.append(self.config.oh_root / "interface" / "sdk-js" / normalized)
        else:
            direct_candidates.extend((document_directory / normalized, self.config.repo_root / normalized))
        for path in direct_candidates:
            if path.is_file():
                return path.resolve(), "resolved"
            if path.is_dir():
                return path.resolve(), "directory"

        if "/" not in normalized and "\\" not in normalized:
            return self._resolve_basename(normalized)
        return None, "missing"

    def _resolve_basename(self, name: str) -> tuple[Path | None, str]:
        if name in self._basename_cache:
            return self._basename_cache[name]
        search_roots = [self.config.repo_root]
        sdk_root = self.config.oh_root / "interface" / "sdk-js"
        if self.is_sdk_declaration_basename(name) and sdk_root.is_dir():
            search_roots.append(sdk_root)
        matches: set[Path] = set()
        try:
            for search_root in search_roots:
                command = ["rg", "--files", "-g", name]
                if search_root == sdk_root:
                    command.extend(["-g", "!zh-cn/**"])
                result = subprocess.run(
                    command,
                    cwd=search_root,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                matches.update(
                    path.resolve()
                    for line in result.stdout.splitlines()
                    if line.strip()
                    for path in (search_root / line,)
                    if path.is_file()
                )
        except OSError:
            self._basename_cache[name] = (None, "missing")
            return self._basename_cache[name]
        if len(matches) == 1:
            value = (next(iter(matches)), "resolved")
        elif len(matches) > 1:
            value = (None, "ambiguous")
        else:
            value = (None, "missing")
        self._basename_cache[name] = value
        return value

    @classmethod
    def is_sdk_declaration_basename(cls, name: str) -> bool:
        return name.lower().endswith(cls.SDK_DECLARATION_SUFFIXES)

    def read_ranges(
        self, path: Path, ranges: tuple[tuple[int, int], ...]
    ) -> tuple[str, str, tuple[tuple[int, int], ...]]:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        lines = raw.decode("utf-8", errors="replace").splitlines()
        if not ranges:
            return "", digest, tuple()
        chunks: list[str] = []
        invalid: list[tuple[int, int]] = []
        for start, end in ranges:
            if start < 1 or end < start or end > len(lines):
                invalid.append((start, end))
                continue
            chunks.append("\n".join(f"{line_no}: {lines[line_no - 1]}" for line_no in range(start, end + 1)))
        return "\n...\n".join(chunks), digest, tuple(invalid)

    def is_disallowed(self, path: Path) -> bool:
        parts = set(path.parts)
        return "site" in parts or "generated" in parts
