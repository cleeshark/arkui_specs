"""Resolve and read repository source citations reproducibly."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from pathlib import Path

from spec_eval.config import EvaluationConfig
from spec_eval.evidence.repository_index import RepositoryFileIndex


class SourceReader:
    SDK_DECLARATION_SUFFIXES = (".static.d.ets", ".d.ets", ".d.ts")
    DEFAULT_CONTENT_CACHE_BYTES = 64 * 1024 * 1024
    MAX_SNIPPET_CHARS = 12_000

    def __init__(
        self,
        config: EvaluationConfig,
        file_index: RepositoryFileIndex | None = None,
        content_cache_bytes: int = DEFAULT_CONTENT_CACHE_BYTES,
    ) -> None:
        self.config = config
        self.file_index = file_index or RepositoryFileIndex(config)
        self._basename_cache: dict[str, tuple[Path | None, str]] = {}
        self._suffix_cache: dict[str, tuple[Path | None, str]] = {}
        self._content_cache: OrderedDict[Path, tuple[tuple[str, ...], str, int]] = OrderedDict()
        self._content_cache_bytes = 0
        self._content_cache_limit = max(content_cache_bytes, 0)
        self._cache_hits = 0
        self._cache_misses = 0
        self._snippet_truncations = 0

    def prepare(self) -> dict[str, int | float]:
        return self.file_index.prepare()

    def stats(self) -> dict[str, int | float]:
        return {
            **self.file_index.stats(),
            "content_cache_hits": self._cache_hits,
            "content_cache_misses": self._cache_misses,
            "content_cache_bytes": self._content_cache_bytes,
            "content_cache_limit_bytes": self._content_cache_limit,
            "snippet_truncation_count": self._snippet_truncations,
        }

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
        if not normalized.startswith(("frameworks/", "interfaces/", "adapter/", "test/", "specs/")):
            return self._resolve_suffix(normalized.replace("\\", "/"))
        return None, "missing"

    def _resolve_basename(self, name: str) -> tuple[Path | None, str]:
        if name in self._basename_cache:
            return self._basename_cache[name]
        matches = self.file_index.basename_matches(
            name,
            include_sdk=self.is_sdk_declaration_basename(name),
        )
        if len(matches) == 1:
            value = (matches[0], "resolved")
        elif len(matches) > 1:
            value = (None, "ambiguous")
        else:
            value = (None, "missing")
        self._basename_cache[name] = value
        return value

    def _resolve_suffix(self, suffix: str) -> tuple[Path | None, str]:
        if suffix in self._suffix_cache:
            return self._suffix_cache[suffix]
        matches = self.file_index.suffix_matches(suffix)
        if len(matches) == 1:
            value = (matches[0], "resolved")
        elif len(matches) > 1:
            value = (None, "ambiguous")
        else:
            value = (None, "missing")
        self._suffix_cache[suffix] = value
        return value

    @classmethod
    def is_sdk_declaration_basename(cls, name: str) -> bool:
        return name.lower().endswith(cls.SDK_DECLARATION_SUFFIXES)

    def read_ranges(
        self, path: Path, ranges: tuple[tuple[int, int], ...]
    ) -> tuple[str, str, tuple[tuple[int, int], ...]]:
        lines, digest = self._read_file(path)
        if not ranges:
            return "", digest, tuple()
        chunks: list[str] = []
        invalid: list[tuple[int, int]] = []
        for start, end in ranges:
            if start < 1 or end < start or end > len(lines):
                invalid.append((start, end))
                continue
            chunks.append("\n".join(f"{line_no}: {lines[line_no - 1]}" for line_no in range(start, end + 1)))
        content = "\n...\n".join(chunks)
        if len(content) > self.MAX_SNIPPET_CHARS:
            self._snippet_truncations += 1
            marker = "\n[truncated by spec_eval evidence budget]"
            content = content[: self.MAX_SNIPPET_CHARS - len(marker)] + marker
        return content, digest, tuple(invalid)

    def _read_file(self, path: Path) -> tuple[tuple[str, ...], str]:
        normalized = path.resolve()
        cached = self._content_cache.get(normalized)
        if cached is not None:
            self._cache_hits += 1
            self._content_cache.move_to_end(normalized)
            return cached[0], cached[1]
        self._cache_misses += 1
        raw = normalized.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        lines = tuple(raw.decode("utf-8", errors="replace").splitlines())
        size = len(raw)
        if self._content_cache_limit and size <= self._content_cache_limit:
            while self._content_cache and self._content_cache_bytes + size > self._content_cache_limit:
                _, (_, _, removed_size) = self._content_cache.popitem(last=False)
                self._content_cache_bytes -= removed_size
            self._content_cache[normalized] = (lines, digest, size)
            self._content_cache_bytes += size
        return lines, digest

    def is_disallowed(self, path: Path) -> bool:
        parts = set(path.parts)
        return "site" in parts or "generated" in parts
