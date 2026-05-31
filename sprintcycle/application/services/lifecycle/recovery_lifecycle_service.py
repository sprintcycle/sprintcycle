"""Recovery lifecycle management service.

**职责边界**：
- 恢复流程编排
- 诊断、修复、观察流程
- 恢复与发布整合

**DDD Architecture**：
- 应用层服务，只做编排
- 依赖通过构造函数注入
- 保持接口与原 LifecycleDeliveryService 兼容
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from sprintcycle.application.services.governance.repair_orchestration_service import RepairOrchestrationService
from sprintcycle.application.services.lifecycle.delivery_service import DeliveryService


@dataclass
class RecoveryLifecycleService:
    project_path: str
    repair_orchestration: RepairOrchestrationService
    delivery_service: DeliveryService
    observability_trace: Callable[[str], Dict[str, Any]]
    observe_execution: Callable[[str], Dict[str, Any]]
    evaluate_promotion: Callable[..., Dict[str, Any]]

    def diagnose_repair_observe(
        self,
        execution_id: str,
        *,
        repair_plan: Optional[Dict[str, Any]] = None,
        diagnose_execution: Callable[[str], Dict[str, Any]],
        repair_execution: Callable[..., Dict[str, Any]],
    ) -> Dict[str, Any]:
        diagnosis = diagnose_execution(execution_id)
        repair = (
            repair_execution(execution_id, repair_plan=repair_plan)
            if diagnosis.get("success", False) and diagnosis.get("data", {}).get("repair_ready", False)
            else diagnosis
        )
        observation = self.observe_execution(execution_id)
        lifecycle_contract = (
            observation.get("data", {}).get("lifecycle_contract", {}) if isinstance(observation, dict) else {}
        )
        if isinstance(repair, dict) and repair.get("success", False):
            repair_data = repair.get("data", {}) if isinstance(repair, dict) else {}
            lifecycle_contract = {
                **dict(lifecycle_contract or {}),
                "recovery_refs": {
                    **dict(lifecycle_contract.get("recovery_refs") or {}),
                    "repair": repair_data.get("repair_contract", {}),
                    "verify": repair_data.get("verify_contract", {}),
                    "closed_loop": repair_data.get("closed_loop", False),
                },
                "diagnostics": {
                    **dict(lifecycle_contract.get("diagnostics") or {}),
                    "diagnosis": diagnosis.get("data", {}) if isinstance(diagnosis, dict) else {},
                },
                "observation_refs": {
                    **dict(lifecycle_contract.get("observation_refs") or {}),
                    "observability": observation.get("data", {}) if isinstance(observation, dict) else {},
                },
            }
        return {
            "success": True,
            "data": {
                "diagnosis": diagnosis,
                "repair": repair,
                "observation": observation,
                "lifecycle_contract": lifecycle_contract,
            },
        }

    async def lifecycle_recovery_and_promotion(
        self,
        execution_id: str,
        *,
        project_path: str = "",
        suggestion: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
        repair_plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        trace = self.observability_trace(execution_id)
        trace_payload = trace.get("data", {}).get("trace", {}) if isinstance(trace, dict) else {}
        recovery = self.repair_orchestration.recover(execution_id, trace_payload=trace_payload, repair_plan=repair_plan)
        lifecycle_contract = {}
        if isinstance(recovery, dict):
            lifecycle_contract = (
                recovery.get("data", {}).get("lifecycle_contract", {})
                if isinstance(recovery.get("data", {}), dict)
                else {}
            )
        promotion = self.evaluate_promotion(
            execution_id, project_path=project_path, suggestion=suggestion, governance=governance
        )
        delivery_bundle = await self.delivery_service.deliver_runtime_governance_promotion(
            execution_id, project_path=project_path, suggestion=suggestion, governance=governance
        )
        return {
            "success": True,
            "data": {
                "recovery": recovery,
                "promotion": promotion,
                "delivery": delivery_bundle,
                "lifecycle_contract": lifecycle_contract,
            },
        }


__all__ = ["RecoveryLifecycleService"]
