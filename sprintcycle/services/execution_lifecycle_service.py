"""Execution lifecycle application service.

Owns execution start, detail, replay, and read flows, including pre-run gate
checks, hook callbacks, observability recording, runtime registry updates, and
structured lifecycle state handoff for the target-state execution chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from ..deployment.runtime_registry import RuntimeRegistry
from ..execution.state.state_store import ExecutionState, get_state_store
from ..execution_core import ExecutionContext, create_execution_engine
from ..governance.policy.gates import GateResult, pre_run_gate
from ..hooks import EXECUTION_STARTED_EVENT, EXECUTION_START_FAILED_EVENT, HookContext, HookRegistry, HookRunner
from ..observability.facade import ObservabilityFacade
from .lifecycle_contracts import build_lifecycle_contract, build_lifecycle_state_machine
from .phase_workflow import build_decompose_artifact, build_plan_artifact, build_prepare_artifact
from .repair_orchestration_service import RepairOrchestrationService


@dataclass
class ExecutionLifecycleService:
    project_path: str
    config: Any
    observability: ObservabilityFacade
    runtime_registry: RuntimeRegistry
    hooks: HookRegistry | None = None

    def __post_init__(self) -> None:
        self._execution_engine = create_execution_engine()
        self._hooks = HookRunner(self.hooks)
        self._repair = RepairOrchestrationService(self.observability)

    def _gate_pre_run(self, context: ExecutionContext) -> GateResult:
        return pre_run_gate(
            run_id=context.run_id,
            task_id=context.task_id,
            project_path=context.project_path,
            suggestion_id=context.suggestion_id,
            evolution_id=context.evolution_id,
            metadata=context.metadata,
        )

    def _state_from_context(self, context: ExecutionContext, *, status: str, error: str | None = None, metadata: Optional[Dict[str, Any]] = None) -> ExecutionState:
        stage = str((metadata or {}).get("stage") or context.stage or "normalized")
        lifecycle = build_lifecycle_state_machine()
        normalized_stage = lifecycle.normalize_stage(stage)
        return ExecutionState(
            execution_id=context.run_id,
            release_plan_name=str(context.metadata.get("release_plan_name") or context.task_id or context.run_id),
            mode=str(context.metadata.get("mode") or "normal"),
            status=status,
            current_sprint=int(context.metadata.get("current_sprint") or 0),
            total_sprints=int(context.metadata.get("total_sprints") or 0),
            completed_tasks=int(context.metadata.get("completed_tasks") or 0),
            total_tasks=int(context.metadata.get("total_tasks") or 0),
            error=error,
            metadata={**dict(context.metadata), **dict(metadata or {}), "task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, "stage": normalized_stage, "step": context.step},
        )

    def _persist_state_snapshot(self, state: ExecutionState, *, contract: Optional[Dict[str, Any]] = None, trace: Optional[Dict[str, Any]] = None, diagnostics: Optional[Dict[str, Any]] = None, runtime_linkage: Optional[Dict[str, Any]] = None, phase_plan: Optional[Dict[str, Any]] = None, phase_prepare: Optional[Dict[str, Any]] = None, phase_decompose: Optional[Dict[str, Any]] = None) -> None:
        payload = dict(state.metadata or {})
        if contract is not None:
            payload["lifecycle_contract"] = contract
        if trace is not None:
            payload["trace"] = trace
        if diagnostics is not None:
            payload["diagnostics"] = diagnostics
        if runtime_linkage is not None:
            payload["runtime_linkage"] = runtime_linkage
        if phase_plan is not None:
            payload["phase_plan"] = phase_plan
        if phase_prepare is not None:
            payload["phase_prepare"] = phase_prepare
        if phase_decompose is not None:
            payload["phase_decompose"] = phase_decompose
        state.metadata = payload
        get_state_store().save(state)

    async def start_execution_run(self, task_id: str, *, suggestion_id: str = "", evolution_id: str = "", metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        metadata = dict(metadata or kwargs.get("metadata") or {})
        lifecycle = build_lifecycle_state_machine()
        context = self._execution_engine.create_context(
            run_id=kwargs.get("run_id") or task_id,
            task_id=task_id,
            project_path=self.project_path,
            suggestion_id=str(suggestion_id or kwargs.get("suggestion_id") or ""),
            evolution_id=str(evolution_id or kwargs.get("evolution_id") or ""),
            stage=lifecycle.normalize_stage(kwargs.get("stage") or "normalized"),
            step=str(kwargs.get("step") or ""),
            metadata=metadata,
        )
        hook_domain, hook_action_name = self._hooks.action("execution", "start")
        hook_ctx = HookContext(
            domain=hook_domain,
            action=hook_action_name,
            subject_id=task_id,
            execution_id=context.run_id,
            project_path=self.project_path,
            payload=context.to_dict(),
            metadata=dict(context.metadata),
        )
        before_results = self._hooks.before(hook_domain, hook_action_name, hook_ctx)
        if any(r.blocked or not r.ok for r in before_results):
            result = next((r for r in before_results if r.blocked or not r.ok), None)
            contract = build_lifecycle_contract(
                execution_id=context.run_id,
                task_id=task_id,
                project_path=self.project_path,
                stage="normalized",
                status="failed",
                metadata=metadata,
                failure_kind="hook_blocked",
                failure_reason=result.message if result and result.message else "blocked by before_execution_start",
            )
            return {"success": False, "error": result.message if result and result.message else "blocked by before_execution_start", "lifecycle_contract": contract.to_dict(), "hook": [r.to_dict() for r in before_results]}
        prepared = self._state_from_context(context, status="running", metadata={"stage": "prepared"})
        self._persist_state_snapshot(prepared, phase_plan={"skipped": False})
        gate = self._gate_pre_run(context)
        if not gate.allowed:
            state = self._state_from_context(context, status="failed", error=gate.reason, metadata={"stage": "prepared", "failure_kind": "policy_gate"})
            get_state_store().save(state)
            self._hooks.failed(hook_domain, hook_action_name, hook_ctx)
            contract = build_lifecycle_contract(execution_id=context.run_id, task_id=task_id, project_path=self.project_path, stage="prepared", status="failed", metadata=metadata, failure_kind="policy_gate", failure_reason=gate.reason, repair_refs={"next_action": "revise_plan", "stage": "prepared"})
            contract = lifecycle.attach_correlation(contract.to_dict(), lifecycle.ensure_correlation({"request_id": kwargs.get("request_id", ""), "execution_id": context.run_id, "task_id": task_id, "suggestion_id": suggestion_id, "runtime_id": kwargs.get("runtime_id", ""), "source": "web", "metadata": metadata}))
            return {"success": False, "error": gate.reason, "gate": gate.__dict__, "lifecycle_state": state.to_dict(), "lifecycle_contract": contract, "lifecycle_stage": "prepared", "failure_kind": "policy_gate", "failure_reason": gate.reason, "hook": [r.to_dict() for r in before_results]}
        try:
            phase_plan = build_plan_artifact(
                build_lifecycle_contract(
                    execution_id=context.run_id,
                    task_id=task_id,
                    project_path=self.project_path,
                    stage="normalized",
                    status="pending",
                    metadata=metadata,
                    input_refs={"task_id": task_id, "suggestion_id": suggestion_id, "evolution_id": evolution_id},
                ),
                objective=str(metadata.get("objective") or task_id),
                success_criteria=list(metadata.get("success_criteria") or []),
                risks=list(metadata.get("risks") or []),
                dependencies=list(metadata.get("dependencies") or []),
            )
            planned = self._state_from_context(context, status="running", metadata={"stage": "planned", "phase_plan": phase_plan.get("plan", {})})
            self._persist_state_snapshot(planned, phase_plan=phase_plan.get("plan", {}))
            phase_prepare = build_prepare_artifact(phase_plan.get("lifecycle_contract", {}), checks={"project_path": bool(self.project_path), "task_id": bool(task_id)}, blockers=list(metadata.get("blockers") or []))
            prepared = self._state_from_context(context, status="running", metadata={"stage": "prepared", "phase_prepare": phase_prepare.get("prepare", {})})
            self._persist_state_snapshot(prepared, phase_plan=phase_plan.get("plan", {}), phase_prepare=phase_prepare.get("prepare", {}))
            phase_decompose = build_decompose_artifact(phase_prepare.get("lifecycle_contract", {}), subtasks=list(metadata.get("subtasks") or []))
            executing = self._state_from_context(context, status="running", metadata={"stage": "executing", "phase_decompose": phase_decompose.get("decompose", {})})
            self._persist_state_snapshot(executing, phase_plan=phase_plan.get("plan", {}), phase_prepare=phase_prepare.get("prepare", {}), phase_decompose=phase_decompose.get("decompose", {}))
            observing = self._state_from_context(context, status="running", metadata={"stage": "observing"})
            self._persist_state_snapshot(observing, phase_plan=phase_plan.get("plan", {}), phase_prepare=phase_prepare.get("prepare", {}), phase_decompose=phase_decompose.get("decompose", {}))
            started = self._execution_engine.basic_flow(context)
            event = {"kind": EXECUTION_STARTED_EVENT, "run_id": context.run_id, "task_id": context.task_id, "data": started}
            self.observability.record(event)
            self._hooks.event("execution", "start", EXECUTION_STARTED_EVENT, {"context": context.to_dict(), "execution": started})
            self.runtime_registry.register(
                {
                    "runtime_id": context.run_id,
                    "project_name": kwargs.get("project_name") or context.task_id,
                    "status": started.get("status") or context.status,
                    "ready": bool(started.get("status") or context.status),
                    "verified": False,
                    "healthy": False,
                    "deploy_ready": bool(started.get("status") or context.status),
                    "port": kwargs.get("port") or 3000,
                    "url": kwargs.get("url") or "http://localhost:3000",
                    "verification": {"verified": False, "healthy": False, "source": "execution_lifecycle"},
                    "metadata": {"task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, **dict(context.metadata)},
                }
            )
            runtime_linkage = self.runtime_registry.update(
                context.run_id,
                status=started.get("status") or context.status,
                ready=bool(started.get("status") or context.status),
                deploy_ready=bool(started.get("status") or context.status),
                verification={"verified": True, "healthy": bool(started.get("status") or context.status), "source": "execution_lifecycle"},
                metadata={"task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, **dict(context.metadata)},
            )
            observing = self._state_from_context(context, status=str(started.get("status") or "running"), metadata={"stage": "observing", "execution": started, "runtime_linkage": runtime_linkage})
            self._persist_state_snapshot(observing, phase_plan=phase_plan.get("plan", {}), phase_prepare=phase_prepare.get("prepare", {}), phase_decompose=phase_decompose.get("decompose", {}), runtime_linkage=runtime_linkage)
            contract = build_lifecycle_contract(
                execution_id=context.run_id,
                task_id=task_id,
                project_path=self.project_path,
                stage="delivering",
                status=str(started.get("status") or "running"),
                metadata={**metadata, "phase_plan": phase_plan.get("plan", {}), "phase_prepare": phase_prepare.get("prepare", {}), "phase_decompose": phase_decompose.get("decompose", {})},
                delivery_refs={"execution": started},
                runtime_refs=runtime_linkage,
                recovery_refs={"prepared": True, "planned": True, "executing": True, "observing": True},
                input_refs={"task_id": task_id, "suggestion_id": suggestion_id, "evolution_id": evolution_id},
                output_refs={"execution": started, "runtime_linkage": runtime_linkage},
                validation_refs={"started": bool(started), "phase_plan": bool(phase_plan), "phase_prepare": bool(phase_prepare), "phase_decompose": bool(phase_decompose)},
                transition_reason="execution started",
            )
            contract = lifecycle.attach_correlation(contract.to_dict(), lifecycle.ensure_correlation({"request_id": kwargs.get("request_id", ""), "execution_id": context.run_id, "task_id": task_id, "suggestion_id": suggestion_id, "runtime_id": kwargs.get("runtime_id", ""), "source": "web", "metadata": metadata}))
            delivery = {"execution": started, "context": context.to_dict(), "runtime_linkage": runtime_linkage, "lifecycle_contract": contract}
            self._hooks.after(hook_domain, hook_action_name, hook_ctx)
            return {"success": True, "data": delivery, "gate": gate.__dict__, "lifecycle_state": observing.to_dict(), "lifecycle_contract": contract, "lifecycle_stage": "delivering", "failure_kind": "", "failure_reason": "", "hook": [r.to_dict() for r in before_results]}
        except Exception as exc:
            logger.exception("failed_execution_start run_id={}", context.run_id)
            failed_state = self._state_from_context(context, status="failed", error=str(exc), metadata={"stage": "executing", "failure_kind": "runtime_error"})
            get_state_store().save(failed_state)
            diagnosis = self._repair.diagnose(context.run_id)
            repair_result = self._repair.repair_and_verify(context.run_id, repair_plan={"source": "execution_failure", "error": str(exc)}) if diagnosis.get("data", {}).get("repair_ready") else diagnosis
            self._hooks.failed(hook_domain, hook_action_name, hook_ctx)
            self._hooks.event("execution", "start", EXECUTION_START_FAILED_EVENT, {"context": context.to_dict(), "error": str(exc), "repair": repair_result})
            contract = build_lifecycle_contract(execution_id=context.run_id, task_id=task_id, project_path=self.project_path, stage="repairing" if diagnosis.get("data", {}).get("repair_ready") else "executing", status="failed", metadata=metadata, failure_kind="runtime_error", failure_reason=str(exc), repair_refs={"retriable": True, "stage": "executing", "diagnosis": diagnosis, "repair_result": repair_result})
            contract = lifecycle.attach_correlation(contract.to_dict(), lifecycle.ensure_correlation({"request_id": kwargs.get("request_id", ""), "execution_id": context.run_id, "task_id": task_id, "suggestion_id": suggestion_id, "runtime_id": kwargs.get("runtime_id", ""), "source": "web", "metadata": metadata}))
            return {"success": False, "error": str(exc), "repair": repair_result, "diagnosis": diagnosis, "lifecycle_state": failed_state.to_dict(), "lifecycle_contract": contract, "lifecycle_stage": contract.get("stage", "executing"), "failure_kind": "runtime_error", "failure_reason": str(exc), "hook": [r.to_dict() for r in before_results]}

    def execution_events(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        trace = self.observability.to_trace_payload(eid)
        return {"success": True, "data": list((trace or {}).get("events", []) or [])[:limit], "backend": "canonical"}

    def replay_execution(self, execution_id: str, *, limit: int = 500) -> Dict[str, Any]:
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        trace = self.observability.to_trace_payload(eid)
        events = list((trace or {}).get("events", []) or [])[:limit]
        return {"success": True, "data": {"execution_id": eid, "event_count": len(events), "latest_event": events[-1] if events else None}, "timeline": events}

    def execution_detail(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        store = get_state_store()
        state = store.load(eid)
        if state is None:
            return {"success": False, "error": f"未找到执行记录: {eid}"}
        trace = self.observability.to_trace_payload(eid)
        return {"success": True, "data": {"state": state.to_dict(), "trace": trace, "limit": limit}}

    def runtime_latest(self) -> Dict[str, Any]:
        return self.runtime_registry.latest()

    def runtime_update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        return self.runtime_registry.update(runtime_id, **changes)


__all__ = ["ExecutionLifecycleService"]
