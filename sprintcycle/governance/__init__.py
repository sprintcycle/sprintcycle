"""
代码治理与质量门禁的对外入口。

优先使用 ``arch_guard`` 的通用模型与引擎；
``governance`` 保留编排、历史、钩子和兼容入口。

详见 ``docs/GOVERNANCE_ENGINEERING.md``。
"""

from .arch_guard.model import GuardFinding as GovernanceViolation
from .arch_guard.model import GuardReport as GovernanceReport
from .model_compare import run_model_compare
from .runner import GovernanceRunner, run_planning_gate_sync, run_review_gate_sync

__all__ = [
    "GovernanceReport",
    "GovernanceViolation",
    "GovernanceRunner",
    "run_planning_gate_sync",
    "run_review_gate_sync",
    "run_model_compare",
]
