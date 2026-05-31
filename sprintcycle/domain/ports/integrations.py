"""集成适配器端口 - Domain 层与外部集成组件的接口

定义各种集成适配器的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class LangGraphRuntimeAdapterProtocol(ABC):
    """LangGraph 运行时适配器协议"""

    @abstractmethod
    def build_graph(self) -> Dict[str, Any]:
        """构建执行图"""
        ...


__all__ = [
    "LangGraphRuntimeAdapterProtocol",
]
