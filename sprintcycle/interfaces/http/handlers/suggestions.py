"""Suggestions handler - API methods for suggestion management operations."""

from __future__ import annotations

from typing import Any, Optional

from .services import ServiceAggregator


class SuggestionsHandler:
    """Handler for suggestion-related API methods."""

    def __init__(self, services: ServiceAggregator):
        self._services = services

    async def suggestion_overview(self) -> Any:
        return await self._services.management_overview.suggestion_overview()

    async def management_overview(self) -> Any:
        return await self._services.management_overview.management_overview(self._services.project_path)

    def suggestion_board(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        from .execution import ExecutionHandler
        return self._services.dashboard_workbench.suggestion_board(ExecutionHandler(self._services), execution_id=execution_id, limit=limit)

    def suggestion_and_hitl_panel(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        from .execution import ExecutionHandler
        return self._services.dashboard_workbench.suggestion_and_hitl_panel(ExecutionHandler(self._services), execution_id=execution_id, limit=limit)

    def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Any:
        return self._services.suggestion_application.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Any:
        return self._services.suggestion_application.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)

    def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Any:
        return self._services.suggestion_application.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)

    def suggestion_archive(self, suggestion_id: str) -> Any:
        return self._services.suggestion.archive_suggestion(suggestion_id)
