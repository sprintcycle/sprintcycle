"""Delivery service - 合并后的交付生命周期服务

**职责边界**：
- 运行时生命周期管理
- 治理生命周期管理
- 发布评估与交付
- 部署生命周期

**设计说明**：
本服务合并了原有的三个服务：
- RuntimeLifecycleService
- GovernanceLifecycleService  
- PromotionLifecycleService

通过合并减少了服务数量，简化了依赖关系，同时保持向后兼容性。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from sprintcycle.application.services.governance.governance_orchestration_service import GovernanceOrchestrationService
from sprintcycle.application.services.lifecycle.lifecycle_evolution_service import LifecycleEvolutionService
from sprintcycle.domain.ports.deploy import PlatformLaunchServiceProtocol
from sprintcycle.domain.ports.registry import RuntimeRegistryProtocol


@dataclass
class DeliveryService:
    """合并后的交付生命周期服务"""
    
    project_path: str
    runtime_registry: RuntimeRegistryProtocol
    governance_orchestration: GovernanceOrchestrationService
    lifecycle_evolution: LifecycleEvolutionService
    platform_launch: PlatformLaunchServiceProtocol
    deploy_view: Callable[[], Dict[str, Any]]
    lifecycle_contract: Callable[[str], Dict[str, Any]]
    evaluate_promotion: Callable[..., Dict[str, Any]]
    runtime_latest: Callable[[], Dict[str, Any]]

    # === Runtime Lifecycle Methods ===
    
    def runtime_lifecycle(self, runtime_id: str = "") -> Dict[str, Any]:
        """获取运行时生命周期状态"""
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

    # === Governance Lifecycle Methods ===
    
    async def governance_lifecycle(self, execution_id: str = "") -> Dict[str, Any]:
        """获取治理生命周期状态"""
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

    # === Promotion Lifecycle Methods ===
    
    async def deliver_runtime_governance_promotion(
        self,
        execution_id: str,
        *,
        project_path: str = "",
        suggestion: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
        lifecycle_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """交付运行时、治理和发布"""
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

    async def deploy_lifecycle(self) -> Dict[str, Any]:
        """部署生命周期"""
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


__all__ = ["DeliveryService"]