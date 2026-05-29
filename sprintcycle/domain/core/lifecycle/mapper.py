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

from .lifecycle_root import LifecycleRoot, LifecycleStage, LifecycleStatus, create_lifecycle
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

        return LifecycleRoot(
            contract_id=f"lifecycle-{contract.execution_id}",
            execution_id=contract.execution_id,
            task_id=contract.task_id,
            project_path=contract.project_path,
            task_type=contract.task_type,
            intent=contract.intent,
            stage=LifecycleStage.from_string(contract.stage),
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
                trace={},
                diagnostics={},
                recovery=contract.recovery_refs or {},
                suggestion={},
            ),
            stage_history=(),
            correlation=correlation,
            metrics={},
            metadata=contract.metadata,
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
        return LifecycleContract(
            execution_id=root.execution_id,
            task_id=root.task_id,
            project_path=root.project_path,
            task_type=root.task_type,
            intent=root.intent,
            stage=root.stage.value,
            status=root.status.value,
            failure_kind=root.failure_kind,
            failure_reason=root.failure_reason,
            failure_code=root.failure_code,
            plan_refs={},
            execution_refs={},
            observation_refs={},
            recovery_refs=root.evidence.recovery if root.evidence else {},
            recovery_plan_refs={},
            delivery_refs={},
            runtime_refs={},
            governance_refs={},
            evolution_refs={},
            evidence=root.evidence.to_dict() if root.evidence else {},
            suggestion_refs=[],
            skill_refs=[],
            skill_matches=[],
            skill_review_checklists=[],
            skill_trace={},
            trace={},
            diagnostics={},
            metrics=root.metrics,
            metadata=root.metadata,
            correlation=root.correlation.to_dict(),
            stage_history=[
                {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
                for h in root.stage_history
            ],
            allowed_next_stages=list(root.allowed_next_stages),
            validation_refs={},
            input_refs={},
            output_refs={},
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
