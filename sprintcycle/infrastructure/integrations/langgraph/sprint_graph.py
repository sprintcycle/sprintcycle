"""LangGraph sprint graph for SprintCycle V2.

This graph drives a single Sprint lifecycle:
Prepare -> Execute -> Observe -> Repair -> Finalize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .graph_runtime import LangGraphExecutionRuntime


@dataclass
class SprintGraphRuntime:
    project_name: str = "sprintcycle"
    config: Dict[str, Any] = field(default_factory=dict)

    def build(self) -> Dict[str, Any]:
        runtime = LangGraphExecutionRuntime().build(checkpointer=self.config.get("checkpointer"))
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "runtime": runtime,
            "nodes": ["sprint_prepare", "sprint_execute", "sprint_observe", "sprint_repair", "sprint_finalize"],
        }

    async def run(self, sprint: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        runtime = LangGraphExecutionRuntime().build(checkpointer=self.config.get("checkpointer"))
        state: Dict[str, Any] = {
            "sprint": dict(sprint),
            "context": {**dict(context), "project_name": self.project_name},
            "attempt": 1,
        }
        if hasattr(runtime["sprint_runtime"].graph, "ainvoke"):
            return await runtime["sprint_runtime"].graph.ainvoke(state)
        return state

    async def resume(self, sprint_id: str) -> Dict[str, Any]:
        return {
            "sprint_id": sprint_id,
            "project_name": self.project_name,
            "status": "resume_not_implemented",
        }

    def observe(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
        }


__all__ = ["SprintGraphRuntime"]
