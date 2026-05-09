"""HITL 生命周期钩子（治理域版本）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

from ...execution.hooks.sprint_hooks import SprintLifecycleHooks
from ...execution.hooks.task_hooks import TaskLifecycleHooks
from ...execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from ...release_plan.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from .coordinator import HitlCoordinator
from .types import (
    CTX_HITL_ABORT_EXECUTION,
    HitlDecision,
    HitlGate,
    apply_after_sprint_decision,
    apply_before_sprint_decision,
    hitl_gate_enabled,
)

if TYPE_CHECKING:
    from ...config.runtime_config import RuntimeConfig


class HitlSprintHooks(SprintLifecycleHooks):
    def __init__(self, config: "RuntimeConfig", coordinator: HitlCoordinator) -> None:
        self._config = config
        self._coord = coordinator

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        if not hitl_gate_enabled(self._config, HitlGate.BEFORE_SPRINT):
            return
        eid = str(context.get("execution_id") or "").strip()
        if not eid:
            logger.warning("HITL before_sprint skipped: missing execution_id in context")
            return
        decision = await self._coord.wait_for_decision(
            execution_id=eid,
            gate=HitlGate.BEFORE_SPRINT,
            title=f"Sprint {sprint_index + 1}: {sprint.name}",
            summary="确认开始本 Sprint（或跳过 / 中止整次执行）",
            context={
                "sprint_index": sprint_index,
                "sprint_name": sprint.name,
                "goals": sprint.goals,
                "tasks": len(sprint.tasks),
                "release_plan": release_plan.to_dict() if hasattr(release_plan, "to_dict") and release_plan else None,
            },
            risk_level="medium",
        )
        apply_before_sprint_decision(context, decision)

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        if not hitl_gate_enabled(self._config, HitlGate.AFTER_SPRINT):
            return
        if result.status == ExecutionStatus.SKIPPED:
            return
        if result.status == ExecutionStatus.SUCCESS and not getattr(
            self._config, "hitl_after_sprint_always", False
        ):
            return
        eid = str(context.get("execution_id") or "").strip()
        if not eid:
            return
        decision = await self._coord.wait_for_decision(
            execution_id=eid,
            gate=HitlGate.AFTER_SPRINT,
            title=f"Sprint 结束确认: {sprint.name}",
            summary=f"状态={result.status.value}，请确认是否继续后续 Sprint",
            context={
                "sprint_index": sprint_index,
                "sprint_name": sprint.name,
                "result_status": result.status.value,
                "release_plan": release_plan.to_dict() if hasattr(release_plan, "to_dict") and release_plan else None,
            },
            risk_level="medium",
        )
        apply_after_sprint_decision(context, decision)


class HitlTaskHooks(TaskLifecycleHooks):
    def __init__(self, config: "RuntimeConfig", coordinator: HitlCoordinator) -> None:
        self._config = config
        self._coord = coordinator

    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        if not hitl_gate_enabled(self._config, HitlGate.AFTER_TASK):
            return
        on_failure_only = getattr(self._config, "hitl_after_task_on_failure", True)
        if on_failure_only and task_result.status == ExecutionStatus.SUCCESS:
            return
        eid = str(context.get("execution_id") or "").strip()
        if not eid:
            return
        preview = (task.description or "")[:400]
        decision = await self._coord.wait_for_decision(
            execution_id=eid,
            gate=HitlGate.AFTER_TASK,
            title=f"任务完成: {preview[:80]}",
            summary=f"Sprint={sprint_name} status={task_result.status.value}",
            context={
                "sprint_name": sprint_name,
                "agent": task.agent,
                "description_preview": preview,
                "task_status": task_result.status.value,
            },
            risk_level="medium",
        )
        if decision == HitlDecision.ABORT_EXECUTION:
            context[CTX_HITL_ABORT_EXECUTION] = True
