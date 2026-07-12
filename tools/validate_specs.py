#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Validate ArkUI feature specs.

This is the specs-repository counterpart of the spec checks that live in
``docs/validate_context.py`` (in the ace_engine repo). It runs standalone
inside the specs repo and re-implements the same rules so that a Feat spec
passes or fails identically no matter which tool checks it:

  * ``index.md`` checks
      - every registered Spec link ``](path.md)`` resolves to an existing file;
      - every ``| Feat-`` row has at least four columns and a valid status
        (``Draft`` / ``Baselined`` / ``Deprecated``); ``待补充`` rows are
        reported as warnings, matching the migration-period policy.

  * ``Feat-NN-*-spec.md`` content checks (for every spec on disk)
      - has a status row ``| 状态 | <status> |`` (or a ``status:`` header) with
        a value that normalizes to an allowed status;
      - has a ``## context-references`` section;
      - contains at least one ``AC-<n>`` acceptance-criterion marker;
      - contains at least one ``VM-<n>`` verification-mapping marker;
      - if ``Baselined``, contains no ``TODO`` / ``TBD`` / ``待定`` placeholder
        text (self-audit lines that merely describe the absence of placeholders
        are recognized and skipped).
      - in the ``## 本次变更范围（Delta）`` section, every table must use the
        exact header ``| 类型 | 内容 | 说明 |`` and each ``类型`` cell must be
        ``ADDED`` / ``MODIFIED`` / ``REMOVED``.
      - the overview metadata table must contain the required fields
        ``特性名称`` / ``特性编号`` / ``优先级`` / ``目标版本`` / ``复杂度``
        (plus ``状态``, validated above); ``特性编号`` must match
        ``Func-NN-NN-NN-Feat-NN`` and ``优先级`` must be ``P0``–``P3``.

The generated ``site/`` tree and ``.git`` are excluded from the scan, since
``site/docs`` holds generated copies of the same spec files.

Usage:
  python3 tools/validate_specs.py
  python3 tools/validate_specs.py --quiet
  python3 tools/validate_specs.py --warnings-as-errors
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "index.md"

ALLOWED_SPEC_STATUS = {"Draft", "Baselined", "Deprecated"}
PLACEHOLDER_STATUS = {"待补充", "*待补充*"}
ALLOWED_DELTA_TYPES = {"ADDED", "MODIFIED", "REMOVED"}
EXPECTED_DELTA_HEADER = ["类型", "内容", "说明"]

# Required 概述 metadata fields. 状态 is intentionally excluded here: it is
# already validated (Draft/Baselined/Deprecated) by extract_status below.
REQUIRED_METADATA_FIELDS = ("特性名称", "特性编号", "优先级", "目标版本", "复杂度")
FEATURE_ID_RE = re.compile(r"Func-\d{2}-\d{2}-\d{2}-Feat-\d{2}")
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3"}

# Directories whose Feat-*.md files are generated/copied, not source specs.
SKIP_DIR_PARTS = {".git", "site"}


def split_table_row(row: str) -> list[str]:
    """Split a markdown table row into its trimmed cell contents."""
    return row.strip().strip("|").split("|")


def is_table_separator(row: str) -> bool:
    """True when a row is a markdown table separator (e.g. ``|---|:--|---|``)."""
    cells = split_table_row(row)
    if not any(cells):
        return False
    return all(re.fullmatch(r":?-{1,}:?", cell.strip()) for cell in cells if cell.strip())


def iter_tables(text: str):
    """Yield ``(header_row, [data_rows])`` for each contiguous markdown table.

    A table is a run of ``|``-prefixed lines whose second line is a separator.
    """
    lines = text.splitlines()
    index = 0
    total = len(lines)
    while index < total:
        if lines[index].lstrip().startswith("|"):
            block: list[str] = []
            while index < total and lines[index].lstrip().startswith("|"):
                block.append(lines[index])
                index += 1
            if len(block) >= 2 and is_table_separator(block[1]):
                yield block[0], block[2:]
        else:
            index += 1


@dataclass
class Finding:
    level: str
    path: str
    message: str


