"""
执行状态 / 事件负载中的 **规范键名** 与小型读取辅助函数。

断点、metadata、上下文字段一律使用 ``release_plan_*`` 键名；不再识别或迁移历史 ``prd_*`` 键。
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
