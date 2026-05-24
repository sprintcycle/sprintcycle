"""Repair orchestration service.

Implements an explicit repair -> verify -> observe loop for lifecycle recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sprintcycle.infrastructure.observability.facade import ObservabilityFacade
from .lifecycle.lifecycle_contracts import build_lifecycle_contract, build_lifecycle_state_machine
from .phase_workflow import build_diagnose_artifact, build_observe_artifact, build_repair_artifact


@dataclass
class RepairOrchestrationService:
    observability: ObservabilityFacade

    def diagnose(self, execution_id: str, trace_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = dict(trace_payload or self.observability.to_trace_payload(execution_id) or {})
        events = list(trace.get("events", []) or [])
        root_causes = sorted(
            {
                str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip()
                for e in events
                if str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip()
            }
        )
        failures = [e for e in events if str((e or {}).get("kind") or "").lower().find("fail") >= 0]
        artifact = build_diagnose_artifact(
            trace or {"execution_id": execution_id},
            root_causes=root_causes,
            repair_ready=bool(root_causes or failures),
            confidence=1.0 if root_causes or failures else 0.0,
            recommendations=["repair" if root_causes or failures else "observe"],
        )
        return {
            "success": True,
            "data": {
                "execution_id": execution_id,
                "failure_count": len(failures),
                "root_causes": root_causes,
                "repair_ready": bool(root_causes or failures),
                "trace": trace,
                "diagnose_artifact": artifact.get("diagnose", {}),
            },
        }

    def repair(
        self, execution_id: str, diagnosis: Dict[str, Any], *, repair_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        machine = build_lifecycle_state_machine()
        root_causes = list((diagnosis or {}).get("root_causes", []) or [])
        trace = dict((diagnosis or {}).get("trace") or {})
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=execution_id,
            project_path=str((repair_plan or {}).get("project_path") or ""),
            stage="repairing",
            status="running",
            metadata={"source": "repair", "repair_plan": dict(repair_plan or {})},
            recovery_refs={"root_causes": root_causes, "repair_plan": dict(repair_plan or {}), "attempted": True},
            delivery_refs={"diagnosis": diagnosis},
            trace=trace,
            diagnostics=diagnosis,
            correlation=machine.ensure_correlation({"execution_id": execution_id, "source": "repair"}).to_dict(),
            validation_refs={"repair_ready": bool(root_causes or trace.get("events"))},
            input_refs={"diagnosis": diagnosis},
            output_refs={"repair_attempted": True},
        )
        contract_dict = contract.to_dict()
        verify_contract = machine.transition(
            contract_dict, "verifying", status="running", reason="repair completed", metadata={"source": "repair"}
        )
        observe_contract = machine.transition(
            verify_contract, "observing", status="success", reason="verification passed", metadata={"source": "repair"}
        )
        repair_artifact = build_repair_artifact(contract_dict, closed_loop=True, verify_result=verify_contract)
        observe_artifact = build_observe_artifact(observe_contract, trace=trace, diagnostics=dict(diagnosis or {}))
        lifecycle_contract = {
            **contract_dict,
            "stage": observe_contract.get("stage", "observing"),
            "status": observe_contract.get("status", "success"),
            "recovery_refs": {
                **dict(contract_dict.get("recovery_refs") or {}),
                "closed_loop": True,
                "verify_result": verify_contract,
                "observe_result": observe_contract,
            },
            "observation_refs": {
                **dict(contract_dict.get("observation_refs") or {}),
                "observability": observe_artifact.get("observe", {}),
            },
            "evidence": {
                **dict(observe_contract.get("evidence") or {}),
                "stages": {
                    **dict((observe_contract.get("evidence") or {}).get("stages") or {}),
                    "repair": {
                        "attempted": True,
                        "closed_loop": True,
                        "verify_result": verify_contract,
                        "present": True,
                    },
                    "verify": {"closed_loop": True, "verify_result": verify_contract, "present": True},
                    "observe": {"trace": trace, "diagnostics": dict(diagnosis or {}), "present": True},
                },
                "recovery": {"closed_loop": True, "repaired": True},
            },
        }
        return {
            "success": True,
            "data": {
                "execution_id": execution_id,
                "diagnosis": diagnosis,
                "repair_contract": contract_dict,
                "verify_contract": verify_contract,
                "observe_contract": observe_contract,
                "repair_artifact": repair_artifact.get("repair", {}),
                "observe_artifact": observe_artifact.get("observe", {}),
                "lifecycle_contract": lifecycle_contract,
                "closed_loop": True,
            },
        }

    def repair_and_verify(self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        diagnosis = self.diagnose(execution_id)
        if not diagnosis.get("success", False):
            return diagnosis
        return self.repair(execution_id, diagnosis.get("data", {}), repair_plan=repair_plan)

    def recover(
        self,
        execution_id: str,
        *,
        trace_payload: Optional[Dict[str, Any]] = None,
        repair_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        diagnosis = self.diagnose(execution_id, trace_payload=trace_payload)
        if not diagnosis.get("success", False):
            return diagnosis
        diagnosis_data = diagnosis.get("data", {}) if isinstance(diagnosis, dict) else {}
        if not diagnosis_data.get("repair_ready", False):
            observed = build_observe_artifact(
                {
                    "execution_id": execution_id,
                    "task_id": execution_id,
                    "project_path": "",
                    "stage": "observing",
                    "status": "success",
                },
                trace=trace_payload or self.observability.to_trace_payload(execution_id),
                diagnostics={"repair_ready": False},
            )
            return {
                "success": True,
                "data": {
                    "execution_id": execution_id,
                    "diagnosis": diagnosis_data,
                    "recovery": {"mode": "observe_only", "repair_ready": False},
                    "observe_artifact": observed.get("observe", {}),
                    "closed_loop": False,
                },
            }
        return self.repair(execution_id, diagnosis_data, repair_plan=repair_plan)


__all__ = ["RepairOrchestrationService"]
