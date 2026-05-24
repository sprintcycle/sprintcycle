from __future__ import annotations

from typing import List

from sprintcycle.domain.core.governance.arch_guard.model import GuardFinding


class TypeCheckAdapter:
    def run(self, project_root: str) -> List[GuardFinding]:
        # TODO: 实际接入 mypy / pyright
        return []
