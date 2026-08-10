"""Extract Function-scoped claims from normalized documents."""

from __future__ import annotations

from spec_eval.models.evidence import Claim
from spec_eval.models.document import DocumentModel


class ClaimBuilder:
    def build(self, documents: list[DocumentModel]) -> list[Claim]:
        claims: list[Claim] = []
        for document in documents:
            if document.kind == "spec" and document.feat_id:
                claims.extend(self._spec_claims(document))
            elif document.kind == "design":
                claims.extend(self._design_claims(document))
        return claims

    def _spec_claims(self, document: DocumentModel) -> list[Claim]:
        claims: list[Claim] = []
        feat = document.feat_id or "Feat-00"
        for table in document.tables:
            if "AC编号" in table.headers and "验收标准" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    local = mapping.get("AC编号", "").strip()
                    if local:
                        claims.append(self._claim(document, f"{feat}/{local}", "acceptance_criterion", mapping.get("验收标准", ""), row.line))
            elif "规则ID" in table.headers and "预期行为" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    local = mapping.get("规则ID", "").strip()
                    text = "；".join(
                        value for value in (
                            mapping.get("触发条件", ""), mapping.get("预期行为", ""), mapping.get("边界/约束", "")
                        ) if value
                    )
                    if local:
                        claims.append(self._claim(document, f"{feat}/{local}", "rule", text, row.line))
            elif "API 名称" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    raw = mapping.get("API 名称", "").strip()
                    if raw:
                        claims.append(self._claim(document, f"{feat}/API-{row.line}", "api", raw, row.line))
            elif "类型" in table.headers and "指标/阈值" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    claims.append(
                        self._claim(
                            document,
                            f"{feat}/NFR-{row.line}",
                            "nfr",
                            f"{mapping.get('类型', '')}: {mapping.get('指标/阈值', '')}",
                            row.line,
                        )
                    )
        claims.extend(self._section_bullets(document, "兼容性声明", feat, "compatibility"))
        return claims

    def _design_claims(self, document: DocumentModel) -> list[Claim]:
        claims: list[Claim] = []
        for table in document.tables:
            if "决策 ID" in table.headers and "推荐方案" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    local = mapping.get("决策 ID", "").strip()
                    if local:
                        claims.append(
                            self._claim(document, f"design/{local}", "adr", mapping.get("推荐方案", ""), row.line)
                        )
            elif "层" in table.headers and "模块" in table.headers and "职责" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    claims.append(
                        self._claim(
                            document,
                            f"design/CALLCHAIN-{row.line}",
                            "call_chain",
                            f"{mapping.get('层', '')}: {mapping.get('模块', '')} - {mapping.get('职责', '')}",
                            row.line,
                        )
                    )
            elif "项" in table.headers and "类型" in table.headers and "影响" in table.headers:
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    claims.append(
                        self._claim(
                            document,
                            f"design/RISK-{row.line}",
                            "risk",
                            f"{mapping.get('项', '')}: {mapping.get('处理方式', '')}",
                            row.line,
                        )
                    )
        return claims

    def _section_bullets(self, document: DocumentModel, section: str, prefix: str, claim_type: str) -> list[Claim]:
        heading = next((item for item in document.headings if item.level == 2 and item.title == section), None)
        if heading is None:
            return []
        end = next((item.line for item in document.headings if item.level == 2 and item.line > heading.line), len(document.lines) + 1)
        claims: list[Claim] = []
        for line_no in range(heading.line + 1, end):
            text = document.line_text(line_no).strip()
            if text.startswith("- "):
                claims.append(self._claim(document, f"{prefix}/{claim_type.upper()}-{line_no}", claim_type, text[2:].strip(), line_no))
        return claims

    @staticmethod
    def _claim(document: DocumentModel, claim_id: str, claim_type: str, text: str, line: int) -> Claim:
        return Claim(
            claim_id=claim_id,
            claim_type=claim_type,
            text=text.strip(),
            path=document.relative_path,
            line=line,
            feat_id=document.feat_id,
        )

