"""ArchGuard 侧的 argv 扩展入口。"""

from __future__ import annotations

from ..argv_extensions import (  # noqa: F401
    extend_argv_items_with_plugins,
    load_entry_point_argv_extensions,
)

__all__ = ["extend_argv_items_with_plugins", "load_entry_point_argv_extensions"]
