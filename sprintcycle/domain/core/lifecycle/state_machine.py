"""Unified lifecycle state machine for SprintCycle.

This module provides a single state machine that handles both:
1. Execution runtime states (PENDING, RUNNING, COMPLETED, FAILED, etc.)
2. Lifecycle business stages (NEW, NORMALIZED, PLANNED, RUNNING, etc.)

**DDD Design:**
- LifecyclePhase: Primary phase grouping (INITIALIZING, EXECUTING, DELIVERING, GOVERNING, TERMINAL)
- LifecycleSubstage: Detailed sub-state within each phase
- State transitions are validated at substage level

**Context Switching:**
- context="execution": Runtime execution states
- context="lifecycle": Business lifecycle stages
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .values import CorrelationContext


# =============================================================================
# Execution Status (Runtime States)
# =============================================================================

class ExecutionStatus(Enum):
    """Execution status enum - for task/execution level state management"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUCCESS = "success"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


EXECUTION_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    ExecutionStatus.PENDING: (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    ExecutionStatus.RUNNING: (
        ExecutionStatus.PAUSED,
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.SUCCESS,
    ),
    ExecutionStatus.PAUSED: (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    ExecutionStatus.FAILED: (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    ExecutionStatus.CANCELLED: (),
    ExecutionStatus.COMPLETED: (),
}


TASK_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    ExecutionStatus.PENDING: (ExecutionStatus.RUNNING, ExecutionStatus.SKIPPED, ExecutionStatus.CANCELLED),
    ExecutionStatus.RUNNING: (
        ExecutionStatus.SUCCESS,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.SKIPPED,
    ),
    ExecutionStatus.FAILED: (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    ExecutionStatus.SUCCESS: (),
    ExecutionStatus.SKIPPED: (),
    ExecutionStatus.TIMEOUT: (),
    ExecutionStatus.CANCELLED: (),
}


# =============================================================================
# Phase and Substage Enumerations (Business Lifecycle)
# =============================================================================

class LifecyclePhase(Enum):
    """Primary lifecycle phases."""
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


class LifecycleSubstage(Enum):
    """Detailed sub-states within each lifecycle phase."""
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

    def is_terminal(self) -> bool:
        return self in (self.PROMOTED, self.FAILED, self.ABORTED, self.CANCELLED)

    def is_recovery(self) -> bool:
        return self in (self.REPAIRING, self.VERIFYING)

    def is_failure(self) -> bool:
        return self in (self.FAILED, self.ABORTED)


# =============================================================================
# State Machine Configuration
# =============================================================================

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


LIFECYCLE_STAGES: tuple[str, ...] = (
    "new", "normalized", "planned", "decomposed",
    "running", "observing", "diagnosed", "repairing", "verifying",
    "delivering", "runtime_linked",
    "governing", "promotion_ready",
    "promoted",
)


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

RECOVERY_STAGES: tuple[str, ...] = ("repairing", "verifying")
FAILURE_STAGES: tuple[str, ...] = ("failed", "aborted", "cancelled")
TERMINAL_STAGES: tuple[str, ...] = ("promoted", "failed", "aborted", "cancelled")


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


CORRELATION_KEY_FIELDS: tuple[str, ...] = (
    "request_id", "execution_id", "task_id", "suggestion_id", "runtime_id", "version_id",
)


# =============================================================================
# Helper Functions
# =============================================================================

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


# =============================================================================
# Unified State Machine
# =============================================================================

@dataclass(slots=True)
class LifecycleStateMachine:
    """
    Unified lifecycle state machine.
    
    Handles both execution runtime states and business lifecycle stages
    through the `context` parameter:
    - context="execution": Uses EXECUTION_TRANSITIONS or TASK_TRANSITIONS
    - context="lifecycle": Uses SUBSTAGE_TRANSITIONS
    
    **Design Principles:**
    - Stateless domain service (no internal state beyond configuration)
    - Methods are pure functions where possible
    - Single source of truth for all transition rules
    - Supports both phase-substage hierarchy and flat stage model
    """
    
    context: str = "lifecycle"
    
    # Class-level constants for reference
    STAGES = LIFECYCLE_STAGES
    TERMINAL_STAGES = TERMINAL_STAGES
    TRANSITIONS = SUBSTAGE_TRANSITIONS
    RECOVERY_TARGETS = RECOVERY_TARGETS
    PHASES = tuple(LifecyclePhase)
    PHASE_SUBSTAGES = PHASE_SUBSTAGES
    
    # Execution context constants
    EXECUTION_STATES = tuple(s.value for s in ExecutionStatus)
    EXECUTION_TRANSITIONS = EXECUTION_TRANSITIONS
    TASK_TRANSITIONS = TASK_TRANSITIONS

    def _get_transitions(self) -> Dict[str, Tuple[str, ...]]:
        """Get the appropriate transition table based on context."""
        if self.context == "execution":
            return EXECUTION_TRANSITIONS
        elif self.context == "task":
            return TASK_TRANSITIONS
        else:
            return SUBSTAGE_TRANSITIONS

    def _get_valid_states(self) -> set[str]:
        """Get valid states for the current context."""
        if self.context == "execution":
            return set(s.value for s in ExecutionStatus)
        elif self.context == "task":
            return set(s.value for s in ExecutionStatus)
        else:
            return set(LIFECYCLE_STAGES) | {"failed", "aborted", "cancelled"}

    # =========================================================================
    # Normalization
    # =========================================================================

    def normalize_state(self, state: object) -> str:
        """Normalize a state value to canonical string form."""
        if hasattr(state, 'value'):
            value = str(state.value).strip().lower()
        else:
            value = str(state or "").strip().lower()
        
        valid_states = self._get_valid_states()
        return value if value in valid_states else ("pending" if self.context in ["execution", "task"] else "new")

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

    # =========================================================================
    # Transition Validation
    # =========================================================================

    def can_transition(self, from_state: object, to_state: object) -> bool:
        """Check if a transition is valid."""
        frm = self.normalize_state(from_state)
        to = self.normalize_state(to_state)
        if frm == to:
            return True
        transitions = self._get_transitions()
        return to in transitions.get(frm, ())

    def validate_transition(self, from_state: object, to_state: object) -> Optional[str]:
        """Validate a state transition. Returns None if valid, or error message."""
        frm = self.normalize_state(from_state)
        to = self.normalize_state(to_state)
        
        if not frm:
            return "state cannot be empty"
        if not to:
            return "target state cannot be empty"

        if self.can_transition(frm, to):
            return None

        return f"illegal {self.context} transition: {frm} -> {to}"

    # =========================================================================
    # Next State Resolution
    # =========================================================================

    def next_states(self, state: object) -> tuple[str, ...]:
        """Get the valid next states for a given state."""
        return self._get_transitions().get(self.normalize_state(state), ())
    
    def next_stages(self, state: object) -> tuple[str, ...]:
        """Get the valid next stages for a given state. Alias for next_states."""
        return self.next_states(state)

    def normalize_stage(self, stage: object) -> str:
        """Normalize a stage value. Alias for normalize_state."""
        return self.normalize_state(stage)

    def get_allowed_next_stages(self, stage: object) -> list[str]:
        """Get allowed next stages as a list (excluding failure/cancellation states)."""
        next_stages_list = list(self.next_stages(stage))
        # Filter out failure and cancelled states to get only "normal" transitions
        return [s for s in next_stages_list if s not in ("failed", "cancelled", "aborted")]

    def build_transition_event(
        self,
        contract: Dict[str, Any],
        to_stage: str,
        *,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a transition event dictionary."""
        return self.transition(contract, to_stage, reason=reason, metadata=metadata)

    def attach_correlation(
        self,
        contract: Dict[str, Any],
        correlation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Attach correlation context to a contract."""
        result = dict(contract)
        result["correlation"] = dict(correlation)
        return result

    # =========================================================================
    # Lifecycle-specific Methods
    # =========================================================================

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

    def can_transition_substage(self, from_substage: LifecycleSubstage, to_substage: LifecycleSubstage) -> bool:
        """Check if a substage transition is valid."""
        return self.can_transition(from_substage.value, to_substage.value)

    def validate_substage_transition(self, from_substage: LifecycleSubstage, to_substage: LifecycleSubstage) -> Optional[str]:
        """Validate a substage transition."""
        return self.validate_transition(from_substage.value, to_substage.value)

    def next_substages(self, substage: LifecycleSubstage) -> Tuple[LifecycleSubstage, ...]:
        """Get the valid next substages for a given substage."""
        next_stage_strings = self.next_states(substage)
        return tuple(LifecycleSubstage.from_string(s) for s in next_stage_strings)

    def get_next_substage(self, substage: LifecycleSubstage) -> Optional[LifecycleSubstage]:
        """Get the next substage in the normal flow."""
        next_substages = self.next_substages(substage)
        for s in next_substages:
            if s not in (LifecycleSubstage.FAILED, LifecycleSubstage.CANCELLED):
                return s
        return None

    # =========================================================================
    # State Classification
    # =========================================================================

    def is_terminal(self, state: object) -> bool:
        """Check if a state is terminal."""
        normalized = self.normalize_state(state)
        if self.context in ["execution", "task"]:
            return normalized in ("completed", "success", "failed", "cancelled", "timeout", "skipped")
        return normalized in TERMINAL_STAGES or normalized in FAILURE_STAGES

    def is_failure(self, state: object) -> bool:
        """Check if a state represents a failure."""
        normalized = self.normalize_state(state)
        if self.context in ["execution", "task"]:
            return normalized in ("failed", "timeout")
        return normalized in FAILURE_STAGES

    def is_recovery(self, state: object) -> bool:
        """Check if a state is a recovery state."""
        if self.context in ["execution", "task"]:
            return False
        return self.normalize_state(state) in RECOVERY_STAGES

    # =========================================================================
    # Recovery Logic (Lifecycle context only)
    # =========================================================================

    def get_recovery_target(self, state: object) -> str:
        """Get the recovery target state for a given state."""
        if self.context in ["execution", "task"]:
            return "running"
        normalized = self.normalize_state(state)
        return RECOVERY_TARGETS.get(normalized, "repairing")

    def get_recovery_target_substage(self, substage: LifecycleSubstage) -> LifecycleSubstage:
        """Get the recovery target substage."""
        target_str = self.get_recovery_target(substage)
        return LifecycleSubstage.from_string(target_str)

    # =========================================================================
    # Failure Handling (Lifecycle context only)
    # =========================================================================

    def get_failure_kind(self, state: object) -> str:
        """Get the failure kind for a given state."""
        if self.context in ["execution", "task"]:
            normalized = self.normalize_state(state)
            if normalized == "timeout":
                return "timeout_error"
            return "execution_error"
        return FAILURE_KIND_BY_STAGE.get(self.normalize_state(state), "")

    def get_failure_kind_for_substage(self, substage: LifecycleSubstage) -> str:
        """Get the failure kind for a given substage."""
        return self.get_failure_kind(substage.value)

    # =========================================================================
    # Status Derivation
    # =========================================================================

    def derive_status(self, state: object) -> str:
        """Derive the lifecycle status from a state."""
        normalized_state = self.normalize_state(state)
        
        if self.context in ["execution", "task"]:
            return normalized_state
        
        if normalized_state == "promoted":
            return "promoted"
        if normalized_state in FAILURE_STAGES:
            if normalized_state == "cancelled":
                return "cancelled"
            return "failed"
        if normalized_state == "new":
            return "pending"
        return "running"

    def derive_status_from_substage(self, substage: LifecycleSubstage) -> str:
        """Derive the lifecycle status from a substage."""
        return self.derive_status(substage.value)

    # =========================================================================
    # Indexing
    # =========================================================================

    def stage_index(self, stage: object) -> int:
        """Get the index of a stage in the lifecycle sequence."""
        normalized = self.normalize_state(stage)
        try:
            return LIFECYCLE_STAGES.index(normalized)
        except ValueError:
            return -1

    def substage_index(self, substage: LifecycleSubstage) -> int:
        """Get the index of a substage within its phase."""
        return get_substage_index(substage)

    # =========================================================================
    # Contract Transition
    # =========================================================================

    def transition(
        self,
        contract: Dict[str, Any],
        to_stage: str,
        *,
        status: Optional[str] = None,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Transition a contract dictionary to a new stage."""
        contract = dict(contract or {})
        from_stage = contract.get("stage", "new") if self.context == "lifecycle" else contract.get("status", "pending")
        
        if from_stage == "failed" and to_stage == "repairing":
            pass
        else:
            error = self.validate_transition(from_stage, to_stage)
            if error:
                raise ValueError(error)
        
        result = dict(contract)
        result["stage" if self.context == "lifecycle" else "status"] = to_stage
        
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

    # =========================================================================
    # Correlation Helpers
    # =========================================================================

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

    def build_default_correlation(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a default correlation dictionary."""
        correlation = self.ensure_correlation(payload)
        return correlation.to_dict()


# =============================================================================
# Singleton Instance
# =============================================================================

_default_machine: Optional[LifecycleStateMachine] = None


def get_lifecycle_state_machine(context: str = "lifecycle") -> LifecycleStateMachine:
    """Get or create the lifecycle state machine instance."""
    global _default_machine
    if _default_machine is None:
        _default_machine = LifecycleStateMachine(context=context)
    return _default_machine


def build_default_correlation(payload: Optional[Dict[str, Any]] = None) -> CorrelationContext:
    """Build a default correlation context."""
    return LifecycleStateMachine().ensure_correlation(payload or {})


__all__ = [
    # Execution Status (Runtime States)
    "ExecutionStatus",
    "EXECUTION_TRANSITIONS",
    "TASK_TRANSITIONS",
    # Lifecycle Phase/Substage Enumerations
    "LifecyclePhase",
    "LifecycleSubstage",
    # Unified State Machine
    "LifecycleStateMachine",
    # Configuration constants
    "LIFECYCLE_STAGES",
    "SUBSTAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "RECOVERY_TARGETS",
    "PHASE_SUBSTAGES",
    "CORRELATION_KEY_FIELDS",
    "FAILURE_KIND_BY_STAGE",
    # Helper functions
    "get_phase_for_substage",
    "get_substage_index",
    "build_default_correlation",
    "get_lifecycle_state_machine",
]