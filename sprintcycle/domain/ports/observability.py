"""Observability 端口 - Domain 层与可观测性组件的接口

定义可观测性门面和追踪运行时的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ObservabilityEventLike:
    """可观测性事件协议"""
    event_type: str
    message: str
    run_id: Optional[str] = None
    execution_id: Optional[str] = None


class ObservabilityFacadeProtocol(ABC):
    """可观测性门面协议"""

    @abstractmethod
    def record(self, event: Dict[str, Any] | ObservabilityEventLike | str) -> Dict[str, Any]:
        """记录事件"""
        ...

    @abstractmethod
    def record_event(self, event: Dict[str, Any] | ObservabilityEventLike | str) -> Dict[str, Any]:
        """记录事件（record 的别名）"""
        ...

    @abstractmethod
    def list_events(self) -> Dict[str, Any]:
        """列出所有事件"""
        ...

    @abstractmethod
    def list_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """按 run_id 列出事件"""
        ...

    @abstractmethod
    def snapshot(self, run_id: str) -> Any:
        """获取快照"""
        ...

    @abstractmethod
    def trace(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """追踪"""
        ...

    @abstractmethod
    def to_trace_payload(self, run_id: str) -> Dict[str, Any]:
        """转换为追踪负载"""
        ...

    @abstractmethod
    def to_replay_payload(self, run_id: str) -> Dict[str, Any]:
        """转换为重放负载"""
        ...

    @abstractmethod
    def replay(self, execution_id: str) -> Dict[str, Any]:
        """重放"""
        ...


__all__ = [
    "ObservabilityEventLike",
    "ObservabilityFacadeProtocol",
]
