"""
任务级生命周期钩子（每个 Sprint Backlog 项执行完成后调用）。

与 ``SprintLifecycleHooks``（Sprint 边界）正交；默认 **NoOp**，无性能开销。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Sequence

from loguru import logger

from sprintcycle.domain.generic.models import SprintBacklogItem
from sprintcycle.domain.generic.interfaces import TaskResult


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


class NoOpTaskLifecycleHooks(TaskLifecycleHooks):
    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        return None


class ChainedTaskHooks(TaskLifecycleHooks):
    """逆序调用 on_after（与常见资源释放语义一致：后注册先执行）。"""

    def __init__(self, hooks: Sequence[TaskLifecycleHooks]):
        self._hooks = tuple(hooks)

    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        for h in reversed(self._hooks):
            try:
                await h.on_after_task_complete(task, sprint_name, context, task_result)
            except Exception as e:
                logger.warning("ChainedTaskHooks on_after [{}]: {}", type(h).__name__, e)
