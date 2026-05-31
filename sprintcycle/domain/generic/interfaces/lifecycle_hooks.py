"""生命周期钩子协议 - Domain 层定义，Execution 层实现

**精简版**：移除了与 execution/hooks 中重复的协议，统一使用 SprintLifecycleHooks 和 TaskLifecycleHooks。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sprintcycle.domain.generic.models import SprintDefinition, SprintBacklogItem, SprintResult


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
    "ExecutionEventProtocol",
]
