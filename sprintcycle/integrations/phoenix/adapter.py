"""Phoenix observability adapter surface for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PhoenixObservabilityAdapter:
    """Thin adapter contract for trace and replay export."""

    project_name: str = "sprintcycle"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
        }


__all__ = ["PhoenixObservabilityAdapter"]
