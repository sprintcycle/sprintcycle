"""Runtime helpers for a LangGraph-style execution backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .graph import LangGraphGraphSpec, build_default_langgraph_graph_spec
from .graph_runtime import LangGraphExecutionRuntime


@dataclass
class LangGraphRuntimeSpec:
    graph_name: str = "sprintcycle-execution"
    entrypoint: str = "run"
    nodes: List[str] = field(default_factory=lambda: ["plan", "run", "observe", "repair"])
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_name": self.graph_name,
            "entrypoint": self.entrypoint,
            "nodes": list(self.nodes),
            "config": dict(self.config),
        }


@dataclass
class LangGraphRuntimeAdapter:
    spec: LangGraphRuntimeSpec = field(default_factory=LangGraphRuntimeSpec)
    graph: LangGraphGraphSpec = field(default_factory=build_default_langgraph_graph_spec)
    runtime: LangGraphExecutionRuntime = field(default_factory=LangGraphExecutionRuntime)

    def build_graph(self) -> Dict[str, Any]:
        return self.runtime.build()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "graph": self.graph.to_dict(),
        }


__all__ = ["LangGraphRuntimeSpec", "LangGraphRuntimeAdapter"]
