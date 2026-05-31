"""Platform overview composition for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

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
    # 延迟导入以避免循环依赖
    from sprintcycle.application.composition.di_container import container
    
    platform = build_platform_spec(project_name).to_dict()
    compose = container.integrations.autogpt_compose_spec(project_name).to_dict()

    intent_compiled = container.integrations.compiled_graph_runtime()
    sprint_compiled = container.integrations.compiled_sprint_graph()
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
    plan_runtime = container.integrations.plan_runtime(project_name).build_release_plan_from_intent("", {})
    runtime = {
        "autogpt": container.integrations.autogpt_runtime_spec(project_name).to_dict(),
        "plan_runtime": plan_runtime.to_dict() if hasattr(plan_runtime, "to_dict") else plan_runtime,
        "intent_graph": intent_graph,
        "sprint_graph": sprint_graph,
        "langgraph": container.integrations.langgraph_adapter(project_name).build_graph(),
    }
    exporter_spec = container.integrations.phoenix_exporter_spec(project_name)
    trace_runtime = container.observability.phoenix_trace_runtime(exporter_spec)
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
