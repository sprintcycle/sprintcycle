"""Value objects for the Lifecycle subdomain.

Value objects are immutable, hashable domain concepts that have no
separate identity. They are defined by their attributes.

**Design Principles:**
- All value objects are frozen dataclasses
- Equality is based on attribute values
- No side effects in methods
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


# =============================================================================
# Stage Evidence
# =============================================================================


@dataclass(frozen=True)
class StageEvidence:
    """
    Evidence collected during a lifecycle stage.

    This is a value object that represents the evidence produced
    when executing within a specific stage.

    **Usage:**
    ```python
    evidence = StageEvidence(
        stage="execute",
        present=True,
        evidence={"trace": {...}, "output": "..."}
    )
    ```
    """

    stage: str
    present: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)

    # Stage-specific evidence key requirements
    EXECUTE_EVIDENCE_KEYS: Tuple[str, ...] = ("trace", "present")
    OBSERVE_EVIDENCE_KEYS: Tuple[str, ...] = ("trace", "diagnostics", "present")
    DIAGNOSE_EVIDENCE_KEYS: Tuple[str, ...] = (
        "root_causes",
        "repair_ready",
        "confidence",
        "recommendations",
        "present",
    )
    REPAIR_EVIDENCE_KEYS: Tuple[str, ...] = (
        "attempted",
        "closed_loop",
        "verify_result",
        "present",
    )
    VERIFY_EVIDENCE_KEYS: Tuple[str, ...] = ("closed_loop", "verify_result", "present")
    DELIVER_EVIDENCE_KEYS: Tuple[str, ...] = ("outputs", "runtime_linkage", "present")
    RUNTIME_EVIDENCE_KEYS: Tuple[str, ...] = ("linked", "healthy", "present")
    GOVERNANCE_EVIDENCE_KEYS: Tuple[str, ...] = ("approved", "present")
    PROMOTION_EVIDENCE_KEYS: Tuple[str, ...] = ("evidence", "completion_score")
    EVOLUTION_EVIDENCE_KEYS: Tuple[str, ...] = ("versioned", "version_id", "present")

    def with_evidence(self, **kwargs: Any) -> "StageEvidence":
        """Return a new StageEvidence with additional evidence."""
        new_evidence = dict(self.evidence)
        new_evidence.update(kwargs)
        return StageEvidence(
            stage=self.stage, present=self.present or bool(kwargs), evidence=new_evidence
        )

    def get_required_keys(self) -> Tuple[str, ...]:
        """Get the required evidence keys for this stage."""
        stage_lower = self.stage.lower()
        if stage_lower == "execute":
            return self.EXECUTE_EVIDENCE_KEYS
        elif stage_lower == "observe":
            return self.OBSERVE_EVIDENCE_KEYS
        elif stage_lower == "diagnose":
            return self.DIAGNOSE_EVIDENCE_KEYS
        elif stage_lower == "repair":
            return self.REPAIR_EVIDENCE_KEYS
        elif stage_lower == "verify":
            return self.VERIFY_EVIDENCE_KEYS
        elif stage_lower == "deliver":
            return self.DELIVER_EVIDENCE_KEYS
        elif stage_lower in ("runtime", "runtime_linked"):
            return self.RUNTIME_EVIDENCE_KEYS
        elif stage_lower in ("governance", "governing"):
            return self.GOVERNANCE_EVIDENCE_KEYS
        elif stage_lower == "promotion":
            return self.PROMOTION_EVIDENCE_KEYS
        elif stage_lower == "evolution":
            return self.EVOLUTION_EVIDENCE_KEYS
        return ()

    def is_complete(self) -> bool:
        """Check if this stage has all required evidence."""
        required = self.get_required_keys()
        if not required:
            return self.present
        return all(self.evidence.get(key) for key in required if key != "present")


@dataclass(frozen=True)
class StageHistoryEntry:
    """
    A single entry in the lifecycle stage history.

    Records a stage transition with timestamp and reason.
    """

    from_stage: str
    to_stage: str
    at: str = field(default_factory=lambda: datetime.now().isoformat())
    reason: str = ""


# =============================================================================
# Correlation Context
# =============================================================================


@dataclass(frozen=True)
class CorrelationContext:
    """
    Correlation context for tracking related domain objects.

    This value object maintains the relationships between
    execution, task, sprint, and version identifiers.

    **Usage:**
    ```python
    correlation = CorrelationContext(
        execution_id="exec-123",
        task_id="task-456",
        trace_id="trace-789",
    )
    ```
    """

    execution_id: str = ""
    task_id: str = ""
    trace_id: str = ""
    version_id: str = ""
    runtime_id: str = ""
    request_id: str = ""
    suggestion_id: str = ""
    parent_id: str = ""
    source: str = "web"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def with_trace_id(self, trace_id: str) -> "CorrelationContext":
        """Return a new CorrelationContext with updated trace_id."""
        return CorrelationContext(
            execution_id=self.execution_id,
            task_id=self.task_id,
            trace_id=trace_id,
            version_id=self.version_id,
            runtime_id=self.runtime_id,
            request_id=self.request_id,
            suggestion_id=self.suggestion_id,
            parent_id=self.parent_id,
            source=self.source,
            metadata=dict(self.metadata),
        )

    def with_version_id(self, version_id: str) -> "CorrelationContext":
        """Return a new CorrelationContext with updated version_id."""
        return CorrelationContext(
            execution_id=self.execution_id,
            task_id=self.task_id,
            trace_id=self.trace_id,
            version_id=version_id,
            runtime_id=self.runtime_id,
            request_id=self.request_id,
            suggestion_id=self.suggestion_id,
            parent_id=self.parent_id,
            source=self.source,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "trace_id": self.trace_id,
            "version_id": self.version_id,
            "runtime_id": self.runtime_id,
            "request_id": self.request_id,
            "suggestion_id": self.suggestion_id,
            "parent_id": self.parent_id,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CorrelationContext":
        """Create CorrelationContext from dictionary."""
        return cls(
            execution_id=str(data.get("execution_id", "")),
            task_id=str(data.get("task_id", "")),
            trace_id=str(data.get("trace_id", "")),
            version_id=str(data.get("version_id", "")),
            runtime_id=str(data.get("runtime_id", "")),
            request_id=str(data.get("request_id", "")),
            suggestion_id=str(data.get("suggestion_id", "")),
            parent_id=str(data.get("parent_id", "")),
            source=str(data.get("source", "web")),
            metadata=dict(data.get("metadata", {})),
        )


# =============================================================================
# Cross-Subdomain References
# =============================================================================


@dataclass(frozen=True)
class GovernanceRef:
    """
    Reference to a Governance session (by ID only).

    This value object prevents direct coupling to Governance aggregates.
    """

    governance_session_id: str = ""
    gate: str = ""
    approved: bool = False
    approved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_session_id": self.governance_session_id,
            "gate": self.gate,
            "approved": self.approved,
            "approved_at": self.approved_at,
        }


@dataclass(frozen=True)
class EvolutionRef:
    """
    Reference to an Evolution request (by ID only).

    This value object prevents direct coupling to Evolution aggregates.
    """

    evolution_request_id: str = ""
    version_id: str = ""
    versioned: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evolution_request_id": self.evolution_request_id,
            "version_id": self.version_id,
            "versioned": self.versioned,
        }


@dataclass(frozen=True)
class RuntimeRef:
    """
    Reference to a Runtime deployment (by ID only).

    This value object prevents direct coupling to Runtime systems.
    """

    runtime_id: str = ""
    linked: bool = False
    healthy: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "linked": self.linked,
            "healthy": self.healthy,
        }


# =============================================================================
# Lifecycle Evidence Container
# =============================================================================


@dataclass(frozen=True)
class LifecycleEvidence:
    """
    Container for all stage evidence in a lifecycle.

    This value object aggregates evidence from all stages
    and provides convenient access patterns.
    """

    contract: Dict[str, Any] = field(default_factory=dict)
    stages: Dict[str, StageEvidence] = field(default_factory=dict)
    runtime: RuntimeRef = field(default_factory=lambda: RuntimeRef())
    governance: GovernanceRef = field(default_factory=lambda: GovernanceRef())
    evolution: EvolutionRef = field(default_factory=lambda: EvolutionRef())
    trace: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    recovery: Dict[str, Any] = field(default_factory=dict)
    suggestion: Dict[str, Any] = field(default_factory=dict)

    def get_stage(self, stage: str) -> Optional[StageEvidence]:
        """Get evidence for a specific stage."""
        return self.stages.get(stage.lower())

    def is_stage_present(self, stage: str) -> bool:
        """Check if a stage has evidence."""
        evidence = self.get_stage(stage)
        return evidence.present if evidence else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract": dict(self.contract),
            "stages": {k: {"stage": v.stage, "present": v.present, "evidence": dict(v.evidence)}
                       for k, v in self.stages.items()},
            "runtime": self.runtime.to_dict(),
            "governance": self.governance.to_dict(),
            "evolution": self.evolution.to_dict(),
            "trace": dict(self.trace),
            "diagnostics": dict(self.diagnostics),
            "recovery": dict(self.recovery),
            "suggestion": dict(self.suggestion),
        }


# =============================================================================
# Failure Information
# =============================================================================


@dataclass(frozen=True)
class FailureInfo:
    """Information about a lifecycle failure."""

    kind: str  # e.g., "execution_error", "diagnosis_error"
    reason: str = ""
    code: str = ""
    stage: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "reason": self.reason,
            "code": self.code,
            "stage": self.stage,
        }


__all__ = [
    "StageEvidence",
    "StageHistoryEntry",
    "CorrelationContext",
    "GovernanceRef",
    "EvolutionRef",
    "RuntimeRef",
    "LifecycleEvidence",
    "FailureInfo",
]
