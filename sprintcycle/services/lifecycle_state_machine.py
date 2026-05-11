"""Unified lifecycle state machine for SprintCycle.

This module is the canonical lifecycle transition source for web-triggered
execution chains. It provides:
- a single stage vocabulary
- authoritative transition rules
- correlation model helpers
- contract mutation helpers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


LIFECYCLE_STAGES: tuple[str, ...] = (
    "new",
    "normalized",
    "planned",
    "prepared",
    "decomposed",
    "executing",
    "observing",
    "diagnosed",
    "repairing",
    "verifying",
    "delivering",
    "runtime_linked",
    "governing",
    "promotion_ready",
    "promoted",
)

TERMINAL_STAGES: tuple[str, ...] = ("promoted", "failed", "aborted", "cancelled")

STAGE_TRANSITIONS: Dict[str, tuple[str, ...]] = {
    "new": ("normalized", "failed", "cancelled"),
    "normalized": ("planned", "failed", "cancelled"),
    "planned": ("prepared", "failed", "cancelled"),
    "prepared": ("decomposed", "failed", "cancelled"),
    "decomposed": ("executing", "failed", "cancelled"),
    "executing": ("observing", "diagnosed", "delivering", "failed", "cancelled"),
    "observing": ("diagnosed", "delivering", "failed", "cancelled"),
    "diagnosed": ("repairing", "delivering", "failed", "cancelled"),
    "repairing": ("verifying", "observing", "failed", "cancelled"),
    "verifying": ("observing", "delivering", "failed", "cancelled"),
    "delivering": ("runtime_linked", "failed", "cancelled"),
    "runtime_linked": ("governing", "failed", "cancelled"),
    "governing": ("promotion_ready", "failed", "cancelled"),
    "promotion_ready": ("promoted", "failed", "cancelled"),
    "promoted": (),
    "failed": (),
    "aborted": (),
    "cancelled": (),
}

CORRELATION_KEY_FIELDS: tuple[str, ...] = ("request_id", "execution_id", "task_id", "suggestion_id", "runtime_id", "version_id")


@dataclass(slots=True)
class CorrelationContext:
    request_id: str = ""
    execution_id: str = ""
    task_id: str = ""
    suggestion_id: str = ""
    runtime_id: str = ""
    version_id: str = ""
    trace_id: str = ""
    parent_id: str = ""
    source: str = "web"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "suggestion_id": self.suggestion_id,
            "runtime_id": self.runtime_id,
            "version_id": self.version_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


@dataclass(slots=True)
class LifecycleStateMachine:
    stage: str = "new"

    def normalize_stage(self, stage: object) -> str:
        value = str(stage or "").strip().lower()
        return value if value in STAGE_TRANSITIONS else "new"

    def can_transition(self, from_stage: object, to_stage: object) -> bool:
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)
        if frm == to:
            return True
        return to in STAGE_TRANSITIONS.get(frm, ())

    def validate_transition(self, from_stage: object, to_stage: object) -> Optional[str]:
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)
        if not frm or not to:
            return "stage cannot be empty"
        if self.can_transition(frm, to):
            return None
        return f"illegal lifecycle transition: {frm} -> {to}"

    def next_stages(self, stage: object) -> tuple[str, ...]:
        return STAGE_TRANSITIONS.get(self.normalize_stage(stage), ())

    def stage_index(self, stage: object) -> int:
        normalized = self.normalize_stage(stage)
        try:
            return LIFECYCLE_STAGES.index(normalized)
        except ValueError:
            return -1

    def is_terminal(self, stage: object) -> bool:
        return self.normalize_stage(stage) in TERMINAL_STAGES

    def transition(self, contract: Dict[str, Any], to_stage: str, *, status: Optional[str] = None, reason: str = "", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = dict(contract or {})
        current = self.normalize_stage(contract.get("stage") or contract.get("current_stage") or "new")
        target = self.normalize_stage(to_stage)
        err = self.validate_transition(current, target)
        if err:
            raise ValueError(err)
        history = list(contract.get("stage_history") or [])
        now = datetime.now(timezone.utc).isoformat()
        if current != target:
            history.append({"from": current, "to": target, "at": now, "reason": reason})
        contract["stage"] = target
        contract["status"] = status or contract.get("status") or "pending"
        contract["stage_history"] = history
        contract["stage_index"] = self.stage_index(target)
        contract["is_terminal"] = self.is_terminal(target) or str(contract.get("status") or "").lower() in {"success", "failed", "cancelled"}
        contract.setdefault("metadata", {})
        if metadata:
            contract["metadata"].update(metadata)
        contract["transition_reason"] = reason
        contract["updated_at"] = now
        return contract

    def ensure_correlation(self, payload: Dict[str, Any]) -> CorrelationContext:
        payload = dict(payload or {})
        metadata = dict(payload.get("metadata") or {})
        trace_id = str(payload.get("trace_id") or metadata.get("trace_id") or uuid4())
        return CorrelationContext(
            request_id=str(payload.get("request_id") or metadata.get("request_id") or ""),
            execution_id=str(payload.get("execution_id") or metadata.get("execution_id") or ""),
            task_id=str(payload.get("task_id") or metadata.get("task_id") or ""),
            suggestion_id=str(payload.get("suggestion_id") or metadata.get("suggestion_id") or ""),
            runtime_id=str(payload.get("runtime_id") or metadata.get("runtime_id") or ""),
            version_id=str(payload.get("version_id") or metadata.get("version_id") or ""),
            trace_id=trace_id,
            parent_id=str(payload.get("parent_id") or metadata.get("parent_id") or ""),
            source=str(payload.get("source") or metadata.get("source") or "web"),
            metadata=metadata,
        )

    def attach_correlation(self, contract: Dict[str, Any], correlation: CorrelationContext) -> Dict[str, Any]:
        contract = dict(contract or {})
        contract["correlation"] = correlation.to_dict()
        contract.setdefault("metadata", {})
        contract["metadata"].update({k: v for k, v in correlation.to_dict().items() if k in CORRELATION_KEY_FIELDS and v})
        return contract

    def build_event(self, *, kind: str, stage: str, status: str = "success", payload: Optional[Dict[str, Any]] = None, correlation: Optional[CorrelationContext] = None, source: str = "web") -> Dict[str, Any]:
        corr = correlation or CorrelationContext(source=source)
        return {
            "event_id": str(uuid4()),
            "kind": kind,
            "stage": self.normalize_stage(stage),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "correlation": corr.to_dict(),
            "payload": dict(payload or {}),
        }


def build_default_correlation(payload: Optional[Dict[str, Any]] = None) -> CorrelationContext:
    return LifecycleStateMachine().ensure_correlation(payload or {})


__all__ = [
    "CorrelationContext",
    "LifecycleStateMachine",
    "LIFECYCLE_STAGES",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "build_default_correlation",
]
