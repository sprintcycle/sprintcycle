"""LifecycleRoot aggregate for the lifecycle subdomain.

The LifecycleRoot is the aggregate root for lifecycle management.
It encapsulates all state and behavior related to the execution lifecycle.

**Design Principles:**
- LifecycleRoot is responsible for stage transitions
- Cross-subdomain references use IDs (not objects)
- Immutable update methods return new instances
- State machine logic is delegated to LifecycleStateMachine
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .state_machine import (
    LifecycleStateMachine,
    LIFECYCLE_STAGES,
    TERMINAL_STAGES,
    FAILURE_KIND_BY_STAGE,
    get_lifecycle_state_machine,
)
from .values import (
    StageEvidence,
    StageHistoryEntry,
    CorrelationContext,
    GovernanceRef,
    EvolutionRef,
    RuntimeRef,
    LifecycleEvidence,
)


# =============================================================================
# Enums
# =============================================================================


class LifecycleStatus(Enum):
    """Lifecycle execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROMOTED = "promoted"


class LifecycleStage(Enum):
    """Lifecycle stage enumeration."""

    NEW = "new"
    NORMALIZED = "normalized"
    PLANNED = "planned"
    PREPARED = "prepared"
    DECOMPOSED = "decomposed"
    EXECUTING = "executing"
    OBSERVING = "observing"
    DIAGNOSED = "diagnosed"
    REPAIRING = "repairing"
    VERIFYING = "verifying"
    DELIVERING = "delivering"
    RUNTIME_LINKED = "runtime_linked"
    GOVERNING = "governing"
    PROMOTION_READY = "promotion_ready"
    PROMOTED = "promoted"
    FAILED = "failed"
    ABORTED = "aborted"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, value: str) -> "LifecycleStage":
        """Create stage from string."""
        normalized = value.strip().lower()
        for stage in cls:
            if stage.value == normalized:
                return stage
        return cls.NEW

    def to_string(self) -> str:
        """Convert to string value."""
        return self.value

    def is_terminal(self) -> bool:
        """Check if this is a terminal stage."""
        return self.value in TERMINAL_STAGES

    def get_failure_kind(self) -> str:
        """Get the failure kind for this stage."""
        return FAILURE_KIND_BY_STAGE.get(self.value, "")


# =============================================================================
# Aggregate Root
# =============================================================================


