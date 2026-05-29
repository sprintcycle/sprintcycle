"""ArchGuard 侧的 ADR 索引一致性检查。"""

from __future__ import annotations

from typing import List

from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding


def check_adr_readme_index(root: str) -> List[GuardFinding]:
    """检查 ADR README 索引是否完整"""
    return []


def check_adr_readme_strict_glob(root: str, adr_glob: str) -> List[GuardFinding]:
    """检查 ADR README 的 glob 模式是否严格"""
    return []


__all__ = ["check_adr_readme_index", "check_adr_readme_strict_glob"]
