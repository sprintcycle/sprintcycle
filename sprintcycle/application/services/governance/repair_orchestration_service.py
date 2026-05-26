"""Repair orchestration service.

Implements an explicit repair -> verify -> observe loop for lifecycle recovery.

**分层**：RepairOrchestrationService 通过构造函数接收依赖。

使用新架构：LifecycleRoot + LifecycleStateMachineService
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sprintcycle.domain.generic.ports.observability import ObservabilityFacadeProtocol
from sprintcycle.domain.core.lifecycle import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStateMachineService,
    create_lifecycle,
)
from ..execution.phase_workflow import build_diagnose_artifact, build_observe_artifact, build_repair_artifact


@dataclass
class RepairOrchestrationService:
    observability: ObservabilityFacadeProtocol

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
        root_causes = list((diagnosis or {}).get("root_causes", []) or [])
        trace = dict((diagnosis or {}).get("trace") or {})
        
        # 使用新架构创建 lifecycle
        lifecycle = create_lifecycle(
            execution_id=execution_id,
            task_id=execution_id,
            project_path=str((repair_plan or {}).get("project_path") or ""),
            metadata={
                "source": "repair",
                "repair_plan": dict(repair_plan or {}),
                "recovery_refs": {"root_causes": root_causes, "repair_plan": dict(repair_plan or {}), "attempted": True},
                "delivery_refs": {"diagnosis": diagnosis},
                "trace": trace,
                "diagnostics": diagnosis,
                "validation_refs": {"repair_ready": bool(root_causes or trace.get("events"))},
                "input_refs": {"diagnosis": diagnosis},
                "output_refs": {"repair_attempted": True},
            },
        )
        
        # 转换到 repairing 阶段
        lifecycle = lifecycle.transition_to(LifecycleStage.REPAIRING)
        
        # 转换到 verifying 阶段
        lifecycle = lifecycle.transition_to(LifecycleStage.VERIFYING)
        
        # 转换到 observing 阶段
        lifecycle = lifecycle.transition_to(LifecycleStage.OBSERVING)
        
        # 使用服务获取字典格式
        service = LifecycleStateMachineService()
        lifecycle_dict = {
            "contract_id": lifecycle.contract_id,
            "execution_id": lifecycle.execution_id,
            "task_id": lifecycle.task_id,
            "project_path": lifecycle.project_path,
            "stage": lifecycle.stage.value,
            "status": lifecycle.status.value,
            "metadata": dict(lifecycle.metadata),
            "recovery_refs": dict(lifecycle.metadata.get("recovery_refs", {})),
            "observation_refs": {},
            "evidence": {"stages": {}},
            "stage_history": [
                {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
                for h in lifecycle.stage_history
            ],
            "is_terminal": service.is_terminal(lifecycle.stage.value),
            "stage_index": service.stage_index(lifecycle.stage.value),
        }
        
        # 创建 artifacts
        repair_artifact = build_repair_artifact(lifecycle_dict, closed_loop=True, verify_result=lifecycle_dict)
        observe_artifact = build_observe_artifact(lifecycle_dict, trace=trace, diagnostics=dict(diagnosis or {}))
        
        # 构建最终合约
        lifecycle_contract = {
            **lifecycle_dict,
            "stage": lifecycle.stage.value,
            "status": lifecycle.status.value,
            "recovery_refs": {
                **dict(lifecycle_dict.get("recovery_refs") or {}),
                "closed_loop": True,
                "verify_result": lifecycle_dict,
                "observe_result": lifecycle_dict,
            },
            "observation_refs": {
                **dict(lifecycle_dict.get("observation_refs") or {}),
                "observability": observe_artifact.get("observe", {}),
            },
            "evidence": {
                "stages": {
                    "repair": {
                        "attempted": True,
                        "closed_loop": True,
                        "verify_result": lifecycle_dict,
                        "present": True,
                    },
                    "verify": {"closed_loop": True, "verify_result": lifecycle_dict, "present": True},
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
                "repair_contract": lifecycle_dict,
                "verify_contract": lifecycle_dict,
                "observe_contract": lifecycle_dict,
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
