"""ArchGuard 侧的 YAML 声明式检查与 argv 运行器。"""

from __future__ import annotations

from typing import Any, Dict, List

from .model import GuardFinding


def checks_for_gate(data: Dict[str, Any], gate: str) -> List[Any]:
    """获取门的检查项"""
    return []


def filter_argv_items_by_governance_sources(argv_items: List[Any], cfg: Any, root: str) -> List[Any]:
    """按治理源过滤 argv 项"""
    return argv_items


def load_governance_yaml(root: str) -> Dict[str, Any]:
    """加载治理 YAML"""
    return {}


def run_argv_checks(argv_items: List[Any], root: str, gate: str) -> List[GuardFinding]:
    """运行 argv 检查"""
    return []


def run_argv_item(argv_item: Any, root: str) -> List[GuardFinding]:
    """运行单个 argv 项"""
    return []


__all__ = [
    "checks_for_gate",
    "filter_argv_items_by_governance_sources",
    "load_governance_yaml",
    "run_argv_checks",
    "run_argv_item",
]
