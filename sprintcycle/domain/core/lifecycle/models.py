"""Lifecycle contract DTO for SprintCycle.

This module provides the LifecycleContract DTO for data transfer between
the domain layer and external interfaces (API, Dashboard, etc.).

**DDD Architecture:**
- LifecycleContract: Pure DTO for serialization/deserialization
- LifecycleRoot: Domain aggregate root with business logic
- Conversion: Handled by application layer services

This DTO maintains backward compatibility with existing API contracts.
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
    "executing": "repair",
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


@dataclass
class LifecycleContract:
    """
    Lifecycle Contract DTO - Pure data transfer object.
    
    This class is designed for serialization/deserialization between
    external interfaces and the domain layer. It should NOT contain
    business logic - validation and business rules belong in the domain.
    
    **Design Principles:**
    - Flat structure for easy serialization
    - Contains only fields needed for external interfaces
    - Uses primitive types (strings) for cross-system compatibility
    - Separated from domain aggregate to avoid coupling
    
    **DTO vs Aggregate Boundary:**
    - DTO (this class): External interface data, flat structure, string-based
    - LifecycleRoot: Domain aggregate, business logic, type-safe enums
    
    **Conversion:**
    - Use LifecycleMapper to convert between LifecycleContract and LifecycleRoot
    """
    
    # Core identity fields
    execution_id: str
    task_id: str
    project_path: str
    
    # Core state fields (string-based for external compatibility)
    stage: str = "new"
    status: str = "pending"
    
    # Metadata fields
    task_type: str = "project_optimization"
    intent: str = ""
    
    # Failure information
    failure_kind: str = ""
    failure_reason: str = ""
    failure_code: str = ""
    
    # Cross-subdomain references (flat dictionaries)
    governance_refs: Dict[str, Any] = field(default_factory=dict)
    evolution_refs: Dict[str, Any] = field(default_factory=dict)
    runtime_refs: Dict[str, Any] = field(default_factory=dict)
    
    # Evidence and trace
    evidence: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata and metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation: Dict[str, Any] = field(default_factory=dict)
    
    # Transition information
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    allowed_next_stages: List[str] = field(default_factory=list)
    transition_reason: str = ""

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
        d = asdict(self)
        validation_errors = self.validate()
        
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
            # Core identity fields
            execution_id=data.get("execution_id", ""),
            task_id=data.get("task_id", ""),
            project_path=data.get("project_path", ""),
            
            # Core state fields
            stage=data.get("stage", "new"),
            status=data.get("status", "pending"),
            
            # Metadata fields
            task_type=data.get("task_type", "project_optimization"),
            intent=data.get("intent", ""),
            
            # Failure information
            failure_kind=data.get("failure_kind", ""),
            failure_reason=data.get("failure_reason", ""),
            failure_code=data.get("failure_code", ""),
            
            # Cross-subdomain references
            governance_refs=dict(data.get("governance_refs", {})),
            evolution_refs=dict(data.get("evolution_refs", {})),
            runtime_refs=dict(data.get("runtime_refs", {})),
            
            # Evidence and trace
            evidence=dict(data.get("evidence", {})),
            trace=dict(data.get("trace", {})),
            diagnostics=dict(data.get("diagnostics", {})),
            
            # Metadata and metrics
            metrics=dict(data.get("metrics", {})),
            metadata=dict(data.get("metadata", {})),
            correlation=dict(data.get("correlation", {})),
            
            # Transition information
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
