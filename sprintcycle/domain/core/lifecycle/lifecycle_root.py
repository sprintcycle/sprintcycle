"""LifecycleRoot aggregate for the lifecycle subdomain.

The LifecycleRoot is the aggregate root for lifecycle management.
It encapsulates all state and behavior related to the execution lifecycle.

**Design Principles:**
- LifecycleRoot is responsible for stage transitions
- Cross-subdomain references use IDs (not objects)
- Immutable update methods return new instances
- State machine logic is delegated to LifecycleStateMachine
- Uses phase-substage hierarchy for better organization

**Phase-Substage Architecture:**
- INITIALIZING: NEW → NORMALIZED → PLANNED → DECOMPOSED
- EXECUTING: RUNNING → OBSERVING → DIAGNOSED → REPAIRING → VERIFYING
- DELIVERING: DELIVERING → RUNTIME_LINKED
- GOVERNING: GOVERNING → PROMOTION_READY
- TERMINAL: PROMOTED, FAILED, ABORTED, CANCELLED

**External Interface Compatibility:**
- to_dict(): Produces JSON-serializable output for API/Dashboard
- from_dict(): Reconstructs from external data
- This single class replaces the previous LifecycleRoot + LifecycleContract duality
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .state_machine import (
    LifecycleStateMachine,
    LifecyclePhase,
    LifecycleSubstage,
    LIFECYCLE_STAGES,
    TERMINAL_STAGES,
    FAILURE_KIND_BY_STAGE,
    get_lifecycle_state_machine,
    get_phase_for_substage,
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
# Status Enumeration
# =============================================================================

class LifecycleStatus(Enum):
    """Lifecycle execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PROMOTED = "promoted"


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
    1. Maintain current phase, substage and status
    2. Validate and execute stage transitions
    3. Track stage history
    4. Manage cross-subdomain references (by ID)
    5. Aggregate stage evidence

    **Immutable Updates:**
    All state-modifying methods return new instances.
    This makes the aggregate thread-safe and easier to test.

    **Phase-Substage Architecture:**
    - INITIALIZING: NEW → NORMALIZED → PLANNED → DECOMPOSED
    - EXECUTING: RUNNING → OBSERVING → DIAGNOSED → REPAIRING → VERIFYING
    - DELIVERING: DELIVERING → RUNTIME_LINKED
    - GOVERNING: GOVERNING → PROMOTION_READY
    - TERMINAL: PROMOTED, FAILED, ABORTED, CANCELLED
    """

    # Identity
    contract_id: str
    execution_id: str
    task_id: str
    project_path: str

    # State (phase-substage model)
    phase: LifecyclePhase = LifecyclePhase.INITIALIZING
    substage: LifecycleSubstage = LifecycleSubstage.NEW
    status: LifecycleStatus = LifecycleStatus.PENDING

    # Task type
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
    allowed_next_substages: Tuple[LifecycleSubstage, ...] = field(default_factory=lambda: ())
    transition_reason: str = ""

    # Validation
    validation_errors: Tuple[str, ...] = field(default_factory=lambda: ())

    def __post_init__(self) -> None:
        """Initialize derived fields after construction."""
        self.phase = get_phase_for_substage(self.substage)
        
        if not self.allowed_next_stages:
            machine = get_lifecycle_state_machine()
            self.allowed_next_stages = machine.next_stages(self.substage)
        
        if not self.allowed_next_substages:
            machine = get_lifecycle_state_machine()
            self.allowed_next_substages = machine.next_substages(self.substage)

    # =========================================================================
    # Identity
    # =========================================================================

    @property
    def is_terminal(self) -> bool:
        """Check if lifecycle is in a terminal state."""
        return self.substage.is_terminal() or self.status in (
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
    def current_stage_value(self) -> str:
        """Get the current stage value."""
        return self.substage.value

    @property
    def contract_id_or_default(self) -> str:
        """Get contract_id or generate a default."""
        return self.contract_id or f"lifecycle-{uuid4()}"

    # =========================================================================
    # Stage Transitions
    # =========================================================================

    def transition_to_substage(
        self,
        new_substage: LifecycleSubstage,
        reason: str = "",
        new_status: Optional[LifecycleStatus] = None,
    ) -> "LifecycleRoot":
        """
        Transition to a new substage.

        This is the primary method for advancing the lifecycle.
        It validates the transition and records history.

        **Rules:**
        - Transition must be valid according to state machine
        - History is recorded for each transition
        - Phase is automatically derived from substage
        - Status can be explicitly set or derived

        Returns a new LifecycleRoot instance with the transition applied.
        """
        if self.is_terminal:
            raise ValueError(
                f"Cannot transition from terminal state: {self.substage.value}"
            )

        machine = get_lifecycle_state_machine()
        error = machine.validate_substage_transition(self.substage, new_substage)
        if error:
            raise ValueError(error)

        history_entry = StageHistoryEntry(
            from_stage=self.substage.value,
            to_stage=new_substage.value,
            reason=reason,
        )

        new_phase = get_phase_for_substage(new_substage)

        final_status = new_status or LifecycleStatus(machine.derive_status_from_substage(new_substage))

        failure_kind = self.failure_kind
        if new_substage.is_failure():
            failure_kind = machine.get_failure_kind_for_substage(new_substage)

        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            phase=new_phase,
            substage=new_substage,
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
            allowed_next_stages=machine.next_stages(new_substage),
            allowed_next_substages=machine.next_substages(new_substage),
            transition_reason=reason,
            validation_errors=(),
        )

    def can_transition_to_substage(self, target_substage: LifecycleSubstage) -> bool:
        """Check if we can transition to a target substage."""
        machine = get_lifecycle_state_machine()
        return machine.can_transition_substage(self.substage, target_substage)

    def get_next_substage(self) -> Optional[LifecycleSubstage]:
        """Get the next substage in the normal flow."""
        machine = get_lifecycle_state_machine()
        return machine.get_next_substage(self.substage)

    # =========================================================================
    # Recovery
    # =========================================================================

    def trigger_recovery(
        self,
        failure_kind: str = "",
        reason: str = "",
    ) -> "LifecycleRoot":
        """
        Trigger recovery flow for the current substage.

        Recovery transitions the lifecycle to the appropriate
        recovery substage (typically 'repairing' or 'verifying').
        """
        machine = get_lifecycle_state_machine()
        recovery_target_substage = machine.get_recovery_target_substage(self.substage)

        new_phase = get_phase_for_substage(recovery_target_substage)
        
        return LifecycleRoot(
            contract_id=self.contract_id,
            execution_id=self.execution_id,
            task_id=self.task_id,
            project_path=self.project_path,
            phase=new_phase,
            substage=recovery_target_substage,
            status=LifecycleStatus(machine.derive_status_from_substage(recovery_target_substage)),
            task_type=self.task_type,
            intent=self.intent,
            failure_kind=failure_kind or machine.get_failure_kind_for_substage(self.substage),
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
            allowed_next_stages=machine.next_stages(recovery_target_substage),
            allowed_next_substages=machine.next_substages(recovery_target_substage),
            transition_reason=f"Recovery: {reason}",
            validation_errors=(),
        )

    # =========================================================================
    # Stage Evidence
    # =========================================================================

    def add_stage_evidence(self, evidence: StageEvidence) -> "LifecycleRoot":
        """Add evidence for the current substage."""
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
            phase=self.phase,
            substage=self.substage,
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
            phase=self.phase,
            substage=self.substage,
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
            allowed_next_substages=self.allowed_next_substages,
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
            phase=self.phase,
            substage=self.substage,
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
            allowed_next_substages=self.allowed_next_substages,
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
            phase=self.phase,
            substage=self.substage,
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
            allowed_next_substages=self.allowed_next_substages,
            transition_reason=self.transition_reason,
            validation_errors=self.validation_errors,
        )

    # =========================================================================
    # Validation
    # =========================================================================

    def validate(self) -> List[str]:
        """Validate the lifecycle state and return errors."""
        errors: List[str] = []

        if not self.execution_id:
            errors.append("execution_id is required")
        if not self.task_id:
            errors.append("task_id is required")
        if not self.project_path:
            errors.append("project_path is required")

        valid_statuses = {"pending", "running", "success", "failed", "cancelled", "promoted"}
        if self.status.value not in valid_statuses:
            errors.append(f"invalid status: {self.status.value}")

        if self.status.value in ("success", "failed", "cancelled", "promoted"):
            if not self.substage.is_terminal():
                errors.append(
                    f"terminal status requires terminal stage: {self.status.value}/{self.substage.value}"
                )

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
    # Conversion - External Interface (replaces LifecycleContract)
    # =========================================================================

    def to_dict(self, include_evidence: bool = True) -> Dict[str, Any]:
        """Convert to dictionary for serialization (API/Dashboard compatible).

        This method produces JSON-serializable output suitable for external interfaces,
        replacing the previous LifecycleContract DTO.

        Args:
            include_evidence: Whether to include full evidence details
        """
        errors = self.validate()
        machine = get_lifecycle_state_machine()

        result: Dict[str, Any] = {
            # Core identity
            "contract_id": self.contract_id,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "project_path": self.project_path,
            
            # Core state
            "task_type": self.task_type,
            "intent": self.intent,
            "phase": self.phase.value,
            "stage": self.substage.value,
            "status": self.status.value,
            
            # Failure info
            "failure_kind": self.failure_kind,
            "failure_reason": self.failure_reason,
            "failure_code": self.failure_code,
            
            # Cross-domain refs
            "governance_refs": self.governance_ref.to_dict() if self.governance_ref else {},
            "evolution_refs": self.evolution_ref.to_dict() if self.evolution_ref else {},
            "runtime_refs": self.runtime_ref.to_dict() if self.runtime_ref else {},
            
            # Metadata
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
            "correlation": self.correlation.to_dict(),
            
            # Transition info
            "stage_history": [
                {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
                for h in self.stage_history
            ],
            "allowed_next_stages": list(self.allowed_next_stages),
            "allowed_next_substages": [s.value for s in self.allowed_next_substages],
            "transition_reason": self.transition_reason,
            
            # Derived fields
            "is_terminal": self.is_terminal,
            "is_valid": not errors,
            "validation_errors": errors,
            "stage_index": machine.stage_index(self.substage),
            "substage_index": machine.substage_index(self.substage),
            "next_substage": self.get_next_substage().value if self.get_next_substage() else None,
        }

        # Evidence (optional)
        if include_evidence:
            result["evidence"] = self.evidence.to_dict()
            result["trace"] = dict(self.evidence.trace)
            result["diagnostics"] = dict(self.evidence.diagnostics)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleRoot":
        """Create from dictionary (reconstruct from external data).

        This method replaces the previous LifecycleContract.from_dict() and
        map_contract_to_root() functions.
        """
        governance_ref = None
        if data.get("governance_ref") or data.get("governance_refs"):
            gr = data.get("governance_refs", data.get("governance_ref", {}))
            governance_ref = GovernanceRef(
                governance_session_id=gr.get("governance_session_id", ""),
                gate=gr.get("gate", ""),
                approved=gr.get("approved", False),
                approved_at=gr.get("approved_at"),
            )

        evolution_ref = None
        if data.get("evolution_ref") or data.get("evolution_refs"):
            er = data.get("evolution_refs", data.get("evolution_ref", {}))
            evolution_ref = EvolutionRef(
                evolution_request_id=er.get("evolution_request_id", ""),
                version_id=er.get("version_id", ""),
                versioned=er.get("versioned", False),
            )

        runtime_ref = None
        if data.get("runtime_ref") or data.get("runtime_refs"):
            rr = data.get("runtime_refs", data.get("runtime_ref", {}))
            runtime_ref = RuntimeRef(
                runtime_id=rr.get("runtime_id", ""),
                linked=rr.get("linked", False),
                healthy=rr.get("healthy", False),
            )

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

        substage_value = data.get("substage", data.get("stage", "new"))
        substage = LifecycleSubstage.from_string(substage_value)
        phase = get_phase_for_substage(substage)
        
        allowed_next_substages_data = data.get("allowed_next_substages", [])
        allowed_next_substages = tuple(
            LifecycleSubstage.from_string(s) for s in allowed_next_substages_data
        )

        return cls(
            contract_id=data.get("contract_id", ""),
            execution_id=data.get("execution_id", ""),
            task_id=data.get("task_id", ""),
            project_path=data.get("project_path", ""),
            task_type=data.get("task_type", "project_optimization"),
            intent=data.get("intent", ""),
            phase=phase,
            substage=substage,
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
            allowed_next_substages=allowed_next_substages,
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
        phase=LifecyclePhase.INITIALIZING,
        substage=LifecycleSubstage.NEW,
        status=LifecycleStatus.PENDING,
        correlation=correlation,
        metadata=dict(metadata or {}),
        allowed_next_stages=machine.next_stages(LifecycleSubstage.NEW),
        allowed_next_substages=machine.next_substages(LifecycleSubstage.NEW),
    )


__all__ = [
    "LifecycleStatus",
    "LifecyclePhase",
    "LifecycleSubstage",
    "LifecycleRoot",
    "create_lifecycle",
]