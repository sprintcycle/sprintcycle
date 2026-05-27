"""Thin application-layer orchestration entrypoint for release execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from sprintcycle.domain.ports.integrations import compile_intent_graph


@dataclass
class ReleaseOrchestrator:
    config: Dict[str, Any] = field(default_factory=dict)

    async def execute_release_plan(self, intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        compiled = compile_intent_graph(checkpointer=self.config.get("checkpointer"))
        state: Dict[str, Any] = {
            "intent": intent,
            "context": dict(context),
            "attempt": 1,
        }
        if hasattr(compiled.graph, "ainvoke"):
            return await compiled.graph.ainvoke(state)
        return state


__all__ = ["ReleaseOrchestrator"]
