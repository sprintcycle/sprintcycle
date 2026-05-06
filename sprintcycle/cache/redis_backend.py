"""Redis 缓存后端（可选依赖 redis）。"""

from __future__ import annotations

import pickle
from typing import Any, Optional

from loguru import logger

from .base import CacheBackend


class RedisCacheBackend(CacheBackend):
    def __init__(self, url: str, *, key_prefix: str = "sc:") -> None:
        try:
            import redis as redis_lib
        except ImportError as e:
            raise ImportError(
                "cache_backend=redis 需要安装 redis 包：pip install 'sprintcycle[cache-redis]' 或 pip install redis"
            ) from e

        self._redis = redis_lib.Redis.from_url(url, decode_responses=False)
        self._prefix = key_prefix
        logger.debug("Cache backend=redis url={}", url.split("@")[-1] if "@" in url else url)

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Any:
        raw = self._redis.get(self._k(key))
        if raw is None:
            return None
        try:
            return pickle.loads(raw)
        except Exception:
            logger.warning("Redis cache unpickle failed for key prefix={}", key[:24])
            return None

    def set(self, key: str, value: Any, *, expire_seconds: Optional[int] = None) -> None:
        payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        k = self._k(key)
        if expire_seconds is not None and expire_seconds > 0:
            self._redis.setex(k, expire_seconds, payload)
        else:
            self._redis.set(k, payload)

    def delete(self, key: str) -> bool:
        return bool(self._redis.delete(self._k(key)))

    def contains(self, key: str) -> bool:
        return bool(self._redis.exists(self._k(key)))

    def clear(self) -> None:
        pattern = f"{self._prefix}*"
        for rk in self._redis.scan_iter(match=pattern):
            self._redis.delete(rk)

    def __len__(self) -> int:
        return sum(1 for _ in self._redis.scan_iter(match=f"{self._prefix}*"))

    def volume_bytes(self) -> int:
        return 0

    @property
    def backend_name(self) -> str:
        return "redis"
