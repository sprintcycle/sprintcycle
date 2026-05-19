"""Assemble full lifecycle contract payloads for dashboard and API consumers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict

from sprintcycle.application.services.governance_orchestration_service import GovernanceOrchestrationService
from sprintcycle.application.services.lifecycle_evolution_service import LifecycleEvolutionService
from sprintcycle.application.services.web_lifecycle_orchestration_service import WebLifecycleOrchestrationService


@dataclass
class LifecycleContractAssemblyService:
    project_path: str
    execution_detail: Callable[[str, int], Dict[str, Any]]
    runtime_lifecycle: Callable[[str], Dict[str, Any]]
    suggestion_overview_payload: Callable[[], Dict[str, Any]]
    governance_orchestration: GovernanceOrchestrationService
    lifecycle_evolution: LifecycleEvolutionService
    web_lifecycle: WebLifecycleOrchestrationService
    deliver_runtime_governance_promotion: Callable[..., Dict[str, Any]]

    def assemble(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        detail = self.execution_detail(execution_id, limit=limit)
        data = detail.get("data", {}) if isinstance(detail, dict) else {}
        state = data.get("state", {}) if isinstance(data, dict) else {}
        trace = data.get("trace", {}) if isinstance(data, dict) else {}
        trace_payload = trace.get("data", trace) if isinstance(trace, dict) else {}
        lifecycle = trace_payload.get("lifecycle", {}) if isinstance(trace_payload, dict) else {}
        diagnostics = trace_payload.get("diagnostics", {}) if isinstance(trace_payload, dict) else {}
        runtime = self.runtime_lifecycle(str(state.get("execution_id") or execution_id))
        suggestions = self.suggestion_overview_payload()
        governance = asyncio.run(
            self.governance_orchestration.summary(execution_id=execution_id, limit=limit)
        )
        suggestion_data = suggestions.get("data", {}) if isinstance(suggestions, dict) else {}
        promotion_overview = {
            "ready": int(suggestion_data.get("promotion_ready", 0) or 0),
            "blocked": int(suggestion_data.get("promotion_blocked", 0) or 0),
            "reasons": dict(suggestion_data.get("promotion_reasons", {}) or {}),
        }
        repair = trace_payload.get("repair", {}) if isinstance(trace_payload, dict) else {}
        health = {
            "is_healthy": bool(lifecycle.get("is_healthy", True)) if isinstance(lifecycle, dict) else True,
            "event_count": diagnostics.get("event_count", 0) if isinstance(diagnostics, dict) else 0,
            "failure_count": diagnostics.get("failure_count", 0) if isinstance(diagnostics, dict) else 0,
            "repair_ready": bool(diagnostics.get("repair_ready", False)) if isinstance(diagnostics, dict) else False,
        }
        stage = (
            str(lifecycle.get("stage") or state.get("metadata", {}).get("stage") or "observing")
            if isinstance(lifecycle, dict)
            else "observing"
        )
        status = (
            str(lifecycle.get("status") or state.get("status") or "unknown")
            if isinstance(lifecycle, dict)
            else "unknown"
        )
        closure_score = float(health["event_count"] > 0 and 100.0 or 0.0)
        runtime_contract = runtime.get("data", {}) if isinstance(runtime, dict) else {}
        runtime_contract = {
            **runtime_contract,
            "verified": bool(runtime_contract.get("verified", False)),
            "healthy": bool(runtime_contract.get("healthy", False)),
            "ready": bool(runtime_contract.get("ready", False)),
            "deploy_ready": bool(runtime_contract.get("deploy_ready", False)),
        }
        governance_contract = governance.get("data", {}) if isinstance(governance, dict) else {}
        suggestion_contract = suggestion_data
        delivery_bundle = self.deliver_runtime_governance_promotion(
            execution_id,
            project_path=self.project_path,
            suggestion=suggestion_contract,
            governance=governance_contract,
        )
        delivery_contract = (
            delivery_bundle.get("data", {}).get("lifecycle_contract", {})
            if isinstance(delivery_bundle, dict)
            else {}
        )
        completion_score = 0.0
        completion_score += 20.0 if state else 0.0
        completion_score += 20.0 if health["event_count"] > 0 else 0.0
        completion_score += 20.0 if runtime_contract else 0.0
        completion_score += 15.0 if governance_contract else 0.0
        completion_score += 15.0 if suggestion_contract else 0.0
        completion_score += 10.0 if promotion_overview.get("ready", 0) else 0.0
        completion_score += 10.0 if repair.get("ready", False) else 0.0
        repair = {
            "ready": bool(diagnostics.get("repair_ready", False)) if isinstance(diagnostics, dict) else False,
            "candidate_count": int(diagnostics.get("repair_candidate_count", 0) if isinstance(diagnostics, dict) else 0),
            "root_causes": list(diagnostics.get("root_cause_tags", []) or []) if isinstance(diagnostics, dict) else [],
        }
        runtime_contract = {
            **runtime_contract,
            "healthy": bool(runtime_contract.get("healthy", False)),
            "verified": bool(runtime_contract.get("verified", False)),
        }
        promotion_eval = self.lifecycle_evolution.evaluate_promotion(
            {
                "execution_id": execution_id,
                "trace": trace_payload,
                "diagnostics": diagnostics,
                "runtime": runtime_contract,
                "governance": governance_contract,
                "suggestion": suggestion_contract,
                "repair": repair,
                "health": health,
                "completion_score": completion_score,
            },
            runtime=runtime_contract,
            governance=governance_contract,
        ).get("data", {})
        normalized_request = self.web_lifecycle.normalize_lifecycle_request(
            execution_id=str(state.get("execution_id") or execution_id),
            task_id=str(
                state.get("metadata", {}).get("task_id") or state.get("execution_id") or execution_id
            ),
            project_path=self.project_path,
            source=str(state.get("metadata", {}).get("source") or "observability"),
            task_type=str(state.get("metadata", {}).get("task_type") or "project_optimization"),
            intent=str(state.get("metadata", {}).get("intent") or state.get("execution_id") or execution_id),
            metadata=dict(state.get("metadata") or {}),
            suggestion_id=str(state.get("metadata", {}).get("suggestion_id") or ""),
            evolution_id=str(state.get("metadata", {}).get("evolution_id") or ""),
        )
        normalized_request_payload = normalized_request.get("request", {})
        lifecycle_payload = {
            **(dict(lifecycle) if isinstance(lifecycle, dict) else {}),
            "stage": stage,
            "status": status,
            "closure_score": closure_score,
        }
        promotion_payload = promotion_eval.get("promotion", {})
        evaluation_payload = promotion_eval
        evidence_package = {
            "normalized_request": normalized_request_payload,
            "state": state,
            "trace": trace_payload,
            "diagnostics": diagnostics,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "delivery": delivery_contract,
            "repair": repair,
            "promotion": promotion_payload,
            "promotion_contract": evaluation_payload,
            "promotion_overview": promotion_overview,
        }
        final_snapshot = {
            "execution_id": execution_id,
            "stage": stage,
            "status": status,
            "normalized_request": normalized_request_payload,
            "lifecycle": lifecycle_payload,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "delivery": delivery_contract,
            "diagnostics": diagnostics,
            "trace": trace_payload,
            "repair": repair,
            "promotion": promotion_payload,
            "promotion_contract": evaluation_payload,
            "health": {**health, "closure_score": closure_score, "completion_score": completion_score},
            "validation_refs": {
                "final_snapshot": True,
                "promotion_input_final_snapshot": bool(evaluation_payload),
            },
        }
        contract = {
            "execution_id": execution_id,
            "normalized_request": normalized_request_payload,
            "state": state,
            "trace": trace_payload,
            "lifecycle": lifecycle_payload,
            "diagnostics": diagnostics,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "delivery": delivery_contract,
            "promotion": promotion_payload,
            "evaluation": evaluation_payload,
            "promotion_contract": evaluation_payload,
            "promotion_overview": promotion_overview,
            "health": {**health, "closure_score": closure_score, "completion_score": completion_score},
            "repair": repair,
            "completion_score": completion_score,
            "evidence_package": evidence_package,
            "final_snapshot": final_snapshot,
        }
        return {
            "success": bool(detail.get("success", False)) if isinstance(detail, dict) else False,
            "data": contract,
        }


__all__ = ["LifecycleContractAssemblyService"]
