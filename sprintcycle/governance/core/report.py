"""治理报告兼容层。"""

from __future__ import annotations

from ..arch_guard.model import GuardFinding as GovernanceViolation
from ..arch_guard.model import GuardReport as GovernanceReport

__all__ = ["GovernanceReport", "GovernanceViolation"]
