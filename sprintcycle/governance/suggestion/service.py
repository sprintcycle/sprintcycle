"""Suggestion service orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional

from ...evolution.models import EvolutionRequest
from .approval import SuggestionApprovalService
from .classifier import SuggestionClassifier
from .models import (
    Suggestion,
    SuggestionOverviewResult,
    SuggestionReviewContext,
    SuggestionSourceType,
    SuggestionStatus,
)
from .reviewer import SuggestionReviewer
from .store import SuggestionStore


class SuggestionService:
    def __init__(self, store: SuggestionStore, *, evolution_facade: Any = None) -> None:
        self._store = store
        self._classifier = SuggestionClassifier()
        self._reviewer = SuggestionReviewer(store)
        self._approval = SuggestionApprovalService(store)
        self._evolution_facade = evolution_facade

    async def capture_suggestion(self, suggestion: Suggestion) -> Suggestion:
        now = datetime.now(timezone.utc).isoformat()
        suggestion.created_at = suggestion.created_at or now
        suggestion.updated_at = now
        suggestion = await self._classifier.classify(suggestion)
        return await self._store.save(suggestion)

    async def list_suggestions(
        self,
        status: Optional[SuggestionStatus] = None,
        source_type: Optional[SuggestionSourceType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Suggestion]:
        return await self._store.list(status=status, source_type=source_type, limit=limit, offset=offset)

    async def get_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
        return await self._store.get(suggestion_id)

    async def review_suggestion(self, suggestion_id: str) -> SuggestionReviewContext:
        suggestion = await self._store.update_status(suggestion_id, "under_review")
        await self._store.save(suggestion)
        return await self._reviewer.build_review_context(suggestion_id)

    async def approve_suggestion(self, suggestion_id: str, approver: str, notes: str = ""):
        record = await self._approval.approve(suggestion_id, approver, notes)
        try:
            suggestion = await self._store.get(suggestion_id)
            if suggestion is not None and suggestion.linked_evolution_id:
                await self._store.update_evolution_link(suggestion_id, suggestion.linked_evolution_id)
        except Exception:
            pass
        return record

    async def reject_suggestion(self, suggestion_id: str, approver: str, notes: str = ""):
        return await self._approval.reject(suggestion_id, approver, notes)

    async def archive_suggestion(self, suggestion_id: str) -> None:
        await self._approval.archive(suggestion_id)

    async def promote_suggestion(self, suggestion_id: str, project_path: str) -> EvolutionRequest:
        suggestion = await self._store.get(suggestion_id)
        if suggestion is None:
            raise KeyError(f"suggestion not found: {suggestion_id}")
        if suggestion.status != "approved":
            raise ValueError(f"suggestion {suggestion_id} is not approved")
        request = EvolutionRequest(
            request_id=f"evo_from_{suggestion.suggestion_id}",
            target="code",
            project_path=project_path,
            mode="multi_sprint",
            context={
                "suggestion_id": suggestion.suggestion_id,
                "source_type": suggestion.source_type,
                "title": suggestion.title,
                "summary": suggestion.summary,
                "details": suggestion.details,
                "impact_scope": suggestion.impact_scope,
                "severity": suggestion.severity,
                "review_notes": suggestion.review_notes,
                "metadata": suggestion.metadata,
            },
        )
        suggestion.status = "promoted"
        suggestion.linked_evolution_id = request.request_id
        suggestion.updated_at = datetime.now(timezone.utc).isoformat()
        await self._store.save(suggestion)
        return request

    async def overview(self) -> SuggestionOverviewResult:
        all_items = await self._store.list(limit=10000)
        counts = {s: 0 for s in ["pending", "under_review", "approved", "rejected", "promoted", "archived"]}
        source_distribution: dict[str, int] = {}
        severity_distribution: dict[str, int] = {}
        impact_scope_distribution: dict[str, int] = {}
        for item in all_items:
            counts[item.status] = counts.get(item.status, 0) + 1
            source_distribution[item.source_type] = source_distribution.get(item.source_type, 0) + 1
            severity_distribution[item.severity] = severity_distribution.get(item.severity, 0) + 1
            for scope in item.impact_scope:
                impact_scope_distribution[scope] = impact_scope_distribution.get(scope, 0) + 1
        recent = [s.to_dict() for s in all_items[:10]]
        return SuggestionOverviewResult(
            success=True,
            pending_count=counts["pending"],
            under_review_count=counts["under_review"],
            approved_count=counts["approved"],
            rejected_count=counts["rejected"],
            promoted_count=counts["promoted"],
            archived_count=counts["archived"],
            recent_suggestions=recent,
            source_distribution=source_distribution,
            severity_distribution=severity_distribution,
            impact_scope_distribution=impact_scope_distribution,
        )
