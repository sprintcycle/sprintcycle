"""Runtime, governance, deploy, and recovery lifecycle delivery.

**分层**：LifecycleDeliveryService 通过构造函数接收依赖。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from sprintcycle.application.services.governance_orchestration_service import GovernanceOrchestrationService
from sprintcycle.application.services.lifecycle.lifecycle_evolution_service import LifecycleEvolutionService
from sprintcycle.application.services.repair_orchestration_service import RepairOrchestrationService

# TYPE_CHECKING: 仅用于类型提示
if TYPE_CHECKING:
    from sprintcycle.infrastructure.deployment.platform_launch_service import PlatformLaunchService
    from sprintcycle.infrastructure.config.runtime_registry import RuntimeRegistry


@dataclass
class LifecycleDeliveryService:
    project_path: str
    runtime_registry: RuntimeRegistry
    governance_orchestration: GovernanceOrchestrationService
    lifecycle_evolution: LifecycleEvolutionService
    repair_orchestration: RepairOrchestrationService
    platform_launch: PlatformLaunchService
    runtime_latest: Callable[[], Dict[str, Any]]
    observability_trace: Callable[[str], Dict[str, Any]]
    observe_execution: Callable[[str], Dict[str, Any]]
    deploy_view: Callable[[], Dict[str, Any]]
    lifecycle_contract: Callable[[str], Dict[str, Any]]
    evaluate_promotion: Callable[..., Dict[str, Any]]

    def runtime_lifecycle(self, runtime_id: str = "") -> Dict[str, Any]:
        latest = self.runtime_latest()
        data = latest.get("data", {}) if isinstance(latest, dict) else {}
        if runtime_id:
            payload = self.runtime_registry.get(runtime_id)
            data = payload if isinstance(payload, dict) else {"runtime_id": runtime_id, "success": bool(payload)}
        has_runtime = bool(data)
        closure_score = 100.0 if has_runtime else 0.0
        lifecycle = {
            "stage": "runtime_linked" if data else "delivering",
            "status": str(data.get("status") or "unknown") if isinstance(data, dict) else "unknown",
            "runtime_id": runtime_id or data.get("runtime_id") or data.get("id") or "",
            "has_runtime": has_runtime,
            "closure_score": closure_score,
        }
        return {
            "success": True,
            "data": {
                "runtime": data,
                "lifecycle": lifecycle,
                "health": {"closure_score": closure_score, "is_healthy": has_runtime},
            },
        }

    async def governance_lifecycle(self, execution_id: str = "") -> Dict[str, Any]:
        summary = await self.governance_orchestration.summary(execution_id=execution_id, limit=50)
        pending = await self.governance_orchestration.pending(execution_id=execution_id)
        history = await self.governance_orchestration.history(execution_id=execution_id, limit=50)
        summary_data = summary.get("data", {}) if isinstance(summary, dict) else {}
        pending_data = pending.get("data", []) if isinstance(pending, dict) else []
        history_data = history.get("data", []) if isinstance(history, dict) else []
        closure_score = 100.0 if summary.get("success", False) and not pending_data else 0.0
        return {
            "success": True,
            "data": {
                "summary": summary_data,
                "pending": pending_data,
                "history": history_data,
                "lifecycle": {
                    "stage": "governing",
                    "status": "success" if summary.get("success", False) else "failed",
                    "execution_id": execution_id,
                    "pending_count": len(pending_data),
                    "history_count": len(history_data),
                    "summary_count": int(summary_data.get("history_count", 0) if isinstance(summary_data, dict) else 0),
                    "closure_score": closure_score,
                },
                "health": {"closure_score": closure_score, "is_healthy": closure_score > 0},
            },
        }

    async def deliver_runtime_governance_promotion(
        self,
        execution_id: str,
        *,
        project_path: str = "",
        suggestion: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
        lifecycle_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        runtime_bundle = self.runtime_lifecycle(execution_id)
        governance_bundle = await self.governance_lifecycle(execution_id)
        promotion_bundle = self.evaluate_promotion(
            execution_id,
            project_path=project_path,
            suggestion=suggestion,
            governance=governance,
            lifecycle_contract=lifecycle_contract,
        )
        lifecycle_payload: Dict[str, Any] = {}
        if isinstance(runtime_bundle, dict):
            lifecycle_payload = (
                runtime_bundle.get("data", {}).get("runtime", {})
                if isinstance(runtime_bundle.get("data", {}), dict)
                else {}
            )
        if isinstance(governance_bundle, dict):
            governance_contract = (
                governance_bundle.get("data", {}).get("summary", {})
                if isinstance(governance_bundle.get("data", {}), dict)
                else {}
            )
        else:
            governance_contract = {}
        return {
            "success": True,
            "data": {
                "runtime": runtime_bundle,
                "governance": governance_bundle,
                "promotion": promotion_bundle,
                "lifecycle_contract": {
                    "runtime": lifecycle_payload,
                    "governance": governance_contract,
                    "promotion": promotion_bundle.get("data", {}) if isinstance(promotion_bundle, dict) else {},
                },
            },
        }

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
        delivery_bundle = await self.deliver_runtime_governance_promotion(
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

    async def deploy_lifecycle(self) -> Dict[str, Any]:
        deployment = self.deploy_view()
        runtime = self.runtime_lifecycle()
        runtime_id = str((runtime.get("data", {}) or {}).get("runtime", {}).get("runtime_id", ""))
        contract = self.lifecycle_contract(runtime_id) if runtime_id else {"success": False, "data": {}}
        governance_summary = await self.governance_lifecycle()
        promotion = self.evaluate_promotion(
            runtime_id or self.project_path,
            project_path=self.project_path,
            governance=governance_summary.get("data", {}).get("summary", {}),
        )
        success = bool(deployment.get("success", False)) and bool(runtime.get("success", False))
        closure_score = 100.0 if success else 0.0
        launch = (
            self.platform_launch.launch(
                contract.get("data", {}) if isinstance(contract, dict) else {},
                launch_mode="auto",
                platform="dashboard",
            )
            if runtime_id
            else {"success": False, "data": {}}
        )
        return {
            "success": success,
            "data": {
                "deployment": deployment.get("data", {}),
                "runtime": runtime.get("data", {}),
                "contract": contract.get("data", {}) if isinstance(contract, dict) else {},
                "promotion": promotion.get("data", {}),
                "launch": launch.get("data", {}),
                "lifecycle": {
                    "stage": "runtime_linked",
                    "status": "success" if success else "failed",
                    "has_deployment": bool(deployment.get("success", False)),
                    "has_runtime": bool(runtime.get("success", False)),
                    "promotion_ready": bool(
                        (promotion.get("data", {}) or {}).get("promotion", {}).get("passed", False)
                    ),
                    "launch_ready": bool((launch.get("data", {}) or {}).get("status") == "running"),
                    "closure_score": closure_score,
                },
                "health": {"closure_score": closure_score, "is_healthy": success},
            },
        }


__all__ = ["LifecycleDeliveryService"]
