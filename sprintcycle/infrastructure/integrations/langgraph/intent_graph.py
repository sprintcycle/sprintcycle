"""LangGraph intent graph for SprintCycle V2.

This graph drives the top-level lifecycle:
Intent -> Plan -> Sprint Split -> Sprint Dispatch -> Finalize.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .graph_runtime import LangGraphExecutionRuntime
from .plan_runtime import PlanRuntime
from .sprint_graph import SprintGraphRuntime


@dataclass
class IntentGraphRuntime:
    project_name: str = "sprintcycle"
    config: Dict[str, Any] = field(default_factory=dict)
    sprint_graph: SprintGraphRuntime = field(default_factory=SprintGraphRuntime)
    plan_runtime: PlanRuntime = field(default_factory=PlanRuntime)

    def build(self) -> Dict[str, Any]:
        runtime = LangGraphExecutionRuntime().build(checkpointer=self.config.get("checkpointer"))
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "runtime": runtime,
            "nodes": ["intent_understand", "plan_generate", "sprint_split", "sprint_dispatch", "intent_evaluate", "intent_finalize"],
        }

    async def run(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        runtime = LangGraphExecutionRuntime().build(checkpointer=self.config.get("checkpointer"))
        state: Dict[str, Any] = {
            "intent": intent,
            "context": {**dict(context), "project_name": self.project_name},
            "attempt": 1,
        }
        if hasattr(runtime["intent_runtime"].graph, "ainvoke"):
            return await runtime["intent_runtime"].graph.ainvoke(state)
        return state

    async def resume(self, run_id: str) -> Dict[str, Any]:
        return {
            "run_id": run_id,
            "project_name": self.project_name,
            "status": "resume_not_implemented",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "sprint_graph": self.sprint_graph.to_dict(),
        }


__all__ = ["IntentGraphRuntime"]
