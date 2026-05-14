"""Concrete LangGraph execution runtime wiring for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict

from .graph import LangGraphGraphSpec, build_default_langgraph_graph_spec


@dataclass
class LangGraphExecutionRuntime:
    graph_spec: LangGraphGraphSpec = field(default_factory=build_default_langgraph_graph_spec)

    def build(self) -> Dict[str, Any]:
        try:
            from langgraph.graph import StateGraph  # type: ignore
        except Exception as exc:
            raise RuntimeError("LangGraph runtime is required for SprintCycle V2") from exc

        graph = StateGraph(dict)

        def _plan(state: Dict[str, Any]) -> Dict[str, Any]:
            return {**state, "stage": "plan", "visited": state.get("visited", []) + ["plan"]}

        def _run(state: Dict[str, Any]) -> Dict[str, Any]:
            return {**state, "stage": "run", "visited": state.get("visited", []) + ["run"]}

        def _observe(state: Dict[str, Any]) -> Dict[str, Any]:
            return {**state, "stage": "observe", "visited": state.get("visited", []) + ["observe"]}

        def _repair(state: Dict[str, Any]) -> Dict[str, Any]:
            return {**state, "stage": "repair", "visited": state.get("visited", []) + ["repair"]}

        handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
            "plan": _plan,
            "run": _run,
            "observe": _observe,
            "repair": _repair,
        }

        for node in self.graph_spec.nodes:
            graph.add_node(node.name, handlers[node.name])
        for edge in self.graph_spec.edges:
            graph.add_edge(edge.source, edge.target)
        graph.set_entry_point(self.graph_spec.nodes[0].name if self.graph_spec.nodes else "plan")
        graph.set_finish_point(self.graph_spec.nodes[-1].name if self.graph_spec.nodes else "repair")

        return {
            "graph_spec": self.graph_spec.to_dict(),
            "graph_runtime": str(graph),
            "nodes": list(handlers.keys()),
        }


__all__ = ["LangGraphExecutionRuntime"]
