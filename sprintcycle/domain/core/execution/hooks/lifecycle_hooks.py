"""
Sprint 和 Task 生命周期钩子统一模块。

**已精简**：将 sprint_hooks.py 和 task_hooks.py 合并到此文件。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan, SprintDefinition, SprintBacklogItem
from sprintcycle.domain.generic.interfaces import SprintResult, TaskResult
from sprintcycle.domain.generic.interfaces.hook_factory import HookFactory, ChainedHooks


class SprintLifecycleHooks(ABC):
    """Sprint 生命周期钩子基类"""

    @abstractmethod
    async def on_before_sprint(
        self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]
    ) -> None:
        pass

    @abstractmethod
    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        pass

    async def after_plan(
        self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]
    ) -> None:
        return None

    async def before_review(
        self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]
    ) -> None:
        return None

    async def after_retro(
        self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]
    ) -> None:
        return None


class TaskLifecycleHooks(ABC):
    """可选 async 钩子；实现类应吞掉非致命异常或交由调用方策略处理。"""

    @abstractmethod
    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        """任务执行结束（成功或失败）后调用。"""


def create_noop_sprint_hooks() -> SprintLifecycleHooks:
    """创建空实现的 Sprint 钩子"""
    return HookFactory.noop(SprintLifecycleHooks)


def create_chained_sprint_hooks(hooks: Sequence[SprintLifecycleHooks]) -> ChainedHooks:
    """创建链式调用的 Sprint 钩子"""
    return HookFactory.chain(hooks)


def create_noop_task_hooks() -> TaskLifecycleHooks:
    """创建空实现的 Task 钩子"""
    return HookFactory.noop(TaskLifecycleHooks)


def create_chained_task_hooks(hooks: Sequence[TaskLifecycleHooks]) -> ChainedHooks:
    """创建链式调用的 Task 钩子"""
    return HookFactory.chain(hooks)


class _OrchestratorSprintHooks(SprintLifecycleHooks):
    """编排器级别的 Sprint 钩子：处理事件发射和测量元数据。"""

    def __init__(self, orchestrator: Any, release_plan: ReleasePlan):
        self._orchestrator = orchestrator
        self._release_plan = release_plan

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        from sprintcycle.domain.core.execution.core.events import Event, EventType

        event = Event(
            type=EventType.SPRINT_START,
            data={
                "sprint_index": sprint_index,
                "sprint_name": getattr(sprint, "name", ""),
                "release_plan_id": getattr(release_plan, "id", ""),
            },
        )
        try:
            await self._orchestrator._emit(event)
        except Exception:
            pass

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        from sprintcycle.domain.core.execution.core.events import Event, EventType

        event = Event(
            type=EventType.SPRINT_COMPLETE if result.status.value == "success" else EventType.SPRINT_FAILED,
            data={
                "sprint_index": sprint_index,
                "sprint_name": getattr(sprint, "name", ""),
                "status": result.status.value,
                "release_plan_id": getattr(release_plan, "id", ""),
            },
        )
        try:
            await self._orchestrator._emit(event)
        except Exception:
            pass


def _measurement_run_metadata(
    config: Any,
    release_plan: Optional[ReleasePlan] = None,
    sprint_index: int = 0,
    sprint: Optional[SprintDefinition] = None,
    sprint_result: Optional[SprintResult] = None,
) -> Dict[str, Any]:
    """生成测量运行的元数据。"""
    import hashlib
    import os

    task_outcomes: List[str] = []
    if sprint_result and sprint_result.task_results:
        task_outcomes = [tr.status.value for tr in sprint_result.task_results]
    outcome_key = ":".join(task_outcomes)
    task_outcome_digest = hashlib.sha256(outcome_key.encode()).hexdigest()[:16] if outcome_key else ""

    ctx_parts = [
        str(sprint_index),
        getattr(sprint, "name", "") if sprint else "",
        getattr(release_plan, "id", "") if release_plan else "",
        outcome_key,
    ]
    ctx_hash = hashlib.sha256("|".join(ctx_parts).encode()).hexdigest()[:16] if any(ctx_parts) else ""

    ci_tags_str = getattr(config, "governance_ci_matrix_tags", "") or ""
    ci_matrix_tags = sorted(t.strip() for t in ci_tags_str.split(",") if t.strip()) if ci_tags_str else []

    config_fingerprint = hashlib.sha256(
        "|".join(
            [
                str(getattr(config, "llm_provider", "")),
                str(getattr(config, "llm_model", "")),
                str(getattr(config, "coding_engine", "")),
                str(getattr(config, "quality_level", "")),
            ]
        ).encode()
    ).hexdigest()[:16]

    from sprintcycle.domain.generic.prompts.prompt_sources import compute_prompt_sources_fingerprint

    prompt_fp = compute_prompt_sources_fingerprint()

    return {
        "sprint_index": sprint_index,
        "sprint_name": getattr(sprint, "name", "") if sprint else "",
        "release_plan_id": getattr(release_plan, "id", "") if release_plan else "",
        "status": sprint_result.status.value if sprint_result else "unknown",
        "task_outcome_digest": task_outcome_digest,
        "measurement_context_hash": ctx_hash,
        "test_command_incremental": getattr(config, "test_command_incremental", ""),
        "ci_matrix_tags": ci_matrix_tags,
        "evolution_llm_model_env": os.environ.get("EVOLUTION_LLM_MODEL", ""),
        "evolution_llm_provider_env": os.environ.get("EVOLUTION_LLM_PROVIDER", ""),
        "llm_provider": getattr(config, "llm_provider", ""),
        "llm_model": getattr(config, "llm_model", ""),
        "coding_engine": getattr(config, "coding_engine", ""),
        "quality_level": getattr(config, "quality_level", ""),
        "dry_run": bool(getattr(config, "dry_run", False)),
        "project_path": getattr(config, "project_path", ""),
        "config_fingerprint": config_fingerprint,
        "release_plan_name": getattr(release_plan.project, "name", "") if release_plan else "",
        "prompt_sources_schema": prompt_fp["prompt_sources_schema"],
        "prompt_sources_aggregate_sha256": prompt_fp["prompt_sources_aggregate_sha256"],
        "prompt_source_digests": prompt_fp["prompt_source_digests"],
    }


__all__ = [
    "SprintLifecycleHooks",
    "TaskLifecycleHooks",
    "create_noop_sprint_hooks",
    "create_chained_sprint_hooks",
    "create_noop_task_hooks",
    "create_chained_task_hooks",
    "_OrchestratorSprintHooks",
    "_measurement_run_metadata",
]
