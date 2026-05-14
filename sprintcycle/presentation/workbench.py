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
        return self.view_service.suggestion_board(sprintcycle, execution_id=execution_id, limit=limit)

    async def hitl_queue(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return await self.view_service.hitl_queue(sprintcycle, execution_id=execution_id, limit=limit)

    async def suggestion_and_hitl_panel(self, sprintcycle: Any, execution_id: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        return await self.view_service.suggestion_and_hitl_panel(sprintcycle, execution_id=execution_id, limit=limit)

    def execution_workspace(self, sprintcycle: Any, execution_id: str, limit: int = 200) -> Dict[str, Any]:
        return self.view_service.execution_workspace(
            sprintcycle,
            execution_id=execution_id,
            limit=limit,
        )

    def platform_workspace(self, sprintcycle: Any) -> Dict[str, Any]:
        return self.view_service.platform_workspace(sprintcycle.platform_overview())


__all__ = ["DashboardWorkbenchService"]
