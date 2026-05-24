"""DiskCache 后端 — 与既有 ExecutionCache 行为对齐（LRU、SQLite）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import diskcache
from loguru import logger

from .base import CacheBackend


class DiskCacheBackend(CacheBackend):
    def __init__(self, cache_dir: str, max_entries: int = 1000) -> None:
        self._path = Path(cache_dir)
        self._path.mkdir(parents=True, exist_ok=True)
        cache_size_limit = max(1, max_entries) * 1024 * 1024
        self._cache = diskcache.Cache(
            str(self._path),
            size_limit=cache_size_limit,
            eviction_policy="least-recently-used",
        )
        self._max_entries = max_entries
        logger.debug(
            "Cache backend=diskcache dir={} size_limit={}",
            self._path,
            cache_size_limit,
        )

    def get(self, key: str) -> Any:
        return self._cache.get(key, default=None)

    def set(self, key: str, value: Any, *, expire_seconds: Optional[int] = None) -> None:
        self._cache.set(key, value, expire=expire_seconds)

    def delete(self, key: str) -> bool:
        try:
            del self._cache[key]
            return True
        except KeyError:
            return False

    def contains(self, key: str) -> bool:
        return key in self._cache

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    def volume_bytes(self) -> int:
        try:
            return int(self._cache.volume())
        except Exception:
            return 0

    @property
    def backend_name(self) -> str:
        return "diskcache"
