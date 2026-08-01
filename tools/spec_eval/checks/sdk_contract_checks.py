"""Locate canonical SDK declarations for externally exposed APIs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from spec_eval.checks.base import make_finding
from spec_eval.config import EvaluationConfig
from spec_eval.evidence.sdk_reader import SdkReader
from spec_eval.models import DocumentModel, Finding, FunctionContext, Severity


@dataclass
class SdkContractResult:
    findings: list[Finding]
    declarations: dict[str, list[dict[str, object]]]


class SdkContractChecker:
    IDENTIFIER_RE = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
    CODE_RE = re.compile(r"`([^`]+)`")
    MODULE_REFERENCE_RE = re.compile(r"@ohos(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+")
    NON_CONCRETE_MARKERS = ("已有实现补录", "模块暴露", "具体签名见")
    STOP_WORDS = {
        "Public", "System", "InnerApi", "API", "N", "A", "void", "number", "string", "boolean",
        "undefined", "null", "true", "false", "get", "set", "static", "const", "interface", "class",
    }

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.reader = SdkReader(config)

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> SdkContractResult:
        findings: list[Finding] = []
        declarations: dict[str, list[dict[str, object]]] = {}
        api_rows = self._api_rows(documents)
        if api_rows and not any(root.is_dir() for root in self.reader.sdk_roots):
            path = documents[0].path if documents else context.function_path
            findings.append(
                make_finding(
                    self.config,
                    context,
                    "SDK-ROOT-MISSING-001",
                    Severity.MAJOR,
                    "canonical SDK API root is unavailable",
                    path,
                    1,
                    sdk_roots=[root.as_posix() for root in self.reader.sdk_roots],
                )
            )
            return SdkContractResult(findings, declarations)

        for document, line, feat_id, raw_api in api_rows:
            modules = self._non_concrete_modules(raw_api)
            if modules:
                key = f"{feat_id or 'design'}/API-{line}-NON-CONCRETE"
                declarations[key] = []
                module_text = ", ".join(f"`{module}`" for module in modules)
                findings.append(
                    make_finding(
                        self.config,
                        context,
                        "SDK-API-NOT-FOUND-001",
                        Severity.MAJOR,
                        "API table entry does not list concrete API names/signatures; "
                        f"enumerate each Public/System API explicitly instead of only referencing module {module_text}",
                        document.path,
                        line,
                        feat_id=feat_id,
                        raw_api=raw_api,
                        modules=list(modules),
                        non_concrete_api_entry=True,
                        required_content="concrete Public/System API names or signatures",
                    )
                )
                continue
            for name in self._api_names(raw_api):
                key = f"{feat_id or 'design'}/API-{line}-{name}"
                matches = self.reader.locate(name)
                declarations[key] = matches
                if not matches:
                    findings.append(
                        make_finding(
                            self.config,
                            context,
                            "SDK-API-NOT-FOUND-001",
                            Severity.MAJOR,
                            f"canonical SDK declaration not found for `{name}`",
                            document.path,
                            line,
                            feat_id=feat_id,
                            api=name,
                        )
                    )
        return SdkContractResult(findings, declarations)

    def _api_rows(self, documents: list[DocumentModel]) -> list[tuple[DocumentModel, int, str | None, str]]:
        result: list[tuple[DocumentModel, int, str | None, str]] = []
        for document in documents:
            for table in document.tables:
                api_column = "API 名称" if "API 名称" in table.headers else "API 签名" if "API 签名" in table.headers else None
                if api_column is None:
                    continue
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    exposure = mapping.get("开放范围") or mapping.get("类型") or ""
                    if not exposure or not any(value in exposure for value in ("Public", "System")):
                        continue
                    raw = mapping.get(api_column, "").strip()
                    if raw and raw.upper() != "N/A":
                        result.append((document, row.line, document.feat_id, raw))
        return result

    def _non_concrete_modules(self, raw: str) -> tuple[str, ...]:
        modules = tuple(dict.fromkeys(self.MODULE_REFERENCE_RE.findall(raw)))
        if not modules:
            return tuple()
        normalized = raw.strip().strip("`")
        module_only = any(normalized == module for module in modules)
        has_placeholder_marker = any(marker in raw for marker in self.NON_CONCRETE_MARKERS)
        return modules if module_only or has_placeholder_marker else tuple()

    def _api_names(self, raw: str) -> tuple[str, ...]:
        chunks = self.CODE_RE.findall(raw) or [raw]
        names: list[str] = []
        for chunk in chunks:
            candidates = self.IDENTIFIER_RE.findall(chunk)
            for candidate in candidates:
                if candidate in self.STOP_WORDS or candidate.startswith("API"):
                    continue
                if candidate not in names:
                    names.append(candidate)
                if "(" in chunk and names:
                    break
        return tuple(names)
