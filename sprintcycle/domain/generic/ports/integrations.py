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


# 工厂函数注册
_autogpt_compose_factory: Optional[callable] = None
_autogpt_runtime_factory: Optional[callable] = None
_langgraph_adapter_factory: Optional[callable] = None
_compiled_graph_runtime_factory: Optional[callable] = None
_plan_runtime_factory: Optional[callable] = None
_phoenix_exporter_factory: Optional[callable] = None
_phoenix_trace_factory: Optional[callable] = None


def register_autogpt_compose_factory(factory: callable) -> None:
    global _autogpt_compose_factory
    _autogpt_compose_factory = factory


def register_autogpt_runtime_factory(factory: callable) -> None:
    global _autogpt_runtime_factory
    _autogpt_runtime_factory = factory


def register_langgraph_adapter_factory(factory: callable) -> None:
    global _langgraph_adapter_factory
    _langgraph_adapter_factory = factory


def register_compiled_graph_runtime_factory(factory: callable) -> None:
    global _compiled_graph_runtime_factory
    _compiled_graph_runtime_factory = factory


def register_plan_runtime_factory(factory: callable) -> None:
    global _plan_runtime_factory
    _plan_runtime_factory = factory


def register_phoenix_exporter_factory(factory: callable) -> None:
    global _phoenix_exporter_factory
    _phoenix_exporter_factory = factory


def register_phoenix_trace_factory(factory: callable) -> None:
    global _phoenix_trace_factory
    _phoenix_trace_factory = factory


def build_default_compose_spec(project_name: str = "sprintcycle") -> AutoGPTComposeSpecProtocol:
    if _autogpt_compose_factory is not None:
        return _autogpt_compose_factory(project_name)
    from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.compose import build_default_compose_spec
    return build_default_compose_spec(project_name)


def create_autogpt_runtime_spec(project_name: str = "sprintcycle") -> AutoGPTRuntimeSpecProtocol:
    if _autogpt_runtime_factory is not None:
        return _autogpt_runtime_factory(project_name)
    from sprintcycle.infrastructure.adapters.generic.integrations.autogpt.runtime import AutoGPTRuntimeSpec
    return AutoGPTRuntimeSpec(project_name=project_name)


def create_langgraph_adapter(graph_name: str) -> LangGraphRuntimeAdapterProtocol:
    if _langgraph_adapter_factory is not None:
        return _langgraph_adapter_factory(graph_name)
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.adapter import LangGraphExecutionAdapter
    return LangGraphExecutionAdapter(graph_name=graph_name)


def compile_intent_graph(**kwargs: Any) -> Any:
    """编译 intent graph 并返回运行时对象"""
    if _compiled_graph_runtime_factory is not None:
        return _compiled_graph_runtime_factory(**kwargs)
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import compile_intent_graph as _compile
    return _compile(**kwargs)


def compile_sprint_graph(**kwargs: Any) -> Any:
    """编译 sprint graph 并返回运行时对象"""
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import compile_sprint_graph as _compile
    return _compile(**kwargs)


def create_plan_runtime(project_name: str = "sprintcycle") -> PlanRuntimeProtocol:
    """创建 Plan Runtime 实例"""
    if _plan_runtime_factory is not None:
        return _plan_runtime_factory(project_name)
    from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.plan_runtime import PlanRuntime
    return PlanRuntime(project_name=project_name)


def create_phoenix_exporter_spec(project_name: str = "sprintcycle") -> PhoenixExporterSpecProtocol:
    if _phoenix_exporter_factory is not None:
        return _phoenix_exporter_factory(project_name)
    from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.exporter import PhoenixExporterSpec
    return PhoenixExporterSpec(project_name=project_name)


def create_phoenix_trace_runtime(exporter_spec: PhoenixExporterSpecProtocol) -> PhoenixTraceRuntimeProtocol:
    if _phoenix_trace_factory is not None:
        return _phoenix_trace_factory(exporter_spec)
    from sprintcycle.infrastructure.adapters.generic.integrations.phoenix.trace_runtime import PhoenixTraceRuntime
    return PhoenixTraceRuntime(exporter_spec)


__all__ = [
    "AutoGPTComposeSpecProtocol",
    "AutoGPTRuntimeSpecProtocol",
    "LangGraphRuntimeAdapterProtocol",
    "CompiledGraphRuntimeProtocol",
    "PlanRuntimeProtocol",
    "PhoenixExporterSpecProtocol",
    "PhoenixTraceRuntimeProtocol",
    "register_autogpt_compose_factory",
    "register_autogpt_runtime_factory",
    "register_langgraph_adapter_factory",
    "register_compiled_graph_runtime_factory",
    "register_plan_runtime_factory",
    "register_phoenix_exporter_factory",
    "register_phoenix_trace_factory",
    "build_default_compose_spec",
    "create_autogpt_runtime_spec",
    "create_langgraph_adapter",
    "compile_intent_graph",
    "compile_sprint_graph",
    "create_plan_runtime",
    "create_phoenix_exporter_spec",
    "create_phoenix_trace_runtime",
]
