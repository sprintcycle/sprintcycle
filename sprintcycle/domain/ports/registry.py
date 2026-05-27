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


# 工厂函数注册
_runtime_registry_factory: Optional[callable] = None


def register_runtime_registry_factory(factory: callable) -> None:
    """注册运行时注册表工厂（由 Infrastructure 层调用）"""
    global _runtime_registry_factory
    _runtime_registry_factory = factory


def create_runtime_registry(config: Any) -> RuntimeRegistryProtocol:
    """创建运行时注册表实例"""
    if _runtime_registry_factory is not None:
        return _runtime_registry_factory(config)
    raise RuntimeError(
        "Runtime registry factory not registered. "
        "Please call register_runtime_registry_factory() from Infrastructure layer before using."
    )


__all__ = [
    "RuntimeRegistryProtocol",
    "register_runtime_registry_factory",
    "create_runtime_registry",
]
