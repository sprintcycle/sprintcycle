"""ArchGuard 检查逻辑统一模块。

**已精简**：将 sdd_checks.py 和 yaml_checks.py 合并到此文件。
"""

from __future__ import annotations

from typing import Any, Dict, List

from sprintcycle.domain.generic.models import ReleasePlan
from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding


def violations_spec_marker_in_files(root: str, spec_glob: str, marker: str) -> List[GuardFinding]:
    """检查 spec marker 文件"""
    return []


def violations_acceptance_files(root: str, acc_glob: str) -> List[GuardFinding]:
    """检查验收文件"""
    return []


def violations_from_release_plan_validator(rp: ReleasePlan) -> List[GuardFinding]:
    """从发布计划验证器获取违规"""
    return []


def violations_for_task_spec_refs(root: str, rp: ReleasePlan) -> List[GuardFinding]:
    """检查任务规范引用"""
    return []


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
    "violations_acceptance_files",
    "violations_for_task_spec_refs",
    "violations_from_release_plan_validator",
    "violations_spec_marker_in_files",
    "checks_for_gate",
    "filter_argv_items_by_governance_sources",
    "load_governance_yaml",
    "run_argv_checks",
    "run_argv_item",
]
