"""禁用缓存时的空后端（不读写、不报错）。"""

from __future__ import annotations

from typing import Any, Optional

from .base import CacheBackend


class NullCacheBackend(CacheBackend):
    def get(self, key: str) -> Any:
        return None

    def set(self, key: str, value: Any, *, expire_seconds: Optional[int] = None) -> None:
        return

    def delete(self, key: str) -> bool:
        return False

    def contains(self, key: str) -> bool:
        return False

    def clear(self) -> None:
        return

    def __len__(self) -> int:
        return 0

    @property
    def backend_name(self) -> str:
        return "disabled"
