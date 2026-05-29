"""治理报告模块。"""

from __future__ import annotations

from sprintcycle.domain.core.governance.common.model import Report as GovernanceReport
from sprintcycle.domain.core.governance.common.model import Finding as GovernanceViolation

__all__ = ["GovernanceReport", "GovernanceViolation"]
