"""HITL 类型与 context 键约定（治理域版本）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class HitlGate(str, Enum):
    BEFORE_SPRINT = "before_sprint"
    AFTER_SPRINT = "after_sprint"
    AFTER_TASK = "after_task"
    SPEC_CONFIRM = "spec_confirm"
    EXECUTION_APPROVAL = "execution_approval"
    RELEASE_APPROVAL = "release_approval"


class HitlDecision(str, Enum):
    APPROVE = "approve"
    SKIP_SPRINT = "skip_sprint"
    ABORT_EXECUTION = "abort_execution"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    MODIFY = "modify"
    RETRY = "retry"
    RESUME = "resume"


class HitlSessionStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    RETRYING = "retrying"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    RESUMED = "resumed"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"


class HitlRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# SprintExecutor / GovernanceRunner 识别的键
CTX_HITL_SPRINT_ACTION = "_hitl_sprint_action"
CTX_HITL_ABORT_EXECUTION = "_hitl_abort_execution"
CTX_HITL_REQUEST_CHANGES = "_hitl_request_changes"
CTX_HITL_RETRY_TARGET = "_hitl_retry_target"
CTX_HITL_RETRY_CONTEXT = "_hitl_retry_context"
CTX_HITL_CORRECTION = "_hitl_correction"


@dataclass
class HitlCorrection:
    targets: List[str] = field(default_factory=list)
    patches: List[Dict[str, Any]] = field(default_factory=list)
    reason: str = ""
    apply_mode: str = "manual"
    inherit_context: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "targets": list(self.targets),
            "patches": list(self.patches),
            "reason": self.reason,
            "apply_mode": self.apply_mode,
            "inherit_context": self.inherit_context,
            "metadata": dict(self.metadata),
        }


@dataclass
class HitlReplayDirective:
    target_gate: Optional[str] = None
    target_stage: Optional[str] = None
    mode: str = "gate_only"
    inherit_context: bool = True
    reset_fields: List[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_gate": self.target_gate,
            "target_stage": self.target_stage,
            "mode": self.mode,
            "inherit_context": self.inherit_context,
            "reset_fields": list(self.reset_fields),
            "reason": self.reason,
        }


@dataclass
class HitlDecisionRecord:
    decision: str
    actor: Optional[str] = None
    note: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HitlRequestRecord:
    request_id: str
    execution_id: str
    gate: str
    status: str  # open | resolved | modified | retrying | ...
    title: str
    summary: str
    context: Dict[str, Any]
    created_at: str
    decided_at: Optional[str] = None
    decision: Optional[str] = None
    decision_note: Optional[str] = None
    timeout_seconds: int = 300
    risk_level: str = HitlRiskLevel.MEDIUM.value
    parent_request_id: Optional[str] = None
    revision: int = 1
    decision_kind: Optional[str] = None
    correction: Optional[HitlCorrection] = None
    replay_directive: Optional[HitlReplayDirective] = None
    status_reason: Optional[str] = None
    superseded_by: Optional[str] = None
    replay_count: int = 0
    applied_context: Dict[str, Any] = field(default_factory=dict)
    available_actions: List[str] = field(default_factory=lambda: [
        HitlDecision.APPROVE.value,
        HitlDecision.SKIP_SPRINT.value,
        HitlDecision.ABORT_EXECUTION.value,
        HitlDecision.REJECT.value,
        HitlDecision.REQUEST_CHANGES.value,
        HitlDecision.MODIFY.value,
        HitlDecision.RETRY.value,
        HitlDecision.RESUME.value,
    ])

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
            "risk_level": self.risk_level,
            "parent_request_id": self.parent_request_id,
            "revision": self.revision,
            "decision_kind": self.decision_kind,
            "correction": self.correction.to_dict() if self.correction else None,
            "replay_directive": self.replay_directive.to_dict() if self.replay_directive else None,
            "status_reason": self.status_reason,
            "superseded_by": self.superseded_by,
            "replay_count": self.replay_count,
            "applied_context": self.applied_context,
            "available_actions": list(self.available_actions),
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


def apply_before_sprint_decision(ctx: Dict[str, Any], decision: HitlDecision) -> None:
    """将 HITL 决策写入 context，供执行器在 before_sprint 后读取。"""
    ctx.pop(CTX_HITL_SPRINT_ACTION, None)
    ctx.pop(CTX_HITL_REQUEST_CHANGES, None)
    ctx.pop(CTX_HITL_RETRY_TARGET, None)
    ctx.pop(CTX_HITL_RETRY_CONTEXT, None)
    ctx.pop(CTX_HITL_CORRECTION, None)
    if decision == HitlDecision.SKIP_SPRINT:
        ctx[CTX_HITL_SPRINT_ACTION] = "skip"
    elif decision == HitlDecision.ABORT_EXECUTION:
        ctx[CTX_HITL_SPRINT_ACTION] = "abort"
    elif decision in (HitlDecision.REQUEST_CHANGES, HitlDecision.MODIFY):
        ctx[CTX_HITL_REQUEST_CHANGES] = True
    elif decision == HitlDecision.RETRY:
        ctx[CTX_HITL_RETRY_TARGET] = "before_sprint"


def apply_after_sprint_decision(ctx: Dict[str, Any], decision: HitlDecision) -> None:
    if decision == HitlDecision.ABORT_EXECUTION:
        ctx[CTX_HITL_ABORT_EXECUTION] = True
    elif decision in (HitlDecision.REQUEST_CHANGES, HitlDecision.MODIFY):
        ctx[CTX_HITL_REQUEST_CHANGES] = True
    elif decision == HitlDecision.RETRY:
        ctx[CTX_HITL_RETRY_TARGET] = "after_sprint"
