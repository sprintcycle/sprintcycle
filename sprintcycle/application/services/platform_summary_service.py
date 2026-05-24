"""Platform summary application service.

Collects dashboard-facing platform/console/view payloads while leaving business
logic in the underlying facades and query services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ...domain.platform.overview import build_platform_overview_view
from ...domain.platform.spec import build_platform_spec
from ...infrastructure.persistence.state import summarize_state_machine
from ...infrastructure.persistence.state import get_state_store
from .dashboard_view_service import DashboardViewService
from .dashboard_workbench_service import DashboardWorkbenchService


@dataclass
class PlatformSummaryService:
    project_path: str
    dashboard_views: DashboardViewService
    dashboard_workbench: DashboardWorkbenchService

    def platform_overview(self) -> Dict[str, Any]:
        overview = build_platform_overview_view(self.project_path)
        data = overview.get("data", {}) if isinstance(overview, dict) else {}
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        lifecycle = data.get("lifecycle", {}) if isinstance(data, dict) else {}
        closure_score = float(summary.get("closure_score", 100.0)) if isinstance(summary, dict) else 100.0
        data["closure_score"] = closure_score
        data["lifecycle"] = {
            **dict(lifecycle),
            "stage": lifecycle.get("stage", "normalized"),
            "status": "success" if overview.get("success", False) else "failed",
            "closure_score": closure_score,
        }
        data["delivery"] = {
            "ready": bool(summary.get("completion_rate", 0) or overview.get("success", False)),
            "artifact_count": int(summary.get("artifact_count", 0) or 0),
            "next_action": summary.get("next_action", ""),
        }
        data["runtime"] = {
            "linked": bool(summary.get("runtime_linked", False)),
            "deploy_ready": bool(summary.get("deploy_ready", False)),
            "runtime_id": summary.get("runtime_id", ""),
        }
        data["evolution"] = {
            "ready": bool(summary.get("evolution_ready", False)),
            "versioned": bool(summary.get("versioned", False)),
            "latest_version": summary.get("latest_version", ""),
            "source_suggestion_id": summary.get("source_suggestion_id", ""),
            "rollback_to": summary.get("rollback_to", ""),
        }
        data["health"] = {
            "closure_score": closure_score,
            "platform_ready": bool(overview.get("success", False)),
            "delivery_ready": bool(data["delivery"]["ready"]),
            "runtime_ready": bool(data["runtime"]["linked"]),
            "evolution_ready": bool(data["evolution"]["ready"]),
            "repair_ready": bool(summary.get("repair_ready", False)),
        }
        ready = int(summary.get("promotion_ready", 0) or 0)
        blocked = int(summary.get("promotion_blocked", 0) or 0)
        data["promotion"] = {
            "ready": ready,
            "blocked": blocked,
            "ready_rate": round((float(ready) / max(1.0, float(ready + blocked))) * 100, 2),
            "reasons": dict(summary.get("promotion_reasons", {}) or {}),
        }
        overview["data"] = data
        return overview

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
        delivery_ready = bool(success_count)
        runtime_ready = any(bool(item.get("metadata", {}).get("runtime_linkage")) for item in executions)
        evolution_ready = any(bool(item.get("metadata", {}).get("release_finalization")) for item in executions)
        lifecycle = {
            "total_executions": total,
            "running_executions": len(running),
            "latest_execution": latest.get("execution_id") if isinstance(latest, dict) else None,
            "closure_score": closure_score,
            "success_count": success_count,
            "failed_count": failed_count,
            "stage": "observing" if total else "normalized",
            "status": "success" if success_count or not total else "failed",
        }
        health = {
            "has_running": bool(running),
            "recent_event_count": len(recent_events),
            "execution_coverage": total,
            "closure_score": closure_score,
            "delivery_ready": delivery_ready,
            "runtime_ready": runtime_ready,
            "evolution_ready": evolution_ready,
        }
        return {
            "success": True,
            "data": {
                "executions": executions,
                "running_executions": running,
                "primary_execution": latest,
                "recent_events": recent_events,
                "platform": build_platform_spec(self.project_path).to_dict(),
                "state_machine": summarize_state_machine(),
                "lifecycle": lifecycle,
                "health": health,
                "closure_score": closure_score,
                "delivery": {
                    "ready": delivery_ready,
                    "artifact_count": success_count,
                    "next_action": "review" if delivery_ready else "execute",
                },
                "runtime": {
                    "linked": runtime_ready,
                    "deploy_ready": runtime_ready,
                    "runtime_id": latest.get("execution_id") if isinstance(latest, dict) else "",
                },
                "evolution": {"ready": evolution_ready, "versioned": evolution_ready, "latest_version": ""},
            },
        }

    def execution_detail(
        self, execution_id: str, state: Any, trace: Dict[str, Any], limit: int = 200
    ) -> Dict[str, Any]:
        lifecycle = trace.get("data", {}).get("lifecycle", {}) if isinstance(trace, dict) else {}
        diagnostics = trace.get("data", {}).get("diagnostics", {}) if isinstance(trace, dict) else {}
        return {
            "success": True,
            "data": {
                "state": state.to_dict(),
                "trace": trace,
                "platform": self.platform_overview().get("data", {}),
                "state_machine": summarize_state_machine(),
                "lifecycle": lifecycle,
                "diagnostics": diagnostics,
                "limit": limit,
            },
        }


__all__ = ["PlatformSummaryService"]
