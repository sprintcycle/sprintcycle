"""缓存端口 - Domain 层与缓存服务的接口

定义缓存后端的协议接口，由 Infrastructure 层实现。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheBackendProtocol(ABC):
    """键值缓存后端协议；值须可被后端序列化"""

    @abstractmethod
    def get(self, key: str) -> Any:
        """获取缓存值，未命中返回 None"""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, *, expire_seconds: Optional[int] = None) -> None:
        """设置缓存值"""
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除单个键；不存在返回 False"""
        ...

    @abstractmethod
    def contains(self, key: str) -> bool:
        """是否存在该键"""
        ...

    @abstractmethod
    def clear(self) -> None:
        """清空全部条目"""
        ...

    @abstractmethod
    def __len__(self) -> int:
        """当前条目数"""
        ...

    def volume_bytes(self) -> int:
        """磁盘或近似占用（字节）；未知时返回 0"""
        return 0

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """用于统计与日志，如 diskcache / redis"""
        ...


# 工厂函数注册
_cache_backend_factory: Optional[callable] = None


def register_cache_backend_factory(factory: callable) -> None:
    """注册缓存后端工厂（由 Infrastructure 层调用）"""
    global _cache_backend_factory
    _cache_backend_factory = factory


def get_cache_backend(runtime: Optional[Any] = None, project_path: str = ".") -> CacheBackendProtocol:
    """获取缓存后端实例"""
    if _cache_backend_factory is not None:
        return _cache_backend_factory(runtime, project_path)
    from sprintcycle.infrastructure.adapters.generic.cache import build_cache_backend as _get
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
    effective_runtime = runtime or RuntimeConfig()
    return _get(effective_runtime, project_path)


__all__ = ["CacheBackendProtocol", "register_cache_backend_factory", "get_cache_backend"]
