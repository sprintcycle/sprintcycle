"""Concrete LangGraph execution runtime wiring for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .compiler import compile_intent_graph, compile_sprint_graph
from .graph import LangGraphGraphSpec, build_default_langgraph_graph_spec


@dataclass
class LangGraphExecutionRuntime:
    graph_spec: LangGraphGraphSpec = field(default_factory=build_default_langgraph_graph_spec)

    def build(self, checkpointer: Optional[Any] = None) -> Dict[str, Any]:
        intent_runtime = compile_intent_graph(checkpointer=checkpointer)
        sprint_runtime = compile_sprint_graph(checkpointer=checkpointer)
        return {
            "graph_spec": self.graph_spec.to_dict(),
            "intent_runtime": intent_runtime,
            "sprint_runtime": sprint_runtime,
            "nodes": {
                "intent": list(intent_runtime.nodes),
                "sprint": list(sprint_runtime.nodes),
            },
            "entrypoints": {
                "intent": intent_runtime.entrypoint,
                "sprint": sprint_runtime.entrypoint,
            },
            "finish_points": {
                "intent": intent_runtime.finish_point,
                "sprint": sprint_runtime.finish_point,
            },
            "checkpointer": checkpointer,
        }


__all__ = ["LangGraphExecutionRuntime"]
