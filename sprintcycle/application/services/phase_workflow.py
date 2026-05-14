"""Phase 2 workflow helpers for plan / prepare / decompose.

This module provides lightweight structured artifacts that sit between the
normalized lifecycle contract and actual execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .lifecycle_contracts import LifecycleContract, build_lifecycle_contract
from .lifecycle_state_machine import build_lifecycle_state_machine


@dataclass
class PlanArtifact:
    execution_id: str
    task_id: str
    project_path: str
    objective: str = ""
    success_criteria: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    version: str = "v1"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PrepareArtifact:
    execution_id: str
    task_id: str
    project_path: str
    ready: bool = False
    checks: Dict[str, Any] = field(default_factory=dict)
    blockers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DecomposeArtifact:
    execution_id: str
    task_id: str
    project_path: str
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    dag: Dict[str, List[str]] = field(default_factory=dict)
    acceptance_criteria: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_plan_artifact(contract: LifecycleContract, *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, version: str = "v1") -> Dict[str, Any]:
    machine = build_lifecycle_state_machine()
    planned = machine.transition(contract.to_dict(), "planned", status="success", reason="plan built", metadata={"phase": "plan"})
    artifact = PlanArtifact(
        execution_id=contract.execution_id,
        task_id=contract.task_id,
        project_path=contract.project_path,
        objective=objective or contract.intent,
        success_criteria=list(success_criteria or []),
        risks=list(risks or []),
        dependencies=list(dependencies or []),
        version=version,
        metadata={"source": "phase_workflow"},
    )
    evidence = dict(planned.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("plan", {}).update({"objective": artifact.objective, "success_criteria": artifact.success_criteria, "risks": artifact.risks, "dependencies": artifact.dependencies, "version": artifact.version, "present": True})
    evidence.setdefault("contract", {})["normalized"] = bool(evidence.get("contract", {}).get("normalized", True))
    return {"lifecycle_contract": {**planned, "evidence": evidence, "plan_refs": artifact.to_dict(), "input_refs": {**dict(contract.input_refs), "objective": artifact.objective}}, "plan": artifact.to_dict()}


def build_prepare_artifact(contract_payload: Dict[str, Any], *, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None) -> Dict[str, Any]:
    machine = build_lifecycle_state_machine()
    prepared = machine.transition(dict(contract_payload or {}), "prepared", status="success", reason="prepare completed", metadata={"phase": "prepare"})
    artifact = PrepareArtifact(
        execution_id=str(prepared.get("execution_id") or ""),
        task_id=str(prepared.get("task_id") or ""),
        project_path=str(prepared.get("project_path") or ""),
        ready=not bool(blockers),
        checks=dict(checks or {}),
        blockers=list(blockers or []),
        metadata={"source": "phase_workflow"},
    )
    prepared["validation_refs"] = {**dict(prepared.get("validation_refs") or {}), **artifact.checks, "ready": artifact.ready, "blockers": artifact.blockers}
    evidence = dict(prepared.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("prepare", {}).update({"ready": artifact.ready, "checks": artifact.checks, "blockers": artifact.blockers, "present": True})
    prepared["evidence"] = evidence
    return {"lifecycle_contract": {**prepared, "plan_refs": dict(prepared.get("plan_refs") or {}), "validation_refs": prepared.get("validation_refs", {}), "evidence": evidence}, "prepare": artifact.to_dict()}


def build_decompose_artifact(contract_payload: Dict[str, Any], *, subtasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    machine = build_lifecycle_state_machine()
    decomposed = machine.transition(dict(contract_payload or {}), "decomposed", status="success", reason="decomposition completed", metadata={"phase": "decompose"})
    subtasks = list(subtasks or [])
    dag: Dict[str, List[str]] = {}
    for item in subtasks:
        task_name = str(item.get("name") or item.get("id") or f"task_{len(dag)}")
        dag[task_name] = list(item.get("depends_on") or [])
    artifact = DecomposeArtifact(
        execution_id=str(decomposed.get("execution_id") or ""),
        task_id=str(decomposed.get("task_id") or ""),
        project_path=str(decomposed.get("project_path") or ""),
        subtasks=subtasks,
        dag=dag,
        acceptance_criteria=[str(item.get("acceptance") or "") for item in subtasks if item.get("acceptance")],
        metadata={"source": "phase_workflow"},
    )
    decomposed["plan_refs"] = {**dict(decomposed.get("plan_refs") or {}), "decompose": artifact.to_dict()}
    evidence = dict(decomposed.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("decompose", {}).update({"subtasks": subtasks, "dag": dag, "acceptance_criteria": artifact.acceptance_criteria, "present": True})
    decomposed["evidence"] = evidence
    return {"lifecycle_contract": {**decomposed, "evidence": evidence}, "decompose": artifact.to_dict()}


@dataclass
class ObserveArtifact:
    execution_id: str
    task_id: str
    project_path: str
    trace: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiagnoseArtifact:
    execution_id: str
    task_id: str
    project_path: str
    root_causes: List[str] = field(default_factory=list)
    repair_ready: bool = False
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RepairArtifact:
    execution_id: str
    task_id: str
    project_path: str
    attempted: bool = False
    closed_loop: bool = False
    verify_result: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DeliverArtifact:
    execution_id: str
    task_id: str
    project_path: str
    outputs: Dict[str, Any] = field(default_factory=dict)
    runtime_linkage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_observe_artifact(contract_payload: Dict[str, Any], *, trace: Optional[Dict[str, Any]] = None, diagnostics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    observed = dict(contract_payload or {})
    artifact = ObserveArtifact(execution_id=str(observed.get("execution_id") or ""), task_id=str(observed.get("task_id") or ""), project_path=str(observed.get("project_path") or ""), trace=dict(trace or {}), diagnostics=dict(diagnostics or {}), metadata={"source": "phase_workflow"})
    observed["trace"] = artifact.trace
    observed["diagnostics"] = artifact.diagnostics
    evidence = dict(observed.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("observe", {}).update({"trace": artifact.trace, "diagnostics": artifact.diagnostics, "present": True})
    observed["evidence"] = evidence
    return {"lifecycle_contract": observed, "observe": artifact.to_dict()}


def build_diagnose_artifact(contract_payload: Dict[str, Any], *, root_causes: Optional[List[str]] = None, repair_ready: bool = False, confidence: float = 0.0, recommendations: Optional[List[str]] = None) -> Dict[str, Any]:
    diagnosed = dict(contract_payload or {})
    artifact = DiagnoseArtifact(execution_id=str(diagnosed.get("execution_id") or ""), task_id=str(diagnosed.get("task_id") or ""), project_path=str(diagnosed.get("project_path") or ""), root_causes=list(root_causes or []), repair_ready=repair_ready, confidence=float(confidence), recommendations=list(recommendations or []), metadata={"source": "phase_workflow"})
    diagnosed["repair_refs"] = {**dict(diagnosed.get("repair_refs") or {}), "root_causes": artifact.root_causes, "repair_ready": artifact.repair_ready, "confidence": artifact.confidence}
    evidence = dict(diagnosed.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("diagnose", {}).update({"root_causes": artifact.root_causes, "repair_ready": artifact.repair_ready, "confidence": artifact.confidence, "recommendations": artifact.recommendations, "present": True})
    diagnosed["evidence"] = evidence
    return {"lifecycle_contract": diagnosed, "diagnose": artifact.to_dict()}


def build_repair_artifact(contract_payload: Dict[str, Any], *, closed_loop: bool = False, verify_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    repaired = dict(contract_payload or {})
    artifact = RepairArtifact(execution_id=str(repaired.get("execution_id") or ""), task_id=str(repaired.get("task_id") or ""), project_path=str(repaired.get("project_path") or ""), attempted=True, closed_loop=closed_loop, verify_result=dict(verify_result or {}), metadata={"source": "phase_workflow"})
    repaired["repair_refs"] = {**dict(repaired.get("repair_refs") or {}), "closed_loop": artifact.closed_loop, "verify_result": artifact.verify_result}
    evidence = dict(repaired.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("repair", {}).update({"attempted": artifact.attempted, "closed_loop": artifact.closed_loop, "verify_result": artifact.verify_result, "present": True})
    evidence.setdefault("stages", {}).setdefault("verify", {}).update({"closed_loop": artifact.closed_loop, "verify_result": artifact.verify_result, "present": True})
    repaired["evidence"] = evidence
    return {"lifecycle_contract": repaired, "repair": artifact.to_dict()}


def build_deliver_artifact(contract_payload: Dict[str, Any], *, outputs: Optional[Dict[str, Any]] = None, runtime_linkage: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    delivered = dict(contract_payload or {})
    artifact = DeliverArtifact(execution_id=str(delivered.get("execution_id") or ""), task_id=str(delivered.get("task_id") or ""), project_path=str(delivered.get("project_path") or ""), outputs=dict(outputs or {}), runtime_linkage=dict(runtime_linkage or {}), metadata={"source": "phase_workflow"})
    delivered["output_refs"] = {**dict(delivered.get("output_refs") or {}), **artifact.outputs}
    delivered["runtime_linkage"] = {**dict(delivered.get("runtime_linkage") or {}), **artifact.runtime_linkage}
    evidence = dict(delivered.get("evidence") or {})
    evidence.setdefault("stages", {}).setdefault("deliver", {}).update({"outputs": artifact.outputs, "runtime_linkage": artifact.runtime_linkage, "present": True})
    evidence.setdefault("runtime", {}).update({"linked": bool(artifact.runtime_linkage), "healthy": bool(artifact.runtime_linkage)})
    delivered["evidence"] = evidence
    return {"lifecycle_contract": delivered, "deliver": artifact.to_dict()}


__all__ = ["PlanArtifact", "PrepareArtifact", "DecomposeArtifact", "ObserveArtifact", "DiagnoseArtifact", "RepairArtifact", "DeliverArtifact", "build_plan_artifact", "build_prepare_artifact", "build_decompose_artifact", "build_observe_artifact", "build_diagnose_artifact", "build_repair_artifact", "build_deliver_artifact"]
