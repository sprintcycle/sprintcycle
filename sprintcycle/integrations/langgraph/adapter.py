"""LangGraph execution adapter surface for SprintCycle V2.

The concrete LangGraph dependency is intentionally not imported here yet; this
module defines the boundary SprintCycle Core will target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class LangGraphExecutionAdapter:
    """Thin adapter contract for graph-based execution."""

    graph_name: str = "sprintcycle-execution"
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_name": self.graph_name,
            "config": dict(self.config),
        }


__all__ = ["LangGraphExecutionAdapter"]
