"""HITL 通用工具。"""

from __future__ import annotations

from typing import Any, Dict


def compact_dict(data: Dict[str, Any], max_items: int = 20) -> Dict[str, Any]:
    if len(data) <= max_items:
        return dict(data)
    out = {}
    for i, (k, v) in enumerate(data.items()):
        if i >= max_items:
            break
        out[k] = v
    out["_truncated"] = True
    out["_total_keys"] = len(data)
    return out
