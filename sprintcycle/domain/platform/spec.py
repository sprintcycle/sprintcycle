"""Platform composition spec for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from ...infrastructure.integrations.autogpt.deploy import AutoGPTDeploymentSpec
from ...infrastructure.integrations.langgraph.adapter import LangGraphExecutionAdapter
from ...infrastructure.integrations.phoenix.adapter import PhoenixObservabilityAdapter


@dataclass
class PlatformSpec:
    """Aggregated platform spec for deployment, execution and observability."""

    deployment: AutoGPTDeploymentSpec = field(default_factory=AutoGPTDeploymentSpec)
    execution: LangGraphExecutionAdapter = field(default_factory=LangGraphExecutionAdapter)
    observability: PhoenixObservabilityAdapter = field(default_factory=PhoenixObservabilityAdapter)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment": self.deployment.to_dict(),
            "execution": self.execution.to_dict(),
            "observability": self.observability.to_dict(),
        }


def build_platform_spec(project_name: str = "sprintcycle") -> PlatformSpec:
    deployment = AutoGPTDeploymentSpec(project_name=project_name)
    execution = LangGraphExecutionAdapter(graph_name=f"{project_name}-execution")
    observability = PhoenixObservabilityAdapter(project_name=project_name)
    return PlatformSpec(deployment=deployment, execution=execution, observability=observability)


__all__ = ["PlatformSpec", "build_platform_spec"]
