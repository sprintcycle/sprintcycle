"""HITL session 与状态机。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import HitlDecision, HitlSessionStatus

_ALLOWED_TRANSITIONS = {
    HitlSessionStatus.CREATED.value: {HitlSessionStatus.PENDING.value},
    HitlSessionStatus.PENDING.value: {
        HitlSessionStatus.APPROVED.value,
        HitlSessionStatus.REJECTED.value,
        HitlSessionStatus.MODIFIED.value,
        HitlSessionStatus.EXPIRED.value,
        HitlSessionStatus.CANCELLED.value,
    },
    HitlSessionStatus.APPROVED.value: {HitlSessionStatus.RESUMED.value},
    HitlSessionStatus.MODIFIED.value: {HitlSessionStatus.PENDING.value, HitlSessionStatus.CANCELLED.value},
    HitlSessionStatus.REJECTED.value: {HitlSessionStatus.CANCELLED.value},
    HitlSessionStatus.EXPIRED.value: {HitlSessionStatus.CANCELLED.value},
    HitlSessionStatus.CANCELLED.value: set(),
    HitlSessionStatus.RESUMED.value: set(),
}


@dataclass
class HitlSession:
    session_id: str
    request_id: str
    execution_id: str
    gate: str
    status: str
    title: str
    summary: str
    reason: str
    risk_level: str
    context: Dict[str, Any]
    created_at: str
    updated_at: str
    deadline_at: Optional[str] = None
    decision: Optional[str] = None
    decision_note: Optional[str] = None
    available_actions: List[str] = field(default_factory=list)


def validate_session_transition(old: str, new: str) -> bool:
    return new in _ALLOWED_TRANSITIONS.get(old, set())


def transition_session_status(old: str, new: str) -> str:
    if not validate_session_transition(old, new):
        raise ValueError(f"invalid hitl session transition: {old} -> {new}")
    return new


def decision_to_terminal_status(decision: str) -> str:
    try:
        d = HitlDecision(decision)
    except ValueError:
        return HitlSessionStatus.CANCELLED.value
    if d == HitlDecision.APPROVE:
        return HitlSessionStatus.APPROVED.value
    if d in (HitlDecision.REJECT, HitlDecision.ABORT_EXECUTION):
        return HitlSessionStatus.REJECTED.value
    if d == HitlDecision.REQUEST_CHANGES:
        return HitlSessionStatus.MODIFIED.value
    if d == HitlDecision.SKIP_SPRINT:
        return HitlSessionStatus.APPROVED.value
    return HitlSessionStatus.CANCELLED.value
