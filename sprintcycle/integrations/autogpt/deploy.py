"""AutoGPT-style deployment wiring for SprintCycle V2.

This module intentionally stays thin and declarative so deployment orchestration
can remain externalized to docker-compose / platform scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AutoGPTDeploymentSpec:
    """Declarative deployment spec for a platform-style runtime."""

    project_name: str = "sprintcycle"
    services: Dict[str, Any] = field(default_factory=lambda: {
        "api": {"port": 8000, "healthcheck": "/health"},
        "dashboard": {"port": 3000},
    })
    environment: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "services": dict(self.services),
            "environment": dict(self.environment),
        }


@dataclass
class AutoGPTRuntimeSpec:
    project_name: str = "sprintcycle"
    entrypoints: list[str] = field(default_factory=lambda: ["api", "dashboard"])
    image: str = "sprintcycle:latest"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "entrypoints": list(self.entrypoints),
            "image": self.image,
            "config": dict(self.config),
        }


__all__ = ["AutoGPTDeploymentSpec", "AutoGPTRuntimeSpec"]
