"""Web lifecycle request normalization and phase orchestration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from .lifecycle_contracts import build_lifecycle_contract
from .phase_workflow import build_decompose_artifact, build_plan_artifact, build_prepare_artifact


@dataclass
class WebLifecycleOrchestrationService:
    project_path: str
    start_execution_run: Callable[..., Any]
    runtime_lifecycle: Callable[[str], Dict[str, Any]]
    observability_trace: Callable[[str], Dict[str, Any]]
    evaluate_sprint_contract: Callable[[Dict[str, Any]], Dict[str, Any]]

    def normalize_lifecycle_request(
        self,
        *,
        execution_id: str,
        task_id: str,
        project_path: Optional[str] = None,
        source: str = "web",
        task_type: str = "project_optimization",
        intent: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        suggestion_id: str = "",
        evolution_id: str = "",
    ) -> Dict[str, Any]:
        normalized_metadata = dict(metadata or {})
        normalized_metadata.update(
            {"source": source, "task_type": task_type, "intent": intent or task_id, "normalized": True}
        )
        normalized_request = {
            "execution_id": execution_id,
            "task_id": task_id,
            "project_path": project_path or self.project_path,
            "source": source,
            "task_type": task_type,
            "intent": intent or task_id,
            "suggestion_id": suggestion_id,
            "evolution_id": evolution_id,
            "metadata": normalized_metadata,
        }
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            stage="normalized",
            status="pending",
            metadata=normalized_metadata,
            evidence={"contract": {"normalized": True}, "stages": {"normalized": {"normalized": True}}},
            input_refs={"execution_id": execution_id, "task_id": task_id, "intent": intent or task_id},
            validation_refs={"normalized": True},
        )
        return {"request": normalized_request, "contract": contract.to_dict()}

    def coerce_execution_contract(self, execution_contract: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self.normalize_lifecycle_request(
            execution_id=str(execution_contract.get("execution_id") or execution_contract.get("task_id") or ""),
            task_id=str(execution_contract.get("task_id") or execution_contract.get("execution_id") or ""),
            project_path=str(execution_contract.get("project_path") or self.project_path),
            source=str(
                execution_contract.get("source") or execution_contract.get("metadata", {}).get("source") or "web"
            ),
            task_type=str(
                execution_contract.get("task_type")
                or execution_contract.get("metadata", {}).get("task_type")
                or "project_optimization"
            ),
            intent=str(execution_contract.get("intent") or execution_contract.get("metadata", {}).get("intent") or ""),
            metadata=dict(execution_contract.get("metadata") or {}),
            suggestion_id=str(
                execution_contract.get("suggestion_id")
                or execution_contract.get("metadata", {}).get("suggestion_id")
                or ""
            ),
            evolution_id=str(
                execution_contract.get("evolution_id")
                or execution_contract.get("metadata", {}).get("evolution_id")
                or ""
            ),
        )
        normalized_contract = dict(normalized.get("contract") or {})
        contract = {
            "execution_id": str(
                normalized_contract.get("execution_id")
                or execution_contract.get("execution_id")
                or execution_contract.get("task_id")
                or ""
            ),
            "task_id": str(
                normalized_contract.get("task_id")
                or execution_contract.get("task_id")
                or execution_contract.get("execution_id")
                or ""
            ),
            "project_path": str(normalized_contract.get("project_path") or self.project_path),
            "stage": str(normalized_contract.get("stage") or "normalized"),
            "status": str(normalized_contract.get("status") or "pending"),
            "metadata": dict(normalized_contract.get("metadata") or {}),
            "input_refs": dict(execution_contract.get("input_refs") or {}),
            "output_refs": dict(execution_contract.get("output_refs") or {}),
            "validation_refs": dict(execution_contract.get("validation_refs") or {}),
            "trace": dict(execution_contract.get("trace") or {}),
            "diagnostics": dict(execution_contract.get("diagnostics") or {}),
            "recovery_refs": dict(execution_contract.get("recovery_refs") or {}),
            "governance_refs": dict(execution_contract.get("governance_refs") or {}),
            "evolution_refs": dict(execution_contract.get("evolution_refs") or {}),
            "evidence": dict(execution_contract.get("evidence") or {"contract": {}, "stages": {}}),
        }
        contract["validation_refs"]["normalized"] = bool(normalized_contract)
        contract["validation_refs"]["has_identity"] = bool(
            contract["execution_id"] and contract["task_id"] and contract["project_path"]
        )
        contract["evidence"].setdefault("contract", {})["normalized"] = True
        contract["evidence"].setdefault("stages", {}).setdefault("normalized", {})["normalized"] = True
        for stage in (
            "plan",
            "prepare",
            "decompose",
            "execute",
            "observe",
            "diagnose",
            "repair",
            "verify",
            "deliver",
        ):
            contract["evidence"].setdefault("stages", {}).setdefault(stage, {})
        for key in ("runtime", "governance", "promotion", "evolution", "recovery"):
            contract["evidence"].setdefault(key, {})
        return contract

    def plan_task_artifact(
        self,
        execution_id: str,
        task_id: str,
        *,
        objective: str = "",
        success_criteria: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        project_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            stage="normalized",
            status="pending",
            metadata={"source": "web", "phase": "plan"},
            evidence={"contract": {"normalized": True}, "stages": {"normalized": {"normalized": True}}},
            input_refs={"execution_id": execution_id, "task_id": task_id, "objective": objective},
            validation_refs={"normalized": True},
        )
        return build_plan_artifact(
            contract,
            objective=objective,
            success_criteria=success_criteria,
            risks=risks,
            dependencies=dependencies,
        )

    def bridge_execution_run(
        self,
        contract: Dict[str, Any],
        *,
        metadata: Optional[Dict[str, Any]] = None,
        suggestion_id: str = "",
        evolution_id: str = "",
        objective: str = "",
        success_criteria: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        execution_metadata = dict(metadata or {})
        if objective:
            execution_metadata.setdefault("objective", objective)
        if success_criteria:
            execution_metadata.setdefault("success_criteria", list(success_criteria))
        if risks:
            execution_metadata.setdefault("risks", list(risks))
        if dependencies:
            execution_metadata.setdefault("dependencies", list(dependencies))
        execution_id = str(contract.get("execution_id") or contract.get("task_id") or "")
        execution_result = asyncio.run(
            self.start_execution_run(
                str(contract.get("task_id") or execution_id),
                run_id=execution_id,
                suggestion_id=suggestion_id,
                evolution_id=evolution_id,
                metadata={**dict(contract.get("metadata") or {}), **execution_metadata},
                stage=str(contract.get("stage") or "normalized"),
                project_name=str(contract.get("project_path") or self.project_path),
            )
        )
        runtime_linkage = self.runtime_lifecycle(execution_id)
        observability = self.observability_trace(execution_id)
        return {
            "execution": execution_result,
            "runtime": runtime_linkage.get("data", {}).get("runtime", {}) if isinstance(runtime_linkage, dict) else {},
            "runtime_lifecycle": runtime_linkage.get("data", {}) if isinstance(runtime_linkage, dict) else {},
            "observability": observability.get("data", {}) if isinstance(observability, dict) else {},
        }

    def orchestrate_web_request(
        self,
        *,
        execution_id: str,
        task_id: str,
        project_path: Optional[str] = None,
        source: str = "web",
        task_type: str = "project_optimization",
        intent: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        objective: str = "",
        success_criteria: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        checks: Optional[Dict[str, Any]] = None,
        blockers: Optional[List[str]] = None,
        subtasks: Optional[List[Dict[str, Any]]] = None,
        suggestion_id: str = "",
        evolution_id: str = "",
        execute: bool = False,
    ) -> Dict[str, Any]:
        normalized = self.normalize_lifecycle_request(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path,
            source=source,
            task_type=task_type,
            intent=intent,
            metadata=metadata,
            suggestion_id=suggestion_id,
            evolution_id=evolution_id,
        )
        contract = self.coerce_execution_contract(normalized["contract"])
        plan_result = self.plan_task_artifact(
            contract["execution_id"],
            contract["task_id"],
            objective=objective,
            success_criteria=success_criteria,
            risks=risks,
            dependencies=dependencies,
            project_path=contract["project_path"],
        )
        prepared_result = build_prepare_artifact(
            plan_result.get("lifecycle_contract", contract), checks=checks, blockers=blockers
        )
        decomposed_result = build_decompose_artifact(
            prepared_result.get("lifecycle_contract", contract), subtasks=subtasks
        )
        execution_bundle = (
            self.bridge_execution_run(
                decomposed_result.get("lifecycle_contract", contract),
                metadata=metadata,
                suggestion_id=suggestion_id,
                evolution_id=evolution_id,
                objective=objective,
                success_criteria=success_criteria,
                risks=risks,
                dependencies=dependencies,
            )
            if execute
            else {}
        )
        lifecycle_contract = decomposed_result.get("lifecycle_contract", contract)
        if execution_bundle:
            lifecycle_contract = {
                **lifecycle_contract,
                "execution_refs": {
                    **dict(lifecycle_contract.get("execution_refs") or {}),
                    "execution": execution_bundle.get("execution", {}),
                },
                "runtime_refs": {
                    **dict(lifecycle_contract.get("runtime_refs") or {}),
                    "runtime": execution_bundle.get("runtime", {}),
                    "runtime_lifecycle": execution_bundle.get("runtime_lifecycle", {}),
                },
                "observation_refs": {
                    **dict(lifecycle_contract.get("observation_refs") or {}),
                    "observability": execution_bundle.get("observability", {}),
                },
                "recovery_refs": {
                    **dict(lifecycle_contract.get("recovery_refs") or {}),
                    "closed_loop": bool(execution_bundle.get("runtime_lifecycle")),
                    "repair_ready": bool(execution_bundle.get("observability")),
                },
                "evolution_refs": {
                    **dict(lifecycle_contract.get("evolution_refs") or {}),
                    "source_execution_id": execution_id,
                },
            }
        lifecycle_contract = {
            **lifecycle_contract,
            "stage": "observing" if execution_bundle else str(lifecycle_contract.get("stage") or "decomposed"),
            "status": "success" if execution_bundle else str(lifecycle_contract.get("status") or "pending"),
            "validation_refs": {
                **dict(lifecycle_contract.get("validation_refs") or {}),
                "normalized": True,
                "plan_present": bool(plan_result),
                "prepare_present": bool(prepared_result),
                "decompose_present": bool(decomposed_result),
                "execution_present": bool(execution_bundle),
                "final_snapshot": True,
            },
            "evidence": {
                **dict(lifecycle_contract.get("evidence") or {}),
                "contract": {
                    **dict((lifecycle_contract.get("evidence") or {}).get("contract") or {}),
                    "normalized": True,
                },
            },
        }
        review = self.evaluate_sprint_contract(
            {"contract": lifecycle_contract, "evidence": lifecycle_contract.get("evidence", {})}
        )
        lifecycle_contract["evaluation_refs"] = review.get("data", {})
        lifecycle_contract["validation_refs"] = {
            **dict(lifecycle_contract.get("validation_refs") or {}),
            "evaluator_reviewed": True,
            "evaluator_passed": bool(review.get("data", {}).get("score_card", {}).get("passed", False)),
        }
        lifecycle_contract["evidence"] = {
            **dict(lifecycle_contract.get("evidence") or {}),
            "promotion": {
                **dict((lifecycle_contract.get("evidence") or {}).get("promotion") or {}),
                "evaluation": review.get("data", {}),
            },
        }
        return {
            "success": True,
            "data": {
                "normalized_request": normalized["request"],
                "lifecycle_contract": lifecycle_contract,
                "evaluation": review.get("data", {}),
                "final_snapshot": lifecycle_contract,
                "plan": plan_result.get("plan", {}),
                "prepare": prepared_result.get("prepare", {}),
                "decompose": decomposed_result.get("decompose", {}),
                "execution": execution_bundle,
            },
        }

    def plan_task(
        self,
        execution_contract: Dict[str, Any],
        *,
        objective: str = "",
        success_criteria: Optional[List[str]] = None,
        risks: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None,
        version: str = "v1",
    ) -> Dict[str, Any]:
        contract_payload = self.coerce_execution_contract(execution_contract)
        contract = build_lifecycle_contract(
            execution_id=contract_payload["execution_id"],
            task_id=contract_payload["task_id"],
            project_path=contract_payload["project_path"],
            stage=contract_payload["stage"],
            status=contract_payload["status"],
            metadata=contract_payload["metadata"],
            input_refs=contract_payload["input_refs"],
            output_refs=contract_payload["output_refs"],
            validation_refs=contract_payload["validation_refs"],
            trace=contract_payload["trace"],
            diagnostics=contract_payload["diagnostics"],
        )
        return build_plan_artifact(
            contract,
            objective=objective,
            success_criteria=success_criteria,
            risks=risks,
            dependencies=dependencies,
            version=version,
        )

    def prepare_task(
        self,
        contract_payload: Dict[str, Any],
        *,
        checks: Optional[Dict[str, Any]] = None,
        blockers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return build_prepare_artifact(
            self.coerce_execution_contract(contract_payload), checks=checks, blockers=blockers
        )

    def decompose_task(
        self,
        contract_payload: Dict[str, Any],
        *,
        subtasks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return build_decompose_artifact(self.coerce_execution_contract(contract_payload), subtasks=subtasks)


__all__ = ["WebLifecycleOrchestrationService"]
