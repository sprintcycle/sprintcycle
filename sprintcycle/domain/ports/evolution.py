"""Evolution 端口 - Domain 层与进化版本管理的接口

定义进化版本管理的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EvolutionRegistryProtocol(ABC):
    """进化版本注册表协议"""

    @abstractmethod
    async def list_versions(self, target: Optional[str] = None, limit: int = 20) -> List[Any]:
        """列出版本"""
        ...

    @abstractmethod
    async def get_active(self, target: str) -> Optional[Any]:
        """获取活跃版本"""
        ...

    @abstractmethod
    async def export_manifest_index(self) -> Dict[str, Any]:
        """导出清单索引"""
        ...


class VersionManifestProtocol(ABC):
    """版本清单协议"""

    @abstractmethod
    async def get_version_manifest_summary(self, registry: Any, version_id: str) -> Dict[str, Any]:
        """获取版本清单摘要"""
        ...


__all__ = [
    "EvolutionRegistryProtocol",
    "VersionManifestProtocol",
]
