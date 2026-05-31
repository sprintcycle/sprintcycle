"""Lifecycle contract DTO for SprintCycle.

This module provides the LifecycleContract DTO for data transfer between
the domain layer and external interfaces (API, Dashboard, etc.).

**DDD Architecture:**
- LifecycleContract: Pure DTO for serialization/deserialization
- LifecycleRoot: Domain aggregate root with business logic
- Conversion: Handled by application layer services

This DTO maintains backward compatibility with existing API contracts.

**Field Grouping:**
- CrossDomainRefs: Cross-subdomain references
- ExecutionContext: Skill and IO context
- EvidenceBundle: Evidence, trace, and diagnostics
- MetadataBundle: Metrics, metadata, and correlation
- TransitionInfo: Stage history and transition data
- FailureInfo: Failure details
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .state_machine import (
    LIFECYCLE_STAGES,
    LifecycleStateMachine,
    build_default_correlation,
    FAILURE_KIND_BY_STAGE,
)


@dataclass
class CrossDomainRefs:
    """Cross-subdomain references grouped into a single object."""
    governance: Dict[str, Any] = field(default_factory=dict)
    evolution: Dict[str, Any] = field(default_factory=dict)
    runtime: Dict[str, Any] = field(default_factory=dict)
    delivery: Dict[str, Any] = field(default_factory=dict)
    recovery: Dict[str, Any] = field(default_factory=dict)
    suggestion: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_refs": self.governance,
            "evolution_refs": self.evolution,
            "runtime_refs": self.runtime,
            "delivery_refs": self.delivery,
            "recovery_refs": self.recovery,
            "suggestion_refs": self.suggestion,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrossDomainRefs":
        return cls(
            governance=dict(data.get("governance_refs", {})),
            evolution=dict(data.get("evolution_refs", {})),
            runtime=dict(data.get("runtime_refs", {})),
            delivery=dict(data.get("delivery_refs", {})),
            recovery=dict(data.get("recovery_refs", {})),
            suggestion=list(data.get("suggestion_refs", [])),
        )


@dataclass
class ExecutionContext:
    """Consolidated execution context."""
    skill: Dict[str, Any] = field(default_factory=dict)
    io: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_context": self.skill,
            "io_context": self.io,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        return cls(
            skill=dict(data.get("skill_context", {})),
            io=dict(data.get("io_context", {})),
        )


@dataclass
class EvidenceBundle:
    """Evidence, trace, and diagnostics grouped together."""
    evidence: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence": self.evidence,
            "trace": self.trace,
            "diagnostics": self.diagnostics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceBundle":
        return cls(
            evidence=dict(data.get("evidence", {})),
            trace=dict(data.get("trace", {})),
            diagnostics=dict(data.get("diagnostics", {})),
        )


@dataclass
class MetadataBundle:
    """Metrics, metadata, and correlation grouped together."""
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "metadata": self.metadata,
            "correlation": self.correlation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetadataBundle":
        return cls(
            metrics=dict(data.get("metrics", {})),
            metadata=dict(data.get("metadata", {})),
            correlation=dict(data.get("correlation", {})),
        )


@dataclass
class TransitionInfo:
    """Stage history and transition data."""
    history: List[Dict[str, Any]] = field(default_factory=list)
    allowed_next_stages: List[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage_history": self.history,
            "allowed_next_stages": self.allowed_next_stages,
            "transition_reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionInfo":
        return cls(
            history=list(data.get("stage_history", [])),
            allowed_next_stages=list(data.get("allowed_next_stages", [])),
            reason=data.get("transition_reason", ""),
        )


@dataclass
class FailureInfo:
    """Failure details grouped together."""
    kind: str = ""
    reason: str = ""
    code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_kind": self.kind,
            "failure_reason": self.reason,
            "failure_code": self.code,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureInfo":
        return cls(
            kind=data.get("failure_kind", ""),
            reason=data.get("failure_reason", ""),
            code=data.get("failure_code", ""),
        )

STAGE_EVIDENCE_SCHEMA: Dict[str, tuple[str, ...]] = {
    "normalized": ("normalized",),
    "plan": ("objective", "present"),
    "prepare": ("ready", "checks", "blockers", "present"),
    "decompose": ("subtasks", "present"),
    "execute": ("trace", "present"),
    "observe": ("trace", "diagnostics", "present"),
    "diagnose": ("root_causes", "repair_ready", "confidence", "recommendations", "present"),
    "repair": ("attempted", "closed_loop", "verify_result", "present"),
    "verify": ("closed_loop", "verify_result", "present"),
    "deliver": ("outputs", "runtime_linkage", "present"),
    "runtime": ("linked", "healthy", "present"),
    "governance": ("approved", "present"),
    "promotion": ("evidence", "completion_score"),
    "evolution": ("versioned", "version_id", "present"),
}

STAGE_EVIDENCE_TRUTHY_KEYS: Dict[str, tuple[str, ...]] = {
    "normalized": ("normalized",),
    "prepare": ("ready", "present"),
    "decompose": ("present",),
    "execute": ("present",),
    "observe": ("present",),
    "diagnose": ("present",),
    "repair": ("attempted", "closed_loop", "present"),
    "verify": ("closed_loop", "present"),
    "deliver": ("present",),
    "runtime": ("linked", "healthy", "present"),
    "governance": ("approved", "present"),
    "promotion": ("evidence", "completion_score"),
    "evolution": ("versioned", "version_id", "present"),
}


STAGE_EVIDENCE_KEYS: tuple[str, ...] = (
    "normalized",
    "plan",
    "prepare",
    "decompose",
    "execute",
    "observe",
    "diagnose",
    "repair",
    "verify",
    "deliver",
    "runtime",
    "governance",
    "promotion",
    "evolution",
)

CANONICAL_EVIDENCE_KEYS: Dict[str, str] = {
    "governing": "governance",
    "governance": "governance",
}

TERMINAL_STATUSES: tuple[str, ...] = ("success", "failed", "cancelled", "promoted")
REQUIRED_EVIDENCE_SECTIONS: tuple[str, ...] = (
    "contract",
    "stages",
    "runtime",
    "governance",
    "promotion",
    "evolution",
)
REQUIRED_STAGE_SEQUENCE: tuple[str, ...] = (
    "normalized",
    "plan",
    "prepare",
    "decompose",
    "execute",
    "observe",
    "diagnose",
    "repair",
    "verify",
    "deliver",
    "runtime",
    "governance",
    "promotion",
    "evolution",
)
RECOVERY_STAGE_TARGETS: Dict[str, str] = {
    "running": "repair",
    "observing": "repair",
    "diagnosed": "repair",
    "repairing": "verify",
    "verifying": "observe",
    "delivering": "repair",
    "runtime_linked": "repair",
    "governing": "repair",
    "promotion_ready": "repair",
    "failed": "repair",
}


def ensure_lifecycle_evidence(evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = dict(evidence or {})
    payload.setdefault("contract", {})
    payload.setdefault("stages", {})
    payload.setdefault("runtime", {})
    payload.setdefault("governance", {})
    payload.setdefault("promotion", {})
    payload.setdefault("evolution", {})
    payload.setdefault("suggestion", {})
    payload.setdefault("trace", {})
    payload.setdefault("diagnostics", {})
    payload.setdefault("recovery", {})
    stages = payload.setdefault("stages", {})
    for stage in STAGE_EVIDENCE_KEYS:
        canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
        stages.setdefault(canonical_stage, {})
    if "governing" in stages and "governance" not in stages:
        stages["governance"] = dict(stages.get("governing") or {})
    return payload


class LifecycleContract:
    """
    Lifecycle Contract DTO - Pure data transfer object.
    
    This class is designed for serialization/deserialization between
    external interfaces and the domain layer. It should NOT contain
    business logic - validation and business rules belong in the domain.
    
    **Design Principles:**
    - Grouped structure with value objects for better organization
    - Contains only fields needed for external interfaces
    - Uses primitive types (strings) for cross-system compatibility
    - Separated from domain aggregate to avoid coupling
    - Reduced field count through grouping
    
    **DTO vs Aggregate Boundary:**
    - DTO (this class): External interface data, grouped structure
    - LifecycleRoot: Domain aggregate, business logic, type-safe enums
    
    **Conversion:**
    - Use LifecycleMapper to convert between LifecycleContract and LifecycleRoot
    
    **Field Organization (Grouped):**
    - Core identity: execution_id, task_id, project_path
    - Core state: stage, status, task_type, intent
    - CrossDomainRefs: governance, evolution, runtime, delivery, recovery, suggestion
    - ExecutionContext: skill, io
    - EvidenceBundle: evidence, trace, diagnostics
    - MetadataBundle: metrics, metadata, correlation
    - TransitionInfo: history, allowed_next_stages, reason
    - FailureInfo: kind, reason, code
    """
    
    def __init__(
        self,
        execution_id: str = "",
        task_id: str = "",
        project_path: str = "",
        stage: str = "new",
        status: str = "pending",
        task_type: str = "project_optimization",
        intent: str = "",
        failure_kind: str = "",
        failure_reason: str = "",
        failure_code: str = "",
        governance_refs: Optional[Dict[str, Any]] = None,
        evolution_refs: Optional[Dict[str, Any]] = None,
        runtime_refs: Optional[Dict[str, Any]] = None,
        delivery_refs: Optional[Dict[str, Any]] = None,
        recovery_refs: Optional[Dict[str, Any]] = None,
        suggestion_refs: Optional[List[Dict[str, Any]]] = None,
        skill_context: Optional[Dict[str, Any]] = None,
        io_context: Optional[Dict[str, Any]] = None,
        evidence: Optional[Dict[str, Any]] = None,
        trace: Optional[Dict[str, Any]] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        correlation: Optional[Dict[str, Any]] = None,
        stage_history: Optional[List[Dict[str, Any]]] = None,
        allowed_next_stages: Optional[List[str]] = None,
        transition_reason: str = "",
    ):
        # Core identity
        self.execution_id = execution_id
        self.task_id = task_id
        self.project_path = project_path
        
        # Core state
        self.stage = stage
        self.status = status
        self.task_type = task_type
        self.intent = intent
        
        # Failure info
        self.failure_kind = failure_kind
        self.failure_reason = failure_reason
        self.failure_code = failure_code
        
        # Cross-domain refs
        self.governance_refs = governance_refs or {}
        self.evolution_refs = evolution_refs or {}
        self.runtime_refs = runtime_refs or {}
        self.delivery_refs = delivery_refs or {}
        self.recovery_refs = recovery_refs or {}
        self.suggestion_refs = suggestion_refs or []
        
        # Context
        self.skill_context = skill_context or {}
        self.io_context = io_context or {}
        
        # Evidence
        self.evidence = evidence or {}
        self.trace = trace or {}
        self.diagnostics = diagnostics or {}
        
        # Metadata
        self.metrics = metrics or {}
        self.metadata = metadata or {}
        self.correlation = correlation or {}
        
        # Transition
        self.stage_history = stage_history or []
        self.allowed_next_stages = allowed_next_stages or []
        self.transition_reason = transition_reason

    def validate(self) -> List[str]:
        """Validate the contract structure (schema validation only).
        
        This is schema-level validation for DTO purposes, not business rule validation.
        Business validation should be done in the domain layer using LifecycleRoot.
        """
        errors: List[str] = []
        machine = LifecycleStateMachine()
        valid_stages = set(LIFECYCLE_STAGES) | {"failed", "aborted", "cancelled"}
        valid_statuses = {"pending", "running", "success", "failed", "cancelled", "promoted"}
        
        if not self.execution_id:
            errors.append("execution_id is required")
        if not self.task_id:
            errors.append("task_id is required")
        if not self.project_path:
            errors.append("project_path is required")
        
        normalized_stage = machine.normalize_stage(self.stage)
        if str(self.stage).strip().lower() not in valid_stages:
            errors.append(f"invalid stage: {self.stage}")
        if normalized_stage != self.stage:
            errors.append(f"stage is not normalized: {self.stage}")
        
        if self.status not in valid_statuses:
            errors.append(f"invalid status: {self.status}")
        
        if self.status in TERMINAL_STATUSES and not machine.is_terminal(self.stage):
            errors.append(f"terminal status requires terminal stage: {self.status}/{self.stage}")
        
        if self.allowed_next_stages and any(stage not in valid_stages for stage in self.allowed_next_stages):
            errors.append("allowed_next_stages contains invalid stage")
        
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        machine = LifecycleStateMachine()
        validation_errors = self.validate()
        
        d: Dict[str, Any] = {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "project_path": self.project_path,
            "stage": self.stage,
            "status": self.status,
            "task_type": self.task_type,
            "intent": self.intent,
            "failure_kind": self.failure_kind,
            "failure_reason": self.failure_reason,
            "failure_code": self.failure_code,
            "governance_refs": self.governance_refs,
            "evolution_refs": self.evolution_refs,
            "runtime_refs": self.runtime_refs,
            "delivery_refs": self.delivery_refs,
            "recovery_refs": self.recovery_refs,
            "suggestion_refs": self.suggestion_refs,
            "skill_context": self.skill_context,
            "io_context": self.io_context,
            "evidence": self.evidence,
            "trace": self.trace,
            "diagnostics": self.diagnostics,
            "metrics": self.metrics,
            "metadata": self.metadata,
            "correlation": self.correlation,
            "stage_history": self.stage_history,
            "allowed_next_stages": self.allowed_next_stages,
            "transition_reason": self.transition_reason,
        }
        
        d["is_terminal"] = machine.is_terminal(self.stage) or self.status in TERMINAL_STATUSES
        d["stage_index"] = machine.stage_index(self.stage)
        d["stage_hints"] = {
            "next_stage": next_stage(self.stage),
            "failure_kind": self.failure_kind or FAILURE_KIND_BY_STAGE.get(self.stage, ""),
        }
        d["allowed_next_stages"] = list(self.allowed_next_stages or machine.next_stages(self.stage))
        d["evidence"] = ensure_lifecycle_evidence(self.evidence)
        d["validation"] = {"ok": not validation_errors, "errors": validation_errors}
        
        if not d.get("correlation"):
            d["correlation"] = build_default_correlation(
                {"execution_id": self.execution_id, "task_id": self.task_id, "metadata": self.metadata}
            ).to_dict()
        
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleContract":
        """Create from dictionary."""
        return cls(
            execution_id=data.get("execution_id", ""),
            task_id=data.get("task_id", ""),
            project_path=data.get("project_path", ""),
            stage=data.get("stage", "new"),
            status=data.get("status", "pending"),
            task_type=data.get("task_type", "project_optimization"),
            intent=data.get("intent", ""),
            failure_kind=data.get("failure_kind", ""),
            failure_reason=data.get("failure_reason", ""),
            failure_code=data.get("failure_code", ""),
            governance_refs=dict(data.get("governance_refs", {})),
            evolution_refs=dict(data.get("evolution_refs", {})),
            runtime_refs=dict(data.get("runtime_refs", {})),
            delivery_refs=dict(data.get("delivery_refs", {})),
            recovery_refs=dict(data.get("recovery_refs", {})),
            suggestion_refs=list(data.get("suggestion_refs", [])),
            skill_context=dict(data.get("skill_context", {})),
            io_context=dict(data.get("io_context", {})),
            evidence=dict(data.get("evidence", {})),
            trace=dict(data.get("trace", {})),
            diagnostics=dict(data.get("diagnostics", {})),
            metrics=dict(data.get("metrics", {})),
            metadata=dict(data.get("metadata", {})),
            correlation=dict(data.get("correlation", {})),
            stage_history=list(data.get("stage_history", [])),
            allowed_next_stages=list(data.get("allowed_next_stages", [])),
            transition_reason=data.get("transition_reason", ""),
        )


def next_stage(stage: str) -> str:
    if stage not in LIFECYCLE_STAGES:
        return ""
    idx = LIFECYCLE_STAGES.index(stage)
    return LIFECYCLE_STAGES[idx + 1] if idx + 1 < len(LIFECYCLE_STAGES) else ""


def normalize_lifecycle_metadata(metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    meta = dict(metadata or {})
    meta.setdefault("task_type", meta.get("task_type") or "project_optimization")
    meta.setdefault("intent", meta.get("intent") or meta.get("task_id") or meta.get("name") or "")
    meta.setdefault("source", meta.get("source") or "web")
    meta.setdefault("stability_contract", "web_end_to_end")
    return meta


def _has_truthy_path(payload: Dict[str, Any], path: str) -> bool:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]
    return bool(current)


def validate_lifecycle_evidence(contract: Dict[str, Any]) -> List[str]:
    payload = dict(contract or {})
    evidence = ensure_lifecycle_evidence(payload.get("evidence"))
    errors: List[str] = []
    stages = dict(evidence.get("stages") or {}) if isinstance(evidence.get("stages"), dict) else {}
    for stage, required_keys in STAGE_EVIDENCE_SCHEMA.items():
        canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
        stage_payload = dict(stages.get(canonical_stage) or {}) if canonical_stage in stages else {}
        if canonical_stage in {"governance", "promotion", "evolution", "runtime"}:
            stage_payload = dict(evidence.get(canonical_stage) or {})
        if not isinstance(stage_payload, dict):
            errors.append(f"evidence.{canonical_stage} must be a mapping")
            continue
        missing = [key for key in required_keys if key not in stage_payload]
        if missing:
            errors.append(f"evidence.{canonical_stage} missing keys: {', '.join(missing)}")
            continue
        truthy_required = STAGE_EVIDENCE_TRUTHY_KEYS.get(stage, ())
        for key in truthy_required:
            if key in stage_payload and not stage_payload.get(key):
                errors.append(f"evidence.{canonical_stage}.{key} must be truthy")
    required_stage_names = [stage for stage in REQUIRED_STAGE_SEQUENCE if stage not in {"governance", "governing"}]
    for stage in required_stage_names:
        canonical_stage = CANONICAL_EVIDENCE_KEYS.get(stage, stage)
        if canonical_stage in {"runtime", "governance", "promotion", "evolution"}:
            if not _has_truthy_path(evidence, canonical_stage):
                errors.append(f"missing evidence section: {canonical_stage}")
            continue
        if not _has_truthy_path(stages, canonical_stage):
            errors.append(f"missing stage evidence: {canonical_stage}")
    contract_section = dict(evidence.get("contract") or {})
    if not contract_section.get("normalized"):
        errors.append("evidence.contract.normalized must be truthy")
    if not evidence.get("runtime"):
        errors.append("evidence.runtime must be present")
    if not evidence.get("promotion"):
        errors.append("evidence.promotion must be present")
    if not evidence.get("evolution"):
        errors.append("evidence.evolution must be present")
    return errors


def build_lifecycle_state_machine() -> LifecycleStateMachine:
    return LifecycleStateMachine()





__all__ = [
    "LifecycleContract",
    "STAGE_EVIDENCE_SCHEMA",
    "STAGE_EVIDENCE_TRUTHY_KEYS",
    "FAILURE_KIND_BY_STAGE",
    "STAGE_EVIDENCE_KEYS",
    "CANONICAL_EVIDENCE_KEYS",
    "TERMINAL_STATUSES",
    "REQUIRED_EVIDENCE_SECTIONS",
    "REQUIRED_STAGE_SEQUENCE",
    "RECOVERY_STAGE_TARGETS",
    "ensure_lifecycle_evidence",
    "next_stage",
    "normalize_lifecycle_metadata",
    "validate_lifecycle_evidence",
    "build_lifecycle_state_machine",
]
