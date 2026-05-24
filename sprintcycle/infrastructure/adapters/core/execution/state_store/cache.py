"""
Agent 执行结果缓存 - 基于 DiskCache 的持久化缓存机制

功能：
1. 基于任务哈希的缓存机制
2. 支持缓存失效策略（TTL、手动失效）
3. 缓存统计和监控
4. 通过 ``CacheBackend`` 持久化（默认 diskcache / SQLite）
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, TypeVar

from loguru import logger

from sprintcycle.infrastructure.adapters.generic.cache.base import CacheBackend
from sprintcycle.infrastructure.adapters.generic.cache.disk import DiskCacheBackend

if TYPE_CHECKING:
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig

T = TypeVar("T")


@dataclass
class CacheEntry:
    """
    缓存条目（保留用于向后兼容）

    内部实现已迁移到 DiskCache，此类仅用于保持 API 兼容
    """

    key: str
    value: Any
    ttl_hours: int = 24
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

    @property
    def ttl(self) -> timedelta:
        """获取 TTL 时长"""
        return timedelta(hours=self.ttl_hours)

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() - self.created_at > self.ttl

    @property
    def age_hours(self) -> float:
        """获取缓存年龄（小时）"""
        return (datetime.now() - self.created_at).total_seconds() / 3600

    def touch(self):
        """更新访问时间"""
        self.last_accessed = datetime.now()
        self.hit_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "created_at": self.created_at.isoformat(),
            "ttl_hours": self.ttl_hours,
            "is_expired": self.is_expired,
            "hit_count": self.hit_count,
            "last_accessed": self.last_accessed.isoformat(),
            "age_hours": round(self.age_hours, 2),
        }


class ExecutionCache:
    """
    Agent 执行结果缓存

    提供基于任务哈希的缓存机制，支持：
    1. TTL 自动过期
    2. 手动失效
    3. LRU 淘汰策略
    4. 缓存统计

    底层由 ``CacheBackend`` 实现（默认 diskcache，可由 ``configure_execution_cache_from_runtime`` 切换为 Redis 等）。
    """

    def __init__(
        self,
        cache_dir: str = ".sprintcycle/cache",
        ttl_hours: int = 24,
        max_entries: int = 1000,
        enable_persistence: bool = True,
        backend: Optional[CacheBackend] = None,
    ):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录（diskcache 默认后端时使用；传入 ``backend`` 时仍作展示路径）
            ttl_hours: 默认 TTL（小时）
            max_entries: 最大缓存条目数（默认 disk 后端 LRU 估算）
            enable_persistence: 是否创建目录（仅默认 disk 后端且无注入 ``backend`` 时）
            backend: 注入的后端；为 None 时在 ``cache_dir`` 下构造 ``DiskCacheBackend``
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl_hours = ttl_hours
        self.max_entries = max_entries
        self.enable_persistence = enable_persistence

        # 异步锁
        self._lock = asyncio.Lock()

        if backend is not None:
            self._backend = backend
        else:
            if self.enable_persistence:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._backend = DiskCacheBackend(str(self.cache_dir), max_entries=max_entries)

        # 统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
            "evictions": 0,
        }

        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None

    def _generate_hash(self, task_key: str) -> str:
        """生成任务哈希"""
        return hashlib.sha256(task_key.encode()).hexdigest()[:32]

    def _make_task_key(self, agent_type: str, task: str, context_hash: Optional[str] = None, **kwargs) -> str:
        """
        生成任务缓存键

        Args:
            agent_type: Agent 类型
            task: 任务描述
            context_hash: 上下文哈希
            **kwargs: 其他参数

        Returns:
            str: 缓存键
        """
        key_parts = [agent_type, task]

        if context_hash:
            key_parts.append(context_hash)

        # 添加其他关键参数
        for k, v in sorted(kwargs.items()):
            if k not in ("self", "ttl_hours"):
                key_parts.append(f"{k}={v}")

        return "|".join(key_parts)

    def get(self, task_hash: str) -> Optional[Any]:
        """
        获取缓存结果

        Args:
            task_hash: 任务哈希

        Returns:
            Optional[Any]: 缓存结果，如果不存在或已过期返回 None
        """
        value = self._backend.get(task_hash)
        if value is None:
            self._stats["misses"] += 1
            logger.debug(f"Cache miss: {task_hash[:8]}")
            return None
        self._stats["hits"] += 1
        logger.debug(f"Cache hit: {task_hash[:8]}")
        return value

    async def get_async(self, task_hash: str) -> Optional[Any]:
        """异步获取缓存"""
        async with self._lock:
            return self.get(task_hash)

    def set(self, task_hash: str, value: Any, ttl_hours: Optional[int] = None) -> None:
        """
        设置缓存

        Args:
            task_hash: 任务哈希
            value: 缓存值
            ttl_hours: TTL 小时数（可选）
        """
        ttl = ttl_hours if ttl_hours is not None else self.default_ttl_hours
        ttl_seconds = ttl * 3600

        self._backend.set(task_hash, value, expire_seconds=ttl_seconds)
        self._stats["sets"] += 1
        logger.debug(f"Cache set: {task_hash[:8]} (TTL={ttl}h)")

    async def set_async(self, task_hash: str, value: Any, ttl_hours: Optional[int] = None) -> None:
        """异步设置缓存"""
        async with self._lock:
            self.set(task_hash, value, ttl_hours)

    def invalidate(self, task_hash: Optional[str] = None) -> int:
        """
        失效缓存

        Args:
            task_hash: 任务哈希（None 表示清空所有缓存）

        Returns:
            int: 失效的条目数
        """
        if task_hash is None:
            count = len(self._backend)
            self._backend.clear()
            self._stats["invalidations"] += count
            logger.info(f"Cache cleared: {count} entries removed")
            return count

        if self._backend.delete(task_hash):
            self._stats["invalidations"] += 1
            logger.debug(f"Cache invalidated: {task_hash[:8]}")
            return 1
        return 0

    async def invalidate_async(self, task_hash: Optional[str] = None) -> int:
        """异步失效缓存"""
        async with self._lock:
            return self.invalidate(task_hash)

    @property
    def stats(self) -> Dict[str, Any]:
        """
        获取缓存统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests * 100 if total_requests > 0 else 0
        hit_rate_percentage = round(hit_rate, 2)

        cache_size = len(self._backend)

        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate_percentage,
            "cache_size": cache_size,
            "max_entries": self.max_entries,
            "memory_usage_estimate_mb": self._estimate_memory_usage(),
            "utilization": round(cache_size / self.max_entries * 100, 2) if self.max_entries > 0 else 0,
            "backend": self._backend.backend_name,
        }

    def _estimate_memory_usage(self) -> float:
        """估算内存使用（MB）"""
        try:
            return round(self._backend.volume_bytes() / 1024 / 1024, 2)
        except Exception:
            return 0.0

    def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            int: 清理的条目数
        """
        # DiskCache 自动处理过期，无需手动清理
        return 0

    async def cleanup_expired_async(self) -> int:
        """异步清理过期缓存"""
        async with self._lock:
            return self.cleanup_expired()

    async def start_cleanup_task(self, interval_hours: int = 1) -> None:
        """
        启动定期清理任务

        Args:
            interval_hours: 清理间隔（小时）
        """

        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval_hours * 3600)
                async with self._lock:
                    self.cleanup_expired()

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started cache cleanup task (interval={interval_hours}h)")

    def __len__(self) -> int:
        """返回缓存条目数"""
        return len(self._backend)


# 全局缓存实例
_global_cache: Optional[ExecutionCache] = None


def get_cache() -> ExecutionCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = ExecutionCache()
    return _global_cache


def set_cache(cache: ExecutionCache) -> None:
    """设置全局缓存实例"""
    global _global_cache
    _global_cache = cache


def configure_execution_cache_from_runtime(runtime: "RuntimeConfig", project_path: str) -> None:
    """
    按 ``RuntimeConfig`` 重建全局 ``ExecutionCache``（含 diskcache / redis / disabled）。

    在 ``SprintCycle`` 初始化时调用；多项目同进程时以后实例为准。
    """
    from sprintcycle.infrastructure.adapters.generic.cache.factory import build_cache_backend, resolve_cache_dir_for_project

    backend = build_cache_backend(runtime, project_path)
    cache_dir = str(resolve_cache_dir_for_project(runtime, project_path))
    ttl = runtime.cache_default_ttl_hours
    max_entries = runtime.cache_max_entries
    set_cache(
        ExecutionCache(
            cache_dir=cache_dir,
            ttl_hours=int(ttl) if ttl is not None else 24,
            max_entries=max(1, int(max_entries)) if max_entries is not None else 1000,
            backend=backend,
        )
    )


__all__ = [
    "ExecutionCache",
    "CacheEntry",
    "get_cache",
    "set_cache",
    "configure_execution_cache_from_runtime",
]
