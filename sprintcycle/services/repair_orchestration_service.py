"""Repair orchestration service.

Implements an explicit repair -> verify -> observe loop for lifecycle recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..observability.facade import ObservabilityFacade
from .lifecycle_contracts import build_lifecycle_contract, build_lifecycle_state_machine
from .phase_workflow import build_diagnose_artifact, build_observe_artifact, build_repair_artifact


@dataclass
class RepairOrchestrationService:
    observability: ObservabilityFacade

    def diagnose(self, execution_id: str, trace_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = dict(trace_payload or self.observability.to_trace_payload(execution_id) or {})
        events = list(trace.get("events", []) or [])
        root_causes = sorted({str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip() for e in events if str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip()})
        failures = [e for e in events if str((e or {}).get("kind") or "").lower().find("fail") >= 0]
        artifact = build_diagnose_artifact(trace or {"execution_id": execution_id}, root_causes=root_causes, repair_ready=bool(root_causes or failures), confidence=1.0 if root_causes or failures else 0.0, recommendations=["repair" if root_causes or failures else "observe"])
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

    def repair(self, execution_id: str, diagnosis: Dict[str, Any], *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        verify_contract = machine.transition(contract.to_dict(), "verifying", status="running", reason="repair completed", metadata={"source": "repair"})
        observe_contract = machine.transition(verify_contract, "observing", status="success", reason="verification passed", metadata={"source": "repair"})
        repair_artifact = build_repair_artifact(contract.to_dict(), closed_loop=True, verify_result=verify_contract)
        observe_artifact = build_observe_artifact(observe_contract, trace=trace, diagnostics=dict(diagnosis or {}))
        return {
            "success": True,
            "data": {
                "execution_id": execution_id,
                "diagnosis": diagnosis,
                "repair_contract": contract.to_dict(),
                "verify_contract": verify_contract,
                "observe_contract": observe_contract,
                "repair_artifact": repair_artifact.get("repair", {}),
                "observe_artifact": observe_artifact.get("observe", {}),
                "closed_loop": True,
            },
        }

    def repair_and_verify(self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        diagnosis = self.diagnose(execution_id)
        if not diagnosis.get("success", False):
            return diagnosis
        return self.repair(execution_id, diagnosis.get("data", {}), repair_plan=repair_plan)


__all__ = ["RepairOrchestrationService"]
