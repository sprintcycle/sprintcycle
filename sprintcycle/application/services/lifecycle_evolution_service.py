"""Lifecycle evolution helpers.

The service converts execution and contract evidence into promotion-ready
artifacts and keeps the promotion contract explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sprintcycle.infrastructure.runtime_registry import RuntimeRegistry
from sprintcycle.observability.facade import ObservabilityFacade
from sprintcycle.application.services.promotion_policy import PromotionPolicy


@dataclass
class LifecycleEvolutionService:
    observability: ObservabilityFacade
    runtime_registry: RuntimeRegistry
    promotion_policy: PromotionPolicy

    def build_contract(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = self.observability.trace(execution_id)
        runtime = self.runtime_registry.records[-1] if self.runtime_registry.records else {}
        return {
            "execution_id": execution_id,
            "project_path": project_path,
            "stage": "promotion_ready" if runtime else "delivering",
            "status": "pending",
            "trace": trace.get("data", trace) if isinstance(trace, dict) else {},
            "runtime": runtime,
            "suggestion": suggestion or {},
            "governance": governance or {},
            "validation_refs": {"final_snapshot": True},
            "evidence": {"contract": {"normalized": True}, "stages": {}, "runtime": runtime, "governance": governance or {}, "promotion": {}, "evolution": {}},
        }

    def evaluate_promotion(self, contract: Dict[str, Any], runtime: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        runtime_payload = dict(runtime or contract.get("runtime") or {})
        evidence = dict(contract.get("evidence") or {})
        promotion = self.promotion_policy.evaluate(contract, runtime=runtime_payload, governance=governance or contract.get("governance"), evidence=evidence)
        return {"success": True, "data": {"promotion": promotion, "contract": contract, "runtime": runtime_payload}}

    def promote(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = self.build_contract(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        evaluation = self.evaluate_promotion(contract, runtime=contract.get("runtime"), governance=governance)
        promotion = evaluation.get("data", {}).get("promotion", {})
        return {"success": True, "data": {"contract": contract, "promotion": promotion, "version": {"version_id": f"version-{execution_id}", "status": promotion.get("status", "blocked")}}}
