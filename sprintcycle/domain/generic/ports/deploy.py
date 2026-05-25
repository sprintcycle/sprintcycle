"""Deploy 端口 - Domain 层与平台部署服务的接口

定义平台部署服务的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class PlatformLaunchServiceProtocol(ABC):
    """平台启动服务协议"""

    @abstractmethod
    def launch(self, contract: Dict[str, Any], launch_mode: str = "auto", platform: str = "dashboard") -> Dict[str, Any]:
        """启动平台"""
        ...


# 工厂函数注册
_platform_launch_factory: Optional[callable] = None


def register_platform_launch_factory(factory: callable) -> None:
    """注册平台启动服务工厂（由 Infrastructure 层调用）"""
    global _platform_launch_factory
    _platform_launch_factory = factory


def create_platform_launch_service() -> PlatformLaunchServiceProtocol:
    """创建平台启动服务实例"""
    if _platform_launch_factory is not None:
        return _platform_launch_factory()
    raise RuntimeError(
        "Platform launch factory not registered. "
        "Please call register_platform_launch_factory() from Infrastructure layer before using."
    )


__all__ = [
    "PlatformLaunchServiceProtocol",
    "register_platform_launch_factory",
    "create_platform_launch_service",
]
