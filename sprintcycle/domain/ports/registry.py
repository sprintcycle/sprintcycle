"""Registry 端口 - Domain 层与运行时注册表的接口

定义运行时注册表的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class RuntimeRegistryProtocol(ABC):
    """运行时注册表协议"""

    @abstractmethod
    def register(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """注册运行时实例"""
        ...

    @abstractmethod
    def get(self, runtime_id: str) -> Optional[Dict[str, Any]]:
        """获取运行时实例"""
        ...

    @property
    def records(self) -> List[Dict[str, Any]]:
        """获取所有记录"""
        ...


__all__ = [
    "RuntimeRegistryProtocol",
]
