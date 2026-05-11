"""Platform summary application service.

Collects dashboard-facing platform/console/view payloads while leaving business
logic in the underlying facades and query services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..dashboard.view_service import DashboardViewService
from ..dashboard.workbench import DashboardWorkbenchService
from ..execution.state import summarize_state_machine
from ..execution.state.state_store import get_state_store
from ..platform.overview import build_platform_overview_view
from ..platform.spec import build_platform_spec


@dataclass
class PlatformSummaryService:
    project_path: str
    dashboard_views: DashboardViewService
    dashboard_workbench: DashboardWorkbenchService

    def platform_overview(self) -> Dict[str, Any]:
        return build_platform_overview_view(self.project_path)

    def platform_spec(self) -> Dict[str, Any]:
        return {"success": True, "data": build_platform_spec(project_name=self.project_path).to_dict()}

    def fitness_payload(self, observability: Any, runtime_registry: Any, suggestion: Any) -> Dict[str, Any]:
        payload = self.dashboard_views.build_fitness_payload(observability, runtime_registry, suggestion)
        payload["lifecycle_health"] = {
            "observability_ready": bool(getattr(observability, "list_events", None)),
            "runtime_ready": bool(getattr(runtime_registry, "latest", None)),
            "suggestion_ready": bool(getattr(suggestion, "overview", None)),
        }
        return payload

    def fitness_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.dashboard_views.fitness_view(payload)

    def deploy_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.dashboard_views.deploy_view(payload)

    def governance_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.dashboard_views.governance_view(payload)

    def fix_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.dashboard_views.fix_view(payload)

    def console_overview(self, trace_payload: Dict[str, Any] | None = None, limit: int = 20) -> Dict[str, Any]:
        store = get_state_store()
        states = store.list_executions(limit=max(1, int(limit)))
        executions = [s.to_dict() for s in states]
        running = [s.to_dict() for s in states if str(s.status.value) == "running"]
        latest = executions[0] if executions else None
        recent_events = list((trace_payload or {}).get("events", []) or [])[:20] if trace_payload else []
        total = len(executions)
        success_count = sum(1 for item in executions if str(item.get("status") or "").lower() == "success")
        failed_count = sum(1 for item in executions if str(item.get("status") or "").lower() == "failed")
        closure_score = round((success_count / total) * 100, 2) if total else 0.0
        lifecycle = {"total_executions": total, "running_executions": len(running), "latest_execution": latest.get("execution_id") if isinstance(latest, dict) else None, "closure_score": closure_score, "success_count": success_count, "failed_count": failed_count}
        health = {"has_running": bool(running), "recent_event_count": len(recent_events), "execution_coverage": total, "closure_score": closure_score}
        return {"success": True, "data": {"executions": executions, "running_executions": running, "primary_execution": latest, "recent_events": recent_events, "platform": build_platform_spec(self.project_path).to_dict(), "state_machine": summarize_state_machine(), "lifecycle": lifecycle, "health": health, "closure_score": closure_score}}

    def execution_detail(self, execution_id: str, state: Any, trace: Dict[str, Any], limit: int = 200) -> Dict[str, Any]:
        lifecycle = trace.get("data", {}).get("lifecycle", {}) if isinstance(trace, dict) else {}
        diagnostics = trace.get("data", {}).get("diagnostics", {}) if isinstance(trace, dict) else {}
        return {"success": True, "data": {"state": state.to_dict(), "trace": trace, "platform": self.platform_overview().get("data", {}), "state_machine": summarize_state_machine(), "lifecycle": lifecycle, "diagnostics": diagnostics, "limit": limit}}


__all__ = ["PlatformSummaryService"]
