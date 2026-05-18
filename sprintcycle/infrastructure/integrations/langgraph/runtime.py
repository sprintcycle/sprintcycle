"""Thin runtime adapter for compiled LangGraph access."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .checkpoint import CheckpointStore
from .compiler import CompiledGraphRuntime, compile_intent_graph, compile_sprint_graph


@dataclass
class LangGraphRuntimeSpec:
    graph_name: str = "sprintcycle-execution"
    entrypoint: str = "compiled_graph"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_name": self.graph_name,
            "entrypoint": self.entrypoint,
            "config": dict(self.config),
        }


@dataclass
class LangGraphRuntimeAdapter:
    spec: LangGraphRuntimeSpec = field(default_factory=LangGraphRuntimeSpec)
    checkpoint_store: Optional[CheckpointStore] = None

    def build_graph(self, checkpointer: Optional[Any] = None) -> Dict[str, CompiledGraphRuntime]:
        if checkpointer is None and self.checkpoint_store is not None:
            checkpointer = self.checkpoint_store
        return {
            "intent_runtime": compile_intent_graph(checkpointer=checkpointer),
            "sprint_runtime": compile_sprint_graph(checkpointer=checkpointer),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"spec": self.spec.to_dict()}


__all__ = ["LangGraphRuntimeSpec", "LangGraphRuntimeAdapter"]
