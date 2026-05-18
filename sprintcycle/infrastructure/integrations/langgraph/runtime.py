"""Runtime helpers for a LangGraph-style execution backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .compiler import compile_intent_graph, compile_sprint_graph
from .graph import LangGraphGraphSpec, build_default_langgraph_graph_spec
from .checkpoint import CheckpointStore, LocalJsonCheckpointStore


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
    checkpoint_store: Optional[CheckpointStore] = None

    def build_graph(self, checkpointer: Optional[Any] = None) -> Dict[str, Any]:
        if checkpointer is None and self.checkpoint_store is not None:
            checkpointer = self.checkpoint_store
        intent_runtime = compile_intent_graph(checkpointer=checkpointer)
        sprint_runtime = compile_sprint_graph(checkpointer=checkpointer)
        return {
            "spec": self.spec.to_dict(),
            "graph": self.graph.to_dict(),
            "intent_graph": intent_runtime.graph,
            "sprint_graph": sprint_runtime.graph,
            "intent_runtime": intent_runtime,
            "sprint_runtime": sprint_runtime,
            "checkpoint_store": checkpointer,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spec": self.spec.to_dict(),
            "graph": self.graph.to_dict(),
        }


__all__ = ["LangGraphRuntimeSpec", "LangGraphRuntimeAdapter"]
