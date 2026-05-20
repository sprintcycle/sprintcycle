"""Compiled LangGraph accessors for SprintCycle orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .graph import LangGraphEdgeSpec, LangGraphGraphSpec, LangGraphNodeSpec
from .intent_nodes import (
    intent_evaluate,
    intent_finalize,
    intent_understand,
    plan_generate,
    should_retry,
    sprint_dispatch,
    sprint_split,
)
from .sprint_nodes import (
    should_retry_sprint,
    sprint_execute,
    sprint_finalize,
    sprint_observe,
    sprint_prepare,
    sprint_repair,
)
from .states import IntentState, SprintState


@dataclass
class CompiledGraphRuntime:
    graph_name: str
    graph: Any
    entrypoint: str
    finish_point: str
    nodes: list[str]
    edges: list[Dict[str, Any]]
    checkpointer: Optional[Any]
    config: Dict[str, Any]


_intent_graph: Any = None
_sprint_graph: Any = None


def _build_intent_graph_spec() -> LangGraphGraphSpec:
    return LangGraphGraphSpec(
        graph_name="sprintcycle-intent",
        nodes=[
            LangGraphNodeSpec(name="intent_understand", type="llm"),
            LangGraphNodeSpec(name="plan_generate", type="llm"),
            LangGraphNodeSpec(name="sprint_split", type="orchestration"),
            LangGraphNodeSpec(name="sprint_dispatch", type="orchestration"),
            LangGraphNodeSpec(name="intent_evaluate", type="routing"),
            LangGraphNodeSpec(name="intent_finalize", type="terminal"),
        ],
        edges=[
            LangGraphEdgeSpec(source="intent_understand", target="plan_generate"),
            LangGraphEdgeSpec(source="plan_generate", target="sprint_split"),
            LangGraphEdgeSpec(source="sprint_split", target="sprint_dispatch"),
            LangGraphEdgeSpec(source="sprint_dispatch", target="intent_evaluate"),
            LangGraphEdgeSpec(source="intent_evaluate", target="intent_understand", condition="retry"),
            LangGraphEdgeSpec(source="intent_evaluate", target="intent_finalize", condition="finalize"),
        ],
    )


def _build_sprint_graph_spec() -> LangGraphGraphSpec:
    return LangGraphGraphSpec(
        graph_name="sprintcycle-sprint",
        nodes=[
            LangGraphNodeSpec(name="sprint_prepare", type="prepare"),
            LangGraphNodeSpec(name="sprint_execute", type="execute"),
            LangGraphNodeSpec(name="sprint_observe", type="observe"),
            LangGraphNodeSpec(name="sprint_repair", type="repair"),
            LangGraphNodeSpec(name="sprint_finalize", type="terminal"),
        ],
        edges=[
            LangGraphEdgeSpec(source="sprint_prepare", target="sprint_execute"),
            LangGraphEdgeSpec(source="sprint_execute", target="sprint_observe"),
            LangGraphEdgeSpec(source="sprint_observe", target="sprint_repair"),
            LangGraphEdgeSpec(source="sprint_repair", target="sprint_execute", condition="retry"),
            LangGraphEdgeSpec(source="sprint_repair", target="sprint_finalize", condition="finalize"),
        ],
    )


def _get_langgraph_state_graph() -> Any:
    from langgraph.graph import END, StateGraph  # type: ignore

    return StateGraph, END


def _compile_intent_graph() -> Any:
    global _intent_graph
    if _intent_graph is not None:
        return _intent_graph

    StateGraph, END = _get_langgraph_state_graph()
    graph = StateGraph(IntentState)
    graph.add_node("intent_understand", intent_understand)
    graph.add_node("plan_generate", plan_generate)
    graph.add_node("sprint_split", sprint_split)
    graph.add_node("sprint_dispatch", sprint_dispatch)
    graph.add_node("intent_evaluate", intent_evaluate)
    graph.add_node("intent_finalize", intent_finalize)
    graph.set_entry_point("intent_understand")
    graph.add_edge("intent_understand", "plan_generate")
    graph.add_edge("plan_generate", "sprint_split")
    graph.add_edge("sprint_split", "sprint_dispatch")
    graph.add_edge("sprint_dispatch", "intent_evaluate")
    graph.add_conditional_edges(
        "intent_evaluate",
        should_retry,
        {
            "intent_understand": "intent_understand",
            "finalize": "intent_finalize",
        },
    )
    graph.add_edge("intent_finalize", END)
    _intent_graph = graph.compile()
    return _intent_graph


def _compile_sprint_graph() -> Any:
    global _sprint_graph
    if _sprint_graph is not None:
        return _sprint_graph

    StateGraph, END = _get_langgraph_state_graph()
    graph = StateGraph(SprintState)
    graph.add_node("sprint_prepare", sprint_prepare)
    graph.add_node("sprint_execute", sprint_execute)
    graph.add_node("sprint_observe", sprint_observe)
    graph.add_node("sprint_repair", sprint_repair)
    graph.add_node("sprint_finalize", sprint_finalize)
    graph.set_entry_point("sprint_prepare")
    graph.add_edge("sprint_prepare", "sprint_execute")
    graph.add_edge("sprint_execute", "sprint_observe")
    graph.add_edge("sprint_observe", "sprint_repair")
    graph.add_conditional_edges(
        "sprint_repair",
        should_retry_sprint,
        {
            "sprint_execute": "sprint_execute",
            "sprint_finalize": "sprint_finalize",
        },
    )
    graph.add_edge("sprint_finalize", END)
    _sprint_graph = graph.compile()
    return _sprint_graph


def compile_intent_graph(checkpointer: Optional[Any] = None) -> CompiledGraphRuntime:
    graph = _compile_intent_graph()
    spec = _build_intent_graph_spec()
    return CompiledGraphRuntime(
        graph_name=spec.graph_name,
        graph=graph,
        entrypoint="intent_understand",
        finish_point="intent_finalize",
        nodes=[node.name for node in spec.nodes],
        edges=[edge.to_dict() for edge in spec.edges],
        checkpointer=checkpointer,
        config={"checkpoint_store": checkpointer},
    )


def compile_sprint_graph(checkpointer: Optional[Any] = None) -> CompiledGraphRuntime:
    graph = _compile_sprint_graph()
    spec = _build_sprint_graph_spec()
    return CompiledGraphRuntime(
        graph_name=spec.graph_name,
        graph=graph,
        entrypoint="sprint_prepare",
        finish_point="sprint_finalize",
        nodes=[node.name for node in spec.nodes],
        edges=[edge.to_dict() for edge in spec.edges],
        checkpointer=checkpointer,
        config={"checkpoint_store": checkpointer},
    )


def get_intent_graph(checkpointer: Optional[Any] = None) -> Any:
    return compile_intent_graph(checkpointer=checkpointer).graph


def get_sprint_graph(checkpointer: Optional[Any] = None) -> Any:
    return compile_sprint_graph(checkpointer=checkpointer).graph


__all__ = [
    "CompiledGraphRuntime",
    "compile_intent_graph",
    "compile_sprint_graph",
    "get_intent_graph",
    "get_sprint_graph",
]
