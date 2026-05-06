"""
代码治理与质量门禁（Review / Planning 检查包 + Sprint 钩子）。

详见 ``docs/GOVERNANCE_ENGINEERING.md``。
"""

from .model_compare import run_model_compare
from .report import GovernanceReport, GovernanceViolation
from .runner import GovernanceRunner, run_planning_gate_sync, run_review_gate_sync

__all__ = [
    "GovernanceReport",
    "GovernanceViolation",
    "GovernanceRunner",
    "run_planning_gate_sync",
    "run_review_gate_sync",
    "run_model_compare",
]
