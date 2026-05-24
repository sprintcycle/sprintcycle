"""生命周期钩子协议 - Domain 层定义，Execution 层实现"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sprintcycle.domain.generic.models import SprintDefinition, SprintBacklogItem, SprintResult


class SprintLifecycleHookProtocol(ABC):
    """Sprint 生命周期钩子接口"""
    
    def on_sprint_start(self, sprint: "SprintDefinition", **kwargs: Any) -> None:
        """Sprint 开始钩子"""
        ...
    
    def on_sprint_complete(
        self,
        sprint: "SprintDefinition",
        result: "SprintResult",
        **kwargs: Any,
    ) -> None:
        """Sprint 完成钩子"""
        ...
    
    def on_sprint_error(
        self,
        sprint: "SprintDefinition",
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """Sprint 错误钩子"""
        ...


class TaskLifecycleHookProtocol(ABC):
    """任务生命周期钩子接口"""
    
    def on_task_start(self, task: "SprintBacklogItem", **kwargs: Any) -> None:
        """任务开始钩子"""
        ...
    
    def on_task_complete(
        self,
        task: "SprintBacklogItem",
        result: "Dict[str, Any]",
        **kwargs: Any,
    ) -> None:
        """任务完成钩子"""
        ...
    
    def on_task_error(
        self,
        task: "SprintBacklogItem",
        error: Exception,
        **kwargs: Any,
    ) -> None:
        """任务错误钩子"""
        ...


class ExecutionEventProtocol(ABC):
    """执行事件协议"""
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件类型"""
        ...
    
    @property
    @abstractmethod
    def execution_id(self) -> Optional[str]:
        """执行ID"""
        ...
    
    @property
    @abstractmethod
    def timestamp(self) -> datetime:
        """时间戳"""
        ...
    
    @property
    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """事件数据"""
        ...


__all__ = [
    "SprintLifecycleHookProtocol",
    "TaskLifecycleHookProtocol",
    "ExecutionEventProtocol",
]
