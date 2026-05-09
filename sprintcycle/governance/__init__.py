"""Governance 域对外入口。

对外推荐使用 ``GovernanceFacade`` 作为统一入口；
``observability`` / ``runner`` / ``arch_guard`` / ``hitl`` 作为治理域子能力。

详见 ``docs/GOVERNANCE_ENGINEERING.md``。
"""

from .facade import GovernanceFacade, create_governance_facade
from .observability import (
    ObservabilityFacade,
    ObservationEvent,
    ObservationGateResult,
    ObservationRequestResult,
    create_observability_facade,
)
from .arch_guard.model import GuardFinding as GovernanceViolation
from .arch_guard.model import GuardReport as GovernanceReport
from .model_compare import run_model_compare
from .runner import GovernanceRunner, run_planning_gate_sync, run_review_gate_sync

__all__ = [
    # Governance 总入口
    "GovernanceFacade",
    "create_governance_facade",
    # Observability 子入口
    "ObservabilityFacade",
    "create_observability_facade",
    "ObservationEvent",
    "ObservationGateResult",
    "ObservationRequestResult",
    # 传统治理能力
    "GovernanceReport",
    "GovernanceViolation",
    "GovernanceRunner",
    "run_planning_gate_sync",
    "run_review_gate_sync",
    "run_model_compare",
]
