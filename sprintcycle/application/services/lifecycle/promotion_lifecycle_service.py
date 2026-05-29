"""Promotion lifecycle management service.

**职责边界**：
- 发布评估与交付
- 运行时、治理、发布的整合
- 部署生命周期

**DDD Architecture**：
- 应用层服务，只做编排
- 依赖通过构造函数注入
- 保持接口与原 LifecycleDeliveryService 兼容
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from sprintcycle.application.services.lifecycle.lifecycle_evolution_service import LifecycleEvolutionService
from sprintcycle.application.services.lifecycle.governance_lifecycle_service import GovernanceLifecycleService
from sprintcycle.application.services.lifecycle.runtime_lifecycle_service import RuntimeLifecycleService
from sprintcycle.domain.ports.deploy import PlatformLaunchServiceProtocol


@dataclass
class PromotionLifecycleService:
    project_path: str
    runtime_lifecycle_service: RuntimeLifecycleService
    governance_lifecycle_service: GovernanceLifecycleService
    lifecycle_evolution: LifecycleEvolutionService
    platform_launch: PlatformLaunchServiceProtocol
    deploy_view: Callable[[], Dict[str, Any]]
    lifecycle_contract: Callable[[str], Dict[str, Any]]
    evaluate_promotion: Callable[..., Dict[str, Any]]

    async def deliver_runtime_governance_promotion(
        self,
        execution_id: str,
        *,
        project_path: str = "",
        suggestion: Optional[Dict[str, Any]] = None,
        governance: Optional[Dict[str, Any]] = None,
        lifecycle_contract: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        runtime_bundle = self.runtime_lifecycle_service.runtime_lifecycle(execution_id)
        governance_bundle = await self.governance_lifecycle_service.governance_lifecycle(execution_id)
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
        deployment = self.deploy_view()
        runtime = self.runtime_lifecycle_service.runtime_lifecycle()
        runtime_id = str((runtime.get("data", {}) or {}).get("runtime", {}).get("runtime_id", ""))
        contract = self.lifecycle_contract(runtime_id) if runtime_id else {"success": False, "data": {}}
        governance_summary = await self.governance_lifecycle_service.governance_lifecycle()
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


__all__ = ["PromotionLifecycleService"]
