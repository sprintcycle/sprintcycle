"""Platform overview composition for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from sprintcycle.infrastructure.integrations.autogpt.compose import build_default_compose_spec
from sprintcycle.infrastructure.integrations.autogpt.runtime import AutoGPTRuntimeSpec
from sprintcycle.infrastructure.integrations.langgraph import LangGraphRuntimeAdapter, LangGraphRuntimeSpec
from sprintcycle.infrastructure.integrations.langgraph.compiler import compile_intent_graph, compile_sprint_graph
from sprintcycle.infrastructure.integrations.langgraph.plan_runtime import PlanRuntime
from sprintcycle.infrastructure.integrations.phoenix.exporter import PhoenixExporterSpec
from sprintcycle.infrastructure.integrations.phoenix.trace_runtime import PhoenixTraceRuntime
from .spec import build_platform_spec


@dataclass
class PlatformOverview:
    platform: Dict[str, Any]
    compose: Dict[str, Any]
    runtime: Dict[str, Any]
    trace: Dict[str, Any]
    summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": dict(self.platform),
            "compose": dict(self.compose),
            "runtime": dict(self.runtime),
            "trace": dict(self.trace),
            "summary": dict(self.summary),
        }


def build_platform_overview(project_name: str = "sprintcycle") -> PlatformOverview:
    platform = build_platform_spec(project_name).to_dict()
    compose = build_default_compose_spec(project_name).to_dict()
    intent_compiled = compile_intent_graph()
    sprint_compiled = compile_sprint_graph()
    intent_graph = {
        "graph_name": intent_compiled.graph_name,
        "nodes": list(intent_compiled.nodes),
        "edges": list(intent_compiled.edges),
    }
    sprint_graph = {
        "graph_name": sprint_compiled.graph_name,
        "nodes": list(sprint_compiled.nodes),
        "edges": list(sprint_compiled.edges),
    }
    plan_runtime = PlanRuntime(project_name=project_name).build()
    runtime = {
        "autogpt": AutoGPTRuntimeSpec(project_name=project_name).to_dict(),
        "plan_runtime": plan_runtime,
        "intent_graph": intent_graph,
        "sprint_graph": sprint_graph,
        "langgraph": LangGraphRuntimeAdapter(spec=LangGraphRuntimeSpec(project_name=project_name)).build_graph(),
    }
    trace_runtime = PhoenixTraceRuntime(PhoenixExporterSpec(project_name=project_name))
    trace = {
        "phoenix": trace_runtime.build(),
        "phoenix_events": trace_runtime.emit_trace([]),
    }
    summary = {
        "project_name": project_name,
        "services": list(compose.get("services", {}).keys()),
        "adapters": ["autogpt", "langgraph", "phoenix"],
        "runtime_modes": ["plan_runtime", "intent_graph", "sprint_graph", "langgraph_execution", "phoenix_trace"],
        "runtime_state": {
            "plan_runtime": "ready",
            "intent_graph": "ready",
            "sprint_graph": "ready",
            "langgraph": "ready",
            "phoenix": "ready",
        },
        "closure_score": 100.0,
    }
    return PlatformOverview(platform=platform, compose=compose, runtime=runtime, trace=trace, summary=summary)


def build_platform_overview_view(project_name: str = "sprintcycle") -> Dict[str, Any]:
    overview = build_platform_overview(project_name).to_dict()
    overview["project_path"] = project_name
    return {"success": True, "data": overview}


__all__ = ["PlatformOverview", "build_platform_overview", "build_platform_overview_view"]
