"""Build and validate Function-scoped traceability graphs."""

from __future__ import annotations

from dataclasses import dataclass

from spec_eval.checks.base import make_finding
from spec_eval.config import EvaluationConfig
from spec_eval.models import DocumentModel, Finding, FunctionContext, Severity, TraceEdge, TraceGraph, TraceNode
from spec_eval.parser.id_parser import IdParser


@dataclass
class TraceabilityResult:
    graph: TraceGraph
    findings: list[Finding]
    metrics: dict[str, object]


class TraceabilityChecker:
    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config
        self.ids = IdParser()

    def run(self, context: FunctionContext, documents: list[DocumentModel]) -> TraceabilityResult:
        graph = TraceGraph()
        findings: list[Finding] = []
        per_feat: dict[str, dict[str, int | float]] = {}
        for document in documents:
            if document.kind != "spec" or not document.feat_id:
                continue
            feat = document.feat_id
            suppress_no_rule: set[str] = set()
            suppress_no_vm: set[str] = set()
            suppress_rule_orphan: set[str] = set()
            for table in document.tables:
                trace_ac_column = next((column for column in ("AC编号", "AC") if column in table.headers), None)
                for row in table.rows:
                    for cell in row.cells:
                        for value in self.ids.find_ranges(cell):
                            findings.append(
                                make_finding(
                                    self.config,
                                    context,
                                    "TRACE-RANGE-ID-001",
                                    Severity.MAJOR,
                                    f"ambiguous ID range `{value}` must be expanded explicitly",
                                    document.path,
                                    row.line,
                                    feat_id=feat,
                                )
                            )
                    mapping = row.as_mapping(table.headers)
                    if "编号" in table.headers and "对应规格项" in table.headers:
                        suppress_no_vm.update(
                            self._qualified_range_members(mapping.get("对应规格项", ""), "ac", feat)
                        )
                    if trace_ac_column and "关联规则" in table.headers:
                        range_acs = self._qualified_range_members(mapping.get(trace_ac_column, ""), "ac", feat)
                        suppress_no_rule.update(range_acs)
                        suppress_rule_orphan.update(
                            self._qualified_range_members(mapping.get("关联规则", ""), "rule", feat)
                        )
                        if range_acs:
                            suppress_rule_orphan.update(
                                self._qualified_ids(mapping.get("关联规则", ""), "rule", feat)
                            )
                    if "规则ID" in table.headers and "关联AC" in table.headers:
                        range_acs = self._qualified_range_members(mapping.get("关联AC", ""), "ac", feat)
                        suppress_no_rule.update(range_acs)
                        if range_acs:
                            suppress_rule_orphan.update(
                                self._qualified_ids(mapping.get("规则ID", ""), "rule", feat)
                            )
                if "AC编号" in table.headers:
                    self._add_nodes(graph, document, table, feat, "AC编号", "ac")
                if "规则ID" in table.headers:
                    self._add_rule_rows(graph, document, table, feat)
                if "编号" in table.headers and "对应规格项" in table.headers:
                    self._add_vm_rows(graph, document, table, feat)
                if trace_ac_column and "关联规则" in table.headers:
                    self._add_trace_rows(graph, document, table, feat, trace_ac_column)

            ac_nodes = [node for node in graph.nodes.values() if node.kind == "ac" and node.node_id.startswith(f"{feat}/")]
            rule_nodes = [node for node in graph.nodes.values() if node.kind == "rule" and node.node_id.startswith(f"{feat}/")]
            vm_nodes = [node for node in graph.nodes.values() if node.kind == "vm" and node.node_id.startswith(f"{feat}/")]
            closed = 0
            for node in ac_nodes:
                has_rule = bool(graph.outgoing(node.node_id, "specified_by"))
                has_vm = bool(graph.outgoing(node.node_id, "verified_by"))
                if has_rule and has_vm:
                    closed += 1
                if not has_rule and node.node_id not in suppress_no_rule:
                    findings.append(self._trace_finding(context, document, feat, node, "TRACE-AC-NO-RULE-001", "AC is not linked to any Rule"))
                if not has_vm and node.node_id not in suppress_no_vm:
                    findings.append(self._trace_finding(context, document, feat, node, "TRACE-AC-NO-VM-001", "AC is not linked to any verification mapping"))
            for node in rule_nodes:
                if not graph.incoming(node.node_id, "specified_by") and node.node_id not in suppress_rule_orphan:
                    findings.append(self._trace_finding(context, document, feat, node, "TRACE-RULE-ORPHAN-001", "Rule is not linked from any AC"))
            per_feat[feat] = {
                "ac_count": len(ac_nodes),
                "rule_count": len(rule_nodes),
                "vm_count": len(vm_nodes),
                "closed_ac_count": closed,
                "closure_rate": closed / len(ac_nodes) if ac_nodes else 0.0,
            }

        all_ac = [node for node in graph.nodes.values() if node.kind == "ac"]
        closed_total = sum(int(item["closed_ac_count"]) for item in per_feat.values())
        metrics: dict[str, object] = {
            "ac_count": len(all_ac),
            "rule_count": sum(1 for node in graph.nodes.values() if node.kind == "rule"),
            "vm_count": sum(1 for node in graph.nodes.values() if node.kind == "vm"),
            "closed_ac_count": closed_total,
            "closure_rate": closed_total / len(all_ac) if all_ac else 0.0,
            "per_feat": per_feat,
        }
        return TraceabilityResult(graph, findings, metrics)

    def _add_nodes(self, graph: TraceGraph, document: DocumentModel, table, feat: str, column: str, kind: str) -> None:
        for row in table.rows:
            mapping = row.as_mapping(table.headers)
            for local_id in self._ids(mapping.get(column, ""), kind):
                graph.add_node(TraceNode(f"{feat}/{local_id}", kind, document.relative_path, row.line, " | ".join(row.cells)))

    def _add_rule_rows(self, graph: TraceGraph, document: DocumentModel, table, feat: str) -> None:
        for row in table.rows:
            mapping = row.as_mapping(table.headers)
            rules = self._ids(mapping.get("规则ID", ""), "rule")
            acs = self._ids(mapping.get("关联AC", ""), "ac")
            for rule in rules:
                rule_id = f"{feat}/{rule}"
                graph.add_node(TraceNode(rule_id, "rule", document.relative_path, row.line, " | ".join(row.cells)))
                for ac in acs:
                    ac_id = f"{feat}/{ac}"
                    graph.add_edge(TraceEdge(ac_id, rule_id, "specified_by", document.relative_path, row.line))

    def _add_vm_rows(self, graph: TraceGraph, document: DocumentModel, table, feat: str) -> None:
        for row in table.rows:
            mapping = row.as_mapping(table.headers)
            vms = self._ids(mapping.get("编号", ""), "vm")
            acs = self._ids(mapping.get("对应规格项", ""), "ac")
            for vm in vms:
                vm_id = f"{feat}/{vm}"
                graph.add_node(TraceNode(vm_id, "vm", document.relative_path, row.line, " | ".join(row.cells)))
                for ac in acs:
                    graph.add_edge(TraceEdge(f"{feat}/{ac}", vm_id, "verified_by", document.relative_path, row.line))

    def _add_trace_rows(
        self, graph: TraceGraph, document: DocumentModel, table, feat: str, ac_column: str
    ) -> None:
        for row in table.rows:
            mapping = row.as_mapping(table.headers)
            acs = self._ids(mapping.get(ac_column, ""), "ac")
            rules = self._ids(mapping.get("关联规则", ""), "rule")
            tasks = self._ids(mapping.get("关联 Task", ""), "task")
            evidence = mapping.get("证据", "").strip()
            for ac in acs:
                ac_id = f"{feat}/{ac}"
                for rule in rules:
                    graph.add_edge(TraceEdge(ac_id, f"{feat}/{rule}", "specified_by", document.relative_path, row.line))
                for task in tasks:
                    task_id = f"{context_id(document, feat)}/{task}"
                    graph.add_node(TraceNode(task_id, "task", document.relative_path, row.line, task))
                    graph.add_edge(TraceEdge(ac_id, task_id, "implemented_by", document.relative_path, row.line))
                if evidence and evidence.upper() != "N/A":
                    evidence_id = f"{feat}/EVIDENCE-{row.line}"
                    graph.add_node(TraceNode(evidence_id, "evidence", document.relative_path, row.line, evidence))
                    graph.add_edge(TraceEdge(ac_id, evidence_id, "evidenced_by", document.relative_path, row.line))

    def _ids(self, text: str, kind: str) -> tuple[str, ...]:
        sanitized = text
        for value in self.ids.find_ranges(text):
            sanitized = sanitized.replace(value, " ")
        return self.ids.extract_line(sanitized).get(kind, tuple())

    def _qualified_range_members(self, text: str, kind: str, feat: str) -> set[str]:
        prefix = {"ac": "AC-", "rule": "R-", "vm": "VM-"}[kind]
        result: set[str] = set()
        for value in self.ids.find_ranges(text):
            members = self.ids.expand_range(value) or self.ids.extract_line(value).get(kind, tuple())
            result.update(f"{feat}/{member}" for member in members if member.startswith(prefix))
        return result

    def _qualified_ids(self, text: str, kind: str, feat: str) -> set[str]:
        return {
            *(f"{feat}/{member}" for member in self._ids(text, kind)),
            *self._qualified_range_members(text, kind, feat),
        }

    def _trace_finding(
        self,
        context: FunctionContext,
        document: DocumentModel,
        feat: str,
        node: TraceNode,
        rule_id: str,
        message: str,
    ) -> Finding:
        return make_finding(
            self.config,
            context,
            rule_id,
            Severity.MAJOR,
            message,
            document.path,
            node.line,
            feat_id=feat,
            node_id=node.node_id,
        )


def context_id(document: DocumentModel, feat: str) -> str:
    return document.relative_path.split("/Feat-", 1)[0].replace("/", "-") + f"/{feat}"
