"""
任务级生命周期钩子（每个 Sprint Backlog 项执行完成后调用）。

与 ``SprintLifecycleHooks``（Sprint 边界）正交；默认 **NoOp**，无性能开销。

**精简版**：移除了重复的 NoOp/Chained 类，统一使用 HookFactory。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Sequence

from loguru import logger

from sprintcycle.domain.generic.models import SprintBacklogItem
from sprintcycle.domain.generic.interfaces import TaskResult
from sprintcycle.domain.generic.interfaces.hook_factory import HookFactory, ChainedHooks


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


# === 使用 HookFactory 创建标准实现 ===

def create_noop_task_hooks() -> TaskLifecycleHooks:
    """创建空实现的 Task 钩子"""
    return HookFactory.noop(TaskLifecycleHooks)


def create_chained_task_hooks(hooks: Sequence[TaskLifecycleHooks]) -> ChainedHooks:
    """创建链式调用的 Task 钩子"""
    return HookFactory.chain(hooks)
