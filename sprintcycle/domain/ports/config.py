"""配置端口 - Domain 层与运行时配置的接口

定义运行时配置的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


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


__all__ = ["RuntimeConfigProtocol"]
