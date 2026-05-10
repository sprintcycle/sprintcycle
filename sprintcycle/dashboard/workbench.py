"""Dashboard workbench service.

V2 workbench composes a single platform-first workspace from the SprintCycle
facade and platform overview.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .service import DashboardQueryService


@dataclass
class DashboardWorkbenchService:
    """Compose dashboard payloads from the SprintCycle API."""

    query_service: DashboardQueryService = DashboardQueryService()

    def suggestion_board(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        payload = sprintcycle.suggestion_overview_dashboard()
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        if execution_id:
            suggestions = [s for s in data.get("suggestions", []) if str(s.get("execution_id", "")) == str(execution_id)]
            data["suggestions"] = suggestions
            data["execution_id"] = execution_id
            data["total"] = len(suggestions)
        data["suggestions"] = (data.get("suggestions", []) or [])[:limit]
        return {"success": True, "data": data}

    async def hitl_queue(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        payload = await sprintcycle.observability_pending(execution_id=execution_id)
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        requests = list(data or [])
        if limit >= 0:
            requests = requests[:limit]
        return {"success": True, "data": {"execution_id": execution_id or "", "requests": requests, "total": len(requests)}}

    async def suggestion_and_hitl_panel(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        suggestions = self.suggestion_board(sprintcycle, execution_id=execution_id, limit=limit)
        hitl = await self.hitl_queue(sprintcycle, execution_id=execution_id, limit=limit)
        return {
            "success": True,
            "data": {
                "execution_id": execution_id or "",
                "suggestions": suggestions.get("data", {}),
                "hitl": hitl.get("data", {}),
            },
        }

    def execution_workspace(self, sprintcycle: Any, execution_id: str, limit: int = 200) -> Dict[str, Any]:
        execution_detail = sprintcycle.execution_detail(execution_id, limit=limit)
        platform = sprintcycle.platform_overview()
        bundle = self.query_service.build_bundle(
            execution_id=execution_id,
            trace=execution_detail.get("data", {}).get("trace", {}),
            replay={},
            suggestions=sprintcycle.suggestion_overview_dashboard(),
            hitl={"requests": []},
            deployment=platform.get("data", {}).get("compose", {}),
            fitness=sprintcycle.fitness_view().get("data", {}),
        )
        return {
            "success": True,
            "data": {
                "execution_id": execution_id,
                "execution": execution_detail.get("data", execution_detail),
                "platform": platform.get("data", platform),
                "bundle": bundle.to_dict(),
            },
        }

    def platform_workspace(self, sprintcycle: Any) -> Dict[str, Any]:
        platform = sprintcycle.platform_overview()
        return {
            "success": True,
            "data": platform.get("data", platform),
        }


__all__ = ["DashboardWorkbenchService"]
