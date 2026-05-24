"""
Release plan 在 **松结构负载**（断点、metadata、Agent 上下文等）中的规范键名与读取辅助。

一律使用 ``release_plan_*`` 键名，由执行层、API、CLI 共用，避免魔法字符串分叉。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

__all__ = [
    "KEY_PLAN_YAML",
    "KEY_PLAN_ID",
    "KEY_PLAN_NAME",
    "checkpoint_plan_yaml",
    "metadata_plan_id",
    "context_plan_id_name",
    "dict_plan_name",
]

KEY_PLAN_YAML = "release_plan_yaml"
KEY_PLAN_ID = "release_plan_id"
KEY_PLAN_NAME = "release_plan_name"


def checkpoint_plan_yaml(checkpoint: Optional[Dict[str, Any]]) -> Optional[str]:
    """从断点字典读取 ``release_plan_yaml``。"""
    if not checkpoint:
        return None
    return checkpoint.get(KEY_PLAN_YAML)


def metadata_plan_id(metadata: Dict[str, Any], *, default: str = "unknown") -> str:
    """从 metadata 读取 ``release_plan_id``。"""
    rid = metadata.get(KEY_PLAN_ID)
    if rid is not None and str(rid).strip():
        return str(rid)
    return default


def context_plan_id_name(context: Dict[str, Any]) -> tuple[str, str]:
    """从 Agent / Sprint 上下文字典取 ``(release_plan_id, release_plan_name)``。"""
    rid = str(context.get(KEY_PLAN_ID) or "")
    name = str(context.get(KEY_PLAN_NAME) or "")
    return rid, name


def dict_plan_name(d: Dict[str, Any]) -> str:
    """状态列表 / CLI：从执行记录 dict 取 ``release_plan_name`` 展示用字符串。"""
    v = d.get(KEY_PLAN_NAME)
    if v is not None and str(v).strip():
        return str(v)
    return ""
