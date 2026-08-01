"""Extract stable local identifiers from Markdown."""

from __future__ import annotations

import re


class IdParser:
    PATTERNS = {
        "feat": re.compile(r"\bFeat-\d{2}\b"),
        "us": re.compile(r"\bUS-\d+\b"),
        "ac": re.compile(r"\bAC-\d+(?:\.\d+)?\b"),
        "rule": re.compile(r"\bR-\d+\b"),
        "vm": re.compile(r"\bVM-\d+\b"),
        "task": re.compile(r"\bTASK-[A-Za-z0-9-]+\b"),
        "adr": re.compile(r"\bADR-(?:F\d+-)?\d+\b"),
    }
    ID_TOKEN = r"(?:AC-\d+(?:\.\d+)?|R-\d+|VM-\d+)"
    FULL_RANGE_PATTERN = re.compile(
        rf"\b(?P<start>{ID_TOKEN})\s*(?:-|~)\s*(?P<end>{ID_TOKEN})\b"
    )
    SHORTHAND_RANGE_PATTERN = re.compile(
        rf"\b(?P<start>{ID_TOKEN})\s*~\s*(?P<end>\d+(?:\.\d+)?)\b"
    )
    MAX_RANGE_MEMBERS = 1000

    def extract_line(self, text: str) -> dict[str, tuple[str, ...]]:
        return {name: tuple(match.group(0) for match in pattern.finditer(text)) for name, pattern in self.PATTERNS.items()}

    def find_ranges(self, text: str) -> tuple[str, ...]:
        matches = list(self.FULL_RANGE_PATTERN.finditer(text)) + list(self.SHORTHAND_RANGE_PATTERN.finditer(text))
        return tuple(match.group(0) for match in sorted(matches, key=lambda item: item.start()))

    def expand_range(self, value: str) -> tuple[str, ...]:
        match = self.FULL_RANGE_PATTERN.fullmatch(value.strip())
        if match is not None:
            start = match.group("start")
            end = match.group("end")
        else:
            match = self.SHORTHAND_RANGE_PATTERN.fullmatch(value.strip())
            if match is None:
                return tuple()
            start = match.group("start")
            end = match.group("end")
        start_kind, start_parts = self._split_id(start)
        if "-" in end:
            end_kind, end_parts = self._split_id(end)
        else:
            end_kind = start_kind
            end_parts = tuple(int(part) for part in end.split("."))
            if start_kind == "AC" and len(start_parts) == 2 and len(end_parts) == 1:
                end_parts = (start_parts[0], end_parts[0])
        if start_kind != end_kind or len(start_parts) != len(end_parts):
            return tuple()
        if len(start_parts) == 2 and start_parts[0] != end_parts[0]:
            return tuple()
        start_index = start_parts[-1]
        end_index = end_parts[-1]
        if end_index < start_index or end_index - start_index + 1 > self.MAX_RANGE_MEMBERS:
            return tuple()
        prefix = start_parts[:-1]
        return tuple(self._format_id(start_kind, prefix + (index,)) for index in range(start_index, end_index + 1))

    @staticmethod
    def _split_id(value: str) -> tuple[str, tuple[int, ...]]:
        kind, number = value.split("-", 1)
        return kind, tuple(int(part) for part in number.split("."))

    @staticmethod
    def _format_id(kind: str, parts: tuple[int, ...]) -> str:
        return f"{kind}-" + ".".join(str(part) for part in parts)
