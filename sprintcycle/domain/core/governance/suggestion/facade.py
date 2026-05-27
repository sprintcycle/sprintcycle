"""Suggestion governance facade."""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING

from .models import (
    Suggestion,
    SuggestionOverviewResult,
    SuggestionReviewContext,
    SuggestionSourceType,
    SuggestionStatus,
)
from .service import SuggestionService

if TYPE_CHECKING:
    pass


class SuggestionFacade:
    def __init__(self, service: SuggestionService) -> None:
        self._service = service

    async def capture_suggestion(self, suggestion: Suggestion) -> Suggestion:
        return await self._service.capture_suggestion(suggestion)

    async def capture_from_execution_event(self, event: Any) -> dict[str, Any]:
        return await self._service.capture_from_execution_event(event)

    async def list_suggestions(
        self,
        status: Optional[SuggestionStatus] = None,
        source_type: Optional[SuggestionSourceType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Suggestion]:
        return await self._service.list_suggestions(status=status, source_type=source_type, limit=limit, offset=offset)

    async def get_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
        return await self._service.get_suggestion(suggestion_id)

    async def review_suggestion(self, suggestion_id: str) -> SuggestionReviewContext:
        return await self._service.review_suggestion(suggestion_id)

    async def approve_suggestion(self, suggestion_id: str, approver: str, notes: str = ""):
        return await self._service.approve_suggestion(suggestion_id, approver, notes)

    async def reject_suggestion(self, suggestion_id: str, approver: str, notes: str = ""):
        return await self._service.reject_suggestion(suggestion_id, approver, notes)

    async def archive_suggestion(self, suggestion_id: str) -> None:
        return await self._service.archive_suggestion(suggestion_id)

    async def promote_suggestion(self, suggestion_id: str, project_path: str):
        return await self._service.promote_suggestion(suggestion_id, project_path)

    async def overview(self) -> SuggestionOverviewResult:
        return await self._service.overview()


def create_suggestion_facade(project_path: str, config: Any, evolution_facade: Any = None) -> SuggestionFacade:
    from sprintcycle.domain.ports.suggestion import get_suggestion_store
    store_root = (
        getattr(getattr(config, "governance_suggestion", None), "root_dir", None)
        or ".sprintcycle/governance/suggestion"
    )
    service = SuggestionService(get_suggestion_store(store_root), evolution_facade=evolution_facade)
    return SuggestionFacade(service)
