"""Unified Lifecycle Service - Application layer orchestration.

This service consolidates the functionality previously split between:
- LifecycleRootService: Domain-level lifecycle operations
- WebLifecycleOrchestrationService: Web-specific lifecycle orchestration

**Design Principles:**
- Single entry point for all lifecycle operations
- Uses request data classes to avoid parameter explosion
- Delegates domain logic to LifecycleRoot aggregate
- Follows hexagonal architecture (ports and adapters)
- Stateless service with dependency injection

**Core Responsibilities:**
1. Lifecycle creation and initialization
2. Stage transitions and validation
3. Recovery orchestration
4. Evidence management
5. Cross-subdomain reference handling
6. Web request adaptation
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStatus,
    LifecycleSubstage,
    LifecycleStateMachine,
    LifecycleEvidence,
    StageEvidence,
    CorrelationContext,
    GovernanceRef,
    EvolutionRef,
    RuntimeRef,
    FailureInfo,
    create_lifecycle,
    get_lifecycle_state_machine,
    BuildLifecycleRequest,
    TransitionRequest,
    WebLifecycleRequest,
    RecoveryRequest,
)


class LifecycleService:
    """
    Unified lifecycle service for SprintCycle.
    
    This service provides a single interface for all lifecycle operations,
    replacing the previous LifecycleRootService and WebLifecycleOrchestrationService.
    
    **Usage:**
    ```python
    service = LifecycleService()
    
    # Create lifecycle
    lifecycle = service.create_lifecycle(request)
    
    # Transition stage
    lifecycle = service.transition_stage(lifecycle, transition_request)
    
    # Trigger recovery
    lifecycle = service.trigger_recovery(lifecycle, recovery_request)
    ```
    """
    
    def __init__(self, state_machine: Optional[LifecycleStateMachine] = None):
        self._state_machine = state_machine or get_lifecycle_state_machine()
    
    # =========================================================================
    # Lifecycle Creation
    # =========================================================================
    
    def create_lifecycle(self, request: BuildLifecycleRequest) -> LifecycleRoot:
        """Create a new lifecycle from a request."""
        lifecycle = create_lifecycle(
            execution_id=request.execution_id,
            task_id=request.task_id,
            project_path=request.project_path,
            task_type=request.task_type,
            intent=request.intent,
            metadata=dict(request.metadata),
        )
        
        if request.governance_ref:
            lifecycle = lifecycle.attach_governance(
                governance_session_id=request.governance_ref.governance_session_id,
                gate=request.governance_ref.gate,
                approved=request.governance_ref.approved,
            )
        
        if request.evolution_ref:
            lifecycle = lifecycle.attach_evolution(
                evolution_request_id=request.evolution_ref.evolution_request_id,
                version_id=request.evolution_ref.version_id,
            )
        
        if request.runtime_ref:
            lifecycle = lifecycle.attach_runtime(
                runtime_id=request.runtime_ref.runtime_id,
                linked=request.runtime_ref.linked,
                healthy=request.runtime_ref.healthy,
            )
        
        if request.correlation:
            lifecycle = LifecycleRoot(
                **{k: v for k, v in lifecycle.__dict__.items() if k != 'correlation'},
                correlation=request.correlation,
            )
        
        if request.initial_stage != LifecycleSubstage.NEW:
            lifecycle = self._transition_to_initial_stage(lifecycle, request.initial_stage)
        
        return lifecycle
    
    def _transition_to_initial_stage(self, lifecycle: LifecycleRoot, target_stage: LifecycleSubstage) -> LifecycleRoot:
        """Transition to the initial stage if it's not NEW."""
        if target_stage == lifecycle.substage:
            return lifecycle
        
        if not self._state_machine.can_transition_substage(lifecycle.substage, target_stage):
            raise ValueError(
                f"Cannot transition from {lifecycle.substage.value} to {target_stage.value}"
            )
        
        return lifecycle.transition_to_substage(target_stage, reason="Initial stage setup")
    
    # =========================================================================
    # Stage Transitions
    # =========================================================================
    
    def transition_stage(self, lifecycle: LifecycleRoot, request: TransitionRequest) -> LifecycleRoot:
        """Transition a lifecycle to a new stage."""
        if lifecycle.is_terminal:
            raise ValueError(f"Cannot transition from terminal state: {lifecycle.substage.value}")
        
        if request.failure_info:
            return self._transition_with_failure(lifecycle, request)
        
        return lifecycle.transition_to_substage(
            new_substage=request.target_stage,
            reason=request.reason,
        )
    
    def _transition_with_failure(self, lifecycle: LifecycleRoot, request: TransitionRequest) -> LifecycleRoot:
        """Transition with failure information."""
        lifecycle = lifecycle.transition_to_substage(
            new_substage=request.target_stage,
            reason=request.reason,
        )
        
        if request.failure_info:
            return LifecycleRoot(
                **{k: v for k, v in lifecycle.__dict__.items() 
                   if k not in ('failure_kind', 'failure_reason', 'failure_code')},
                failure_kind=request.failure_info.kind,
                failure_reason=request.failure_info.reason,
                failure_code=request.failure_info.code,
            )
        
        return lifecycle
    
    def advance_to_next_stage(self, lifecycle: LifecycleRoot, reason: str = "") -> LifecycleRoot:
        """Advance to the next stage in the normal flow."""
        next_stage = self._state_machine.get_next_substage(lifecycle.substage)
        if not next_stage:
            raise ValueError(f"No next stage available from {lifecycle.substage.value}")
        
        return lifecycle.transition_to_substage(next_stage, reason=reason)
    
    # =========================================================================
    # Recovery
    # =========================================================================
    
    def trigger_recovery(self, lifecycle: LifecycleRoot, request: RecoveryRequest) -> LifecycleRoot:
        """Trigger recovery for a failed lifecycle."""
        return lifecycle.trigger_recovery(
            failure_kind=request.failure_kind,
            reason=request.failure_reason,
        )
    
    def can_recover(self, lifecycle: LifecycleRoot) -> bool:
        """Check if the lifecycle can be recovered."""
        if lifecycle.is_terminal and lifecycle.substage not in (
            LifecycleSubstage.FAILED,
            LifecycleSubstage.CANCELLED,
        ):
            return False
        return self._state_machine.get_recovery_target(lifecycle.substage) != ""
    
    # =========================================================================
    # Evidence Management
    # =========================================================================
    
    def add_stage_evidence(self, lifecycle: LifecycleRoot, evidence: StageEvidence) -> LifecycleRoot:
        """Add evidence for a specific stage."""
        return lifecycle.add_stage_evidence(evidence)
    
    def update_lifecycle_evidence(
        self,
        lifecycle: LifecycleRoot,
        evidence: LifecycleEvidence,
    ) -> LifecycleRoot:
        """Update the entire evidence container."""
        return LifecycleRoot(
            **{k: v for k, v in lifecycle.__dict__.items() if k != 'evidence'},
            evidence=evidence,
        )
    
    # =========================================================================
    # Cross-Subdomain References
    # =========================================================================
    
    def attach_governance(
        self,
        lifecycle: LifecycleRoot,
        governance_session_id: str,
        gate: str = "",
        approved: bool = False,
    ) -> LifecycleRoot:
        """Attach governance reference to lifecycle."""
        return lifecycle.attach_governance(governance_session_id, gate, approved)
    
    def attach_evolution(
        self,
        lifecycle: LifecycleRoot,
        evolution_request_id: str,
        version_id: str = "",
    ) -> LifecycleRoot:
        """Attach evolution reference to lifecycle."""
        return lifecycle.attach_evolution(evolution_request_id, version_id)
    
    def attach_runtime(
        self,
        lifecycle: LifecycleRoot,
        runtime_id: str,
        linked: bool = False,
        healthy: bool = False,
    ) -> LifecycleRoot:
        """Attach runtime reference to lifecycle."""
        return lifecycle.attach_runtime(runtime_id, linked, healthy)
    
    # =========================================================================
    # Web Request Orchestration
    # =========================================================================
    
    def orchestrate_web_request(self, request: WebLifecycleRequest) -> LifecycleRoot:
        """Orchestrate a web lifecycle request."""
        correlation = CorrelationContext(
            execution_id=request.execution_id,
            task_id=request.task_id,
            request_id=request.request_id,
            source=request.source,
            metadata=dict(request.metadata),
            **dict(request.correlation_data),
        )
        
        governance_ref = None
        if request.governance_session_id:
            governance_ref = GovernanceRef(
                governance_session_id=request.governance_session_id,
            )
        
        evolution_ref = None
        if request.evolution_request_id:
            evolution_ref = EvolutionRef(
                evolution_request_id=request.evolution_request_id,
            )
        
        runtime_ref = None
        if request.runtime_id:
            runtime_ref = RuntimeRef(
                runtime_id=request.runtime_id,
            )
        
        build_request = BuildLifecycleRequest(
            execution_id=request.execution_id,
            task_id=request.task_id,
            project_path=request.project_path,
            intent=request.intent,
            governance_ref=governance_ref,
            evolution_ref=evolution_ref,
            runtime_ref=runtime_ref,
            correlation=correlation,
            metadata=dict(request.metadata),
        )
        
        lifecycle = self.create_lifecycle(build_request)
        
        if request.evidence:
            for stage_name, stage_evidence in request.evidence.items():
                if isinstance(stage_evidence, dict):
                    evidence = StageEvidence(
                        stage=stage_name,
                        present=stage_evidence.get("present", False),
                        evidence=dict(stage_evidence.get("evidence", {})),
                    )
                    lifecycle = self.add_stage_evidence(lifecycle, evidence)
        
        return lifecycle
    
    def create_or_update_from_web(self, request: WebLifecycleRequest) -> LifecycleRoot:
        """Create or update a lifecycle from a web request."""
        return self.orchestrate_web_request(request)
    
    # =========================================================================
    # Validation
    # =========================================================================
    
    def validate_lifecycle(self, lifecycle: LifecycleRoot) -> list[str]:
        """Validate the lifecycle state."""
        return lifecycle.validate()
    
    def is_lifecycle_valid(self, lifecycle: LifecycleRoot) -> bool:
        """Check if the lifecycle is valid."""
        return lifecycle.is_valid
    
    def can_transition(self, lifecycle: LifecycleRoot, target_stage: LifecycleSubstage) -> bool:
        """Check if a transition is valid."""
        return lifecycle.can_transition_to_substage(target_stage)
    
    def validate_transition(
        self,
        lifecycle: LifecycleRoot,
        target_stage: LifecycleSubstage,
    ) -> Optional[str]:
        """Validate a transition and return error message if invalid."""
        if lifecycle.is_terminal:
            return f"Cannot transition from terminal state: {lifecycle.substage.value}"
        
        error = self._state_machine.validate_substage_transition(lifecycle.substage, target_stage)
        if error:
            return error
        
        return None
    
    # =========================================================================
    # Conversion
    # =========================================================================
    
    def to_dict(self, lifecycle: LifecycleRoot, include_evidence: bool = True) -> Dict[str, Any]:
        """Convert lifecycle to dictionary for external interfaces."""
        return lifecycle.to_dict(include_evidence=include_evidence)
    
    def from_dict(self, data: Dict[str, Any]) -> LifecycleRoot:
        """Create lifecycle from dictionary."""
        return LifecycleRoot.from_dict(data)
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def get_next_stage(self, lifecycle: LifecycleRoot) -> Optional[LifecycleSubstage]:
        """Get the next stage in the normal flow."""
        return self._state_machine.get_next_substage(lifecycle.substage)
    
    def get_allowed_next_stages(self, lifecycle: LifecycleRoot) -> tuple[str, ...]:
        """Get allowed next stages."""
        return lifecycle.allowed_next_stages
    
    def get_recovery_target(self, lifecycle: LifecycleRoot) -> str:
        """Get the recovery target stage."""
        return self._state_machine.get_recovery_target(lifecycle.substage)
    
    def is_terminal(self, lifecycle: LifecycleRoot) -> bool:
        """Check if lifecycle is terminal."""
        return lifecycle.is_terminal
    
    def is_running(self, lifecycle: LifecycleRoot) -> bool:
        """Check if lifecycle is running."""
        return lifecycle.is_running


__all__ = ["LifecycleService"]