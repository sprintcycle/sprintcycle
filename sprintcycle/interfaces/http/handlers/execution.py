"""Execution handler - API methods for execution operations."""

from __future__ import annotations

from typing import Any

from .services import ServiceAggregator


class ExecutionHandler:
    """Handler for execution-related API methods."""

    def __init__(self, services: ServiceAggregator):
        self._services = services

    def status(self, execution_id: str = "") -> Any:
        if execution_id:
            return self._services.execution_lifecycle.execution_detail(execution_id)
        return self._services.platform_summary.console_overview()

    def execution_detail(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.execution_lifecycle.execution_detail(execution_id, limit=limit)

    def execution_events(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.execution_lifecycle.execution_events(execution_id, limit=limit)

    def replay_execution(self, execution_id: str, limit: int = 500) -> Any:
        return self._services.execution_lifecycle.replay_execution(execution_id, limit=limit)

    def observability_trace(self, run_id: str) -> Any:
        return self._services.observability_service.trace(run_id)

    def observability_replay(self, run_id: str) -> Any:
        return self._services.observability_service.replay(run_id)

    def platform_overview(self) -> Any:
        return self._services.platform_summary.platform_overview()

    def console_overview(self, limit: int = 20) -> Any:
        return self._services.platform_summary.console_overview(limit=limit)

    def deploy_view(self) -> Any:
        return self._services.platform_summary.deploy_view({})

    def fitness_view(self) -> Any:
        payload = self._services.platform_summary.fitness_payload(
            observability=self._services.observability,
            runtime_registry=self._services.runtime_registry,
            suggestion=self._services.suggestion,
        )
        return self._services.platform_summary.fitness_view(payload)

    def governance_view(self) -> Any:
        return self._services.platform_summary.governance_view({})

    def execution_workspace(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.dashboard_views.execution_workspace(self, execution_id=execution_id, limit=limit)

    def dashboard_platform_workspace(self) -> Any:
        return self._services.dashboard_views.platform_workspace(self.platform_overview())

    def diagnose(self, execution_id: str = "") -> Any:
        from sprintcycle.domain.ports.diagnostics import get_diagnostic_adapter
        
        adapter = get_diagnostic_adapter()
        return adapter.diagnose(execution_id=execution_id)

    def stop_execution(self, execution_id: str = "") -> Any:
        from sprintcycle.domain.ports.state_store import get_state_store, ExecutionStatus
        from sprintcycle.application.dto.results import StopResult

        if execution_id:
            store = get_state_store()
            state = store.load(execution_id)
            if state is None:
                return StopResult(
                    success=False,
                    execution_id=execution_id,
                    cancelled=False,
                    error=f"Execution {execution_id} not found",
                    duration=0.0,
                ).to_dict()
            store.update_status(execution_id, ExecutionStatus.CANCELLED)
            return StopResult(
                success=True,
                execution_id=execution_id,
                cancelled=True,
                message="已标记为 CANCELLED",
                duration=0.1,
            ).to_dict()
        return StopResult(
            success=True,
            cancelled=True,
            duration=0.0,
        ).to_dict()

    def rollback(self, execution_id: str) -> Any:
        from sprintcycle.application.dto.results import RollbackResult
        from sprintcycle.domain.ports.state_store import get_state_store

        store = get_state_store()
        state = store.load(execution_id)
        if state is None:
            return RollbackResult(
                success=False,
                execution_id=execution_id,
                rollback_point="",
                error=f"Execution {execution_id} not found",
                duration=0.0,
            ).to_dict()
        rollback_point = getattr(state, "metadata", {}).get("pre_execution_commit", "")
        return RollbackResult(
            success=bool(rollback_point),
            execution_id=execution_id,
            rollback_point=rollback_point or "",
            duration=0.1,
        ).to_dict()
