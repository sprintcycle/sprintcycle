"""HITL 生命周期钩子（治理域版本）。

使用 Domain 定义的接口协议，打破 Governance → Execution 循环依赖。

**分层**：HitlHooks 通过构造函数接收依赖。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from sprintcycle.domain.generic.interfaces import SprintLifecycleHookProtocol, TaskLifecycleHookProtocol
from sprintcycle.domain.generic.interfaces import ExecutionStatus, TaskResult, SprintResult
from sprintcycle.domain.ports.config import RuntimeConfigProtocol
from .types import (
    CTX_HITL_ABORT_EXECUTION,
    HitlDecision,
    HitlGate,
    apply_after_sprint_decision,
    apply_before_sprint_decision,
    hitl_gate_enabled,
)

if TYPE_CHECKING:
    from sprintcycle.domain.ports.observability import ObservabilityFacadeProtocol


class HitlSprintHooks(SprintLifecycleHookProtocol):
    """HITL Sprint 钩子 - 实现协议接口"""

    def __init__(self, config: RuntimeConfigProtocol, observability: "ObservabilityFacadeProtocol") -> None:
        self._config = config
        self._observability = observability

    async def on_sprint_start(
        self,
        sprint: SprintDefinition,
        **kwargs: Any,
    ) -> None:
        """Sprint 开始钩子"""
        sprint_index = kwargs.get("sprint_index", 0)
        context = kwargs.get("context", {})
        release_plan = kwargs.get("release_plan")

        if not hitl_gate_enabled(self._config, HitlGate.BEFORE_SPRINT):
            return
        eid = str(context.get("execution_id") or "").strip()
        if not eid:
            logger.warning("HITL before_sprint skipped: missing execution_id in context")
            return
        result = await self._observability.request_human_decision(
            execution_id=eid,
            gate=HitlGate.BEFORE_SPRINT.value,
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
            wait=True,
        )
        if result.decision:
            try:
                apply_before_sprint_decision(context, HitlDecision(result.decision))
            except Exception:
                logger.warning("HITL before_sprint decision not applied: {}", result.decision)

    async def on_sprint_complete(
        self,
        sprint: SprintDefinition,
        result: SprintResult,
        **kwargs: Any,
    ) -> None:
        """Sprint 完成钩子"""
        sprint_index = kwargs.get("sprint_index", 0)
        context = kwargs.get("context", {})
        release_plan = kwargs.get("release_plan")

        if not hitl_gate_enabled(self._config, HitlGate.AFTER_SPRINT):
            return
        if result.status == ExecutionStatus.SKIPPED:
            return
        if result.status == ExecutionStatus.SUCCESS and not getattr(self._config, "hitl_after_sprint_always", False):
            return
        eid = str(context.get("execution_id") or "").strip()
        if not eid:
            return
        decision = await self._observability.request_human_decision(
            execution_id=eid,
            gate=HitlGate.AFTER_SPRINT.value,
            title=f"Sprint 结束确认: {sprint.name}",
            summary=f"状态={result.status.value}，请确认是否继续后续 Sprint",
            context={
                "sprint_index": sprint_index,
                "sprint_name": sprint.name,
                "result_status": result.status.value,
                "release_plan": release_plan.to_dict() if hasattr(release_plan, "to_dict") and release_plan else None,
            },
            risk_level="medium",
            wait=True,
        )
        if decision.decision:
            try:
                apply_after_sprint_decision(context, HitlDecision(decision.decision))
            except Exception:
                logger.warning("HITL after_sprint decision not applied: {}", decision.decision)


class HitlTaskHooks(TaskLifecycleHookProtocol):
    """HITL Task 钩子 - 实现协议接口"""

    def __init__(self, config: RuntimeConfigProtocol, observability: "ObservabilityFacadeProtocol") -> None:
        self._config = config
        self._observability = observability

    async def on_task_complete(
        self,
        task: SprintBacklogItem,
        result: Dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Task 完成钩子"""
        task_result = kwargs.get("task_result")
        if task_result is None:
            return

        sprint_name = kwargs.get("sprint_name", "")
        context = kwargs.get("context", {})

        if not hitl_gate_enabled(self._config, HitlGate.AFTER_TASK):
            return
        on_failure_only = getattr(self._config, "hitl_after_task_on_failure", True)
        if on_failure_only and task_result.status == ExecutionStatus.SUCCESS:
            return
        eid = str(context.get("execution_id") or "").strip()
        if not eid:
            return
        preview = (task.description or "")[:400]
        decision = await self._observability.request_human_decision(
            execution_id=eid,
            gate=HitlGate.AFTER_TASK.value,
            title=f"任务完成: {preview[:80]}",
            summary=f"Sprint={sprint_name} status={task_result.status.value}",
            context={
                "sprint_name": sprint_name,
                "agent": task.agent,
                "description_preview": preview,
                "task_status": task_result.status.value,
            },
            risk_level="medium",
            wait=True,
        )
        if decision.decision == HitlDecision.ABORT_EXECUTION.value:
            context[CTX_HITL_ABORT_EXECUTION] = True
