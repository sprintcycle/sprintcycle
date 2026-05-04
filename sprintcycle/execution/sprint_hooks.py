"""
Sprint 生命周期钩子 — 编排内核（execute_sprints）与横切能力（事件、测量等）解耦。

由 TaskDispatcher 等注册实现；SprintExecutor 在「每个 Sprint 前后」调用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence

from ..prd.models import PRD, PRDSprint
from .sprint_types import SprintResult


class SprintLifecycleHooks(ABC):
    """可选 async 钩子；实现类应吞掉非致命异常或交由调用方策略处理。"""

    @abstractmethod
    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        """即将执行该 Sprint（含 context 已写入 sprint_index / sprint_name / project_goals）。"""

    @abstractmethod
    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        result: SprintResult,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        """该 Sprint 本轮最终结果已确定（含反馈重试后的最终结果）。"""


class NoOpSprintLifecycleHooks(SprintLifecycleHooks):
    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        return None

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        result: SprintResult,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        return None


class ChainedSprintHooks(SprintLifecycleHooks):
    """按顺序调用多个钩子（before 正序，after 逆序）。"""

    def __init__(self, hooks: Sequence[SprintLifecycleHooks]):
        self._hooks = tuple(hooks)

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        for h in self._hooks:
            await h.on_before_sprint(sprint_index, sprint, context, prd)

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        result: SprintResult,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        for h in reversed(self._hooks):
            await h.on_after_sprint(sprint_index, sprint, result, context, prd)
