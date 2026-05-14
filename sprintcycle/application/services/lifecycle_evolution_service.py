"""Lifecycle evolution orchestration.

Connects execution, observability, runtime, governance, and promotion policy
into a single promotion-ready entrypoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .lifecycle_contracts import build_lifecycle_contract, build_lifecycle_state_machine, ensure_lifecycle_evidence
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
        runtime_bundle = self.runtime_registry.latest() if hasattr(self.runtime_registry, "latest") else {}
        runtime = runtime_bundle.get("data", {}) if isinstance(runtime_bundle, dict) else {}
        suggestion_payload = dict(suggestion or {})
        governance_payload = dict(governance or {})
        suggestion_approved = bool(suggestion_payload.get("approved") or governance_payload.get("approved") or governance_payload.get("status") == "approved")
        closed_loop = bool(state_events) or bool(runtime)
        deliver_artifact = build_deliver_artifact({"execution_id": execution_id, "task_id": execution_id, "project_path": project_path, "output_refs": {"trace": trace}, "runtime_linkage": runtime}, outputs={"trace": trace}, runtime_linkage=runtime)
        plan_present = bool(state_events or suggestion_payload or governance_payload or runtime)
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=execution_id,
            project_path=project_path,
            stage="promotion_ready",
            status="success",
            metadata={"source": "lifecycle_evolution"},
            delivery_refs={"trace": trace},
            runtime_refs=runtime,
            suggestion_refs=[suggestion_payload] if suggestion_payload else [],
            governance_refs=governance_payload,
            evolution_refs={"versioned": False, "version_id": f"version_{execution_id}"},
            evidence=ensure_lifecycle_evidence({
                "contract": {"normalized": True},
                "stages": {
                    "normalized": {"normalized": True},
                    "plan": {"objective": suggestion_payload.get("objective", ""), "present": plan_present},
                    "prepare": {"ready": plan_present, "checks": {"runtime": bool(runtime), "trace": bool(state_events)}, "blockers": [], "present": True},
                    "decompose": {"subtasks": suggestion_payload.get("subtasks", []), "present": True},
                    "execute": {"trace": trace, "present": True},
                    "observe": {"trace": trace, "diagnostics": {"event_count": len(state_events)}, "present": True},
                    "diagnose": {"present": bool(state_events), "root_causes": ["trace_observed"] if state_events else [], "repair_ready": bool(state_events or runtime), "confidence": 0.9 if state_events else 0.0, "recommendations": []},
                    "repair": {"attempted": bool(state_events or runtime), "closed_loop": closed_loop, "verify_result": {"healthy": bool(runtime)}, "present": True},
                    "verify": {"closed_loop": closed_loop, "verify_result": {"healthy": bool(runtime)}, "present": True},
                    "deliver": {"outputs": {"trace": trace}, "runtime_linkage": runtime, "present": True, "artifact": deliver_artifact.get("deliver", {})},
                    "runtime": {"linked": bool(runtime), "healthy": bool(runtime), "present": True},
                    "governance": {"approved": suggestion_approved, "present": True},
                    "promotion": {"evidence": True, "completion_score": 100.0 if suggestion_approved and closed_loop else 80.0},
                    "evolution": {"versioned": False, "version_id": f"version_{execution_id}", "present": True},
                },
                "runtime": {"healthy": bool(runtime), "linked": bool(runtime), "runtime": runtime},
                "suggestion": {**suggestion_payload, "approved": suggestion_approved},
                "governance": {"approved": suggestion_approved, **governance_payload},
                "promotion": {"evidence": True, "completion_score": 100.0 if suggestion_approved and closed_loop else 80.0},
                "evolution": {"versioned": False, "version_id": f"version_{execution_id}"},
            }),
            metrics={"event_count": len(state_events)},
            recovery_refs={"closed_loop": closed_loop, "recovered": closed_loop, "repair_ready": bool(state_events or runtime)},
            trace=trace,
            diagnostics={"event_count": len(state_events), "repair_ready": bool(state_events or runtime), "trace_present": bool(state_events)},
            input_refs={"execution_id": execution_id, "project_path": project_path},
            output_refs={"runtime": runtime, "deliver": deliver_artifact.get("deliver", {})},
            validation_refs={"trace_present": bool(state_events), "runtime_present": bool(runtime), "delivery_present": bool(deliver_artifact), "recovered": closed_loop, "versioned_evolution": False, "suggestion_approved": suggestion_approved, "promotion_allowed": False},
            transition_reason="promotion contract build",
        )
        machine = build_lifecycle_state_machine()
        correlation = machine.ensure_correlation({"execution_id": execution_id, "runtime_id": runtime.get("runtime_id", ""), "source": "lifecycle_evolution"})
        contract_dict = machine.attach_correlation(contract.to_dict(), correlation)
        contract_dict.setdefault("evidence", {}).setdefault("evolution", {})["versioned"] = False
        contract_dict.setdefault("validation_refs", {})["versioned_evolution"] = bool(contract_dict.get("evidence", {}).get("evolution", {}).get("versioned"))
        return contract_dict

    def evaluate_promotion(self, contract: Dict[str, Any], *, runtime: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = dict(contract or {})
        decision = self.promotion_policy.evaluate(contract, runtime=runtime, governance=governance)
        missing_evidence = [reason.split(":", 1)[1] for reason in decision.get("reasons", []) if str(reason).startswith("evidence_invalid:")]
        return {
            "success": True,
            "data": {
                "contract": contract,
                "promotion": decision,
                "promotable": bool(decision.get("allowed", False)),
                "blocked": not bool(decision.get("allowed", False)),
                "missing_evidence": missing_evidence,
                "readiness": {
                    "runtime_present": bool(runtime),
                    "governance_present": bool(governance),
                    "trace_present": bool((contract.get("trace") or {}).get("events") if isinstance(contract.get("trace"), dict) else contract.get("trace")),
                },
            },
        }

    def promote(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = self.build_contract(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        runtime_bundle = self.runtime_registry.latest() if hasattr(self.runtime_registry, "latest") else {}
        runtime = runtime_bundle.get("data", {}) if isinstance(runtime_bundle, dict) else {}
        decision = self.promotion_policy.evaluate(contract, runtime=runtime, governance=governance)
        if not decision.get("allowed", False):
            return {"success": False, "error": "promotion blocked", "data": {"contract": contract, "promotion": decision, "blocked": True}}
        machine = build_lifecycle_state_machine()
        contract["validation_refs"] = {**dict(contract.get("validation_refs") or {}), "promotion_allowed": True}
        contract.setdefault("evidence", {})
        contract["evidence"] = ensure_lifecycle_evidence(contract.get("evidence"))
        contract["evidence"].setdefault("promotion", {})
        contract["evidence"]["promotion"].update({"evidence": True, "completion_score": float(decision.get("score") or 100.0)})
        promoted = machine.transition(contract, "promoted", status="promoted", reason="promotion gate passed", metadata={"source": "lifecycle_evolution"})
        version = {"version_id": f"version_{execution_id}", "source_execution_id": execution_id, "stage": "promoted", "versioned": True, "contract_stage": promoted.get("stage", "promoted")}
        promoted.setdefault("evolution_refs", {})
        promoted["evolution_refs"].update(version)
        promoted.setdefault("evidence", {})
        promoted["evidence"] = ensure_lifecycle_evidence(promoted.get("evidence"))
        promoted["evidence"].setdefault("evolution", {})
        promoted["evidence"]["evolution"].update(version)
        promoted.setdefault("validation_refs", {})
        promoted["validation_refs"]["versioned_evolution"] = True
        promoted["validation_refs"]["promotion_allowed"] = True
        return {
            "success": True,
            "data": {
                "contract": promoted,
                "promotion": decision,
                "version": version,
                "audit": {"execution_id": execution_id, "allowed": True, "reasons": decision.get("reasons", [])},
            },
        }


__all__ = ["LifecycleEvolutionService"]
