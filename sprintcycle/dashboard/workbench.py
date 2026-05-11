"""Dashboard workbench service.

V2 workbench composes a single platform-first workspace from the SprintCycle
facade and platform overview.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .view_service import DashboardViewService


@dataclass
class DashboardWorkbenchService:
    """Compatibility wrapper kept thin for dashboard routes."""

    view_service: DashboardViewService

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
        return self.view_service.execution_workspace(
            sprintcycle,
            execution_id=execution_id,
            limit=limit,
        )

    def platform_workspace(self, sprintcycle: Any) -> Dict[str, Any]:
        return self.view_service.platform_workspace(sprintcycle.platform_overview())


__all__ = ["DashboardWorkbenchService"]
