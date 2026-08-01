"""Normalized Markdown document model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    line: int


@dataclass(frozen=True)
class TableRow:
    cells: tuple[str, ...]
    line: int

    def as_mapping(self, headers: tuple[str, ...]) -> dict[str, str]:
        return {header: self.cells[index] if index < len(self.cells) else "" for index, header in enumerate(headers)}


@dataclass(frozen=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[TableRow, ...]
    line: int
    section: str | None = None
    subsection: str | None = None

    def has_headers(self, *headers: str) -> bool:
        return all(header in self.headers for header in headers)


@dataclass(frozen=True)
class CodeBlock:
    language: str
    content: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Link:
    label: str
    target: str
    line: int


@dataclass(frozen=True)
class Checkbox:
    checked: bool
    text: str
    line: int


@dataclass
class DocumentModel:
    path: Path
    relative_path: str
    kind: str
    feat_id: str | None
    text: str
    lines: tuple[str, ...]
    headings: tuple[Heading, ...] = field(default_factory=tuple)
    tables: tuple[Table, ...] = field(default_factory=tuple)
    code_blocks: tuple[CodeBlock, ...] = field(default_factory=tuple)
    links: tuple[Link, ...] = field(default_factory=tuple)
    checkboxes: tuple[Checkbox, ...] = field(default_factory=tuple)
    ids: dict[str, tuple[tuple[str, int], ...]] = field(default_factory=dict)

    def h2_titles(self) -> list[str]:
        return [heading.title for heading in self.headings if heading.level == 2]

    def tables_in_section(self, section: str) -> list[Table]:
        return [table for table in self.tables if table.section == section]

    def metadata(self) -> dict[str, str]:
        for table in self.tables:
            if len(table.headers) != 2:
                continue
            mapping: dict[str, str] = {}
            for row in table.rows:
                if len(row.cells) >= 2:
                    mapping[row.cells[0].strip()] = row.cells[1].strip()
            if "特性编号" in mapping or "Design ID" in mapping:
                return mapping
        return {}

    def line_text(self, line: int) -> str:
        if line < 1 or line > len(self.lines):
            return ""
        return self.lines[line - 1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "kind": self.kind,
            "feat_id": self.feat_id,
            "headings": [asdict(item) for item in self.headings],
            "tables": [
                {
                    "headers": list(table.headers),
                    "rows": [asdict(row) for row in table.rows],
                    "line": table.line,
                    "section": table.section,
                    "subsection": table.subsection,
                }
                for table in self.tables
            ],
            "code_blocks": [asdict(item) for item in self.code_blocks],
            "links": [asdict(item) for item in self.links],
            "checkboxes": [asdict(item) for item in self.checkboxes],
            "ids": {key: [list(value) for value in values] for key, values in self.ids.items()},
        }

