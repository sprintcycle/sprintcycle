"""
Agent 执行结果缓存 - 基于任务哈希的缓存机制

功能：
1. 基于任务哈希的缓存机制
2. 支持缓存失效策略（TTL、手动失效）
3. 缓存统计和监控
"""

import asyncio
import hashlib
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from collections import OrderedDict
from typing import Any, Dict, List, Optional, TypeVar

from .sprint_executor import TaskResult

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEntry:
    """缓存条目"""
    
    def __init__(
        self,
        key: str,
        value: Any,
        ttl_hours: int = 24,
        created_at: Optional[datetime] = None
    ):
        self.key = key
        self.value = value
        self.created_at = created_at or datetime.now()
        self.ttl = timedelta(hours=ttl_hours)
        self.hit_count = 0
        self.last_accessed = self.created_at
    
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
            "ttl_hours": self.ttl.total_seconds() / 3600,
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
    """
    
    def __init__(
        self,
        cache_dir: str = ".sprintcycle/cache",
        ttl_hours: int = 24,
        max_entries: int = 1000,
        enable_persistence: bool = True
    ):
        """
        初始化缓存
        
        Args:
            cache_dir: 缓存目录
            ttl_hours: 默认 TTL（小时）
            max_entries: 最大缓存条目数
            enable_persistence: 是否启用持久化
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = timedelta(hours=ttl_hours)
        self.max_entries = max_entries
        self.enable_persistence = enable_persistence
        
        # 内存缓存 - 使用 OrderedDict 实现高效 LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # 统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "invalidations": 0,
            "evictions": 0,
        }
        
        # 异步锁
        self._lock = asyncio.Lock()
        
        # 初始化
        if self.enable_persistence:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            asyncio.create_task(self._load_persistence())
    
    def _generate_hash(self, task_key: str) -> str:
        """生成任务哈希"""
        return hashlib.sha256(task_key.encode()).hexdigest()[:32]
    
    def _make_task_key(
        self,
        agent_type: str,
        task: str,
        context_hash: Optional[str] = None,
        **kwargs
    ) -> str:
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
        entry = self._cache.get(task_hash)
        
        if entry is None:
            self._stats["misses"] += 1
            logger.debug(f"Cache miss: {task_hash[:8]}")
            return None
        
        # 检查过期
        if entry.is_expired:
            self._stats["misses"] += 1
            logger.debug(f"Cache expired: {task_hash[:8]}")
            del self._cache[task_hash]
            return None
        
        # 更新访问统计并移动到末尾（LRU）
        entry.touch()
        self._cache.move_to_end(task_hash)
        self._stats["hits"] += 1
        logger.debug(f"Cache hit: {task_hash[:8]}, hit_count={entry.hit_count}")
        
        return entry.value
    
    async def get_async(self, task_hash: str) -> Optional[Any]:
        """异步获取缓存"""
        async with self._lock:
            return self.get(task_hash)
    
    def set(
        self,
        task_hash: str,
        value: Any,
        ttl_hours: Optional[int] = None
    ) -> None:
        """
        设置缓存
        
        Args:
            task_hash: 任务哈希
            value: 缓存值
            ttl_hours: TTL 小时数（可选）
        """
        ttl = ttl_hours or int(self.default_ttl.total_seconds() / 3600)
        entry = CacheEntry(
            key=task_hash,
            value=value,
            ttl_hours=ttl
        )
        
        # 如果键已存在，移动到末尾；否则检查是否需要淘汰
        if task_hash in self._cache:
            self._cache.move_to_end(task_hash)
        else:
            if len(self._cache) >= self.max_entries:
                self._evict_lru()
        
        self._cache[task_hash] = entry
        self._stats["sets"] += 1
        
        logger.debug(f"Cache set: {task_hash[:8]}")
        
        # 异步持久化
        if self.enable_persistence:
            asyncio.create_task(self._persist_entry(task_hash, entry))
    
    async def set_async(
        self,
        task_hash: str,
        value: Any,
        ttl_hours: Optional[int] = None
    ) -> None:
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
            count = len(self._cache)
            self._cache.clear()
            self._stats["invalidations"] += count
            logger.info(f"Cache cleared: {count} entries removed")
            return count
        
        if task_hash in self._cache:
            del self._cache[task_hash]
            self._stats["invalidations"] += 1
            logger.debug(f"Cache invalidated: {task_hash[:8]}")
            
            # 删除持久化文件
            if self.enable_persistence:
                self._delete_persistence(task_hash)
            
            return 1
        
        return 0
    
    async def invalidate_async(self, task_hash: Optional[str] = None) -> int:
        """异步失效缓存"""
        async with self._lock:
            return self.invalidate(task_hash)
    
    def _evict_lru(self) -> None:
        """LRU 淘汰 - OrderedDict.popitem(last=False) 移除最旧的条目"""
        if not self._cache:
            return
        
        # OrderedDict.popitem(last=False) 高效移除最旧的条目
        lru_key, _ = self._cache.popitem(last=False)
        self._stats["evictions"] += 1
        logger.debug(f"Cache evicted (LRU): {lru_key[:8]}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0 else 0
        )
        hit_rate_percentage = round(hit_rate, 2)
        
        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate": hit_rate_percentage,
            "cache_size": len(self._cache),
            "max_entries": self.max_entries,
            "memory_usage_estimate_mb": self._estimate_memory_usage(),
            "utilization": round(len(self._cache) / self.max_entries * 100, 2) if self.max_entries > 0 else 0,
        }
    
    def _estimate_memory_usage(self) -> float:
        """估算内存使用（MB）"""
        try:
            import sys
            total_size = 0
            for entry in self._cache.values():
                total_size += sys.getsizeof(pickle.dumps(entry.value))
            return round(total_size / 1024 / 1024, 2)
        except Exception:
            return 0.0
    
    def cleanup_expired(self) -> int:
        """
        清理过期缓存
        
        Returns:
            int: 清理的条目数
        """
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        count = len(expired_keys)
        if count > 0:
            logger.info(f"Cleaned up {count} expired cache entries")
        
        return count
    
    async def cleanup_expired_async(self) -> int:
        """异步清理过期缓存"""
        async with self._lock:
            return self.cleanup_expired()
    
    def _persist_path(self, task_hash: str) -> Path:
        """获取持久化文件路径"""
        return self.cache_dir / f"{task_hash}.pkl"
    
    async def _persist_entry(self, task_hash: str, entry: CacheEntry) -> None:
        """持久化缓存条目"""
        try:
            persist_path = self._persist_path(task_hash)
            data = {
                "entry": entry,
                "persisted_at": datetime.now().isoformat(),
            }
            with open(persist_path, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to persist cache entry: {e}")
    
    async def _load_persistence(self) -> None:
        """加载持久化缓存"""
        try:
            if not self.cache_dir.exists():
                return
            
            for pkl_file in self.cache_dir.glob("*.pkl"):
                try:
                    with open(pkl_file, "rb") as f:
                        data = pickle.load(f)
                    
                    entry: CacheEntry = data["entry"]
                    
                    # 跳过过期的
                    if entry.is_expired:
                        pkl_file.unlink()
                        continue
                    
                    self._cache[entry.key] = entry
                    
                except Exception as e:
                    logger.warning(f"Failed to load cache entry {pkl_file}: {e}")
            
            loaded = len(self._cache)
            if loaded > 0:
                logger.info(f"Loaded {loaded} cache entries from persistence")
                
        except Exception as e:
            logger.warning(f"Failed to load cache persistence: {e}")
    
    def _delete_persistence(self, task_hash: str) -> None:
        """删除持久化文件"""
        try:
            persist_path = self._persist_path(task_hash)
            if persist_path.exists():
                persist_path.unlink()
        except Exception as e:
            logger.warning(f"Failed to delete persistence: {e}")
    
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
        
        asyncio.create_task(cleanup_loop())
        logger.info(f"Started cache cleanup task (interval={interval_hours}h)")


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


__all__ = [
    "ExecutionCache",
    "CacheEntry",
    "get_cache",
    "set_cache",
]
