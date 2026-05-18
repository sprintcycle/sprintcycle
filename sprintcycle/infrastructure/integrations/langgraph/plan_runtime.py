"""Release plan shaping for LangGraph orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PlanRuntime:
    def build_release_plan_from_intent(self, intent: str, context: Dict[str, Any]) -> Any:
        sprints = [
            {
                "name": "sprint-1",
                "goals": [intent or "deliver value"],
                "tasks": [],
            }
        ]
        return _ReleasePlan(intent=intent, sprints=sprints, context=dict(context))


@dataclass
class _ReleasePlan:
    intent: str
    sprints: list[Dict[str, Any]]
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "sprints": list(self.sprints),
            "context": dict(self.context),
        }


__all__ = ["PlanRuntime"]
