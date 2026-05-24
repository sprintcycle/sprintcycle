"""治理报告兼容层。"""

from __future__ import annotations

__all__ = ["GovernanceReport", "GovernanceViolation"]

# 延迟导入避免循环依赖
_GovernanceReport = None
_GovernanceViolation = None


def _get_governance_report():
    global _GovernanceReport
    if _GovernanceReport is None:
        from sprintcycle.domain.core.governance.arch_guard.model import GuardReport
        _GovernanceReport = GuardReport
    return _GovernanceReport


def _get_governance_violation():
    global _GovernanceViolation
    if _GovernanceViolation is None:
        from sprintcycle.domain.core.governance.arch_guard.model import GuardFinding
        _GovernanceViolation = GuardFinding
    return _GovernanceViolation


# 模块级访问器
def __getattr__(name):
    if name == "GovernanceReport":
        return _get_governance_report()
    if name == "GovernanceViolation":
        return _get_governance_violation()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
