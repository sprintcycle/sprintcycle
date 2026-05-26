"""Domain events for cross-subdomain communication.

This module defines the canonical domain events that flow between
Execution, Governance, and Evolution subdomains.

**Design Principles:**
- Events are immutable (frozen dataclass)
- Events contain only IDs and scalar metadata (no aggregate objects)
- Events follow the past-tense naming convention (e.g., SprintCompleted)
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4


@dataclass(frozen=True)
class DomainEvent(ABC):
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        """Event type derived from class name."""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# Execution Subdomain Events
# =============================================================================


@dataclass(frozen=True)
class ExecutionStarted(DomainEvent):
    """Execution lifecycle has started."""

    execution_id: str = ""
    task_id: str = ""
    project_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "project_path": self.project_path,
            }
        )
        return base


@dataclass(frozen=True)
class SprintStarted(DomainEvent):
    """A sprint has started execution."""

    sprint_id: str = ""
    release_plan_id: str = ""
    sprint_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "sprint_id": self.sprint_id,
                "release_plan_id": self.release_plan_id,
                "sprint_index": self.sprint_index,
            }
        )
        return base


@dataclass(frozen=True)
class TaskStarted(DomainEvent):
    """A task within a sprint has started."""

    sprint_id: str = ""
    task_id: str = ""
    task_description: str = ""
    agent: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "sprint_id": self.sprint_id,
                "task_id": self.task_id,
                "task_description": self.task_description,
                "agent": self.agent,
            }
        )
        return base


@dataclass(frozen=True)
class TaskCompleted(DomainEvent):
    """A task within a sprint has completed."""

    sprint_id: str = ""
    task_id: str = ""
    status: str = ""  # "success", "failed", "skipped"
    duration: float = 0.0
    output: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "sprint_id": self.sprint_id,
                "task_id": self.task_id,
                "status": self.status,
                "duration": self.duration,
                "output": self.output[:500] if len(self.output) > 500 else self.output,
            }
        )
        return base


@dataclass(frozen=True)
class SprintCompleted(DomainEvent):
    """A sprint has completed."""

    sprint_id: str = ""
    release_plan_id: str = ""
    status: str = ""  # "success", "failed", "partial"
    success_rate: float = 0.0
    task_count: int = 0
    success_count: int = 0
    failed_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "sprint_id": self.sprint_id,
                "release_plan_id": self.release_plan_id,
                "status": self.status,
                "success_rate": self.success_rate,
                "task_count": self.task_count,
                "success_count": self.success_count,
                "failed_count": self.failed_count,
            }
        )
        return base


@dataclass(frozen=True)
class ReleasePlanCompleted(DomainEvent):
    """All sprints in a release plan have completed."""

    release_plan_id: str = ""
    execution_id: str = ""
    overall_success_rate: float = 0.0
    sprint_count: int = 0
    governance_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "release_plan_id": self.release_plan_id,
                "execution_id": self.execution_id,
                "overall_success_rate": self.overall_success_rate,
                "sprint_count": self.sprint_count,
                "governance_required": self.governance_required,
            }
        )
        return base


# =============================================================================
# Lifecycle Subdomain Events
# =============================================================================


@dataclass(frozen=True)
class StageTransitioned(DomainEvent):
    """Lifecycle stage has transitioned."""

    execution_id: str = ""
    task_id: str = ""
    from_stage: str = ""
    to_stage: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "from_stage": self.from_stage,
                "to_stage": self.to_stage,
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class RecoveryTriggered(DomainEvent):
    """Recovery flow has been triggered."""

    execution_id: str = ""
    task_id: str = ""
    from_stage: str = ""
    target_stage: str = ""
    failure_kind: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "from_stage": self.from_stage,
                "target_stage": self.target_stage,
                "failure_kind": self.failure_kind,
            }
        )
        return base


# =============================================================================
# Governance Subdomain Events
# =============================================================================


@dataclass(frozen=True)
class GovernanceStarted(DomainEvent):
    """Governance check has started."""

    session_id: str = ""
    gate: str = ""  # "planning", "review", "production", "promotion"
    execution_id: str = ""
    release_plan_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "session_id": self.session_id,
                "gate": self.gate,
                "execution_id": self.execution_id,
                "release_plan_id": self.release_plan_id,
            }
        )
        return base


@dataclass(frozen=True)
class RuleEvaluated(DomainEvent):
    """A governance rule has been evaluated."""

    session_id: str = ""
    rule_id: str = ""
    passed: bool = False
    severity: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "session_id": self.session_id,
                "rule_id": self.rule_id,
                "passed": self.passed,
                "severity": self.severity,
            }
        )
        return base


@dataclass(frozen=True)
class GovernanceCompleted(DomainEvent):
    """Governance check has completed."""

    session_id: str = ""
    gate: str = ""
    passed: bool = False
    error_count: int = 0
    warning_count: int = 0
    hitl_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "session_id": self.session_id,
                "gate": self.gate,
                "passed": self.passed,
                "error_count": self.error_count,
                "warning_count": self.warning_count,
                "hitl_required": self.hitl_required,
            }
        )
        return base


@dataclass(frozen=True)
class HitlDecisionRequested(DomainEvent):
    """Human-in-the-loop decision has been requested."""

    interaction_id: str = ""
    session_id: str = ""
    gate: str = ""
    title: str = ""
    summary: str = ""
    risk_level: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "interaction_id": self.interaction_id,
                "session_id": self.session_id,
                "gate": self.gate,
                "title": self.title,
                "summary": self.summary,
                "risk_level": self.risk_level,
            }
        )
        return base


@dataclass(frozen=True)
class HitlDecisionMade(DomainEvent):
    """Human-in-the-loop decision has been made."""

    interaction_id: str = ""
    session_id: str = ""
    decision: str = ""  # "approve", "reject", "retry", "modify"
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "interaction_id": self.interaction_id,
                "session_id": self.session_id,
                "decision": self.decision,
                "note": self.note,
            }
        )
        return base


# =============================================================================
# Evolution Subdomain Events
# =============================================================================


@dataclass(frozen=True)
class EvolutionRequested(DomainEvent):
    """Evolution process has been requested."""

    request_id: str = ""
    target: str = ""  # "code", "requirement"
    project_path: str = ""
    mode: str = ""  # "multi_sprint", "single_sprint"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "request_id": self.request_id,
                "target": self.target,
                "project_path": self.project_path,
                "mode": self.mode,
            }
        )
        return base


@dataclass(frozen=True)
class SandboxCreated(DomainEvent):
    """Evolution sandbox has been created."""

    sandbox_id: str = ""
    request_id: str = ""
    backend: str = ""  # "worktree", "docker", "hybrid"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "sandbox_id": self.sandbox_id,
                "request_id": self.request_id,
                "backend": self.backend,
            }
        )
        return base


@dataclass(frozen=True)
class VersionCreated(DomainEvent):
    """A version artifact has been created."""

    version_id: str = ""
    request_id: str = ""
    commit_hash: str = ""
    tag: str = ""
    branch: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "version_id": self.version_id,
                "request_id": self.request_id,
                "commit_hash": self.commit_hash,
                "tag": self.tag,
                "branch": self.branch,
            }
        )
        return base


@dataclass(frozen=True)
class ValidationCompleted(DomainEvent):
    """Version validation has completed."""

    version_id: str = ""
    request_id: str = ""
    success: bool = False
    checks_passed: int = 0
    checks_failed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "version_id": self.version_id,
                "request_id": self.request_id,
                "success": self.success,
                "checks_passed": self.checks_passed,
                "checks_failed": self.checks_failed,
            }
        )
        return base


@dataclass(frozen=True)
class EvolutionPromoted(DomainEvent):
    """Evolution has been promoted to production."""

    request_id: str = ""
    version_id: str = ""
    promoted_by: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "request_id": self.request_id,
                "version_id": self.version_id,
                "promoted_by": self.promoted_by,
            }
        )
        return base


@dataclass(frozen=True)
class RollbackPerformed(DomainEvent):
    """A rollback has been performed."""

    request_id: str = ""
    version_id: str = ""
    restored_to: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "request_id": self.request_id,
                "version_id": self.version_id,
                "restored_to": self.restored_to,
            }
        )
        return base


# =============================================================================
# Event Registry
# =============================================================================

# All domain events for validation and discovery
ALL_EVENTS: Tuple[type[DomainEvent], ...] = (
    # Execution
    ExecutionStarted,
    SprintStarted,
    TaskStarted,
    TaskCompleted,
    SprintCompleted,
    ReleasePlanCompleted,
    # Lifecycle
    StageTransitioned,
    RecoveryTriggered,
    # Governance
    GovernanceStarted,
    RuleEvaluated,
    GovernanceCompleted,
    HitlDecisionRequested,
    HitlDecisionMade,
    # Evolution
    EvolutionRequested,
    SandboxCreated,
    VersionCreated,
    ValidationCompleted,
    EvolutionPromoted,
    RollbackPerformed,
)


def get_event_by_type(event_type: str) -> Optional[type[DomainEvent]]:
    """Get event class by event type name."""
    for event_cls in ALL_EVENTS:
        if event_cls.__name__ == event_type:
            return event_cls
    return None


__all__ = [
    "DomainEvent",
    # Execution
    "ExecutionStarted",
    "SprintStarted",
    "TaskStarted",
    "TaskCompleted",
    "SprintCompleted",
    "ReleasePlanCompleted",
    # Lifecycle
    "StageTransitioned",
    "RecoveryTriggered",
    # Governance
    "GovernanceStarted",
    "RuleEvaluated",
    "GovernanceCompleted",
    "HitlDecisionRequested",
    "HitlDecisionMade",
    # Evolution
    "EvolutionRequested",
    "SandboxCreated",
    "VersionCreated",
    "ValidationCompleted",
    "EvolutionPromoted",
    "RollbackPerformed",
    # Helpers
    "ALL_EVENTS",
    "get_event_by_type",
]
