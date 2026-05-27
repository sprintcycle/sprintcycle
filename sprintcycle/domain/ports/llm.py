"""LLM 引擎适配器端口 - Domain 层与编码引擎的接口

定义 LLM 引擎适配器的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class EngineResult:
    """引擎执行结果"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    request_id: str = ""
    trace_id: str = ""


@dataclass
class EngineAdapterConfig:
    """引擎适配器配置"""
    timeout_seconds: int = 900
    cwd: str = "."
    max_output_chars: int = 20000


class EngineAdapterProtocol(ABC):
    """LLM 引擎适配器协议"""

    name: str

    @abstractmethod
    async def execute(self, prompt: str, context: Dict[str, Any]) -> EngineResult:
        """执行引擎调用"""
        ...


# 工厂函数注册
_engine_adapter_factory: Optional[callable] = None


def register_engine_adapter_factory(factory: callable) -> None:
    """注册引擎适配器工厂（由 Infrastructure 层调用）"""
    global _engine_adapter_factory
    _engine_adapter_factory = factory


def resolve_engine_adapter(
    engine: str,
    config: EngineAdapterConfig,
) -> EngineAdapterProtocol:
    """解析引擎适配器"""
    if _engine_adapter_factory is not None:
        return _engine_adapter_factory(engine, config)
    raise RuntimeError(
        "Engine adapter factory not registered. "
        "Please call register_engine_adapter_factory() from Infrastructure layer before using."
    )


__all__ = [
    "EngineResult",
    "EngineAdapterConfig",
    "EngineAdapterProtocol",
    "register_engine_adapter_factory",
    "resolve_engine_adapter",
]
