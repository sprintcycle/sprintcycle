"""ArchGuard 侧的 SDD / release-plan 检查。"""

from __future__ import annotations

from typing import List

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


__all__ = [
    "violations_acceptance_files",
    "violations_for_task_spec_refs",
    "violations_from_release_plan_validator",
    "violations_spec_marker_in_files",
]
