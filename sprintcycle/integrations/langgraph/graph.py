"""LangGraph graph specification for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class LangGraphNodeSpec:
    name: str
    type: str
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "config": dict(self.config),
        }


@dataclass
class LangGraphEdgeSpec:
    source: str
    target: str
    condition: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "condition": self.condition,
        }


@dataclass
class LangGraphGraphSpec:
    graph_name: str = "sprintcycle-execution"
    nodes: List[LangGraphNodeSpec] = field(default_factory=list)
    edges: List[LangGraphEdgeSpec] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_name": self.graph_name,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }


def build_default_langgraph_graph_spec(graph_name: str = "sprintcycle-execution") -> LangGraphGraphSpec:
    return LangGraphGraphSpec(
        graph_name=graph_name,
        nodes=[
            LangGraphNodeSpec(name="plan", type="planner"),
            LangGraphNodeSpec(name="run", type="executor"),
            LangGraphNodeSpec(name="observe", type="observer"),
            LangGraphNodeSpec(name="repair", type="recovery"),
        ],
        edges=[
            LangGraphEdgeSpec(source="plan", target="run"),
            LangGraphEdgeSpec(source="run", target="observe"),
            LangGraphEdgeSpec(source="observe", target="repair", condition="on_error"),
            LangGraphEdgeSpec(source="repair", target="run", condition="retry"),
        ],
    )


__all__ = ["LangGraphNodeSpec", "LangGraphEdgeSpec", "LangGraphGraphSpec", "build_default_langgraph_graph_spec"]
