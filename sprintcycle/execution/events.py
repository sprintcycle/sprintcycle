"""
事件总线 - 执行过程中的事件通知

事件类型：
- execution_start: 执行开始
- sprint_start: Sprint 开始
- sprint_complete: Sprint 完成
- sprint_failed: Sprint 失败
- task_start: 任务开始
- task_complete: 任务完成
- task_failed: 任务失败
- execution_complete: 执行完成
- execution_failed: 执行失败
- evolution_candidate: 发现进化候选
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    EXECUTION_START = "execution_start"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_FAILED = "execution_failed"
    SPRINT_START = "sprint_start"
    SPRINT_COMPLETE = "sprint_complete"
    SPRINT_FAILED = "sprint_failed"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    EVOLUTION_CANDIDATE = "evolution_candidate"


@dataclass
class Event:
    """事件数据类"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        ts = self.timestamp.isoformat() if self.timestamp else "none"
        return f"Event({self.type.value}, {ts})"
    
    def to_sse_dict(self) -> Dict[str, Any]:
        """转换为适合SSE推送的字典"""
        return {
            "event_type": self.type.value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            **self.data,
        }
    
    def to_sse_message(self) -> str:
        """转换为SSE格式的消息"""
        event_name = self.type.value
        data = self.to_sse_dict()
        return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class EventBus:
    """
    事件总线
    
    提供事件注册、触发机制，支持同步/异步事件处理。
    采用发布-订阅模式，事件处理器错误不会影响主流程。
    """
    
    def __init__(self) -> None:
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._once_handlers: Dict[EventType, List[Callable]] = {}
    
    def on(self, event_type: EventType, handler: Callable) -> "EventBus":
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            EventBus: 支持链式调用
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
        return self
    
    def once(self, event_type: EventType, handler: Callable) -> "EventBus":
        """
        注册一次性事件处理器（触发后自动移除）
        
        Args:
            event_type: 事件类型
            handler: 事件处理函数
            
        Returns:
            EventBus: 支持链式调用
        """
        if event_type not in self._once_handlers:
            self._once_handlers[event_type] = []
        if handler not in self._once_handlers[event_type]:
            self._once_handlers[event_type].append(handler)
        return self
    
    def off(self, event_type: EventType, handler: Optional[Callable] = None) -> "EventBus":
        """
        移除事件处理器
        
        Args:
            event_type: 事件类型
            handler: 特定处理函数，不传则移除该类型所有处理器
            
        Returns:
            EventBus: 支持链式调用
        """
        if handler is None:
            self._handlers[event_type] = []
            if event_type in self._once_handlers:
                self._once_handlers[event_type] = []
        else:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                except ValueError:
                    pass
            if event_type in self._once_handlers:
                try:
                    self._once_handlers[event_type].remove(handler)
                except ValueError:
                    pass
        return self
    
    async def emit(self, event: Event) -> None:
        """
        异步触发事件
        
        Args:
            event: 事件对象
        """
        # 先执行普通处理器
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            await self._safe_call(handler, event)
        
        # 再执行一次性处理器，并移除
        once_handlers = self._once_handlers.get(event.type, [])
        for handler in once_handlers:
            await self._safe_call(handler, event)
        self._once_handlers[event.type] = []
    
    def emit_sync(self, event: Event) -> None:
        """
        同步触发事件（用于非异步场景）
        
        Args:
            event: 事件对象
        """
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            self._safe_call_sync(handler, event)
        
        once_handlers = self._once_handlers.get(event.type, [])
        for handler in once_handlers:
            self._safe_call_sync(handler, event)
        self._once_handlers[event.type] = []
    
    async def _safe_call(self, handler: Callable, event: Event) -> None:
        """安全调用异步处理器"""
        try:
            result = handler(event)
            if hasattr(result, '__await__'):
                await result
        except Exception as e:
            logger.error(f"Event handler error for {event.type.value}: {e}")
    
    def _safe_call_sync(self, handler: Callable, event: Event) -> None:
        """安全调用同步处理器"""
        try:
            handler(event)
        except Exception as e:
            logger.error(f"Event handler error for {event.type.value}: {e}")
    
    def clear(self) -> None:
        """清除所有事件处理器"""
        self._handlers.clear()
        self._once_handlers.clear()
    
    def has_listeners(self, event_type: EventType) -> bool:
        """检查是否有监听器"""
        return bool(
            self._handlers.get(event_type, []) or 
            self._once_handlers.get(event_type, [])
        )


# 全局默认事件总线实例
_default_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取默认事件总线实例"""
    global _default_event_bus
    if _default_event_bus is None:
        _default_event_bus = EventBus()
    return _default_event_bus


def reset_event_bus() -> EventBus:
    """重置事件总线（用于测试）"""
    global _default_event_bus
    _default_event_bus = EventBus()
    return _default_event_bus


# 便捷的事件创建函数
def create_event(
    event_type: EventType,
    sprint_number: Optional[int] = None,
    sprint_name: Optional[str] = None,
    agent_type: Optional[str] = None,
    task: Optional[str] = None,
    status: Optional[str] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    execution_id: Optional[str] = None,
    duration: Optional[float] = None,
    **extra: Any,
) -> Event:
    """创建Sprint执行相关的事件"""
    data: Dict[str, Any] = {
        k: v for k, v in {
            "sprint_number": sprint_number,
            "sprint_name": sprint_name,
            "agent_type": agent_type,
            "task": task,
            "status": status,
            "message": message,
            "error": error,
            "execution_id": execution_id,
            "duration": duration,
        }.items() if v is not None
    }
    data.update(extra)
    return Event(type=event_type, data=data)
