from __future__ import annotations

from typing import List

from sprintcycle.domain.core.governance.common.model import Finding as GuardFinding


class ArchonAdapter:
    def run(self, project_root: str) -> List[GuardFinding]:
        # TODO: 接入 pytest-archon / PyTestArch 做架构测试。
        return []
