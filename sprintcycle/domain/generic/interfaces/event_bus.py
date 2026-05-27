"""事件总线协议 - Domain 层定义，Infrastructure 层实现"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """事件类型"""
    SPRINT_STARTED = "sprint_started"
    SPRINT_COMPLETED = "sprint_completed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    ERROR = "error"
    CUSTOM = "custom"


@dataclass
class Event:
    """事件"""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    execution_id: Optional[str] = None


class EventSubscriber(ABC):
    """事件订阅者接口"""

    @abstractmethod
    def handle(self, event: Event) -> None:
        """处理事件"""
        ...


class EventBusProtocol(ABC):
    """事件总线接口"""

    @abstractmethod
    def publish(self, event: Event) -> None:
        """发布事件"""
        ...

    @abstractmethod
    def subscribe(self, event_type: EventType, subscriber: EventSubscriber) -> None:
        """订阅事件"""
        ...

    @abstractmethod
    def unsubscribe(self, event_type: EventType, subscriber: EventSubscriber) -> None:
        """取消订阅"""
        ...



class ExecutionEventBackendProtocol(ABC):
    """执行事件后端接口"""

    @abstractmethod
    def publish(self, event: Event) -> None:
        """发布事件"""
        ...

    @abstractmethod
    def get_events(self, execution_id: str, limit: int = 100) -> List[Event]:
        """获取事件"""
        ...


__all__ = [
    "EventType",
    "Event",
    "EventSubscriber",
    "EventBusProtocol",
    "ExecutionEventBackendProtocol",
]
