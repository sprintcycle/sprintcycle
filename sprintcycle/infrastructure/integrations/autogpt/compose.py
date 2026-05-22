"""Docker-compose style deployment spec for SprintCycle V2.

This spec is declarative, but it now reflects a more realistic platform layout
with API, dashboard, and observability services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ComposeService:
    name: str
    image: str
    ports: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    command: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image": self.image,
            "ports": list(self.ports),
            "environment": dict(self.environment),
            "depends_on": list(self.depends_on),
            "command": self.command,
        }


@dataclass
class ComposeSpec:
    project_name: str = "sprintcycle"
    services: Dict[str, ComposeService] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "services": {name: service.to_dict() for name, service in self.services.items()},
        }


def build_default_compose_spec(project_name: str = "sprintcycle") -> ComposeSpec:
    return ComposeSpec(
        project_name=project_name,
        services={
            "api": ComposeService(
                name="api",
                image=f"{project_name}:latest",
                ports=["8000:8000"],
                environment={
                    "SPRINTCYCLE_SERVICE": "api",
                    "SPRINTCYCLE_ENTRYPOINT": "sprintcycle.api:app",
                },
                command="uvicorn sprintcycle.api:app --host 0.0.0.0 --port 8000",
            ),
            "dashboard": ComposeService(
                name="dashboard",
                image=f"{project_name}:latest",
                ports=["3000:3000"],
                environment={
                    "SPRINTCYCLE_SERVICE": "dashboard",
                    "SPRINTCYCLE_ENTRYPOINT": "sprintcycle.interfaces.http.app:create_app",
                },
                depends_on=["api"],
                command="uvicorn sprintcycle.interfaces.http.app:create_app --factory --host 0.0.0.0 --port 3000",
            ),
            "phoenix": ComposeService(
                name="phoenix",
                image="arizephoenix/phoenix:latest",
                ports=["6006:6006"],
                environment={"PHOENIX_HOST": "0.0.0.0", "PHOENIX_PORT": "6006"},
                command="python -m phoenix.server --host 0.0.0.0 --port 6006",
            ),
        },
    )


__all__ = ["ComposeService", "ComposeSpec", "build_default_compose_spec"]
