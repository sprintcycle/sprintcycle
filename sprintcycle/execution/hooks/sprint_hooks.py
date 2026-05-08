"""
Sprint 生命周期钩子 — 编排内核（execute_sprints）与横切能力（事件、测量等）解耦。

由 ``SprintOrchestrator`` 等注册实现；SprintExecutor 在「每个 Sprint 前后」调用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence

from loguru import logger

from ...release_plan.models import ReleasePlan, SprintDefinition
from ..sprint_types import SprintResult


class SprintLifecycleHooks(ABC):
    @abstractmethod
    async def on_before_sprint(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        pass

    @abstractmethod
    async def on_after_sprint(self, sprint_index: int, sprint: SprintDefinition, result: SprintResult, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        pass

    async def after_plan(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        return None

    async def before_review(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        return None

    async def after_retro(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        return None


class NoOpSprintLifecycleHooks(SprintLifecycleHooks):
    async def on_before_sprint(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        return None

    async def on_after_sprint(self, sprint_index: int, sprint: SprintDefinition, result: SprintResult, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        return None


class ChainedSprintHooks(SprintLifecycleHooks):
    def __init__(self, hooks: Sequence[SprintLifecycleHooks]):
        self._hooks = tuple(hooks)

    async def on_before_sprint(self, sprint_index: int, sprint: SprintDefinition, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        for h in self._hooks:
            try:
                await h.on_before_sprint(sprint_index, sprint, context, release_plan)
            except Exception as e:
                logger.warning("ChainedSprintHooks on_before [{}]: {}", type(h).__name__, e)

    async def on_after_sprint(self, sprint_index: int, sprint: SprintDefinition, result: SprintResult, context: Dict[str, Any], release_plan: Optional[ReleasePlan]) -> None:
        for h in reversed(self._hooks):
            try:
                await h.on_after_sprint(sprint_index, sprint, result, context, release_plan)
            except Exception as e:
                logger.warning("ChainedSprintHooks on_after [{}]: {}", type(h).__name__, e)
