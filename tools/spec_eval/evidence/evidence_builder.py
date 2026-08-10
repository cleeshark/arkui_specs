"""Combine claims, resolved source citations and SDK declarations."""

from __future__ import annotations

from spec_eval.checks.reference_checks import ReferenceResult
from spec_eval.checks.sdk_contract_checks import SdkContractResult
from spec_eval.evidence.claim_builder import ClaimBuilder
from spec_eval.models.document import DocumentModel
from spec_eval.models.evidence import EvidenceBundle
from spec_eval.models.function import FunctionContext
from spec_eval.parser.id_parser import IdParser


class FunctionEvidenceBuilder:
    def __init__(self) -> None:
        self.claim_builder = ClaimBuilder()
        self.id_parser = IdParser()

    def build(
        self,
        context: FunctionContext,
        documents: list[DocumentModel],
        references: ReferenceResult,
        sdk: SdkContractResult,
        finding_rule_ids: list[str] | None = None,
    ) -> EvidenceBundle:
        claims = self.claim_builder.build(documents)
        trace_citations = self._trace_citations(documents, references)
        resolved_count = 0
        for claim in claims:
            claim.citations.extend(references.citations_at(claim.path, claim.line))
            claim.citations.extend(trace_citations.get(claim.claim_id, []))
            claim.citations = self._unique_citations(claim.citations)
            if claim.claim_type == "api":
                prefix = f"{claim.feat_id or 'design'}/API-{claim.line}-"
                for key, values in sdk.declarations.items():
                    if key.startswith(prefix):
                        claim.sdk_declarations.extend(values)
            if claim.citations and all(item.resolved for item in claim.citations):
                claim.evidence_status = "RESOLVED"
                resolved_count += 1
            elif any(item.resolved for item in claim.citations):
                claim.evidence_status = "PARTIALLY_RESOLVED"
            elif claim.citations:
                claim.evidence_status = "UNRESOLVED"
            if finding_rule_ids:
                claim.static_finding_ids = list(finding_rule_ids)
        total = len(claims)
        metrics = {
            "claim_count": total,
            "resolved_claim_count": resolved_count,
            "evidence_coverage": resolved_count / total if total else 0.0,
            "claims_by_type": self._count_types(claims),
        }
        return EvidenceBundle(context.func_id, context.source_revision, claims, metrics)

    def _trace_citations(self, documents: list[DocumentModel], references: ReferenceResult) -> dict[str, list]:
        result: dict[str, list] = {}
        for document in documents:
            if document.kind != "spec" or not document.feat_id:
                continue
            for table in document.tables:
                ac_column = next((column for column in ("AC编号", "AC") if column in table.headers), None)
                if ac_column is None or "关联规则" not in table.headers or "证据" not in table.headers:
                    continue
                for row in table.rows:
                    mapping = row.as_mapping(table.headers)
                    citations = references.citations_at(document.relative_path, row.line)
                    if not citations:
                        continue
                    for ac in self.id_parser.extract_line(mapping.get(ac_column, "")).get("ac", tuple()):
                        result.setdefault(f"{document.feat_id}/{ac}", []).extend(citations)
        return result

    @staticmethod
    def _unique_citations(citations):
        result = []
        seen = set()
        for citation in citations:
            key = (citation.source_path or citation.path, citation.line_ranges)
            if key not in seen:
                seen.add(key)
                result.append(citation)
        return result

    @staticmethod
    def _count_types(claims) -> dict[str, int]:
        result: dict[str, int] = {}
        for claim in claims:
            result[claim.claim_type] = result.get(claim.claim_type, 0) + 1
        return result
