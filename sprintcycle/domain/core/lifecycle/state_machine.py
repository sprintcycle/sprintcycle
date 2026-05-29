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
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .values import CorrelationContext

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

RECOVERY_STAGES: tuple[str, ...] = ("repairing", "verifying")
FAILURE_STAGES: tuple[str, ...] = ("failed", "aborted", "cancelled")
RECOVERY_TARGETS: Dict[str, str] = {
    "executing": "repairing",
    "observing": "repairing",
    "diagnosed": "repairing",
    "repairing": "verifying",
    "verifying": "observing",
    "delivering": "repairing",
    "runtime_linked": "repairing",
    "governing": "repairing",
    "promotion_ready": "repairing",
    "failed": "repairing",
}

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
    "failed": ("repairing", "cancelled"),
    "aborted": (),
    "cancelled": (),
}
REPAIR_ROUTE_BY_STAGE: Dict[str, str] = {
    "executing": "repairing",
    "observing": "repairing",
    "diagnosed": "repairing",
    "repairing": "verifying",
    "verifying": "observing",
    "delivering": "repairing",
    "runtime_linked": "repairing",
    "governing": "repairing",
    "promotion_ready": "repairing",
    "failed": "repairing",
}

CORRELATION_KEY_FIELDS: tuple[str, ...] = (
    "request_id",
    "execution_id",
    "task_id",
    "suggestion_id",
    "runtime_id",
    "version_id",
)

FAILURE_KIND_BY_STAGE: Dict[str, str] = {
    "new": "",
    "normalized": "",
    "planned": "",
    "prepared": "",
    "decomposed": "",
    "executing": "execution_error",
    "observing": "observation_error",
    "diagnosed": "diagnosis_error",
    "repairing": "repair_error",
    "verifying": "verification_error",
    "delivering": "delivery_error",
    "runtime_linked": "integration_error",
    "governing": "policy_error",
    "promotion_ready": "policy_error",
    "promoted": "",
}


