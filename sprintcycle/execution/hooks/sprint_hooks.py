"""
Sprint 生命周期钩子 — 编排内核（execute_sprints）与横切能力（事件、测量等）解耦。

由 ``SprintOrchestrator`` 等注册实现；SprintExecutor 在「每个 Sprint 前后」调用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger

from sprintcycle.domain.models import ReleasePlan, SprintDefinition
from ..core.sprint_types import SprintResult


class SprintLifecycleHooks(ABC):
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


class NoOpSprintLifecycleHooks(SprintLifecycleHooks):
    async def on_before_sprint(
        self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]
    ) -> None:
        return None

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        return None


class ChainedSprintHooks(SprintLifecycleHooks):
    def __init__(self, hooks: Sequence[SprintLifecycleHooks]):
        self._hooks = tuple(hooks)

    async def on_before_sprint(
        self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]
    ) -> None:
        for h in self._hooks:
            try:
                await h.on_before_sprint(sprint_index, sprint, context, release_plan)
            except Exception as e:
                logger.warning("ChainedSprintHooks on_before [{}]: {}", type(h).__name__, e)

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        for h in reversed(self._hooks):
            try:
                await h.on_after_sprint(sprint_index, sprint, result, context, release_plan)
            except Exception as e:
                logger.warning("ChainedSprintHooks on_after [{}]: {}", type(h).__name__, e)


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
        # 发射 sprint 开始事件
        from ..events import Event, EventType

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
        # 发射 sprint 完成事件
        from ..events import Event, EventType

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

    # Task outcome digest
    task_outcomes: List[str] = []
    if sprint_result and sprint_result.task_results:
        task_outcomes = [tr.status.value for tr in sprint_result.task_results]
    outcome_key = ":".join(task_outcomes)
    task_outcome_digest = hashlib.sha256(outcome_key.encode()).hexdigest()[:16] if outcome_key else ""

    # Context hash
    ctx_parts = [
        str(sprint_index),
        getattr(sprint, "name", "") if sprint else "",
        getattr(release_plan, "id", "") if release_plan else "",
        outcome_key,
    ]
    ctx_hash = hashlib.sha256("|".join(ctx_parts).encode()).hexdigest()[:16] if any(ctx_parts) else ""

    # CI matrix tags
    ci_tags_str = getattr(config, "governance_ci_matrix_tags", "") or ""
    ci_matrix_tags = sorted(t.strip() for t in ci_tags_str.split(",") if t.strip()) if ci_tags_str else []

    # Config fingerprint
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

    # Prompt sources fingerprint
    from sprintcycle.domain.prompts.prompt_sources import compute_prompt_sources_fingerprint

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
        # Config-derived fields
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
