"""AutoGPT-style runtime helpers for SprintCycle V2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AutoGPTRuntimeSpec:
    project_name: str = "sprintcycle"
    entrypoints: List[str] = field(default_factory=lambda: ["api", "dashboard"])
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "entrypoints": list(self.entrypoints),
            "config": dict(self.config),
        }


__all__ = ["AutoGPTRuntimeSpec"]
