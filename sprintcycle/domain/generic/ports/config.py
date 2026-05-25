"""配置端口 - Domain 层与运行时配置的接口

定义运行时配置的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class RuntimeConfigProtocol(ABC):
    """运行时配置协议接口"""

    @abstractmethod
    def __getattr__(self, item: str) -> Any:
        """获取配置属性"""
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        ...

    @abstractmethod
    def effective_quality_level(self) -> str:
        """获取有效的质量级别"""
        ...

    @classmethod
    @abstractmethod
    def from_project(cls, project_path: str) -> "RuntimeConfigProtocol":
        """从项目目录加载配置"""
        ...


# 工厂函数注册
_runtime_config_factory: Optional[callable] = None


def register_runtime_config_factory(factory: callable) -> None:
    """注册运行时配置工厂（由 Infrastructure 层调用）"""
    global _runtime_config_factory
    _runtime_config_factory = factory


def get_runtime_config(project_path: Optional[str] = None) -> RuntimeConfigProtocol:
    """获取运行时配置实例"""
    if _runtime_config_factory is not None:
        return _runtime_config_factory(project_path)
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
    if project_path:
        return RuntimeConfig.from_project(project_path)
    return RuntimeConfig()


__all__ = ["RuntimeConfigProtocol", "register_runtime_config_factory", "get_runtime_config"]
