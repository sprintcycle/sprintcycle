"""SprintCycle 质量层生命周期桥接钩子。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ...quality_spec.context import build_quality_context
from ...quality_spec.hooks.quality_hooks import QualityLifecycleHooks
from ...quality_spec.hooks.lifecycle_report import LifecycleReport
from ...quality_spec.reports.report import Report
from ...release_plan.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from .sprint_hooks import SprintLifecycleHooks
from .task_hooks import TaskLifecycleHooks
from ..sprint_types import SprintResult, TaskResult


class QualitySprintLifecycleHooks(SprintLifecycleHooks):
    def __init__(self, quality_hooks: Optional[QualityLifecycleHooks] = None) -> None:
        self._quality_hooks = quality_hooks or QualityLifecycleHooks()

    async def on_before_sprint(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        ctx = build_quality_context(
            project_path=str(context.get("project_path", ".")),
            gate="planning",
            task_id=None,
            sprint_id=str(sprint_index),
            extra={"sprint_name": sprint.name, "sprint_index": sprint_index, "release_plan": release_plan, "runtime_config": context.get("runtime_config"), "execution_id": context.get("execution_id")},
        )
        await self._quality_hooks.on_before_task(ctx)

    async def on_after_sprint(self, sprint_index: int, sprint: SprintDefinition, result: SprintResult, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        ctx = build_quality_context(
            project_path=str(context.get("project_path", ".")),
            gate="release",
            task_id=None,
            sprint_id=str(sprint_index),
            extra={"sprint_name": sprint.name, "sprint_result": result, "release_plan": release_plan, "runtime_config": context.get("runtime_config"), "execution_id": context.get("execution_id")},
        )
        await self._quality_hooks.on_after_release(ctx)


class QualityTaskLifecycleHooks(TaskLifecycleHooks):
    def __init__(self, quality_hooks: Optional[QualityLifecycleHooks] = None) -> None:
        self._quality_hooks = quality_hooks or QualityLifecycleHooks()

    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        ctx = build_quality_context(
            project_path=str(context.get("project_path", ".")),
            gate="task",
            task_id=task.description,
            sprint_id=str(context.get("sprint_index", "")),
            changed_files=list(context.get("changed_files") or []),
            extra={
                "task": task,
                "sprint_name": sprint_name,
                "task_result": task_result,
                "runtime_config": context.get("runtime_config"),
                "execution_id": context.get("execution_id"),
            },
        )
        await self._quality_hooks.on_after_task(ctx)


def build_quality_lifecycle_report(report: Report) -> LifecycleReport:
    return LifecycleReport.from_report(report)
