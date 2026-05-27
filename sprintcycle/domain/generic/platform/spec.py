"""Platform composition spec for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from sprintcycle.domain.ports.integrations import (
    AutoGPTRuntimeSpecProtocol,
    LangGraphRuntimeAdapterProtocol,
    PhoenixExporterSpecProtocol,
    create_autogpt_runtime_spec,
    create_langgraph_adapter,
    create_phoenix_exporter_spec,
)


@dataclass
class PlatformSpec:
    """Aggregated platform spec for deployment, execution and observability."""

    deployment: AutoGPTRuntimeSpecProtocol
    execution: LangGraphRuntimeAdapterProtocol
    observability: PhoenixExporterSpecProtocol

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment": self.deployment.to_dict(),
            "execution": self.execution.to_dict(),
            "observability": self.observability.to_dict(),
        }


def build_platform_spec(project_name: str = "sprintcycle") -> PlatformSpec:
    deployment = create_autogpt_runtime_spec(project_name)
    execution = create_langgraph_adapter(f"{project_name}-execution")
    observability = create_phoenix_exporter_spec(project_name)
    return PlatformSpec(deployment=deployment, execution=execution, observability=observability)


__all__ = ["PlatformSpec", "build_platform_spec"]
