"""ArchGuard 侧的 YAML 声明式检查与 argv 运行器。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 checks.py。
"""

from __future__ import annotations

from typing import Any, Dict, List

from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding

from .checks import (
    checks_for_gate,
    filter_argv_items_by_governance_sources,
    load_governance_yaml,
    run_argv_checks,
    run_argv_item,
)

__all__ = [
    "checks_for_gate",
    "filter_argv_items_by_governance_sources",
    "load_governance_yaml",
    "run_argv_checks",
    "run_argv_item",
]
