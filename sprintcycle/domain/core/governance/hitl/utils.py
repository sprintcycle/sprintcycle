"""HITL 通用工具。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 coordinator.py。
"""

from __future__ import annotations

from typing import Any, Dict

from .coordinator import compact_dict

__all__ = ["compact_dict"]
