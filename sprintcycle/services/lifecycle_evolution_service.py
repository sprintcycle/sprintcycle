"""Lifecycle evolution orchestration.

Connects execution, observability, runtime, governance, and promotion policy
into a single promotion-ready entrypoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .lifecycle_contracts import build_lifecycle_contract, build_lifecycle_state_machine
from .phase_workflow import build_deliver_artifact
from .promotion_policy import PromotionPolicy
from .suggestion_application_service import SuggestionApplicationService
from ..deployment.runtime_registry import RuntimeRegistry
from ..observability.facade import ObservabilityFacade


@dataclass
class LifecycleEvolutionService:
    observability: ObservabilityFacade
    runtime_registry: RuntimeRegistry
    promotion_policy: PromotionPolicy

    def build_contract(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        trace = self.observability.to_trace_payload(execution_id)
        state_events = list((trace or {}).get("events", []) or [])
        runtime = self.runtime_registry.latest().get("data", {}) if hasattr(self.runtime_registry, "latest") else {}
        deliver_artifact = build_deliver_artifact({"execution_id": execution_id, "task_id": execution_id, "project_path": project_path, "output_refs": {"trace": trace}, "runtime_linkage": runtime}, outputs={"trace": trace}, runtime_linkage=runtime)
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=execution_id,
            project_path=project_path,
            stage="promotion_ready",
            status="pending",
            metadata={"source": "lifecycle_evolution"},
            delivery_refs={"trace": trace},
            runtime_refs=runtime,
            suggestion_refs=[dict(suggestion or {})] if suggestion else [],
            governance_refs=dict(governance or {}),
            metrics={"event_count": len(state_events)},
            recovery_refs={"closed_loop": bool(state_events)},
            trace=trace,
            diagnostics={"event_count": len(state_events)},
            input_refs={"execution_id": execution_id, "project_path": project_path},
            output_refs={"runtime": runtime, "deliver": deliver_artifact.get("deliver", {})},
            validation_refs={"trace_present": bool(state_events), "runtime_present": bool(runtime), "delivery_present": bool(deliver_artifact)},
            transition_reason="promotion contract build",
        )
        machine = build_lifecycle_state_machine()
        correlation = machine.ensure_correlation({"execution_id": execution_id, "runtime_id": runtime.get("runtime_id", ""), "source": "lifecycle_evolution"})
        return machine.attach_correlation(contract.to_dict(), correlation)

    def evaluate_promotion(self, contract: Dict[str, Any], *, runtime: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = dict(contract or {})
        decision = self.promotion_policy.evaluate(contract, runtime=runtime, governance=governance)
        return {
            "success": True,
            "data": {
                "contract": contract,
                "promotion": decision,
                "promotable": bool(decision.get("allowed", False)),
                "readiness": {
                    "runtime_present": bool(runtime),
                    "governance_present": bool(governance),
                    "trace_present": bool((contract.get("trace") or {}).get("events") if isinstance(contract.get("trace"), dict) else contract.get("trace")),
                },
            },
        }

    def promote(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = self.build_contract(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        runtime = self.runtime_registry.latest().get("data", {}) if hasattr(self.runtime_registry, "latest") else {}
        decision = self.promotion_policy.evaluate(contract, runtime=runtime, governance=governance)
        if not decision.get("allowed", False):
            return {"success": False, "error": "promotion blocked", "data": {"contract": contract, "promotion": decision}}
        machine = build_lifecycle_state_machine()
        promoted = machine.transition(contract, "promoted", status="promoted", reason="promotion gate passed", metadata={"source": "lifecycle_evolution"})
        return {
            "success": True,
            "data": {
                "contract": promoted,
                "promotion": decision,
                "version": {"version_id": f"version_{execution_id}", "source_execution_id": execution_id, "stage": "promoted"},
                "audit": {"execution_id": execution_id, "allowed": True, "reasons": decision.get("reasons", [])},
            },
        }


__all__ = ["LifecycleEvolutionService"]