@dataclass
class LifecycleRoot:
    """
    Lifecycle aggregate root.

    This aggregate manages the complete lifecycle of an execution,
    from initialization through promotion or termination.

    **Key Responsibilities:**
    1. Maintain current stage and status
    2. Validate and execute stage transitions
    3. Track stage history
    4. Manage cross-subdomain references (by ID)
    5. Aggregate stage evidence

    **Immutable Updates:**
    All state-modifying methods return new instances.
    This makes the aggregate thread-safe and easier to test.
    """

    # Identity
    contract_id: str
    execution_id: str
    task_id: str
    project_path: str

    # State
    stage: LifecycleStage = LifecycleStage.NEW
    status: LifecycleStatus = LifecycleStatus.PENDING

    # Task type (preserved from original LifecycleContract)
    task_type: str = "project_optimization"
    intent: str = ""

    # Failure information
    failure_kind: str = ""
    failure_reason: str = ""
    failure_code: str = ""

    # Cross-subdomain references (use IDs only)
    governance_ref: Optional[GovernanceRef] = None
    evolution_ref: Optional[EvolutionRef] = None
    runtime_ref: Optional[RuntimeRef] = None

    # Stage evidence
    evidence: LifecycleEvidence = field(
        default_factory=lambda: LifecycleEvidence()
    )

    # History
    stage_history: Tuple[StageHistoryEntry, ...] = field(default_factory=lambda: ())

    # Correlation
    correlation: CorrelationContext = field(default_factory=lambda: CorrelationContext())

    # Metadata
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Transition tracking
    allowed_next_stages: Tuple[str, ...] = field(default_factory=lambda: ())
    transition_reason: str = ""

    # Validation
    validation_errors: Tuple[str, ...] = field(default_factory=lambda: ())

    def __post_init__(self) -> None:
        """Initialize derived fields after construction."""
        # Set up allowed next stages
        if not self.allowed_next_stages:
            machine = get_lifecycle_state_machine()
            self.allowed_next_stages = machine.next_stages(self.stage)

    # =========================================================================
    # Identity
    # =========================================================================

    @property
    def is_terminal(self) -> bool:
        """Check if lifecycle is in a terminal state."""
        return self.stage.is_terminal() or self.status in (
            LifecycleStatus.SUCCESS,
            LifecycleStatus.FAILED,
            LifecycleStatus.CANCELLED,
            LifecycleStatus.PROMOTED,
        )

    @property
    def is_running(self) -> bool:
        """Check if lifecycle is currently running."""
        return self.status == LifecycleStatus.RUNNING

    @property
    def contract_id_or_default(self) -> str:
        """Get contract_id or generate a default."""
        return self.contract_id or f"lifecycle-{uuid4()}"

    # =========================================================================
    # Stage Transitions
    # =========================================================================

    def transition_to(
        self,
        new_stage: LifecycleStage,
        reason: str = "",
        new_status: Optional[LifecycleStatus] = None,
    ) -> "LifecycleRoot":
        """
        Transition to a new stage.

        This is the primary method for advancing the lifecycle.
        It validates the transition and records history.

        **Rules:**
        - Transition must be valid according to state machine
        - History is recorded for each transition
        - Status can be explicitly set or derived

        Returns a new LifecycleRoot instance with the transition applied.
        """
        if self.is_terminal:
            raise ValueError(
                f"Cannot transition from terminal state: {self.stage.value}"
            )

        machine = get_lifecycle_state_machine()
        error = machine.validate_transition(self.stage.value, new_stage.value)
        if error:
            raise ValueError(error)

        # Build history entry
        history_entry = StageHistoryEntry(
            from_stage=self.stage.value,
            to_stage=new_stage.value,
            reason=reason,
        )

        # Determine status
        final_status = new_status or LifecycleStatus(machine.derive_status(new_stage))

        # Determine failure kind if transitioning to failure
        failure_kind = self.failure_kind
        if new_stage in (LifecycleStage.FAILED, LifecycleStage.ABORTED):
            failure_kind = new_stage.get_failure_kind()

        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            stage=new_stage,
            status=final_status,
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=failure_kind,
            failure_reason=self.failure_reason,
            failure_code=self.failure_code,
            governance_ref=self.governance_ref,
            evolution_ref=self.evolution_ref,
            runtime_ref=self.runtime_ref,
            evidence=self.evidence,
            stage_history=self.stage_history + (history_entry,),
            correlation=self.correlation,
            metrics=dict(self.metrics),
            metadata=dict(self.metadata),
            allowed_next_stages=machine.next_stages(new_stage),
            transition_reason=reason,
            validation_errors=(),
        )

    def can_advance_to(self, target_stage: LifecycleStage) -> bool:
        """Check if we can advance to a target stage."""
        machine = get_lifecycle_state_machine()
        return machine.can_transition(self.stage.value, target_stage.value)

    def get_next_stage(self) -> Optional[LifecycleStage]:
        """Get the next stage in the normal flow."""
        machine = get_lifecycle_state_machine()
        next_stages = machine.next_stages(self.stage)
        for stage_str in next_stages:
            if stage_str not in ("failed", "cancelled"):
                return LifecycleStage.from_string(stage_str)
        return None

    # =========================================================================
    # Recovery
    # =========================================================================

    def trigger_recovery(
        self,
        failure_kind: str = "",
        reason: str = "",
    ) -> "LifecycleRoot":
        """
        Trigger recovery flow for the current stage.

        Recovery transitions the lifecycle to the appropriate
        recovery stage (typically 'repairing' or 'verifying').
        """
        machine = get_lifecycle_state_machine()
        recovery_target = machine.get_recovery_target(self.stage)

        recovery_stage = LifecycleStage.from_string(recovery_target)
        
        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            stage=recovery_stage,
            status=LifecycleStatus(machine.derive_status(recovery_stage)),
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=failure_kind or machine.get_failure_kind(self.stage),
            failure_reason=reason,
            failure_code=self.failure_code,
            governance_ref=self.governance_ref,
            evolution_ref=self.evolution_ref,
            runtime_ref=self.runtime_ref,
            evidence=self.evidence,
            stage_history=self.stage_history,
            correlation=self.correlation,
            metrics=dict(self.metrics),
            metadata=dict(self.metadata),
            allowed_next_stages=machine.next_stages(recovery_stage),
            transition_reason=f"Recovery: {reason}",
            validation_errors=(),
        )

    # =========================================================================
    # Stage Evidence
    # =========================================================================

    def add_stage_evidence(self, evidence: StageEvidence) -> "LifecycleRoot":
        """Add evidence for the current stage."""
        new_stages = dict(self.evidence.stages)
        new_stages[evidence.stage] = evidence

        new_evidence = LifecycleEvidence(
            contract=dict(self.evidence.contract),
            stages=new_stages,
            runtime=self.evidence.runtime,
            governance=self.evidence.governance,
            evolution=self.evidence.evolution,
            trace=dict(self.evidence.trace),
            diagnostics=dict(self.evidence.diagnostics),
            recovery=dict(self.evidence.recovery),
            suggestion=dict(self.evidence.suggestion),
        )

        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            stage=self.stage,
            status=self.status,
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=self.failure_kind,
            failure_reason=self.failure_reason,
            failure_code=self.failure_code,
            governance_ref=self.governance_ref,
            evolution_ref=self.evolution_ref,
            runtime_ref=self.runtime_ref,
            evidence=new_evidence,
            stage_history=self.stage_history,
            correlation=self.correlation,
            metrics=dict(self.metrics),
            metadata=dict(self.metadata),
            allowed_next_stages=self.allowed_next_stages,
            transition_reason=self.transition_reason,
            validation_errors=self.validation_errors,
        )

    # =========================================================================
    # Cross-Subdomain References
    # =========================================================================

    def attach_governance(
        self,
        governance_session_id: str,
        gate: str = "",
        approved: bool = False,
    ) -> "LifecycleRoot":
        """Attach a governance reference."""
        ref = GovernanceRef(
            governance_session_id=governance_session_id,
            gate=gate,
            approved=approved,
        )
        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            stage=self.stage,
            status=self.status,
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=self.failure_kind,
            failure_reason=self.failure_reason,
            failure_code=self.failure_code,
            governance_ref=ref,
            evolution_ref=self.evolution_ref,
            runtime_ref=self.runtime_ref,
            evidence=self.evidence,
            stage_history=self.stage_history,
            correlation=self.correlation,
            metrics=dict(self.metrics),
            metadata=dict(self.metadata),
            allowed_next_stages=self.allowed_next_stages,
            transition_reason=self.transition_reason,
            validation_errors=self.validation_errors,
        )

    def attach_evolution(
        self,
        evolution_request_id: str,
        version_id: str = "",
    ) -> "LifecycleRoot":
        """Attach an evolution reference."""
        ref = EvolutionRef(
            evolution_request_id=evolution_request_id,
            version_id=version_id,
        )
        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            stage=self.stage,
            status=self.status,
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=self.failure_kind,
            failure_reason=self.failure_reason,
            failure_code=self.failure_code,
            governance_ref=self.governance_ref,
            evolution_ref=ref,
            runtime_ref=self.runtime_ref,
            evidence=self.evidence,
            stage_history=self.stage_history,
            correlation=self.correlation,
            metrics=dict(self.metrics),
            metadata=dict(self.metadata),
            allowed_next_stages=self.allowed_next_stages,
            transition_reason=self.transition_reason,
            validation_errors=self.validation_errors,
        )

    def attach_runtime(
        self,
        runtime_id: str,
        linked: bool = False,
        healthy: bool = False,
    ) -> "LifecycleRoot":
        """Attach a runtime reference."""
        ref = RuntimeRef(
            runtime_id=runtime_id,
            linked=linked,
            healthy=healthy,
        )
        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            stage=self.stage,
            status=self.status,
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=self.failure_kind,
            failure_reason=self.failure_reason,
            failure_code=self.failure_code,
            governance_ref=self.governance_ref,
            evolution_ref=self.evolution_ref,
            runtime_ref=ref,
            evidence=self.evidence,
            stage_history=self.stage_history,
            correlation=self.correlation,
            metrics=dict(self.metrics),
            metadata=dict(self.metadata),
            allowed_next_stages=self.allowed_next_stages,
            transition_reason=self.transition_reason,
            validation_errors=self.validation_errors,
        )

    # =========================================================================
    # Validation
    # =========================================================================

    def validate(self) -> List[str]:
        """Validate the lifecycle state and return errors."""
        errors: List[str] = []

        # Required fields
        if not self.execution_id:
            errors.append("execution_id is required")
        if not self.task_id:
            errors.append("task_id is required")
        if not self.project_path:
            errors.append("project_path is required")

        # Stage validation
        machine = get_lifecycle_state_machine()
        normalized = machine.normalize_stage(self.stage.value)
        if normalized != self.stage.value:
            errors.append(f"stage is not normalized: {self.stage.value}")

        # Status validation
        valid_statuses = {"pending", "running", "success", "failed", "cancelled", "promoted"}
        if self.status.value not in valid_statuses:
            errors.append(f"invalid status: {self.status.value}")

        # Terminal consistency
        if self.status.value in ("success", "failed", "cancelled", "promoted"):
            if not self.stage.is_terminal():
                errors.append(
                    f"terminal status requires terminal stage: {self.status.value}/{self.stage.value}"
                )

        # Next stages validation
        if self.allowed_next_stages:
            valid_stages_set = set(LIFECYCLE_STAGES) | {"failed", "aborted", "cancelled"}
            if any(stage not in valid_stages_set for stage in self.allowed_next_stages):
                errors.append("allowed_next_stages contains invalid stage")

        return errors

    @property
    def is_valid(self) -> bool:
        """Check if lifecycle state is valid."""
        return not self.validate()

    # =========================================================================
    # Conversion
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for serialization)."""
        errors = self.validate()
        machine = get_lifecycle_state_machine()

        return {
            "contract_id": self.contract_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "project_path": self.project_path,
            "task_type": self.task_type,
            "intent": self.intent,
            "stage": self.stage.value,
            "status": self.status.value,
            "failure_kind": self.failure_kind,
            "failure_reason": self.failure_reason,
            "failure_code": self.failure_code,
            "governance_ref": self.governance_ref.to_dict() if self.governance_ref else None,
            "evolution_ref": self.evolution_ref.to_dict() if self.evolution_ref else None,
            "runtime_ref": self.runtime_ref.to_dict() if self.runtime_ref else None,
            "evidence": self.evidence.to_dict(),
            "stage_history": [
                {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
                for h in self.stage_history
            ],
            "correlation": self.correlation.to_dict(),
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
            "allowed_next_stages": list(self.allowed_next_stages),
            "transition_reason": self.transition_reason,
            # Derived fields
            "is_terminal": self.is_terminal,
            "is_valid": not errors,
            "validation_errors": errors,
            "stage_index": machine.stage_index(self.stage),
            "next_stage": self.get_next_stage().value if self.get_next_stage() else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleRoot":
        """Create from dictionary."""
        governance_ref = None
        if data.get("governance_ref"):
            gr = data["governance_ref"]
            governance_ref = GovernanceRef(
                governance_session_id=gr.get("governance_session_id", ""),
                gate=gr.get("gate", ""),
                approved=gr.get("approved", False),
            )

        evolution_ref = None
        if data.get("evolution_ref"):
            er = data["evolution_ref"]
            evolution_ref = EvolutionRef(
                evolution_request_id=er.get("evolution_request_id", ""),
                version_id=er.get("version_id", ""),
            )

        runtime_ref = None
        if data.get("runtime_ref"):
            rr = data["runtime_ref"]
            runtime_ref = RuntimeRef(
                runtime_id=rr.get("runtime_id", ""),
                linked=rr.get("linked", False),
                healthy=rr.get("healthy", False),
            )

        # Parse stage history
        history = ()
        for entry in data.get("stage_history", []):
            if isinstance(entry, dict):
                history += (
                    StageHistoryEntry(
                        from_stage=entry.get("from", ""),
                        to_stage=entry.get("to", ""),
                        at=entry.get("at", ""),
                        reason=entry.get("reason", ""),
                    ),
                )

        return cls(
            contract_id=data.get("contract_id", ""),
            execution_id=data.get("execution_id", ""),
            task_id=data.get("task_id", ""),
            project_path=data.get("project_path", ""),
            task_type=data.get("task_type", "project_optimization"),
            intent=data.get("intent", ""),
            stage=LifecycleStage.from_string(data.get("stage", "new")),
            status=LifecycleStatus(data.get("status", "pending")),
            failure_kind=data.get("failure_kind", ""),
            failure_reason=data.get("failure_reason", ""),
            failure_code=data.get("failure_code", ""),
            governance_ref=governance_ref,
            evolution_ref=evolution_ref,
            runtime_ref=runtime_ref,
            evidence=LifecycleEvidence(),
            stage_history=history,
            correlation=CorrelationContext.from_dict(data.get("correlation", {})),
            metrics=dict(data.get("metrics", {})),
            metadata=dict(data.get("metadata", {})),
            allowed_next_stages=tuple(data.get("allowed_next_stages", [])),
            transition_reason=data.get("transition_reason", ""),
            validation_errors=tuple(data.get("validation_errors", [])),
        )


# =============================================================================
# Factory
# =============================================================================


def create_lifecycle(
    execution_id: str,
    task_id: str,
    project_path: str,
    task_type: str = "project_optimization",
    intent: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> LifecycleRoot:
    """
    Factory function to create a new lifecycle.

    This is the preferred way to create LifecycleRoot instances
    as it handles all the initialization correctly.
    """
    machine = get_lifecycle_state_machine()
    correlation = CorrelationContext(
        execution_id=execution_id,
        task_id=task_id,
        metadata=dict(metadata or {}),
    )

    return LifecycleRoot(
        contract_id=f"lifecycle-{uuid4()}",
        execution_id=execution_id,
        task_id=task_id,
        project_path=project_path,
        task_type=task_type,
        intent=intent,
        stage=LifecycleStage.NEW,
        status=LifecycleStatus.PENDING,
        correlation=correlation,
        metadata=dict(metadata or {}),
        allowed_next_stages=machine.next_stages(LifecycleStage.NEW),
    )


__all__ = [
    "LifecycleStage",
    "LifecycleStatus",
    "LifecycleRoot",
    "create_lifecycle",
]