class SpecValidator:
    def __init__(self, root: Path = ROOT, quiet: bool = False) -> None:
        self.root = root
        self.index_file = root / "index.md"
        self.quiet = quiet
        self.findings: list[Finding] = []

    def error(self, path: str | Path, message: str) -> None:
        self.findings.append(Finding("ERROR", str(path), message))

    def warn(self, path: str | Path, message: str) -> None:
        self.findings.append(Finding("WARN", str(path), message))

    # ------------------------------------------------------------------ driver

    def validate(self) -> tuple[int, int]:
        self.validate_index()
        self.validate_feat_specs()
        return self.print_summary()

    # -------------------------------------------------------------- index.md

    def validate_index(self) -> None:
        if not self.index_file.is_file():
            self.error(self.index_file.relative_to(self.root), "index.md does not exist")
            return
        text = self.index_file.read_text(encoding="utf-8")
        rel_index = self.index_file.relative_to(self.root)

        for link_target in sorted(set(re.findall(r"\]\(([^)]+\.md)\)", text))):
            if not (self.root / link_target).exists():
                self.error(rel_index, f"registered Spec link does not exist: {link_target}")

        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.startswith("| Feat-"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 4:
                self.error(f"{rel_index}:{line_no}", "Feat row must have at least 4 columns")
                continue
            status = cells[3]
            spec_cell = cells[2]
            if status in PLACEHOLDER_STATUS or "待补充" in spec_cell:
                self.warn(f"{rel_index}:{line_no}", "Feat row is still a placeholder")
                continue
            if status not in ALLOWED_SPEC_STATUS:
                self.error(f"{rel_index}:{line_no}", f"invalid Spec status `{status}`")

    # ----------------------------------------------------------- Feat-*.md

    def feat_spec_paths(self) -> list[Path]:
        paths: list[Path] = []
        for spec_path in self.root.rglob("Feat-*-spec.md"):
            if SKIP_DIR_PARTS & set(spec_path.parts):
                continue
            paths.append(spec_path)
        return sorted(paths)

    def validate_feat_specs(self) -> None:
        for spec_path in self.feat_spec_paths():
            rel_path = spec_path.relative_to(self.root)
            text = spec_path.read_text(encoding="utf-8")

            status, raw_status = self.extract_status(text)
            if not status:
                self.error(rel_path, "missing status row, expected `| 状态 | <status> |`")
            elif status not in ALLOWED_SPEC_STATUS:
                self.error(rel_path, f"invalid status `{raw_status}`")
            elif raw_status and raw_status != status:
                self.warn(rel_path, f"status `{raw_status}` contains annotation; normalized to `{status}`")

            if "## context-references" not in text:
                self.error(rel_path, "missing `## context-references` section")
            if not re.search(r"\bAC-\d+", text):
                self.error(rel_path, "missing AC entries")
            if not re.search(r"\bVM-\d+", text):
                self.error(rel_path, "missing VM entries")

            if status == "Baselined":
                self.validate_no_baselined_placeholders(rel_path, text)

            self.validate_delta_table(rel_path, text)
            self.validate_overview_metadata(rel_path, text)

    def validate_delta_table(self, rel_path: Path, text: str) -> None:
        # Validate the "本次变更范围（Delta）" section: any table it contains
        # must use the strict header `| 类型 | 内容 | 说明 |`, and every 类型
        # cell must be ADDED / MODIFIED / REMOVED.
        section_match = re.search(
            r"^##\s+本次变更范围[^\n]*\n(.*?)(?=\n##\s|\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not section_match:
            return
        section = section_match.group(1)
        for header_row, data_rows in iter_tables(section):
            header_cells = [cell.strip() for cell in split_table_row(header_row)]
            if header_cells != EXPECTED_DELTA_HEADER:
                self.error(
                    rel_path,
                    "Delta table must use the header `| 类型 | 内容 | 说明 |`; got `| "
                    + " | ".join(header_cells) + " |`",
                )
                continue
            for row in data_rows:
                if is_table_separator(row):
                    continue
                cells = [cell.strip() for cell in split_table_row(row)]
                if not cells:
                    continue
                value = cells[0]
                if value not in ALLOWED_DELTA_TYPES:
                    self.error(
                        rel_path,
                        f"Delta 类型 must be one of {sorted(ALLOWED_DELTA_TYPES)}; got `{value}`",
                    )

    def metadata_fields(self, text: str) -> dict[str, str]:
        """Collect known metadata fields from any 2-column 属性|值 table.

        状态 is intentionally excluded; it is validated by ``extract_status``.
        """
        result: dict[str, str] = {}
        for header_row, data_rows in iter_tables(text):
            if len(split_table_row(header_row)) != 2:
                continue
            for row in data_rows:
                if is_table_separator(row):
                    continue
                cells = [cell.strip() for cell in split_table_row(row)]
                if len(cells) < 2:
                    continue
                key, value = cells[0], cells[1]
                if key in REQUIRED_METADATA_FIELDS and key not in result:
                    result[key] = value
        return result

    def validate_overview_metadata(self, rel_path: Path, text: str) -> None:
        meta = self.metadata_fields(text)
        if not meta:
            self.error(
                rel_path,
                "missing 属性|值 metadata table with 特性名称/特性编号/优先级/目标版本/复杂度",
            )
            return
        for field in REQUIRED_METADATA_FIELDS:
            if field not in meta or not meta[field].strip():
                self.error(rel_path, f"metadata: missing required field `{field}`")
        feature_id = meta.get("特性编号", "").strip()
        if feature_id and not FEATURE_ID_RE.fullmatch(feature_id):
            self.error(
                rel_path,
                f"特性编号 must match `Func-NN-NN-NN-Feat-NN`; got `{feature_id}`",
            )
        priority = meta.get("优先级", "").strip()
        if priority and priority not in ALLOWED_PRIORITIES:
            self.error(
                rel_path,
                f"优先级 must be one of {sorted(ALLOWED_PRIORITIES)}; got `{priority}`",
            )

    def extract_status(self, text: str) -> tuple[str | None, str | None]:
        match = re.search(r"^\|\s*状态\s*\|\s*([^|]+?)\s*\|", text, flags=re.MULTILINE)
        if match:
            raw_status = match.group(1).strip()
            return self.normalize_status(raw_status), raw_status
        match = re.search(r"^\s*status\s*:\s*([A-Za-z]+)\s*$", text, flags=re.MULTILINE)
        if match:
            raw_status = match.group(1).strip()
            return self.normalize_status(raw_status), raw_status
        return None, None

    def normalize_status(self, raw_status: str) -> str | None:
        for status in ALLOWED_SPEC_STATUS:
            if raw_status == status or raw_status.startswith(status):
                return status
        return raw_status

    def validate_no_baselined_placeholders(self, rel_path: Path, text: str) -> None:
        for line_no, line in enumerate(text.splitlines(), 1):
            if not re.search(r"TODO|TBD|待定", line):
                continue
            # Self-audit lines document the *absence* of placeholders and are not
            # placeholders themselves. Skip Chinese ("无...占位符" /
            # "不允许存在") and English ("placeholder") audit phrasing.
            if "无" in line and "占位符" in line:
                continue
            if "不允许存在" in line:
                continue
            if re.search(r"placeholder", line, flags=re.IGNORECASE):
                continue
            self.error(f"{rel_path}:{line_no}", "Baselined spec contains placeholder text")

    # --------------------------------------------------------------- summary

    def print_summary(self) -> tuple[int, int]:
        errors = sum(1 for finding in self.findings if finding.level == "ERROR")
        warnings = sum(1 for finding in self.findings if finding.level == "WARN")
        if not self.quiet:
            for finding in self.findings:
                print(f"{finding.level}: {finding.path}: {finding.message}")
        print(f"validate_specs: {errors} error(s), {warnings} warning(s)")
        return errors, warnings


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ArkUI feature specs")
    parser.add_argument("--quiet", action="store_true", help="Only print the final summary")
    parser.add_argument("--warnings-as-errors", action="store_true", help="Return non-zero when warnings exist")
    args = parser.parse_args(argv)

    validator = SpecValidator(quiet=args.quiet)
    errors, warnings = validator.validate()
    if errors or (args.warnings_as_errors and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
