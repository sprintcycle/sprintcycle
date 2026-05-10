"""缓存后端抽象 — 默认 diskcache，可选 Redis。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheBackend(ABC):
    """键值缓存后端；值须可被后端序列化（diskcache: pickle；Redis: pickle）。"""

    @abstractmethod
    def get(self, key: str) -> Any:
        """未命中返回 None。"""

    @abstractmethod
    def set(self, key: str, value: Any, *, expire_seconds: Optional[int] = None) -> None:
        """expire_seconds 为 None 时表示默认永不过期（由上层 ExecutionCache 传入 TTL）。"""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除单个键；不存在返回 False。"""

    @abstractmethod
    def contains(self, key: str) -> bool:
        """是否存在该键。"""

    @abstractmethod
    def clear(self) -> None:
        """清空全部条目。"""

    @abstractmethod
    def __len__(self) -> int:
        """当前条目数。"""

    def volume_bytes(self) -> int:
        """磁盘或近似占用（字节）；未知时返回 0。"""
        return 0

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """用于统计与日志，如 diskcache / redis。"""


__all__ = ["CacheBackend"]
