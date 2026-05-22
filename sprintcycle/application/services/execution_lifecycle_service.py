"""Execution lifecycle helpers.

This service provides a minimal bridge between execution state, runtime linkage,
and dashboard-facing lifecycle snapshots.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sprintcycle.execution.state.state_store import get_state_store
from sprintcycle.hooks import EXECUTION_STARTED_EVENT, HookContext, HookPhase, HookRegistry, HookRunner
from sprintcycle.infrastructure.runtime_registry import RuntimeRegistry
from sprintcycle.infrastructure.observability.facade import ObservabilityFacade


class ExecutionLifecycleService:
    def __init__(
        self,
        project_path: str,
        config: Any,
        observability: ObservabilityFacade,
        runtime_registry: RuntimeRegistry,
        hooks: Optional[HookRegistry] = None,
    ):
        self.project_path = project_path
        self.config = config
        self.observability = observability
        self.runtime_registry = runtime_registry
        self.hooks = hooks or HookRegistry()
        self._hook_runner = HookRunner(self.hooks)

    async def start_execution_run(self, task_id: str, **kwargs: Any) -> Dict[str, Any]:
        runtime_id = str(kwargs.get("run_id") or task_id)
        metadata = dict(kwargs.get("metadata") or {})

        # Hook check before execution
        ctx = HookContext(
            domain="execution",
            action="start",
            subject_id=runtime_id,
            payload={"task_id": task_id, **{k: v for k, v in kwargs.items() if k != "metadata"}},
            metadata=metadata,
        )
        results = self._hook_runner.emit(domain="execution", action="start", phase=HookPhase.BEFORE, context=ctx)
        if any((not r.ok or r.blocked) for r in results):
            result = next((r for r in results if not r.ok or r.blocked), None)
            return {
                "success": False,
                "error": result.message if result and result.message else "blocked by hook",
                "hook": [r.to_dict() for r in results],
            }

        runtime_payload = {
            "runtime_id": runtime_id,
            "project_name": str(kwargs.get("project_name") or self.project_path),
            "status": "running",
            "url": str(kwargs.get("url") or ""),
            "suggestion_id": str(kwargs.get("suggestion_id") or ""),
            "evolution_id": str(kwargs.get("evolution_id") or ""),
            "deploy_ready": True,
            "healthy": True,
            "verified": True,
            "metadata": dict(kwargs.get("metadata") or {}),
        }
        self.runtime_registry.register(runtime_payload)
        state_store = get_state_store()
        try:
            state_store.update_execution_status(runtime_id, "running")
        except Exception:
            pass
        self.observability.record_event(
            {
                "type": "execution_start",
                "execution_id": runtime_id,
                "task_id": task_id,
                "status": "running",
                "metadata": metadata,
            }
        )

        # Emit AFTER hook on success
        self._hook_runner.emit(domain="execution", action="start", phase=HookPhase.AFTER, context=ctx)

        # Emit domain event
        self._hook_runner.event(
            "execution",
            "start",
            EXECUTION_STARTED_EVENT,
            {
                "execution_id": runtime_id,
                "task_id": task_id,
                "context": {"metadata": dict(ctx.metadata), "payload": dict(ctx.payload)},
            },
        )

        return {
            "success": True,
            "data": {
                "execution_id": runtime_id,
                "runtime": runtime_payload,
                "status": "running",
                "context": {"metadata": ctx.metadata, "payload": dict(ctx.payload)},
            },
        }

    def runtime_latest(self) -> Dict[str, Any]:
        payload = self.runtime_registry.records[-1] if self.runtime_registry.records else {}
        return {"success": True, "data": payload}

    def runtime_update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        current = self.runtime_registry.get(runtime_id)
        merged = {**current, **changes, "runtime_id": runtime_id}
        return self.runtime_registry.register(merged)

    def execution_detail(self, execution_id: str, limit: int = 200) -> Dict[str, Any]:
        state_store = get_state_store()
        state = state_store.get_execution(execution_id)
        trace = self.observability.trace(execution_id)
        return {
            "success": True,
            "data": {"state": state.to_dict() if hasattr(state, "to_dict") else state, "trace": trace, "limit": limit},
        }

    def execution_events(self, execution_id: str, limit: int = 200) -> Dict[str, Any]:
        return self.observability.trace(execution_id)

    def replay_execution(self, execution_id: str, limit: int = 500) -> Dict[str, Any]:
        trace = self.observability.replay(execution_id)
        return {
            "success": True,
            "data": trace.get("data", trace),
            "timeline": trace.get("data", {}).get("events", [])[:limit] if isinstance(trace, dict) else [],
        }
