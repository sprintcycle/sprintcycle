"""
SprintCycle 统一缓存抽象层。

- 默认 **diskcache**（本地 SQLite + LRU），零额外服务。
- 可选 **redis**（配置 ``cache_backend`` + ``cache_redis_url``，依赖 ``redis`` 包）。

业务侧优先通过 ``sprintcycle.execution.get_cache()`` 获取带统计与任务键约定的
``ExecutionCache``；底层存储由 ``CacheBackend`` 实现。
"""

from .base import CacheBackend
from .disk import DiskCacheBackend
from .factory import build_cache_backend
from .null_backend import NullCacheBackend
from .redis_backend import RedisCacheBackend

__all__ = [
    "CacheBackend",
    "DiskCacheBackend",
    "NullCacheBackend",
    "RedisCacheBackend",
    "build_cache_backend",
]
