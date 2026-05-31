"""HITL 上下文构建与摘要。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 coordinator.py。
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .coordinator import (
    build_hitl_context,
    build_replay_context,
    compact_dict,
    merge_correction_into_context,
    summarize_context_diff,
    summarize_hitl_context,
)
from .types import HitlCorrection, HitlReplayDirective

__all__ = [
    "build_hitl_context",
    "build_replay_context",
    "compact_dict",
    "merge_correction_into_context",
    "summarize_context_diff",
    "summarize_hitl_context",
]
