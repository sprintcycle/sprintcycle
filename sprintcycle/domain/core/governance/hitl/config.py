"""HITL 配置适配。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 types.py。
"""

from __future__ import annotations

from typing import Any

from .types import HitlGate, get_hitl_gates, get_hitl_timeout_behavior, get_hitl_timeout_seconds, hitl_gate_enabled, is_hitl_enabled

__all__ = [
    "is_hitl_enabled",
    "get_hitl_timeout_seconds",
    "get_hitl_timeout_behavior",
    "get_hitl_gates",
]
