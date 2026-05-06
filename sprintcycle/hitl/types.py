"""HITL 类型与 context 键约定（与 SprintExecutor 协作）。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class HitlGate(str, Enum):
    BEFORE_SPRINT = "before_sprint"
    AFTER_SPRINT = "after_sprint"
    AFTER_TASK = "after_task"


class HitlDecision(str, Enum):
    APPROVE = "approve"
    SKIP_SPRINT = "skip_sprint"
    ABORT_EXECUTION = "abort_execution"


# SprintExecutor 识别的键（见 sprint_executor._execute_normal_sprints）
CTX_HITL_SPRINT_ACTION = "_hitl_sprint_action"
CTX_HITL_ABORT_EXECUTION = "_hitl_abort_execution"


def apply_before_sprint_decision(ctx: Dict[str, Any], decision: HitlDecision) -> None:
    """将 HITL 决策写入 context，供 SprintExecutor 在 on_before_sprint 之后读取。"""
    ctx.pop(CTX_HITL_SPRINT_ACTION, None)
    if decision == HitlDecision.SKIP_SPRINT:
        ctx[CTX_HITL_SPRINT_ACTION] = "skip"
    elif decision == HitlDecision.ABORT_EXECUTION:
        ctx[CTX_HITL_SPRINT_ACTION] = "abort"


def apply_after_sprint_decision(ctx: Dict[str, Any], decision: HitlDecision) -> None:
    if decision == HitlDecision.ABORT_EXECUTION:
        ctx[CTX_HITL_ABORT_EXECUTION] = True


@dataclass
class HitlRequestRecord:
    request_id: str
    execution_id: str
    gate: str
    status: str  # open | resolved
    title: str
    summary: str
    context: Dict[str, Any]
    created_at: str
    decided_at: Optional[str] = None
    decision: Optional[str] = None
    decision_note: Optional[str] = None
    timeout_seconds: int = 300

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "execution_id": self.execution_id,
            "gate": self.gate,
            "status": self.status,
            "title": self.title,
            "summary": self.summary,
            "context": self.context,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
            "decision": self.decision,
            "decision_note": self.decision_note,
            "timeout_seconds": self.timeout_seconds,
            "available_actions": [
                HitlDecision.APPROVE.value,
                HitlDecision.SKIP_SPRINT.value,
                HitlDecision.ABORT_EXECUTION.value,
            ],
        }


def parse_hitl_gates(s: str) -> frozenset[str]:
    raw = (s or "").strip().lower()
    if not raw:
        return frozenset()
    parts = {p.strip() for p in raw.split(",") if p.strip()}
    allowed = {g.value for g in HitlGate}
    return frozenset(p for p in parts if p in allowed)


def hitl_gate_enabled(config: Any, gate: HitlGate) -> bool:
    if not getattr(config, "hitl_enabled", False):
        return False
    g = parse_hitl_gates(getattr(config, "hitl_gates", "") or "")
    return gate.value in g
