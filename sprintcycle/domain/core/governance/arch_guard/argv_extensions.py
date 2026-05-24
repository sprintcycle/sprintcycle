"""ArchGuard 侧的 argv 扩展入口。"""

from __future__ import annotations

from typing import Any, List


def extend_argv_items_with_plugins(gate: str, argv_items: List[Any], cfg: Any, root: str) -> List[Any]:
    """扩展 argv 项"""
    return argv_items


def load_entry_point_argv_extensions() -> list:
    """加载入口点扩展"""
    return []


__all__ = ["extend_argv_items_with_plugins", "load_entry_point_argv_extensions"]
