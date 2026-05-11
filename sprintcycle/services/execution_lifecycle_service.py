"""Execution lifecycle application service.

This service owns the execution start/detail/replay/read paths so the facade can
stay thin and only coordinate calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from ..deployment.runtime_registry import RuntimeRegistry
from ..execution.state.state_store import get_state_store
from ..execution_core import ExecutionContext, create_execution_engine
from ..governance.policy.gates import GateResult, pre_run_gate
from ..hooks import HookContext, HookPhase, HookRegistry
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

    def _gate_pre_run(self, context: ExecutionContext) -> GateResult:
        return pre_run_gate(
            run_id=context.run_id,
            task_id=context.task_id,
            project_path=context.project_path,
            suggestion_id=context.suggestion_id,
            evolution_id=context.evolution_id,
            metadata=context.metadata,
        )

    async def start_execution_run(self, task_id: str, *, suggestion_id: str = "", evolution_id: str = "", metadata: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        context = self._execution_engine.create_context(
            run_id=kwargs.get("run_id") or task_id,
            task_id=task_id,
            project_path=self.project_path,
            suggestion_id=str(suggestion_id or kwargs.get("suggestion_id") or ""),
            evolution_id=str(evolution_id or kwargs.get("evolution_id") or ""),
            stage=str(kwargs.get("stage") or "created"),
            step=str(kwargs.get("step") or ""),
            metadata=dict(metadata or kwargs.get("metadata") or {}),
        )
        hook_ctx = HookContext(
            domain="execution",
            action="start",
            subject_id=task_id,
            execution_id=context.run_id,
            project_path=self.project_path,
            payload=context.to_dict(),
            metadata=dict(context.metadata),
        )
        if self.hooks is not None:
            for result in self.hooks.emit(domain="execution", action="start", phase=HookPhase.BEFORE, context=hook_ctx):
                if result.blocked or not result.ok:
                    return {"success": False, "error": result.message or "blocked by before_execution_start", "hook": result.to_dict()}
        gate = self._gate_pre_run(context)
        if not gate.allowed:
            return {"success": False, "error": gate.reason, "gate": gate.__dict__}
        started = self._execution_engine.basic_flow(context)
        event = {"kind": "execution.started", "run_id": context.run_id, "task_id": context.task_id, "data": started}
        self.observability.record(event)
        if self.hooks is not None:
            self.hooks.emit_domain_event("execution.started", {"context": context.to_dict(), "execution": started})
            self.hooks.emit(domain="execution", action="start", phase=HookPhase.AFTER, context=hook_ctx)
        try:
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
        except Exception:
            logger.exception("failed_to_register_runtime run_id={}", context.run_id)
            if self.hooks is not None:
                self.hooks.emit(domain="execution", action="start", phase=HookPhase.FAILED, context=hook_ctx)
        try:
            self.runtime_registry.update(
                context.run_id,
                status=started.get("status") or context.status,
                metadata={"task_id": context.task_id, "suggestion_id": context.suggestion_id, "evolution_id": context.evolution_id, **dict(context.metadata)},
            )
        except Exception:
            logger.exception("failed_to_update_runtime run_id={}", context.run_id)
            if self.hooks is not None:
                self.hooks.emit(domain="execution", action="start", phase=HookPhase.FAILED, context=hook_ctx)
        return {"success": True, "data": {"execution": started, "context": context.to_dict()}, "gate": gate.__dict__}

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
