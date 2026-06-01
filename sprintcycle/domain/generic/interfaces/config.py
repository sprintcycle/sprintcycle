"""Domain 层配置接口协议。

定义配置相关的接口，让 Infrastructure 层实现。
避免 Domain 层直接依赖 Infrastructure 层。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional


class ConfigProtocol(ABC):
    """配置接口协议。"""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """设置配置值。"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        pass

    @classmethod
    @abstractmethod
    def from_project(cls, project_path: str) -> "ConfigProtocol":
        """从项目目录加载配置。"""
        pass


# 便捷函数：从项目加载配置（由 Infrastructure 实现）
_config_loader: Optional["Callable[[str], ConfigProtocol]"] = None


def register_config_loader(loader: "Callable[[str], ConfigProtocol]") -> None:
    """注册配置加载器（由 Infrastructure 层调用）"""
    global _config_loader
    _config_loader = loader


def load_project_config(project_path: str) -> ConfigProtocol:
    """从项目目录加载配置。"""
    if _config_loader is not None:
        return _config_loader(project_path)
    raise RuntimeError(
        "配置加载器未注册。请先调用 register_config_loader() 注册配置加载器。"
    )
