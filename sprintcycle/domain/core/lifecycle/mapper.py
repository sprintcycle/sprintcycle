"""Mapper for converting between LifecycleContract (DTO) and LifecycleRoot (aggregate).

This module provides a central location for conversion logic, reducing
duplication and ensuring consistency across the codebase.

**Design Principles:**
- Single source of truth for conversion logic
- Immutable updates where appropriate
- Type-safe conversions with clear error handling
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .lifecycle_root import LifecycleRoot, LifecycleStatus, create_lifecycle
from .state_machine import LifecycleSubstage, get_phase_for_substage
from .models import LifecycleContract
from .values import CorrelationContext, GovernanceRef, EvolutionRef, RuntimeRef, LifecycleEvidence


class LifecycleMapper:
    """Mapper for lifecycle domain objects."""

    @staticmethod
    def contract_to_root(contract: LifecycleContract) -> LifecycleRoot:
        """Convert LifecycleContract DTO to LifecycleRoot aggregate.
        
        Args:
            contract: The DTO to convert
            
        Returns:
            A new LifecycleRoot instance with values from the contract
        """
        governance_ref = None
        if contract.governance_refs:
            gr = contract.governance_refs
            governance_ref = GovernanceRef(
                governance_session_id=gr.get("governance_session_id", ""),
                gate=gr.get("gate", ""),
                approved=gr.get("approved", False),
                approved_at=gr.get("approved_at"),
            )

        evolution_ref = None
        if contract.evolution_refs:
            er = contract.evolution_refs
            evolution_ref = EvolutionRef(
                evolution_request_id=er.get("evolution_request_id", ""),
                version_id=er.get("version_id", ""),
                versioned=er.get("versioned", False),
            )

        runtime_ref = None
        if contract.runtime_refs:
            rr = contract.runtime_refs
            runtime_ref = RuntimeRef(
                runtime_id=rr.get("runtime_id", ""),
                linked=rr.get("linked", False),
                healthy=rr.get("healthy", False),
            )

        corr_data = contract.correlation or {}
        correlation = CorrelationContext(
            execution_id=contract.execution_id,
            task_id=contract.task_id,
            trace_id=corr_data.get("trace_id", ""),
            version_id=corr_data.get("version_id", ""),
            runtime_id=corr_data.get("runtime_id", ""),
            request_id=corr_data.get("request_id", ""),
            suggestion_id=corr_data.get("suggestion_id", ""),
            parent_id=corr_data.get("parent_id", ""),
            source=corr_data.get("source", "web"),
            metadata=contract.metadata,
        )

        substage = LifecycleSubstage.from_string(contract.stage)
        phase = get_phase_for_substage(substage)
        
        metadata = dict(contract.metadata or {})
        
        metadata["delivery_refs"] = dict(contract.delivery_refs or {})
        metadata["recovery_refs"] = dict(contract.recovery_refs or {})
        metadata["suggestion_refs"] = list(contract.suggestion_refs or [])
        metadata["skill_context"] = dict(contract.skill_context or {})
        metadata["io_context"] = dict(contract.io_context or {})
        
        return LifecycleRoot(
            contract_id=f"lifecycle-{contract.execution_id}",
            execution_id=contract.execution_id,
            task_id=contract.task_id,
            project_path=contract.project_path,
            task_type=contract.task_type,
            intent=contract.intent,
            phase=phase,
            substage=substage,
            status=LifecycleStatus(contract.status),
            failure_kind=contract.failure_kind,
            failure_reason=contract.failure_reason,
            failure_code=contract.failure_code,
            governance_ref=governance_ref,
            evolution_ref=evolution_ref,
            runtime_ref=runtime_ref,
            evidence=LifecycleEvidence(
                contract=contract.to_dict(),
                stages={},
                runtime=runtime_ref or RuntimeRef(),
                governance=governance_ref or GovernanceRef(),
                evolution=evolution_ref or EvolutionRef(),
                trace=contract.trace or {},
                diagnostics=contract.diagnostics or {},
                recovery=contract.recovery_refs or {},
                suggestion={},
            ),
            stage_history=(),
            correlation=correlation,
            metrics=contract.metrics or {},
            metadata=metadata,
            allowed_next_stages=tuple(contract.allowed_next_stages or []),
            transition_reason=contract.transition_reason,
            validation_errors=(),
        )

    @staticmethod
    def root_to_contract(root: LifecycleRoot) -> LifecycleContract:
        """Convert LifecycleRoot aggregate to LifecycleContract DTO.
        
        Args:
            root: The aggregate to convert
            
        Returns:
            A new LifecycleContract instance with values from the root
        """
        metadata = dict(root.metadata or {})
        
        return LifecycleContract(
            # Core identity fields
            execution_id=root.execution_id,
            task_id=root.task_id,
            project_path=root.project_path,
            
            # Core state fields
            stage=root.substage.value,
            status=root.status.value,
            
            # Metadata fields
            task_type=root.task_type,
            intent=root.intent,
            
            # Failure information
            failure_kind=root.failure_kind,
            failure_reason=root.failure_reason,
            failure_code=root.failure_code,
            
            # Cross-subdomain references (consolidated)
            governance_refs={
                "governance_session_id": root.governance_ref.governance_session_id if root.governance_ref else "",
                "gate": root.governance_ref.gate if root.governance_ref else "",
                "approved": root.governance_ref.approved if root.governance_ref else False,
            } if root.governance_ref else {},
            evolution_refs={
                "evolution_request_id": root.evolution_ref.evolution_request_id if root.evolution_ref else "",
                "version_id": root.evolution_ref.version_id if root.evolution_ref else "",
            } if root.evolution_ref else {},
            runtime_refs={
                "runtime_id": root.runtime_ref.runtime_id if root.runtime_ref else "",
                "linked": root.runtime_ref.linked if root.runtime_ref else False,
                "healthy": root.runtime_ref.healthy if root.runtime_ref else False,
            } if root.runtime_ref else {},
            delivery_refs=dict(metadata.get("delivery_refs", {})),
            recovery_refs=dict(metadata.get("recovery_refs", {})),
            
            # Consolidated context fields
            suggestion_refs=list(metadata.get("suggestion_refs", [])),
            skill_context=dict(metadata.get("skill_context", {})),
            io_context=dict(metadata.get("io_context", {})),
            
            # Evidence and trace
            evidence=root.evidence.to_dict() if root.evidence else {},
            trace=root.evidence.trace if root.evidence else {},
            diagnostics=root.evidence.diagnostics if root.evidence else {},
            
            # Metadata and metrics
            metrics=root.metrics,
            metadata=root.metadata,
            correlation=root.correlation.to_dict(),
            
            # Transition information
            stage_history=[
                {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
                for h in root.stage_history
            ],
            allowed_next_stages=list(root.allowed_next_stages),
            transition_reason=root.transition_reason,
        )

    @staticmethod
    def dict_to_root(data: Dict[str, Any]) -> LifecycleRoot:
        """Convert dictionary to LifecycleRoot aggregate.
        
        Args:
            data: Dictionary representation of a lifecycle
            
        Returns:
            A new LifecycleRoot instance
        """
        return LifecycleRoot.from_dict(data)

    @staticmethod
    def root_to_dict(root: LifecycleRoot) -> Dict[str, Any]:
        """Convert LifecycleRoot aggregate to dictionary.
        
        Args:
            root: The aggregate to convert
            
        Returns:
            Dictionary representation of the lifecycle
        """
        return root.to_dict()

    @staticmethod
    def dict_to_contract(data: Dict[str, Any]) -> LifecycleContract:
        """Convert dictionary to LifecycleContract DTO.
        
        Args:
            data: Dictionary representation
            
        Returns:
            A new LifecycleContract instance
        """
        return LifecycleContract(**data)


def map_contract_to_root(contract: LifecycleContract) -> LifecycleRoot:
    """Convert LifecycleContract to LifecycleRoot (convenience function)."""
    return LifecycleMapper.contract_to_root(contract)


def map_root_to_contract(root: LifecycleRoot) -> LifecycleContract:
    """Convert LifecycleRoot to LifecycleContract (convenience function)."""
    return LifecycleMapper.root_to_contract(root)


__all__ = [
    "LifecycleMapper",
    "map_contract_to_root",
    "map_root_to_contract",
]
