"""Phoenix export specification for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PhoenixExporterSpec:
    project_name: str = "sprintcycle"
    endpoint: str = "http://localhost:6006"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "endpoint": self.endpoint,
            "config": dict(self.config),
        }


__all__ = ["PhoenixExporterSpec"]
