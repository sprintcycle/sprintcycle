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


__all__ = [
    "PlatformLaunchServiceProtocol",
]
