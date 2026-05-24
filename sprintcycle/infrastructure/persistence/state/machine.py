"""Execution state machine helpers.

This module formalizes the allowed lifecycle transitions for execution / sprint / task
states so the console can reason about recovery, replay, and invalid transitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sprintcycle.domain.interfaces import ExecutionStatus

EXECUTION_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    ExecutionStatus.PENDING.value: (ExecutionStatus.RUNNING.value, ExecutionStatus.CANCELLED.value),
    ExecutionStatus.RUNNING.value: (
        ExecutionStatus.PAUSED.value,
        ExecutionStatus.COMPLETED.value,
        ExecutionStatus.FAILED.value,
        ExecutionStatus.CANCELLED.value,
        ExecutionStatus.SUCCESS.value,
    ),
    ExecutionStatus.PAUSED.value: (
        ExecutionStatus.RUNNING.value,
        ExecutionStatus.CANCELLED.value,
    ),
    ExecutionStatus.FAILED.value: (
        ExecutionStatus.RUNNING.value,
        ExecutionStatus.CANCELLED.value,
    ),
    ExecutionStatus.CANCELLED.value: (),
    ExecutionStatus.COMPLETED.value: (),
}

TASK_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    ExecutionStatus.PENDING.value: (
        ExecutionStatus.RUNNING.value,
        ExecutionStatus.SKIPPED.value,
        ExecutionStatus.CANCELLED.value,
    ),
    ExecutionStatus.RUNNING.value: (
        ExecutionStatus.SUCCESS.value,
        ExecutionStatus.FAILED.value,
        ExecutionStatus.TIMEOUT.value,
        ExecutionStatus.CANCELLED.value,
        ExecutionStatus.SKIPPED.value,
    ),
    ExecutionStatus.FAILED.value: (ExecutionStatus.RUNNING.value, ExecutionStatus.CANCELLED.value),
    ExecutionStatus.SUCCESS.value: (),
    ExecutionStatus.SKIPPED.value: (),
    ExecutionStatus.TIMEOUT.value: (),
    ExecutionStatus.CANCELLED.value: (),
}


@dataclass
class StateTransition:
    entity: str
    entity_id: str
    from_status: str
    to_status: str
    reason: str = ""
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return {
            "entity": self.entity,
            "entity_id": self.entity_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


def allowed_transitions(entity: str) -> Dict[str, Tuple[str, ...]]:
    entity = (entity or "").strip().lower()
    if entity == "task":
        return TASK_TRANSITIONS
    return EXECUTION_TRANSITIONS


def can_transition(entity: str, from_status: str, to_status: str) -> bool:
    table = allowed_transitions(entity)
    frm = (from_status or "").strip().lower()
    to = (to_status or "").strip().lower()
    if frm == to:
        return True
    return to in table.get(frm, ())


def normalize_status(value: object) -> str:
    if isinstance(value, ExecutionStatus):
        return value.value
    return str(value or "").strip().lower()


def validate_transition(entity: str, from_status: object, to_status: object) -> Optional[str]:
    frm = normalize_status(from_status)
    to = normalize_status(to_status)
    if not frm or not to:
        return "状态不能为空"
    if can_transition(entity, frm, to):
        return None
    return f"非法状态迁移: {entity} {frm} -> {to}"


@dataclass
class ExecutionStateMachine:
    entity: str = "execution"

    def can_transition(self, from_status: object, to_status: object) -> bool:
        return can_transition(self.entity, normalize_status(from_status), normalize_status(to_status))

    def validate_transition(self, from_status: object, to_status: object) -> Optional[str]:
        return validate_transition(self.entity, from_status, to_status)

    def allowed_transitions(self) -> Dict[str, Tuple[str, ...]]:
        return allowed_transitions(self.entity)


def summarize_state_machine() -> Dict[str, List[str]]:
    return {
        "execution": {k: list(v) for k, v in EXECUTION_TRANSITIONS.items()},
        "task": {k: list(v) for k, v in TASK_TRANSITIONS.items()},
    }
