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


__all__ = [
    "EngineResult",
    "EngineAdapterConfig",
    "EngineAdapterProtocol",
]
