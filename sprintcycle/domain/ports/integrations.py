"""集成适配器端口 - Domain 层与外部集成组件的接口

定义各种集成适配器的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AutoGPTComposeSpecProtocol(ABC):
    """AutoGPT Compose 规格协议"""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...


class AutoGPTRuntimeSpecProtocol(ABC):
    """AutoGPT Runtime 规格协议"""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...


class LangGraphRuntimeAdapterProtocol(ABC):
    """LangGraph 运行时适配器协议"""

    @abstractmethod
    def build_graph(self) -> Dict[str, Any]:
        """构建执行图"""
        ...


class CompiledGraphRuntimeProtocol(ABC):
    """编译后的 LangGraph 运行时协议"""

    @abstractmethod
    def compile_intent_graph(self, **kwargs: Any) -> Any:
        """编译 intent graph"""
        ...

    @abstractmethod
    def compile_sprint_graph(self, **kwargs: Any) -> Any:
        """编译 sprint graph"""
        ...


class PlanRuntimeProtocol(ABC):
    """Plan Runtime 协议"""

    @abstractmethod
    def build_release_plan_from_intent(self, intent: str, context: Dict[str, Any]) -> Any:
        """从意图构建发布计划"""
        ...


class PhoenixExporterSpecProtocol(ABC):
    """Phoenix Exporter 规格协议"""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...


class PhoenixTraceRuntimeProtocol(ABC):
    """Phoenix Trace 运行时协议"""

    @abstractmethod
    def build(self) -> Dict[str, Any]:
        """构建追踪运行时"""
        ...

    @abstractmethod
    def emit_trace(self, events: list) -> Dict[str, Any]:
        """发送追踪事件"""
        ...


__all__ = [
    "AutoGPTComposeSpecProtocol",
    "AutoGPTRuntimeSpecProtocol",
    "LangGraphRuntimeAdapterProtocol",
    "CompiledGraphRuntimeProtocol",
    "PlanRuntimeProtocol",
    "PhoenixExporterSpecProtocol",
    "PhoenixTraceRuntimeProtocol",
]
