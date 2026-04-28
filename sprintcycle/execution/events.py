"""
事件总线 - 执行过程中的事件通知

事件类型：
- on_execution_start: 执行开始
- on_sprint_start: Sprint 开始
- on_sprint_complete: Sprint 完成
- on_task_start: 任务开始
- on_task_complete: 任务完成
- on_task_failed: 任务失败
- on_evolution_candidate: 发现进化候选
- on_execution_complete: 执行完成
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    EXECUTION_START = "execution_start"
    SPRINT_START = "sprint_start"
    SPRINT_COMPLETE = "sprint_complete"
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    EVOLUTION_CANDIDATE = "evolution_candidate"
    EXECUTION_COMPLETE = "execution_complete"


@dataclass
class Event:
    """事件数据类"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        return f"Event({self.type.value}, {self.timestamp.isoformat()})"


class EventBus:
    """
    事件总线
    
    提供事件注册、触发机制，支持同步/异步事件处理。
    采用发布-订阅模式，事件处理器错误不会影响主流程。
    """
    
    def __init__(self):
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
