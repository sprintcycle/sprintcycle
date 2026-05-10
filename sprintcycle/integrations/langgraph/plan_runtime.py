"""Plan runtime helpers for SprintCycle V2.

This module turns an intent into a normalized ReleasePlan-like payload that can
be consumed by the LangGraph intent graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...release_plan.models import ExecutionMode, ProductAnchor, ReleasePlan, SprintBacklogItem, SprintDefinition


@dataclass
class PlanRuntime:
    project_name: str = "sprintcycle"
    config: Dict[str, Any] = field(default_factory=dict)

    def build(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "config": dict(self.config),
            "status": "ready",
        }

    def build_release_plan_from_intent(self, intent: str, context: Dict[str, Any]) -> ReleasePlan:
        project_path = str(context.get("project_path", "") or ".")
        project_name = str(context.get("project_name", self.project_name) or self.project_name)
        runtime_config = dict(context.get("runtime_config", {}) or {})
        goals = self._derive_goals(intent, context)
        task_specs = self._derive_task_specs(intent, context)
        sprint_count = self._derive_sprint_count(context, task_specs)
        sprints: List[SprintDefinition] = self._split_tasks_into_sprints(goals, task_specs, sprint_count)
        metadata = {
            "source": "langgraph.intent_graph",
            "intent": intent,
            "project_path": project_path,
            "runtime_config": runtime_config,
            "planning_rules": {
                "max_tasks_per_sprint": int(context.get("max_tasks_per_sprint", runtime_config.get("max_tasks_per_sprint", 5)) or 5),
                "max_sprints": int(context.get("max_sprints", runtime_config.get("max_sprints", sprint_count)) or sprint_count),
                "parallel_tasks": int(context.get("parallel_tasks", runtime_config.get("parallel_tasks", 3)) or 3),
            },
            "task_allocation_strategy": "round_robin_by_sprint_capacity",
        }
        return ReleasePlan(
            project=ProductAnchor(name=project_name, path=project_path, version=str(context.get("project_version", "v1.0.0"))),
            mode=ExecutionMode.NORMAL,
            sprints=sprints,
            metadata=metadata,
        )

    def normalize_release_plan(self, release_plan: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(release_plan, ReleasePlan):
            return release_plan.to_dict()
        if isinstance(release_plan, dict):
            return dict(release_plan)
        return self.build_release_plan_from_intent(str(context.get("intent", "")), context).to_dict()

    def _derive_goals(self, intent: str, context: Dict[str, Any]) -> List[str]:
        goals = list(context.get("goals", []) or [])
        if intent and intent not in goals:
            goals.insert(0, intent)
        if not goals:
            goals = [intent or "deliver value"]
        return goals

    def _derive_task_specs(self, intent: str, context: Dict[str, Any]) -> List[SprintBacklogItem]:
        tasks = context.get("tasks")
        if isinstance(tasks, list) and tasks:
            normalized: List[SprintBacklogItem] = []
            for item in tasks:
                if isinstance(item, SprintBacklogItem):
                    normalized.append(item)
                elif isinstance(item, dict):
                    normalized.append(
                        SprintBacklogItem(
                            description=str(item.get("description", "") or intent or "deliver value"),
                            agent=str(item.get("agent", "coder") or "coder"),
                            target=item.get("target"),
                            constraints=list(item.get("constraints", []) or []),
                            expected_output=item.get("expected_output"),
                            timeout=int(item.get("timeout", 600) or 600),
                            spec_ref=item.get("spec_ref"),
                        )
                    )
            if normalized:
                return normalized
        return [
            SprintBacklogItem(
                description=intent or "deliver value",
                agent=str(context.get("default_agent", "coder") or "coder"),
                target=context.get("target"),
                constraints=list(context.get("constraints", []) or []),
                expected_output=context.get("expected_output"),
                timeout=int(context.get("timeout", 600) or 600),
                spec_ref=context.get("spec_ref"),
            )
        ]

    def _derive_sprint_count(self, context: Dict[str, Any], tasks: List[SprintBacklogItem]) -> int:
        runtime_config = dict(context.get("runtime_config", {}) or {})
        max_sprints = int(context.get("max_sprints", runtime_config.get("max_sprints", 1)) or 1)
        max_tasks_per_sprint = int(context.get("max_tasks_per_sprint", runtime_config.get("max_tasks_per_sprint", 5)) or 5)
        task_count = max(1, len(tasks))
        implied_by_tasks = (task_count + max_tasks_per_sprint - 1) // max_tasks_per_sprint
        return max(1, min(max_sprints, implied_by_tasks))

    def _split_tasks_into_sprints(self, goals: List[str], tasks: List[SprintBacklogItem], sprint_count: int) -> List[SprintDefinition]:
        sprint_count = max(1, sprint_count)
        if not tasks:
            return [SprintDefinition(name="sprint-1", goals=list(goals), tasks=[])]
        chunks: List[List[SprintBacklogItem]] = [[] for _ in range(sprint_count)]
        for idx, task in enumerate(tasks):
            chunks[idx % sprint_count].append(task)
        sprints: List[SprintDefinition] = []
        for i, chunk in enumerate(chunks, start=1):
            sprint_goals = list(goals)
            if len(goals) > 1:
                sprint_goals = [goals[min(i - 1, len(goals) - 1)]]
            if chunk:
                sprints.append(SprintDefinition(name=f"sprint-{i}", goals=sprint_goals, tasks=chunk))
        return sprints


__all__ = ["PlanRuntime"]
