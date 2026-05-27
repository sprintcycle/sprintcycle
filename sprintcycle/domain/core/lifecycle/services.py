"""Lifecycle state machine domain service.

This module provides the authoritative state transition rules for the
lifecycle subdomain. It encapsulates all the business rules around
stage transitions.

**Design Principles:**
- This is a stateless domain service (no internal state)
- All transition rules are defined as class constants
- Methods are pure functions where possible
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# =============================================================================
# Constants (Transition Tables)
# =============================================================================

LIFECYCLE_STAGES: Tuple[str, ...] = (
    "new",
    "normalized",
    "planned",
    "prepared",
    "decomposed",
    "executing",
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

TERMINAL_STAGES: Tuple[str, ...] = ("promoted", "failed", "aborted", "cancelled")
FAILURE_STAGES: Tuple[str, ...] = ("failed", "aborted", "cancelled")
RECOVERY_STAGES: Tuple[str, ...] = ("repairing", "verifying")

STAGE_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    "new": ("normalized", "failed", "cancelled"),
    "normalized": ("planned", "failed", "cancelled"),
    "planned": ("prepared", "failed", "cancelled"),
    "prepared": ("decomposed", "failed", "cancelled"),
    "decomposed": ("executing", "failed", "cancelled"),
    "executing": ("observing", "diagnosed", "delivering", "failed", "cancelled"),
    "observing": ("diagnosed", "delivering", "failed", "cancelled"),
    "diagnosed": ("repairing", "delivering", "failed", "cancelled"),
    "repairing": ("verifying", "observing", "failed", "cancelled"),
    "verifying": ("observing", "delivering", "failed", "cancelled"),
    "delivering": ("runtime_linked", "failed", "cancelled"),
    "runtime_linked": ("governing", "failed", "cancelled"),
    "governing": ("promotion_ready", "failed", "cancelled"),
    "promotion_ready": ("promoted", "failed", "cancelled"),
    "promoted": (),
    "failed": ("repairing", "cancelled"),  # Can recover to repairing
    "aborted": (),
    "cancelled": (),
}

RECOVERY_TARGETS: Dict[str, str] = {
    "executing": "repairing",
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

REPAIR_ROUTE_BY_STAGE: Dict[str, str] = {
    "executing": "repairing",
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

CORRELATION_KEY_FIELDS: Tuple[str, ...] = (
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
    "prepared": "",
    "decomposed": "",
    "executing": "execution_error",
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


# =============================================================================
# Domain Service
# =============================================================================


class LifecycleStateMachineService:
    """
    Lifecycle state machine domain service.

    This service provides authoritative methods for:
    - Validating stage transitions
    - Getting next valid stages
    - Determining recovery targets
    - Building correlation context

    **Usage:**
    ```python
    service = LifecycleStateMachineService()

    # Validate transition
    error = service.validate_transition("executing", "observing")
    if error:
        raise ValueError(error)

    # Get next stages
    next_stages = service.next_stages("executing")

    # Get recovery target
    recovery = service.get_recovery_target("executing")
    ```
    """

    # Class-level constants for subclasses to reference
    STAGES = LIFECYCLE_STAGES
    TERMINAL_STAGES = TERMINAL_STAGES
    TRANSITIONS = STAGE_TRANSITIONS
    RECOVERY_TARGETS = RECOVERY_TARGETS

    def __init__(self) -> None:
        pass

    def normalize_stage(self, stage: object) -> str:
        """Normalize a stage value to canonical string form."""
        # Handle Enum types (e.g., LifecycleStage)
        if hasattr(stage, 'value'):
            value = str(stage.value).strip().lower()
        else:
            value = str(stage or "").strip().lower()
        return value if value in STAGE_TRANSITIONS else "new"

    def can_transition(self, from_stage: object, to_stage: object) -> bool:
        """
        Check if a transition is valid.

        Returns True if:
        - from_stage equals to_stage (no-op transitions are allowed)
        - to_stage is in the allowed transitions for from_stage
        """
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)
        if frm == to:
            return True
        return to in STAGE_TRANSITIONS.get(frm, ())

    def validate_transition(
        self, from_stage: object, to_stage: object
    ) -> Optional[str]:
        """
        Validate a stage transition.

        Returns None if valid, or an error message if invalid.
        """
        frm = self.normalize_stage(from_stage)
        to = self.normalize_stage(to_stage)

        if not frm:
            return "stage cannot be empty"
        if not to:
            return "target stage cannot be empty"

        if self.can_transition(frm, to):
            return None

        return f"illegal lifecycle transition: {frm} -> {to}"

    def next_stages(self, stage: object) -> Tuple[str, ...]:
        """Get the valid next stages for a given stage."""
        return STAGE_TRANSITIONS.get(self.normalize_stage(stage), ())

    def stage_index(self, stage: object) -> int:
        """Get the index of a stage in the lifecycle sequence."""
        normalized = self.normalize_stage(stage)
        try:
            return LIFECYCLE_STAGES.index(normalized)
        except ValueError:
            return -1

    def is_terminal(self, stage: object) -> bool:
        """Check if a stage is terminal (no further transitions)."""
        normalized = self.normalize_stage(stage)
        return (
            normalized in TERMINAL_STAGES or normalized in FAILURE_STAGES
        )

    def is_failure(self, stage: object) -> bool:
        """Check if a stage represents a failure state."""
        return self.normalize_stage(stage) in FAILURE_STAGES

    def is_recovery(self, stage: object) -> bool:
        """Check if a stage is a recovery stage."""
        return self.normalize_stage(stage) in RECOVERY_STAGES

    def get_recovery_target(self, stage: object) -> str:
        """
        Get the recovery target stage for a given stage.

        Returns the stage to transition to when recovery is needed.
        """
        normalized = self.normalize_stage(stage)
        return RECOVERY_TARGETS.get(normalized, "repairing")

    def get_failure_kind(self, stage: object) -> str:
        """Get the failure kind for a given stage."""
        return FAILURE_KIND_BY_STAGE.get(self.normalize_stage(stage), "")

    def get_allowed_next_stages(self, stage: object) -> List[str]:
        """Get a list of allowed next stages (excludes failure states by default)."""
        all_next = list(self.next_stages(stage))
        # Filter out failure states for "normal" progression
        return [
            s for s in all_next if s not in FAILURE_STAGES
        ]

    def build_transition_event(
        self,
        from_stage: str,
        to_stage: str,
        reason: str = "",
        correlation: Optional[Dict[str, Any]] = None,
        source: str = "web",
    ) -> Dict[str, Any]:
        """
        Build a transition event dictionary.

        This is used to record stage transitions in the event log.
        """
        return {
            "from": from_stage,
            "to": to_stage,
            "reason": reason,
            "at": datetime.now().isoformat(),
            "correlation": dict(correlation or {}),
            "source": source,
        }

    def build_default_correlation(
        self, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a default correlation context from a payload.

        Extracts correlation key fields from the payload metadata.
        """
        from .values import CorrelationContext

        payload = dict(payload or {})
        metadata = dict(payload.get("metadata") or {})

        trace_id = str(
            payload.get("trace_id")
            or metadata.get("trace_id")
            or uuid4()
        )

        correlation = CorrelationContext(
            request_id=str(
                payload.get("request_id") or metadata.get("request_id") or ""
            ),
            execution_id=str(
                payload.get("execution_id") or metadata.get("execution_id") or ""
            ),
            task_id=str(payload.get("task_id") or metadata.get("task_id") or ""),
            suggestion_id=str(
                payload.get("suggestion_id") or metadata.get("suggestion_id") or ""
            ),
            runtime_id=str(
                payload.get("runtime_id") or metadata.get("runtime_id") or ""
            ),
            version_id=str(
                payload.get("version_id") or metadata.get("version_id") or ""
            ),
            trace_id=trace_id,
            parent_id=str(
                payload.get("parent_id") or metadata.get("parent_id") or ""
            ),
            source=str(payload.get("source") or metadata.get("source") or "web"),
            metadata=metadata,
        )
        return correlation.to_dict()

    def attach_correlation(
        self, contract: Dict[str, Any], correlation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attach correlation to a contract dictionary.

        Updates both the correlation field and metadata.
        """
        contract = dict(contract or {})
        contract["correlation"] = dict(correlation)
        contract.setdefault("metadata", {})
        contract["metadata"].update(
            {
                k: v
                for k, v in correlation.items()
                if k in CORRELATION_KEY_FIELDS and v
            }
        )
        return contract

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
        error = self.validate_transition(from_stage, to_stage)
        if error:
            raise ValueError(error)
        
        result = dict(contract)
        
        # Update stage and status
        result["stage"] = to_stage
        if status:
            result["status"] = status
        elif to_stage in TERMINAL_STAGES or to_stage in FAILURE_STAGES:
            result["status"] = "failed" if to_stage in FAILURE_STAGES else "success"
        
        # Update metadata
        result.setdefault("metadata", {})
        if metadata:
            result["metadata"].update(dict(metadata))
        
        # Add transition to history
        result.setdefault("stage_history", [])
        result["stage_history"].append({
            "from": from_stage,
            "to": to_stage,
            "at": datetime.now().isoformat(),
            "reason": reason
        })
        
        # Update terminal state
        result["is_terminal"] = self.is_terminal(to_stage)
        result["stage_index"] = self.stage_index(to_stage)
        
        # Set failure kind if needed
        if to_stage in FAILURE_STAGES:
            result["failure_kind"] = self.get_failure_kind(from_stage)
        
        return result

    def lifecycle_to_dict(self, lifecycle) -> Dict[str, Any]:
        """
        Convert a LifecycleRoot instance to a legacy contract dictionary.
        
        Provides compatibility for code that expects the old format.
        """
        from .lifecycle_root import LifecycleRoot
        from .values import LifecycleEvidence
        
        if not isinstance(lifecycle, LifecycleRoot):
            return dict(lifecycle or {})
        
        # Process evidence - handle both formats
        evidence_dict = {"stages": {}}
        if lifecycle.evidence:
            if isinstance(lifecycle.evidence, LifecycleEvidence):
                # New format - use LifecycleEvidence's to_dict
                evidence_dict = lifecycle.evidence.to_dict()
            elif hasattr(lifecycle.evidence, 'to_dict'):
                # If it has to_dict method (like StageEvidence)
                evidence_dict = lifecycle.evidence.to_dict()
            elif hasattr(lifecycle.evidence, 'stages'):
                # If it has stages attribute
                evidence_dict = {'stages': {k: v.to_dict() for k, v in getattr(lifecycle.evidence, 'stages', {}).items()}}
            elif isinstance(lifecycle.evidence, dict):
                # If it's already a dictionary
                evidence_dict = dict(lifecycle.evidence)
        
        # Ensure stages always exists
        if 'stages' not in evidence_dict:
            evidence_dict['stages'] = {}
        
        return {
            "contract_id": lifecycle.contract_id,
            "execution_id": lifecycle.execution_id,
            "task_id": lifecycle.task_id,
            "project_path": lifecycle.project_path,
            "stage": lifecycle.stage.value,
            "status": lifecycle.status.value,
            "intent": lifecycle.intent,
            "metadata": dict(lifecycle.metadata),
            "evidence": evidence_dict,
            "stage_history": [
                {
                    "from": transition.from_stage,
                    "to": transition.to_stage,
                    "at": transition.at.isoformat() if hasattr(transition.at, 'isoformat') else str(transition.at),
                    "reason": transition.reason
                }
                for transition in lifecycle.stage_history
            ],
            "is_terminal": self.is_terminal(lifecycle.stage.value),
            "stage_index": self.stage_index(lifecycle.stage.value),
            "correlation": lifecycle.correlation.to_dict() if lifecycle.correlation else {},
        }


# Singleton instance for convenience
_default_service: Optional[LifecycleStateMachineService] = None


def get_lifecycle_state_machine_service() -> LifecycleStateMachineService:
    """Get or create the default lifecycle state machine service."""
    global _default_service
    if _default_service is None:
        _default_service = LifecycleStateMachineService()
    return _default_service


__all__ = [
    "LifecycleStateMachineService",
    "LIFECYCLE_STAGES",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "STAGE_TRANSITIONS",
    "RECOVERY_TARGETS",
    "REPAIR_ROUTE_BY_STAGE",
    "CORRELATION_KEY_FIELDS",
    "FAILURE_KIND_BY_STAGE",
    "get_lifecycle_state_machine_service",
]
