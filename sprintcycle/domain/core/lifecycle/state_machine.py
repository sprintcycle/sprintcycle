"""Unified lifecycle state machine for SprintCycle.

This module is the canonical lifecycle transition source for web-triggered
execution chains. It provides:
- a single stage vocabulary with phase-substage hierarchy
- authoritative transition rules
- correlation model helpers
- contract mutation helpers

**DDD Design:**
- LifecyclePhase: Primary phase grouping (INITIALIZING, EXECUTING, DELIVERING, GOVERNING, TERMINAL)
- LifecycleSubstage: Detailed sub-state within each phase
- State transitions are validated at substage level
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .values import CorrelationContext


# =============================================================================
# Phase and Substage Enumerations (DDD Domain Concepts)
# =============================================================================

class LifecyclePhase(Enum):
    """
    Primary lifecycle phases.
    
    Phases represent high-level groupings of the lifecycle flow,
    providing a clearer structure for understanding the overall process.
    """
    INITIALIZING = "initializing"
    EXECUTING = "executing"
    DELIVERING = "delivering"
    GOVERNING = "governing"
    TERMINAL = "terminal"

    @classmethod
    def from_string(cls, value: str) -> "LifecyclePhase":
        normalized = str(value or "").strip().lower()
        for phase in cls:
            if phase.value == normalized:
                return phase
        return cls.INITIALIZING

    def to_string(self) -> str:
        return self.value


class LifecycleSubstage(Enum):
    """
    Detailed sub-states within each lifecycle phase.
    
    Substages provide fine-grained tracking while maintaining
    the broader phase context.
    """
    # INITIALIZING substages
    NEW = "new"
    NORMALIZED = "normalized"
    PLANNED = "planned"
    DECOMPOSED = "decomposed"
    
    # EXECUTING substages
    RUNNING = "running"
    OBSERVING = "observing"
    DIAGNOSED = "diagnosed"
    REPAIRING = "repairing"
    VERIFYING = "verifying"
    
    # DELIVERING substages
    DELIVERING = "delivering"
    RUNTIME_LINKED = "runtime_linked"
    
    # GOVERNING substages
    GOVERNING = "governing"
    PROMOTION_READY = "promotion_ready"
    
    # TERMINAL substages
    PROMOTED = "promoted"
    FAILED = "failed"
    ABORTED = "aborted"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, value: str) -> "LifecycleSubstage":
        normalized = str(value or "").strip().lower()
        for substage in cls:
            if substage.value == normalized:
                return substage
        return cls.NEW

    def to_string(self) -> str:
        return self.value

    def is_terminal(self) -> bool:
        return self in (self.PROMOTED, self.FAILED, self.ABORTED, self.CANCELLED)

    def is_recovery(self) -> bool:
        return self in (self.REPAIRING, self.VERIFYING)

    def is_failure(self) -> bool:
        return self in (self.FAILED, self.ABORTED)


# =============================================================================
# State Machine Configuration
# =============================================================================

# Mapping of phases to their substages
PHASE_SUBSTAGES: Dict[LifecyclePhase, Tuple[LifecycleSubstage, ...]] = {
    LifecyclePhase.INITIALIZING: (
        LifecycleSubstage.NEW,
        LifecycleSubstage.NORMALIZED,
        LifecycleSubstage.PLANNED,
        LifecycleSubstage.DECOMPOSED,
    ),
    LifecyclePhase.EXECUTING: (
        LifecycleSubstage.RUNNING,
        LifecycleSubstage.OBSERVING,
        LifecycleSubstage.DIAGNOSED,
        LifecycleSubstage.REPAIRING,
        LifecycleSubstage.VERIFYING,
    ),
    LifecyclePhase.DELIVERING: (
        LifecycleSubstage.DELIVERING,
        LifecycleSubstage.RUNTIME_LINKED,
    ),
    LifecyclePhase.GOVERNING: (
        LifecycleSubstage.GOVERNING,
        LifecycleSubstage.PROMOTION_READY,
    ),
    LifecyclePhase.TERMINAL: (
        LifecycleSubstage.PROMOTED,
        LifecycleSubstage.FAILED,
        LifecycleSubstage.ABORTED,
        LifecycleSubstage.CANCELLED,
    ),
}

# Legacy stage list for backward compatibility
LIFECYCLE_STAGES: tuple[str, ...] = (
    "new",
    "normalized",
    "planned",
    "decomposed",
    "running",
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
    "running": "repairing",
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

# Updated transitions using new substage naming
SUBSTAGE_TRANSITIONS: Dict[str, tuple[str, ...]] = {
    "new": ("normalized", "failed", "cancelled"),
    "normalized": ("planned", "failed", "cancelled"),
    "planned": ("decomposed", "failed", "cancelled"),
    "decomposed": ("running", "failed", "cancelled"),
    "running": ("observing", "diagnosed", "repairing", "failed", "cancelled"),
    "observing": ("diagnosed", "delivering", "repairing", "failed", "cancelled"),
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

# Legacy STAGE_TRANSITIONS for backward compatibility
STAGE_TRANSITIONS: Dict[str, tuple[str, ...]] = SUBSTAGE_TRANSITIONS

REPAIR_ROUTE_BY_STAGE: Dict[str, str] = {
    "running": "repairing",
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
    "decomposed": "",
    "running": "execution_error",
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


def get_phase_for_substage(substage: LifecycleSubstage) -> LifecyclePhase:
    """Get the phase that contains the given substage."""
    for phase, substages in PHASE_SUBSTAGES.items():
        if substage in substages:
            return phase
    return LifecyclePhase.INITIALIZING


def get_substage_index(substage: LifecycleSubstage) -> int:
    """Get the index of a substage within its phase."""
    phase = get_phase_for_substage(substage)
    substages = PHASE_SUBSTAGES[phase]
    return substages.index(substage) if substage in substages else -1


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
    - Supports both phase-substage hierarchy and legacy flat stage model
    
    **Phase-Substage Architecture:**
    - INITIALIZING: NEW → NORMALIZED → PLANNED → DECOMPOSED
    - EXECUTING: RUNNING → OBSERVING → DIAGNOSED → REPAIRING → VERIFYING (recovery loop)
    - DELIVERING: DELIVERING → RUNTIME_LINKED
    - GOVERNING: GOVERNING → PROMOTION_READY
    - TERMINAL: PROMOTED, FAILED, ABORTED, CANCELLED
    """
    
    # Class-level constants for reference
    STAGES = LIFECYCLE_STAGES
    TERMINAL_STAGES = TERMINAL_STAGES
    TRANSITIONS = STAGE_TRANSITIONS
    RECOVERY_TARGETS = RECOVERY_TARGETS
    PHASES = tuple(LifecyclePhase)
    PHASE_SUBSTAGES = PHASE_SUBSTAGES

    # =========================================================================
    # Phase/Substage Normalization
    # =========================================================================

    def normalize_stage(self, stage: object) -> str:
        """Normalize a stage value to canonical string form."""
        if hasattr(stage, 'value'):
            value = str(stage.value).strip().lower()
        else:
            value = str(stage or "").strip().lower()
        
        return value if value in STAGE_TRANSITIONS else "new"

    def normalize_phase(self, phase: object) -> LifecyclePhase:
        """Normalize a phase value to LifecyclePhase enum."""
        if isinstance(phase, LifecyclePhase):
            return phase
        return LifecyclePhase.from_string(str(phase or ""))

    def normalize_substage(self, substage: object) -> LifecycleSubstage:
        """Normalize a substage value to LifecycleSubstage enum."""
        if isinstance(substage, LifecycleSubstage):
            return substage
        return LifecycleSubstage.from_string(str(substage or ""))

    def get_phase_for_substage(self, substage: object) -> LifecyclePhase:
        """Get the phase that contains the given substage."""
        normalized = self.normalize_substage(substage)
        return get_phase_for_substage(normalized)

    def get_substages_for_phase(self, phase: object) -> Tuple[LifecycleSubstage, ...]:
        """Get all substages for a given phase."""
        normalized = self.normalize_phase(phase)
        return PHASE_SUBSTAGES.get(normalized, ())

    def derive_phase(self, substage: object) -> str:
        """Derive the phase from a substage."""
        phase = self.get_phase_for_substage(substage)
        return phase.value

    # =========================================================================
    # Transition Validation (Substage Level)
    # =========================================================================

    def can_transition(self, from_stage: object, to_stage: object) -> bool:
        """Check if a transition is valid (works with both stage strings and enums)."""
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)
        if frm == to:
            return True
        return to in SUBSTAGE_TRANSITIONS.get(frm, ())

    def can_transition_substage(
        self,
        from_substage: LifecycleSubstage,
        to_substage: LifecycleSubstage,
    ) -> bool:
        """Check if a substage transition is valid."""
        return self.can_transition(from_substage.value, to_substage.value)

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

    def validate_substage_transition(
        self,
        from_substage: LifecycleSubstage,
        to_substage: LifecycleSubstage,
    ) -> Optional[str]:
        """Validate a substage transition. Returns None if valid, or error message."""
        return self.validate_transition(from_substage.value, to_substage.value)

    # =========================================================================
    # Next Stage Resolution
    # =========================================================================

    def next_stages(self, stage: object) -> tuple[str, ...]:
        """Get the valid next stages for a given stage."""
        return SUBSTAGE_TRANSITIONS.get(self.normalize_stage(stage), ())

    def next_substages(self, substage: LifecycleSubstage) -> Tuple[LifecycleSubstage, ...]:
        """Get the valid next substages for a given substage."""
        next_stage_strings = self.next_stages(substage)
        return tuple(LifecycleSubstage.from_string(s) for s in next_stage_strings)

    def get_next_substage(self, substage: LifecycleSubstage) -> Optional[LifecycleSubstage]:
        """Get the next substage in the normal flow (skipping failure states)."""
        next_substages = self.next_substages(substage)
        for s in next_substages:
            if s not in (LifecycleSubstage.FAILED, LifecycleSubstage.CANCELLED):
                return s
        return None

    # =========================================================================
    # Stage/Substage Indexing
    # =========================================================================

    def stage_index(self, stage: object) -> int:
        """Get the index of a stage in the lifecycle sequence."""
        normalized = self.normalize_stage(stage)
        try:
            return LIFECYCLE_STAGES.index(normalized)
        except ValueError:
            return -1

    def substage_index(self, substage: LifecycleSubstage) -> int:
        """Get the index of a substage within its phase."""
        return get_substage_index(substage)

    # =========================================================================
    # State Classification
    # =========================================================================

    def is_terminal(self, stage: object) -> bool:
        """Check if a stage is terminal (no further transitions)."""
        normalized = self.normalize_stage(stage)
        return (
            normalized in TERMINAL_STAGES or normalized in FAILURE_STAGES
        )

    def is_terminal_substage(self, substage: LifecycleSubstage) -> bool:
        """Check if a substage is terminal."""
        return substage.is_terminal()

    def is_failure(self, stage: object) -> bool:
        """Check if a stage represents a failure state."""
        return self.normalize_stage(stage) in FAILURE_STAGES

    def is_failure_substage(self, substage: LifecycleSubstage) -> bool:
        """Check if a substage represents a failure state."""
        return substage.is_failure()

    def is_recovery(self, stage: object) -> bool:
        """Check if a stage is a recovery stage."""
        return self.normalize_stage(stage) in RECOVERY_STAGES

    def is_recovery_substage(self, substage: LifecycleSubstage) -> bool:
        """Check if a substage is a recovery stage."""
        return substage.is_recovery()

    # =========================================================================
    # Recovery Logic
    # =========================================================================

    def get_recovery_target(self, stage: object) -> str:
        """Get the recovery target stage for a given stage."""
        normalized = self.normalize_stage(stage)
        return RECOVERY_TARGETS.get(normalized, "repairing")

    def get_recovery_target_substage(self, substage: LifecycleSubstage) -> LifecycleSubstage:
        """Get the recovery target substage for a given substage."""
        target_str = self.get_recovery_target(substage)
        return LifecycleSubstage.from_string(target_str)

    # =========================================================================
    # Failure Handling
    # =========================================================================

    def get_failure_kind(self, stage: object) -> str:
        """Get the failure kind for a given stage."""
        return FAILURE_KIND_BY_STAGE.get(self.normalize_stage(stage), "")

    def get_failure_kind_for_substage(self, substage: LifecycleSubstage) -> str:
        """Get the failure kind for a given substage."""
        return self.get_failure_kind(substage.value)

    # =========================================================================
    # Status Derivation
    # =========================================================================

    def derive_status(self, stage: object) -> str:
        """
        Derive the lifecycle status from a stage.
        
        This method provides the canonical mapping from stage to status.
        Status is derived based on whether the stage represents:
        - A terminal success state
        - A failure state
        - A cancelled state
        - A pending state
        - An active running state
        """
        normalized_stage = self.normalize_stage(stage)
        
        if normalized_stage == "promoted":
            return "promoted"
        if normalized_stage in FAILURE_STAGES:
            if normalized_stage == "cancelled":
                return "cancelled"
            return "failed"
        if normalized_stage == "new":
            return "pending"
        return "running"

    def derive_status_from_substage(self, substage: LifecycleSubstage) -> str:
        """Derive the lifecycle status from a substage."""
        return self.derive_status(substage.value)

    # =========================================================================
    # Allowed Stages
    # =========================================================================

    def get_allowed_next_stages(self, stage: object) -> List[str]:
        """Get a list of allowed next stages (excludes failure states by default)."""
        all_next = list(self.next_stages(stage))
        return [
            s for s in all_next if s not in FAILURE_STAGES
        ]

    def get_allowed_next_substages(self, substage: LifecycleSubstage) -> List[LifecycleSubstage]:
        """Get a list of allowed next substages (excludes failure states by default)."""
        all_next = self.next_substages(substage)
        return [
            s for s in all_next if not s.is_failure() and s != LifecycleSubstage.CANCELLED
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
    # Enumerations
    "LifecyclePhase",
    "LifecycleSubstage",
    
    # State machine
    "LifecycleStateMachine",
    
    # Configuration constants
    "LIFECYCLE_STAGES",
    "SUBSTAGE_TRANSITIONS",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "RECOVERY_TARGETS",
    "PHASE_SUBSTAGES",
    "REPAIR_ROUTE_BY_STAGE",
    "CORRELATION_KEY_FIELDS",
    "FAILURE_KIND_BY_STAGE",
    
    # Helper functions
    "get_phase_for_substage",
    "get_substage_index",
    "build_default_correlation",
    "get_lifecycle_state_machine",
]