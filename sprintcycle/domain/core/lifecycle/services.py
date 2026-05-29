"""Lifecycle domain services.

This module provides:
- ExecutionStateMachine: for runtime execution states (PENDING, RUNNING, etc.)
- Validation utilities for execution state machine

**Design Principles:**
- ExecutionStateMachine handles runtime execution/task states
- LifecycleStateMachine (in state_machine.py) handles business lifecycle stages
- Services are stateless and follow DDD domain service patterns
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .state_machine import (
    LIFECYCLE_STAGES,
    STAGE_TRANSITIONS,
    TERMINAL_STAGES,
    FAILURE_STAGES,
    RECOVERY_STAGES,
    RECOVERY_TARGETS,
    REPAIR_ROUTE_BY_STAGE,
    CORRELATION_KEY_FIELDS,
    FAILURE_KIND_BY_STAGE,
    get_lifecycle_state_machine,
)


# =============================================================================
# Execution State Machine (Runtime States)
# =============================================================================

class ExecutionStatus:
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
    ExecutionStatus.PAUSED: (
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
    ),
    ExecutionStatus.FAILED: (
        ExecutionStatus.RUNNING,
        ExecutionStatus.CANCELLED,
    ),
    ExecutionStatus.CANCELLED: (),
    ExecutionStatus.COMPLETED: (),
}

TASK_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    ExecutionStatus.PENDING: (
        ExecutionStatus.RUNNING,
        ExecutionStatus.SKIPPED,
        ExecutionStatus.CANCELLED,
    ),
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


@dataclass
class StateTransition:
    """State transition record"""
    entity: str
    entity_id: str
    from_status: str
    to_status: str
    reason: str = ""
    metadata: Dict[str, object] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, object]:
        return {
            "entity": self.entity,
            "entity_id": self.entity_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


def _allowed_execution_transitions(entity: str) -> Dict[str, Tuple[str, ...]]:
    """Get the state transition table for an entity type"""
    entity = (entity or "").strip().lower()
    if entity == "task":
        return TASK_TRANSITIONS
    return EXECUTION_TRANSITIONS


def _can_execute_transition(entity: str, from_status: str, to_status: str) -> bool:
    """Check if an execution state transition is allowed"""
    table = _allowed_execution_transitions(entity)
    frm = (from_status or "").strip().lower()
    to = (to_status or "").strip().lower()
    if frm == to:
        return True
    return to in table.get(frm, ())


def _normalize_execution_status(value: object) -> str:
    """Normalize an execution status value"""
    if isinstance(value, ExecutionStatus):
        return value.value
    return str(value or "").strip().lower()


def _validate_execution_transition(entity: str, from_status: object, to_status: object) -> Optional[str]:
    """Validate an execution state transition"""
    frm = _normalize_execution_status(from_status)
    to = _normalize_execution_status(to_status)
    if not frm or not to:
        return "status cannot be empty"
    if _can_execute_transition(entity, frm, to):
        return None
    return f"illegal state transition: {entity} {frm} -> {to}"


class ExecutionStateMachine:
    """Execution state machine - manages runtime states for tasks/executions"""

    def __init__(self, entity: str = "execution"):
        self.entity = entity

    def can_transition(self, from_status: object, to_status: object) -> bool:
        return _can_execute_transition(
            self.entity, 
            _normalize_execution_status(from_status), 
            _normalize_execution_status(to_status)
        )

    def validate_transition(self, from_status: object, to_status: object) -> Optional[str]:
        return _validate_execution_transition(self.entity, from_status, to_status)

    def allowed_transitions(self) -> Dict[str, Tuple[str, ...]]:
        return _allowed_execution_transitions(self.entity)


def summarize_execution_state_machine() -> Dict[str, Dict[str, List[str]]]:
    """Summarize execution state machine configuration"""
    return {
        "execution": {k: list(v) for k, v in EXECUTION_TRANSITIONS.items()},
        "task": {k: list(v) for k, v in TASK_TRANSITIONS.items()},
    }


def validate_transition(machine_type: str, from_state: object, to_state: object) -> Optional[str]:
    """
    Validate a transition for the specified state machine type.
    
    Args:
        machine_type: "execution" for execution state machine, or "lifecycle" for lifecycle state machine
        from_state: The current state
        to_state: The target state
    
    Returns:
        None if valid, or an error message if invalid.
    """
    if machine_type == "execution":
        service = ExecutionStateMachine()
        return service.validate_transition(from_state, to_state)
    else:
        machine = get_lifecycle_state_machine()
        return machine.validate_transition(from_state, to_state)


__all__ = [
    # Execution State Machine (Runtime States)
    "ExecutionStatus",
    "EXECUTION_TRANSITIONS",
    "TASK_TRANSITIONS",
    "StateTransition",
    "ExecutionStateMachine",
    "summarize_execution_state_machine",
    # Lifecycle State Machine constants (re-exported for convenience)
    "LIFECYCLE_STAGES",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "STAGE_TRANSITIONS",
    "RECOVERY_TARGETS",
    "REPAIR_ROUTE_BY_STAGE",
    "CORRELATION_KEY_FIELDS",
    "FAILURE_KIND_BY_STAGE",
    "validate_transition",
]