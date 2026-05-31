"""Human-in-the-loop（HITL）治理域入口。

**分层**：HITL 相关类型与工厂函数由 Infrastructure 层实现，通过延迟导入获取。
"""

from .types import (
    CTX_HITL_ABORT_EXECUTION,
    CTX_HITL_CORRECTION,
    CTX_HITL_REQUEST_CHANGES,
    CTX_HITL_RETRY_CONTEXT,
    CTX_HITL_RETRY_TARGET,
    CTX_HITL_SPRINT_ACTION,
    HitlCorrection,
    HitlDecision,
    HitlDecisionRecord,
    HitlGate,
    HitlReplayDirective,
    HitlRequestRecord,
    HitlRiskLevel,
    HitlSessionStatus,
    apply_after_sprint_decision,
    apply_before_sprint_decision,
    hitl_gate_enabled,
    parse_hitl_gates,
    is_hitl_enabled,
    get_hitl_timeout_seconds,
    get_hitl_timeout_behavior,
    get_hitl_gates,
)
from .coordinator import (
    HitlCoordinator,
    create_hitl_coordinator,
    build_hitl_context,
    build_replay_context,
    merge_correction_into_context,
    summarize_context_diff,
    summarize_hitl_context,
    compact_dict,
)
from .decision_normalize import (
    normalize_hitl_decision,
    normalize_hitl_decision_with_intent,
    validate_hitl_decision_for_submit,
)
from .events import HitlEventType
from .facade import HitlFacade, create_hitl_facade
from .hooks import HitlSprintHooks, HitlTaskHooks
from .policy import HitlPolicyResult, evaluate_hitl_policy
from .service import HitlService
from .session import (
    HitlSession,
    decision_to_terminal_status,
    transition_session_status,
    validate_session_transition,
)

__all__ = [
    "normalize_hitl_decision",
    "normalize_hitl_decision_with_intent",
    "validate_hitl_decision_for_submit",
    "HitlCoordinator",
    "HitlSprintHooks",
    "HitlTaskHooks",
    "HitlDecision",
    "HitlGate",
    "HitlRequestRecord",
    "HitlRiskLevel",
    "HitlSessionStatus",
    "HitlDecisionRecord",
    "HitlCorrection",
    "HitlReplayDirective",
    "apply_before_sprint_decision",
    "apply_after_sprint_decision",
    "hitl_gate_enabled",
    "parse_hitl_gates",
    "CTX_HITL_SPRINT_ACTION",
    "CTX_HITL_ABORT_EXECUTION",
    "CTX_HITL_REQUEST_CHANGES",
    "CTX_HITL_RETRY_TARGET",
    "CTX_HITL_RETRY_CONTEXT",
    "CTX_HITL_CORRECTION",
    "is_hitl_enabled",
    "get_hitl_timeout_seconds",
    "get_hitl_timeout_behavior",
    "get_hitl_gates",
    "evaluate_hitl_policy",
    "HitlPolicyResult",
    "build_hitl_context",
    "merge_correction_into_context",
    "build_replay_context",
    "summarize_context_diff",
    "summarize_hitl_context",
    "compact_dict",
    "HitlEventType",
    "HitlService",
    "HitlSession",
    "validate_session_transition",
    "transition_session_status",
    "decision_to_terminal_status",
    "HitlFacade",
    "create_hitl_facade",
    "create_hitl_coordinator",
]
