"""Lifecycle contract models for SprintCycle.

This module centralizes the minimal structured payload used to keep the
Web -> plan -> execute -> observe -> deliver -> runtime -> suggestion ->
evolution chain consistent across services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .state_machine import LIFECYCLE_STAGES, LifecycleStateMachine, build_default_correlation

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
    execution_id: str
    task_id: str
    project_path: str
    task_type: str = "project_optimization"
    intent: str = ""
    stage: str = "new"
    status: str = "pending"
    failure_kind: str = ""
    failure_reason: str = ""
    plan_refs: Dict[str, Any] = field(default_factory=dict)
    execution_refs: Dict[str, Any] = field(default_factory=dict)
    observation_refs: Dict[str, Any] = field(default_factory=dict)
    recovery_refs: Dict[str, Any] = field(default_factory=dict)
    recovery_plan_refs: Dict[str, Any] = field(default_factory=dict)
    delivery_refs: Dict[str, Any] = field(default_factory=dict)
    runtime_refs: Dict[str, Any] = field(default_factory=dict)
    governance_refs: Dict[str, Any] = field(default_factory=dict)
    evolution_refs: Dict[str, Any] = field(default_factory=dict)
    evidence: Dict[str, Any] = field(default_factory=dict)
    suggestion_refs: List[Dict[str, Any]] = field(default_factory=list)
    skill_refs: List[Dict[str, Any]] = field(default_factory=list)
    skill_matches: List[Dict[str, Any]] = field(default_factory=list)
    skill_review_checklists: List[Dict[str, Any]] = field(default_factory=list)
    skill_trace: Dict[str, Any] = field(default_factory=dict)
    trace: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation: Dict[str, Any] = field(default_factory=dict)
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    allowed_next_stages: List[str] = field(default_factory=list)
    validation_refs: Dict[str, Any] = field(default_factory=dict)
    input_refs: Dict[str, Any] = field(default_factory=dict)
    output_refs: Dict[str, Any] = field(default_factory=dict)
    transition_reason: str = ""
    failure_code: str = ""

    def validate(self) -> List[str]:
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
        if self.stage_history and not isinstance(self.stage_history, list):
            errors.append("stage_history must be a list")
        if self.stage_history and machine.stage_index(self.stage) < 0:
            errors.append("stage_history present but stage is invalid")
        if self.stage_history:
            order = {stage: idx for idx, stage in enumerate(REQUIRED_STAGE_SEQUENCE)}
            seen = [str(item.get("to") or "").strip().lower() for item in self.stage_history if isinstance(item, dict)]
            valid_seen = [stage for stage in seen if stage in order]
            if valid_seen:
                last_index = -1
                for stage in valid_seen:
                    index = order[stage]
                    if index < last_index:
                        errors.append("stage_history is out of order")
                        break
                    last_index = index
        return errors

    def to_dict(self) -> Dict[str, Any]:
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
        d["plan_hints"] = dict(self.plan_refs or {})
        d["execution_hints"] = dict(self.execution_refs or {})
        d["observation_hints"] = dict(self.observation_refs or {})
        d["recovery_hints"] = dict(self.recovery_refs or {})
        d["recovery_plan_hints"] = dict(self.recovery_plan_refs or {})
        d["delivery_hints"] = dict(self.delivery_refs or {})
        d["runtime_hints"] = dict(self.runtime_refs or {})
        d["governance_hints"] = dict(self.governance_refs or {})
        d["evolution_hints"] = dict(self.evolution_refs or {})
        d["evidence"] = ensure_lifecycle_evidence(self.evidence)
        d["suggestion_hints"] = list(self.suggestion_refs or [])
        d["skill_hints"] = {
            "skill_refs": list(self.skill_refs or []),
            "skill_matches": list(self.skill_matches or []),
            "skill_review_checklists": list(self.skill_review_checklists or []),
            "skill_trace": dict(self.skill_trace or {}),
        }
        d["validation"] = {"ok": not validation_errors, "errors": validation_errors}
        d["validation_refs"] = {
            **dict(d.get("validation_refs") or {}),
            "schema_valid": not validation_errors,
            "normalized": d.get("stage") == "normalized",
            "trace_present": bool(
                d.get("trace")
                or d.get("evidence", {}).get("stages", {}).get("execute", {}).get("trace")
                or d.get("evidence", {}).get("stages", {}).get("observe", {}).get("trace")
            ),
            "versioned_evolution": bool(
                d.get("evidence", {}).get("evolution", {}).get("versioned")
                or d.get("evolution_refs", {}).get("versioned")
            ),
        }
        if not d.get("correlation"):
            d["correlation"] = build_default_correlation(
                {"execution_id": self.execution_id, "task_id": self.task_id, "metadata": self.metadata}
            ).to_dict()
        return d


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


# Backwards-compatible alias for external callers that use the older helper name.
build_lifecycle_machine = build_lifecycle_state_machine


def build_lifecycle_contract(
    *,
    execution_id: str,
    task_id: str,
    project_path: str,
    stage: str,
    status: str,
    metadata: Optional[Dict[str, Any]] = None,
    failure_kind: str = "",
    failure_reason: str = "",
    delivery_refs: Optional[Dict[str, Any]] = None,
    runtime_refs: Optional[Dict[str, Any]] = None,
    suggestion_refs: Optional[List[Dict[str, Any]]] = None,
    skill_refs: Optional[List[Dict[str, Any]]] = None,
    skill_matches: Optional[List[Dict[str, Any]]] = None,
    skill_review_checklists: Optional[List[Dict[str, Any]]] = None,
    skill_trace: Optional[Dict[str, Any]] = None,
    evolution_refs: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    recovery_refs: Optional[Dict[str, Any]] = None,
    recovery_plan_refs: Optional[Dict[str, Any]] = None,
    governance_refs: Optional[Dict[str, Any]] = None,
    trace: Optional[Dict[str, Any]] = None,
    diagnostics: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    correlation: Optional[Dict[str, Any]] = None,
    stage_history: Optional[List[Dict[str, Any]]] = None,
    allowed_next_stages: Optional[List[str]] = None,
    validation_refs: Optional[Dict[str, Any]] = None,
    input_refs: Optional[Dict[str, Any]] = None,
    output_refs: Optional[Dict[str, Any]] = None,
    transition_reason: str = "",
    failure_code: str = "",
) -> LifecycleContract:
    meta = normalize_lifecycle_metadata(metadata)
    machine = LifecycleStateMachine()
    normalized_stage = machine.normalize_stage(stage)
    normalized_status = status or "pending"
    evidence_payload = ensure_lifecycle_evidence(evidence)
    contract = LifecycleContract(
        execution_id=execution_id,
        task_id=task_id,
        project_path=project_path,
        task_type=str(meta.get("task_type") or "project_optimization"),
        intent=str(meta.get("intent") or ""),
        stage=normalized_stage,
        status=normalized_status,
        failure_kind=failure_kind or FAILURE_KIND_BY_STAGE.get(normalized_stage, ""),
        failure_reason=failure_reason,
        delivery_refs=dict(delivery_refs or {}),
        runtime_refs=dict(runtime_refs or {}),
        suggestion_refs=list(suggestion_refs or []),
        skill_refs=list(skill_refs or []),
        skill_matches=list(skill_matches or []),
        skill_review_checklists=list(skill_review_checklists or []),
        skill_trace=dict(skill_trace or {}),
        evolution_refs=dict(evolution_refs or {}),
        evidence=evidence_payload,
        recovery_refs=dict(recovery_refs or {}),
        recovery_plan_refs=dict(recovery_plan_refs or {}),
        governance_refs=dict(governance_refs or {}),
        trace=dict(trace or {}),
        diagnostics=dict(diagnostics or {}),
        metrics=dict(metrics or {}),
        metadata=meta,
        correlation=dict(correlation or {}),
        stage_history=list(stage_history or []),
        allowed_next_stages=list(allowed_next_stages or machine.next_stages(normalized_stage)),
        validation_refs=dict(validation_refs or {}),
        input_refs=dict(input_refs or {}),
        output_refs=dict(output_refs or {}),
        transition_reason=transition_reason,
        failure_code=failure_code,
    )
    if not contract.correlation:
        contract.correlation = build_default_correlation(
            {"execution_id": execution_id, "task_id": task_id, "metadata": meta}
        ).to_dict()
    return contract


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
    "build_lifecycle_machine",
    "build_lifecycle_contract",
]
