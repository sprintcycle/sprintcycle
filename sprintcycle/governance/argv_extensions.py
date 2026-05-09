"""治理层 argv 扩展入口。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .pluggy_host import merge_argv_via_pluggy


def load_entry_point_argv_extensions() -> List[Dict[str, Any]]:
    return []


def extend_argv_items_with_plugins(
    gate: str,
    base_items: List[Dict[str, Any]],
    cfg: Any,
    root: Path,
) -> List[Dict[str, Any]]:
    items = list(base_items)
    items.extend(load_entry_point_argv_extensions())
    return merge_argv_via_pluggy(gate, items, cfg, root)
