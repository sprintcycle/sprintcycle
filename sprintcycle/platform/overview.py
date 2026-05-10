"""Platform overview composition for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..integrations.autogpt.compose import build_default_compose_spec
from ..integrations.autogpt.runtime import AutoGPTRuntimeSpec
from ..integrations.langgraph.graph_runtime import LangGraphExecutionRuntime
from ..integrations.phoenix.exporter import PhoenixExporterSpec
from ..integrations.phoenix.trace_runtime import PhoenixTraceRuntime
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
    langgraph_runtime = LangGraphExecutionRuntime().build()
    phoenix_runtime = PhoenixTraceRuntime(PhoenixExporterSpec(project_name=project_name)).build()
    trace = {
        "phoenix": phoenix_runtime,
        "phoenix_events": PhoenixTraceRuntime(PhoenixExporterSpec(project_name=project_name)).emit_trace([]),
    }
    runtime = {
        "autogpt": AutoGPTRuntimeSpec(project_name=project_name).to_dict(),
        "langgraph": langgraph_runtime,
    }
    summary = {
        "project_name": project_name,
        "services": list(compose.get("services", {}).keys()),
        "adapters": ["autogpt", "langgraph", "phoenix"],
        "runtime_modes": ["langgraph_execution", "phoenix_trace"],
        "runtime_state": {
            "langgraph": "ready" if langgraph_runtime else "unknown",
            "phoenix": "ready" if phoenix_runtime else "unknown",
        },
    }
    return PlatformOverview(platform=platform, compose=compose, runtime=runtime, trace=trace, summary=summary)


__all__ = ["PlatformOverview", "build_platform_overview"]
