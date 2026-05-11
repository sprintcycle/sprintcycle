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
from ..hooks import EXECUTION_STARTED_EVENT, EXECUTION_START_FAILED_EVENT, HookContext, HookPhase, HookRegistry, HookRunner
from ..observability.facade import ObservabilityFacade


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
            metadata={**dict(context.metadata), **dict(metadata or {}), "task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, "stage": context.stage, "step": context.step},
        )

    async def start_execution_run(self, task_id: str, *, suggestion_id: str = "", evolution_id: str = "", metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        context = self._execution_engine.create_context(
            run_id=kwargs.get("run_id") or task_id,
            task_id=task_id,
            project_path=self.project_path,
            suggestion_id=str(suggestion_id or kwargs.get("suggestion_id") or ""),
            evolution_id=str(evolution_id or kwargs.get("evolution_id") or ""),
            stage=str(kwargs.get("stage") or "normalized"),
            step=str(kwargs.get("step") or ""),
            metadata=dict(metadata or kwargs.get("metadata") or {}),
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
            return {"success": False, "error": result.message if result and result.message else "blocked by before_execution_start", "hook": [r.to_dict() for r in before_results]}
        gate = self._gate_pre_run(context)
        if not gate.allowed:
            state = self._state_from_context(context, status="failed", error=gate.reason, metadata={"stage": "pre_run_gate", "failure_kind": "policy_gate"})
            get_state_store().save(state)
            self._hooks.failed(hook_domain, hook_action_name, hook_ctx)
            return {"success": False, "error": gate.reason, "gate": gate.__dict__, "lifecycle_state": state.to_dict(), "lifecycle_stage": "pre_run_gate", "failure_kind": "policy_gate", "failure_reason": gate.reason, "hook": [r.to_dict() for r in before_results]}
        try:
            planned = self._state_from_context(context, status="running", metadata={"stage": "planned"})
            get_state_store().save(planned)
            started = self._execution_engine.basic_flow(context)
            event = {"kind": EXECUTION_STARTED_EVENT, "run_id": context.run_id, "task_id": context.task_id, "data": started}
            self.observability.record(event)
            self._hooks.event("execution", "start", EXECUTION_STARTED_EVENT, {"context": context.to_dict(), "execution": started})
            self.runtime_registry.register(
                {
                    "runtime_id": context.run_id,
                    "project_name": kwargs.get("project_name") or context.task_id,
                    "status": started.get("status") or context.status,
                    "port": kwargs.get("port") or 3000,
                    "url": kwargs.get("url") or "http://localhost:3000",
                    "metadata": {"task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, **dict(context.metadata)},
                }
            )
            self.runtime_registry.update(
                context.run_id,
                status=started.get("status") or context.status,
                metadata={"task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, **dict(context.metadata)},
            )
            completed = self._state_from_context(context, status=str(started.get("status") or "running"), metadata={"stage": "delivering", "execution": started})
            get_state_store().save(completed)
            self._hooks.after(hook_domain, hook_action_name, hook_ctx)
            delivery = {"execution": started, "context": context.to_dict(), "runtime_linkage": self.runtime_registry.latest()}
            return {"success": True, "data": delivery, "gate": gate.__dict__, "lifecycle_state": completed.to_dict(), "lifecycle_stage": "delivering", "failure_kind": "", "failure_reason": "", "hook": [r.to_dict() for r in before_results]}
        except Exception as exc:
            logger.exception("failed_execution_start run_id={}", context.run_id)
            failed_state = self._state_from_context(context, status="failed", error=str(exc), metadata={"stage": "execution", "failure_kind": "runtime_error"})
            get_state_store().save(failed_state)
            self._hooks.failed(hook_domain, hook_action_name, hook_ctx)
            self._hooks.event("execution", "start", EXECUTION_START_FAILED_EVENT, {"context": context.to_dict(), "error": str(exc)})
            return {"success": False, "error": str(exc), "lifecycle_state": failed_state.to_dict(), "lifecycle_stage": "execution", "failure_kind": "runtime_error", "failure_reason": str(exc), "hook": [r.to_dict() for r in before_results]}

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
