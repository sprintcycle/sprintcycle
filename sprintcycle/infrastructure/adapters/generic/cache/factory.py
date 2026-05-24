"""由 RuntimeConfig 构造 CacheBackend。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from .base import CacheBackend
from .disk import DiskCacheBackend
from .null_backend import NullCacheBackend
from .redis_backend import RedisCacheBackend

if TYPE_CHECKING:
    from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig


def resolve_cache_dir_for_project(runtime: "RuntimeConfig", project_path: str) -> Path:
    raw = (runtime.cache_dir or ".sprintcycle/cache").strip()
    p = Path(raw)
    if not p.is_absolute():
        p = Path(project_path).resolve() / p
    return p


def build_cache_backend(runtime: "RuntimeConfig", project_path: str) -> CacheBackend:
    """
    根据 ``cache_backend`` 选择实现。
    ``redis`` 且无 ``cache_redis_url`` / ``REDIS_URL`` 时回退 diskcache。
    """
    if not getattr(runtime, "cache_enabled", True):
        return NullCacheBackend()

    kind = (runtime.cache_backend or "diskcache").strip().lower()
    raw_max = runtime.cache_max_entries
    max_entries = max(1, int(raw_max)) if raw_max is not None else 1000

    if kind == "redis":
        url = (runtime.cache_redis_url or os.getenv("REDIS_URL") or "").strip()
        if not url:
            logger.warning("cache_backend=redis 但未配置 cache_redis_url / REDIS_URL，回退 diskcache")
            kind = "diskcache"
        else:
            try:
                return RedisCacheBackend(url)
            except ImportError as e:
                logger.warning("Redis 后端不可用: {}，回退 diskcache", e)
                kind = "diskcache"

    cache_dir = resolve_cache_dir_for_project(runtime, project_path)
    return DiskCacheBackend(str(cache_dir), max_entries=max_entries)


__all__ = ["build_cache_backend", "resolve_cache_dir_for_project"]
