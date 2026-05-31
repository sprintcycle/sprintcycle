"""ArchGuard 侧的 SDD / release-plan 检查。

**已精简**：本模块保留用于向后兼容，实际函数已合并到 checks.py。
"""

from __future__ import annotations

from typing import List

from sprintcycle.domain.generic.models import ReleasePlan
from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding

from .checks import (
    violations_acceptance_files,
    violations_for_task_spec_refs,
    violations_from_release_plan_validator,
    violations_spec_marker_in_files,
)

__all__ = [
    "violations_acceptance_files",
    "violations_for_task_spec_refs",
    "violations_from_release_plan_validator",
    "violations_spec_marker_in_files",
]
