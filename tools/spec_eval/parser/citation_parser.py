"""Parse repository and SDK source citations from text."""

from __future__ import annotations

import re

from spec_eval.models.evidence import Citation


class CitationParser:
    # Do not restart matching inside relative paths, root placeholders, shell variables, URLs, or GN // labels.
    PATH_LEFT_BOUNDARY = r"(?<![\w@.<>/\\\-})])"
    NON_EXACT_PATH_MARKERS = frozenset("*{}<>")
    COMBINED_EXTENSION_RE = re.compile(
        r"^(?P<stem>.+)\.(?P<first>h|hpp|c|cc|cpp)/\.?(?P<second>h|hpp|c|cc|cpp)$",
        re.IGNORECASE,
    )
    PATH_PATTERN = re.compile(
        PATH_LEFT_BOUNDARY
        + r"(?P<path>(?:[A-Za-z]:\\(?:[^\s`|，。、；：）):<>\[\]\"']+\\)+[^\s`|，。、；：）):<>\[\]\"']+\.[A-Za-z0-9.]+|"
        r"/(?!/)(?:[^\s`|，。、；：）):/<>\[\]\"']+/)*[^\s`|，。、；：）):/<>\[\]\"']+\.[A-Za-z0-9.]+|"
        r"(?:frameworks|interfaces|adapter|test|interface(?:_sdk-js|/sdk-js)|specs)/"
        r"[^\s`|，。、；：）):<>\[\]\"']+))"
        r"(?::(?P<ranges>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*))?"
    )
    SHORT_SOURCE_PATTERN = re.compile(
        PATH_LEFT_BOUNDARY
        + r"(?P<path>[A-Za-z0-9_@./-]+\.(?:h|hpp|c|cc|cpp|ts|ets|d\.ts|d\.ets))"
        r"(?::(?P<ranges>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*))"
    )

    def parse(self, text: str, line: int | None = None) -> list[Citation]:
        citations: list[Citation] = []
        seen: set[tuple[str, str]] = set()
        for pattern in (self.PATH_PATTERN, self.SHORT_SOURCE_PATTERN):
            for match in pattern.finditer(text):
                path = match.group("path").rstrip(".,;；：:")
                ranges_text = match.group("ranges") or ""
                if text[match.end() :].lower().startswith("<br"):
                    continue
                expanded_paths = self._expand_combined_extensions(path)
                for expanded_path in expanded_paths:
                    if not self._is_exact_reference(expanded_path):
                        continue
                    if self._looks_like_file(expanded_path) and not ranges_text and not self._is_complete_code_span(
                        text, match.start(), match.end()
                    ):
                        continue
                    key = (expanded_path, ranges_text)
                    if key in seen:
                        continue
                    seen.add(key)
                    raw = match.group(0) if len(expanded_paths) == 1 else expanded_path
                    if ranges_text and len(expanded_paths) > 1:
                        raw = f"{raw}:{ranges_text}"
                    citations.append(
                        Citation(
                            raw=raw,
                            path=expanded_path,
                            line_ranges=self._parse_ranges(ranges_text),
                            line=line,
                        )
                    )
        return citations

    @classmethod
    def _expand_combined_extensions(cls, path: str) -> tuple[str, ...]:
        match = cls.COMBINED_EXTENSION_RE.match(path)
        if match is None:
            return (path,)
        stem = match.group("stem")
        return (f"{stem}.{match.group('first')}", f"{stem}.{match.group('second')}")

    @classmethod
    def _is_exact_reference(cls, path: str) -> bool:
        if any(marker in path for marker in cls.NON_EXACT_PATH_MARKERS):
            return False
        normalized = path.replace("\\", "/").rstrip("/")
        basename = normalized.rsplit("/", 1)[-1]
        if not basename or basename in (".", ".."):
            return False
        return cls._looks_like_file(normalized) or "/" in normalized

    @staticmethod
    def _looks_like_file(path: str) -> bool:
        normalized = path.replace("\\", "/").rstrip("/")
        basename = normalized.rsplit("/", 1)[-1]
        return bool(basename and "." in basename and not basename.endswith("."))

    @staticmethod
    def _is_complete_code_span(text: str, start: int, end: int) -> bool:
        return start > 0 and end < len(text) and text[start - 1] == "`" and text[end] == "`"

    @staticmethod
    def _parse_ranges(value: str) -> tuple[tuple[int, int], ...]:
        if not value:
            return tuple()
        result: list[tuple[int, int]] = []
        for part in value.split(","):
            if "-" in part:
                start_text, end_text = part.split("-", 1)
                result.append((int(start_text), int(end_text)))
            else:
                line = int(part)
                result.append((line, line))
        return tuple(result)
