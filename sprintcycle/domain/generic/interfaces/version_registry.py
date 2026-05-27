"""版本注册表协议 - Domain 层定义接口，Infrastructure 层实现"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VersionRegistryProtocol(ABC):
    """版本注册表接口"""

    @abstractmethod
    def register(self, version: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """注册新版本"""
        ...

    @abstractmethod
    def get_active(self) -> Optional[str]:
        """获取当前活跃版本"""
        ...

    @abstractmethod
    def list_versions(self) -> List[str]:
        """列出所有版本"""
        ...

    @abstractmethod
    def get_metadata(self, version: str) -> Optional[Dict[str, Any]]:
        """获取版本元数据"""
        ...


class RollbackManagerProtocol(ABC):
    """回滚管理器接口"""

    @abstractmethod
    def prepare(self, version: str) -> str:
        """准备回滚到指定版本，返回 variant ID"""
        ...

    @abstractmethod
    def commit(self, variant_id: str) -> None:
        """提交回滚"""
        ...

    @abstractmethod
    def rollback(self, variant_id: str) -> None:
        """执行回滚"""
        ...

    @abstractmethod
    def cleanup(self, variant_id: str) -> None:
        """清理回滚快照"""
        ...


__all__ = [
    "VersionRegistryProtocol",
    "RollbackManagerProtocol",
]
