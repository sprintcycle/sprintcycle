"""统一的 Hook 工厂 - 合并 NoOp/Chained 模式

这个模块提供了统一的工厂方法，替代原来分散的 NoOp/Chained 实现。
"""

from __future__ import annotations

from abc import ABC
from typing import Any, Dict, List, Optional, Sequence, TypeVar, Generic

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from sprintcycle.domain.generic.interfaces import SprintResult, TaskResult


T = TypeVar("T", bound=ABC)


class HookFactory:
    """统一的 Hook 工厂 - 提供 NoOp 和 Chain 工厂方法"""
    
    @staticmethod
    def noop(base_class: type[T]) -> T:
        """创建空实现的 Hook
        
        替代分散的 NoOp* 类，统一管理模式。
        """
        name = f"NoOp{base_class.__name__}"
        return type(name, (base_class,), {
            "async def on_before_sprint": lambda self, *args, **kwargs: None,
            "async def on_after_sprint": lambda self, *args, **kwargs: None,
            "async def on_sprint_start": lambda self, *args, **kwargs: None,
            "async def on_sprint_complete": lambda self, *args, **kwargs: None,
            "async def on_task_start": lambda self, *args, **kwargs: None,
            "async def on_task_complete": lambda self, *args, **kwargs: None,
            "async def on_task_error": lambda self, *args, **kwargs: None,
            "async def on_sprint_error": lambda self, *args, **kwargs: None,
            "async def on_after_task_complete": lambda self, *args, **kwargs: None,
        })(base_class)
    
    @staticmethod
    def chain(hooks: Sequence[Any]) -> ChainedHooks:
        """创建链式调用的 Hook
        
        替代分散的 Chained* 类，统一管理模式。
        """
        return ChainedHooks(hooks)


class ChainedHooks:
    """统一的链式 Hook 实现"""
    
    def __init__(self, hooks: Sequence[Any]) -> None:
        self._hooks = tuple(hooks)
    
    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
    ) -> None:
        for h in self._hooks:
            try:
                if hasattr(h, "on_before_sprint"):
                    await h.on_before_sprint(sprint_index, sprint, context, release_plan)
                elif hasattr(h, "on_sprint_start"):
                    await h.on_sprint_start(sprint, sprint_index=sprint_index, context=context, release_plan=release_plan)
            except Exception as e:
                logger.warning("ChainedHooks on_before [{}]: {}", type(h).__name__, e)
    
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
                if hasattr(h, "on_after_sprint"):
                    await h.on_after_sprint(sprint_index, sprint, result, context, release_plan)
                elif hasattr(h, "on_sprint_complete"):
                    await h.on_sprint_complete(sprint, result=result, sprint_index=sprint_index, context=context, release_plan=release_plan)
            except Exception as e:
                logger.warning("ChainedHooks on_after [{}]: {}", type(h).__name__, e)
    
    async def on_after_task_complete(
        self,
        task: SprintBacklogItem,
        sprint_name: str,
        context: Dict[str, Any],
        task_result: TaskResult,
    ) -> None:
        for h in reversed(self._hooks):
            try:
                if hasattr(h, "on_after_task_complete"):
                    await h.on_after_task_complete(task, sprint_name, context, task_result)
                elif hasattr(h, "on_task_complete"):
                    await h.on_task_complete(task, task_result, sprint_name=sprint_name, context=context)
            except Exception as e:
                logger.warning("ChainedHooks on_task [{}]: {}", type(h).__name__, e)


__all__ = ["HookFactory", "ChainedHooks"]
