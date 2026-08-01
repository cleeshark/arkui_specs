"""Parse spec and design Markdown into a normalized line-aware model."""

from __future__ import annotations

import re
from pathlib import Path

from spec_eval.config import EvaluationConfig
from spec_eval.errors import ParseError
from spec_eval.models.document import Checkbox, CodeBlock, DocumentModel, Heading, Link, Table, TableRow
from spec_eval.parser.id_parser import IdParser
from spec_eval.parser.table_parser import is_separator, split_table_row


class MarkdownParser:
    HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
    LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    CHECKBOX_RE = re.compile(r"^\s*-\s*\[([ xX])\]\s*(.+)$")
    FENCE_RE = re.compile(r"^\s*(```+|~~~+)\s*([^\s]*)?.*$")
    FEAT_FROM_NAME_RE = re.compile(r"^(Feat-\d{2})-")

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.id_parser = IdParser()

    def parse(self, path: Path) -> DocumentModel:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            raise ParseError(f"cannot read Markdown {path}: {error}") from error
        lines = tuple(text.splitlines())
        headings: list[Heading] = []
        tables: list[Table] = []
        code_blocks: list[CodeBlock] = []
        links: list[Link] = []
        checkboxes: list[Checkbox] = []
        ids: dict[str, list[tuple[str, int]]] = {key: [] for key in self.id_parser.PATTERNS}

        section: str | None = None
        subsection: str | None = None
        fence_token: str | None = None
        fence_language = ""
        fence_start = 0
        fence_content: list[str] = []
        index = 0
        while index < len(lines):
            line = lines[index]
            line_no = index + 1
            fence_match = self.FENCE_RE.match(line)
            if fence_token is not None:
                if fence_match and fence_match.group(1).startswith(fence_token[0]):
                    code_blocks.append(
                        CodeBlock(fence_language, "\n".join(fence_content), fence_start, line_no)
                    )
                    fence_token = None
                    fence_language = ""
                    fence_content = []
                else:
                    fence_content.append(line)
                index += 1
                continue
            if fence_match:
                fence_token = fence_match.group(1)
                fence_language = fence_match.group(2) or ""
                fence_start = line_no
                index += 1
                continue

            heading_match = self.HEADING_RE.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                headings.append(Heading(level, title, line_no))
                if level == 2:
                    section = title
                    subsection = None
                elif level == 3:
                    subsection = title

            if line.lstrip().startswith("|"):
                block: list[tuple[int, str]] = []
                cursor = index
                while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
                    block.append((cursor + 1, lines[cursor]))
                    cursor += 1
                if len(block) >= 2 and is_separator(block[1][1]):
                    for row_line, row_text in block:
                        for link_match in self.LINK_RE.finditer(row_text):
                            links.append(Link(link_match.group(1), link_match.group(2), row_line))
                        for name, values in self.id_parser.extract_line(row_text).items():
                            ids[name].extend((value, row_line) for value in values)
                    headers = split_table_row(block[0][1])
                    rows = tuple(TableRow(split_table_row(value), row_line) for row_line, value in block[2:])
                    tables.append(Table(headers, rows, block[0][0], section, subsection))
                    index = cursor
                    continue

            for link_match in self.LINK_RE.finditer(line):
                links.append(Link(link_match.group(1), link_match.group(2), line_no))
            checkbox_match = self.CHECKBOX_RE.match(line)
            if checkbox_match:
                checkboxes.append(Checkbox(checkbox_match.group(1).lower() == "x", checkbox_match.group(2), line_no))
            for name, values in self.id_parser.extract_line(line).items():
                ids[name].extend((value, line_no) for value in values)
            index += 1

        if fence_token is not None:
            code_blocks.append(CodeBlock(fence_language, "\n".join(fence_content), fence_start, len(lines)))

        kind = "design" if path.name == "design.md" else "spec" if path.name.startswith("Feat-") else "markdown"
        feat_match = self.FEAT_FROM_NAME_RE.match(path.name)
        feat_id = feat_match.group(1) if feat_match else None
        return DocumentModel(
            path=path.resolve(),
            relative_path=self.config.repo_relative(path),
            kind=kind,
            feat_id=feat_id,
            text=text,
            lines=lines,
            headings=tuple(headings),
            tables=tuple(tables),
            code_blocks=tuple(code_blocks),
            links=tuple(links),
            checkboxes=tuple(checkboxes),
            ids={key: tuple(value) for key, value in ids.items()},
        )
