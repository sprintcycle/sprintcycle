"""Phoenix-style trace helpers for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PhoenixTraceSpec:
    project_name: str = "sprintcycle"
    export_mode: str = "trace"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "export_mode": self.export_mode,
            "config": dict(self.config),
        }


@dataclass
class PhoenixTraceAdapter:
    spec: PhoenixTraceSpec = field(default_factory=PhoenixTraceSpec)

    def to_dict(self) -> Dict[str, Any]:
        return self.spec.to_dict()


__all__ = ["PhoenixTraceSpec", "PhoenixTraceAdapter"]
