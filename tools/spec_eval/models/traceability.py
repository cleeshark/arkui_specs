"""Traceability graph models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class TraceNode:
    node_id: str
    kind: str
    path: str
    line: int
    text: str = ""


@dataclass(frozen=True)
class TraceEdge:
    source: str
    target: str
    kind: str
    path: str
    line: int


@dataclass
class TraceGraph:
    nodes: dict[str, TraceNode] = field(default_factory=dict)
    edges: list[TraceEdge] = field(default_factory=list)

    def add_node(self, node: TraceNode) -> None:
        self.nodes.setdefault(node.node_id, node)

    def add_edge(self, edge: TraceEdge) -> None:
        self.edges.append(edge)

    def incoming(self, node_id: str, kind: str | None = None) -> list[TraceEdge]:
        return [edge for edge in self.edges if edge.target == node_id and (kind is None or edge.kind == kind)]

    def outgoing(self, node_id: str, kind: str | None = None) -> list[TraceEdge]:
        return [edge for edge in self.edges if edge.source == node_id and (kind is None or edge.kind == kind)]

    def to_dict(self) -> dict[str, object]:
        return {
            "nodes": [asdict(node) for node in sorted(self.nodes.values(), key=lambda item: item.node_id)],
            "edges": [asdict(edge) for edge in sorted(self.edges, key=lambda item: (item.source, item.target, item.kind))],
        }

