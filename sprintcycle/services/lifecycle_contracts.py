"""Lifecycle contract helpers for web-triggered execution chains.

This module centralizes the minimal structured payload used to keep the
Web -> plan -> execute -> observe -> deliver -> runtime -> suggestion ->
evolution chain consistent across services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .lifecycle_state_machine import LIFECYCLE_STAGES, LifecycleStateMachine, build_default_correlation


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
    "runtime": ("linked", "healthy"),
    "governance": ("approved",),
    "promotion": ("evidence", "completion_score"),
    "evolution": ("versioned", "version_id"),
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
    "runtime": ("linked", "healthy"),
    "governance": ("approved",),
    "promotion": ("evidence", "completion_score"),
    "evolution": ("versioned", "version_id"),
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

TERMINAL_STATUSES: tuple[str, ...] = ("success", "failed", "cancelled", "promoted")


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
        return errors

    def to_dict(self) -> Dict[str, Any]:
        machine = LifecycleStateMachine()
        payload = asdict(self)
        validation_errors = self.validate()
        payload["is_terminal"] = machine.is_terminal(self.stage) or self.status in TERMINAL_STATUSES
        payload["stage_index"] = machine.stage_index(self.stage)
        payload["stage_hints"] = {
            "next_stage": next_stage(self.stage),
            "failure_kind": self.failure_kind or FAILURE_KIND_BY_STAGE.get(self.stage, ""),
        }
        payload["allowed_next_stages"] = list(self.allowed_next_stages or machine.next_stages(self.stage))
        payload["plan_hints"] = dict(self.plan_refs or {})
        payload["execution_hints"] = dict(self.execution_refs or {})
        payload["observation_hints"] = dict(self.observation_refs or {})
        payload["recovery_hints"] = dict(self.recovery_refs or {})
        payload["delivery_hints"] = dict(self.delivery_refs or {})
        payload["runtime_hints"] = dict(self.runtime_refs or {})
        payload["governance_hints"] = dict(self.governance_refs or {})
        payload["evolution_hints"] = dict(self.evolution_refs or {})
        payload["evidence"] = dict(self.evidence or {})
        payload["evidence"].setdefault("stages", {})
        payload["evidence"]["stages"] = dict(payload["evidence"].get("stages") or {})
        for key in STAGE_EVIDENCE_KEYS:
            payload["evidence"]["stages"].setdefault(key, {})
        payload["suggestion_hints"] = list(self.suggestion_refs or [])
        payload["skill_hints"] = {
            "skill_refs": list(self.skill_refs or []),
            "skill_matches": list(self.skill_matches or []),
            "skill_review_checklists": list(self.skill_review_checklists or []),
            "skill_trace": dict(self.skill_trace or {}),
        }
        payload["validation"] = {"ok": not validation_errors, "errors": validation_errors}
        if not payload.get("correlation"):
            payload["correlation"] = build_default_correlation({"execution_id": self.execution_id, "task_id": self.task_id, "metadata": self.metadata}).to_dict()
        return payload


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


def validate_lifecycle_evidence(contract: Dict[str, Any]) -> List[str]:
    payload = dict(contract or {})
    evidence = dict(payload.get("evidence") or {})
    errors: List[str] = []
    stages = dict(evidence.get("stages") or {}) if isinstance(evidence.get("stages"), dict) else {}
    for stage, required_keys in STAGE_EVIDENCE_SCHEMA.items():
        stage_payload = dict(stages.get(stage) or {}) if stage in stages else {}
        if stage in {"governance", "promotion", "evolution", "runtime"}:
            stage_payload = dict(evidence.get(stage) or {})
        if not isinstance(stage_payload, dict):
            errors.append(f"evidence.{stage} must be a mapping")
            continue
        missing = [key for key in required_keys if key not in stage_payload]
        if missing:
            errors.append(f"evidence.{stage} missing keys: {', '.join(missing)}")
            continue
        truthy_required = STAGE_EVIDENCE_TRUTHY_KEYS.get(stage, ())
        for key in truthy_required:
            if key in stage_payload and not stage_payload.get(key):
                errors.append(f"evidence.{stage}.{key} must be truthy")
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
    evidence_payload = dict(evidence or {})
    evidence_payload.setdefault("contract", {})
    evidence_payload.setdefault("stages", {})
    evidence_payload.setdefault("runtime", {})
    evidence_payload.setdefault("suggestion", {})
    evidence_payload.setdefault("governance", {})
    evidence_payload.setdefault("promotion", {})
    evidence_payload.setdefault("evolution", {})
    for key in STAGE_EVIDENCE_KEYS:
        evidence_payload["stages"].setdefault(key, {})
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
        contract.correlation = build_default_correlation({"execution_id": execution_id, "task_id": task_id, "metadata": meta}).to_dict()
    return contract