@dataclass(slots=True)
class LifecycleStateMachine:
    """
    Authoritative lifecycle state machine.
    
    This class provides the single source of truth for lifecycle stage
    transitions and validation rules. It combines the functionality
    previously split between LifecycleStateMachine and LifecycleStateMachineService.
    
    **Design Principles:**
    - Stateless domain service (no internal state beyond configuration)
    - Methods are pure functions where possible
    - Single source of truth for all transition rules
    """
    
    # Class-level constants for reference
    STAGES = LIFECYCLE_STAGES
    TERMINAL_STAGES = TERMINAL_STAGES
    TRANSITIONS = STAGE_TRANSITIONS
    RECOVERY_TARGETS = RECOVERY_TARGETS

    def normalize_stage(self, stage: object) -> str:
        """Normalize a stage value to canonical string form."""
        if hasattr(stage, 'value'):
            value = str(stage.value).strip().lower()
        else:
            value = str(stage or "").strip().lower()
        return value if value in STAGE_TRANSITIONS else "new"

    def can_transition(self, from_stage: object, to_stage: object) -> bool:
        """Check if a transition is valid."""
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)
        if frm == to:
            return True
        return to in STAGE_TRANSITIONS.get(frm, ())

    def validate_transition(self, from_stage: object, to_stage: object) -> Optional[str]:
        """Validate a stage transition. Returns None if valid, or error message."""
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)
        
        if not frm:
            return "stage cannot be empty"
        if not to:
            return "target stage cannot be empty"

        if self.can_transition(frm, to):
            return None

        return f"illegal lifecycle transition: {frm} -> {to}"

    def next_stages(self, stage: object) -> tuple[str, ...]:
        """Get the valid next stages for a given stage."""
        return STAGE_TRANSITIONS.get(self.normalize_stage(stage), ())

    def stage_index(self, stage: object) -> int:
        """Get the index of a stage in the lifecycle sequence."""
        normalized = self.normalize_stage(stage)
        try:
            return LIFECYCLE_STAGES.index(normalized)
        except ValueError:
            return -1

    def is_terminal(self, stage: object) -> bool:
        """Check if a stage is terminal (no further transitions)."""
        normalized = self.normalize_stage(stage)
        return (
            normalized in TERMINAL_STAGES or normalized in FAILURE_STAGES
        )

    def is_failure(self, stage: object) -> bool:
        """Check if a stage represents a failure state."""
        return self.normalize_stage(stage) in FAILURE_STAGES

    def is_recovery(self, stage: object) -> bool:
        """Check if a stage is a recovery stage."""
        return self.normalize_stage(stage) in RECOVERY_STAGES

    def get_recovery_target(self, stage: object) -> str:
        """Get the recovery target stage for a given stage."""
        normalized = self.normalize_stage(stage)
        return RECOVERY_TARGETS.get(normalized, "repairing")

    def get_failure_kind(self, stage: object) -> str:
        """Get the failure kind for a given stage."""
        return FAILURE_KIND_BY_STAGE.get(self.normalize_stage(stage), "")

    def get_allowed_next_stages(self, stage: object) -> List[str]:
        """Get a list of allowed next stages (excludes failure states by default)."""
        all_next = list(self.next_stages(stage))
        return [
            s for s in all_next if s not in FAILURE_STAGES
        ]

    def transition(
        self,
        contract: Dict[str, Any],
        to_stage: str,
        *,
        status: Optional[str] = None,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Transition a contract dictionary to a new stage.
        
        This is the primary method for advancing the lifecycle state.
        It validates the transition before applying it.
        """
        contract = dict(contract or {})
        from_stage = contract.get("stage", "new")
        
        if from_stage == "failed" and to_stage == "repairing":
            pass
        else:
            error = self.validate_transition(from_stage, to_stage)
            if error:
                raise ValueError(error)
        
        result = dict(contract)
        
        result["stage"] = to_stage
        if status:
            result["status"] = status
        elif to_stage in TERMINAL_STAGES or to_stage in FAILURE_STAGES:
            result["status"] = "failed" if to_stage in FAILURE_STAGES else "success"
        
        result.setdefault("metadata", {})
        if metadata:
            result["metadata"].update(dict(metadata))
        
        result.setdefault("stage_history", [])
        if from_stage != to_stage:
            result["stage_history"].append({
                "from": from_stage,
                "to": to_stage,
                "at": datetime.now(timezone.utc).isoformat(),
                "reason": reason
            })
        
        result["is_terminal"] = self.is_terminal(to_stage)
        result["stage_index"] = self.stage_index(to_stage)
        
        if to_stage in FAILURE_STAGES:
            result["failure_kind"] = self.get_failure_kind(from_stage)
        
        return result

    def build_transition_event(
        self,
        from_stage: str,
        to_stage: str,
        reason: str = "",
        correlation: Optional[Dict[str, Any]] = None,
        source: str = "web",
    ) -> Dict[str, Any]:
        """Build a transition event dictionary."""
        return {
            "from": from_stage,
            "to": to_stage,
            "reason": reason,
            "at": datetime.now(timezone.utc).isoformat(),
            "correlation": dict(correlation or {}),
            "source": source,
        }

    def ensure_correlation(self, payload: Dict[str, Any]) -> CorrelationContext:
        """Build a CorrelationContext from a payload."""
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

    def build_default_correlation(
        self, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build a default correlation dictionary from a payload."""
        correlation = self.ensure_correlation(payload)
        return correlation.to_dict()

    def attach_correlation(self, contract: Dict[str, Any], correlation: Dict[str, Any]) -> Dict[str, Any]:
        """Attach correlation to a contract dictionary."""
        from .values import CorrelationContext
        corr = CorrelationContext.from_dict(correlation)
        return self._attach_correlation(contract, corr)

    def _attach_correlation(self, contract: Dict[str, Any], correlation: CorrelationContext) -> Dict[str, Any]:
        """Attach correlation to a contract dictionary (internal)."""
        contract = dict(contract or {})
        contract["correlation"] = correlation.to_dict()
        contract.setdefault("metadata", {})
        contract["metadata"].update(
            {k: v for k, v in correlation.to_dict().items() if k in CORRELATION_KEY_FIELDS and v}
        )
        return contract

    def build_event(
        self,
        *,
        kind: str,
        stage: str,
        status: str = "success",
        payload: Optional[Dict[str, Any]] = None,
        correlation: Optional[CorrelationContext] = None,
        source: str = "web",
    ) -> Dict[str, Any]:
        """Build a lifecycle event dictionary."""
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
    """Build a default correlation context from a payload."""
    return LifecycleStateMachine().ensure_correlation(payload or {})


# Singleton instance for convenience
_default_machine: Optional[LifecycleStateMachine] = None


def get_lifecycle_state_machine() -> LifecycleStateMachine:
    """Get or create the default lifecycle state machine instance."""
    global _default_machine
    if _default_machine is None:
        _default_machine = LifecycleStateMachine()
    return _default_machine


__all__ = [
    "LifecycleStateMachine",
    "LIFECYCLE_STAGES",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "RECOVERY_TARGETS",
    "REPAIR_ROUTE_BY_STAGE",
    "CORRELATION_KEY_FIELDS",
    "FAILURE_KIND_BY_STAGE",
    "build_default_correlation",
    "get_lifecycle_state_machine",
]