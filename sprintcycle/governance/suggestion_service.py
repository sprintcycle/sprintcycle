"""Suggestion application service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .suggestion.bridge import SuggestionBridge
from .suggestion.facade import SuggestionFacade
from .suggestion.models import (
    Suggestion,
    SuggestionApprovalRecord,
    SuggestionOverviewResult,
    SuggestionReviewContext,
    SuggestionReviewRecord,
    SuggestionStatus,
)
from .suggestion_analyzer import SuggestionAnalyzer


@dataclass
class SuggestionService:
    """Service wrapper that bridges observability analysis and suggestion storage."""

    facade: SuggestionFacade = field(default_factory=SuggestionFacade)
    analyzer: SuggestionAnalyzer = field(default_factory=SuggestionAnalyzer)
    bridge: Optional[SuggestionBridge] = None

    def create(self, suggestion: Suggestion) -> Suggestion:
        return self.facade.create(suggestion)

    def get(self, suggestion_id: str) -> Optional[Suggestion]:
        return self.facade.get(suggestion_id)

    def list(self, execution_id: Optional[str] = None) -> List[Suggestion]:
        return self.facade.list(execution_id)

    def review(self, record: SuggestionReviewRecord) -> SuggestionReviewRecord:
        return self.facade.review(record)

    def approve(self, record: SuggestionApprovalRecord) -> SuggestionApprovalRecord:
        return self.facade.approve(record)

    def overview(self, execution_id: Optional[str] = None) -> SuggestionOverviewResult:
        return self.facade.overview(execution_id)

    def analyze_events(self, execution_id: str, events: Iterable[Dict[str, Any]]) -> List[Suggestion]:
        suggestions = self.analyzer.analyze_events(execution_id, events)
        for suggestion in suggestions:
            self.create(suggestion)
        return suggestions

    def analyze_and_overview(self, execution_id: str, events: Iterable[Dict[str, Any]]) -> SuggestionOverviewResult:
        self.analyze_events(execution_id, events)
        return self.overview(execution_id)

    def mark_reviewing(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "", metadata: Optional[Dict[str, Any]] = None) -> SuggestionReviewRecord:
        record = SuggestionReviewRecord(
            suggestion_id=suggestion_id,
            reviewer=reviewer,
            decision=SuggestionStatus.REVIEWING.value,
            notes=notes,
            metadata={**(metadata or {}), "execution_id": execution_id},
        )
        return self.review(record)

    def mark_approved(self, execution_id: str, suggestion_id: str, approved_by: str = "", note: str = "", metadata: Optional[Dict[str, Any]] = None) -> SuggestionApprovalRecord:
        record = SuggestionApprovalRecord(
            suggestion_id=suggestion_id,
            approved_by=approved_by,
            note=note,
            metadata={**(metadata or {}), "execution_id": execution_id},
        )
        return self.approve(record)

    def reject(self, execution_id: str, suggestion_id: str, rejected_by: str = "", note: str = "", metadata: Optional[Dict[str, Any]] = None) -> SuggestionReviewRecord:
        record = SuggestionReviewRecord(
            suggestion_id=suggestion_id,
            reviewer=rejected_by,
            decision=SuggestionStatus.REJECTED.value,
            notes=note,
            metadata={**(metadata or {}), "execution_id": execution_id},
        )
        return self.review(record)

    def archive(self, execution_id: str, suggestion_id: str, note: str = "", metadata: Optional[Dict[str, Any]] = None) -> Optional[Suggestion]:
        suggestion = self.get(suggestion_id)
        if suggestion is None:
            return None
        suggestion.status = SuggestionStatus.CLOSED
        suggestion.metadata.update({**(metadata or {}), "execution_id": execution_id, "archive_note": note})
        return self.create(suggestion)

    def apply(self, execution_id: str, suggestion_id: str, note: str = "", metadata: Optional[Dict[str, Any]] = None) -> Optional[Suggestion]:
        suggestion = self.get(suggestion_id)
        if suggestion is None:
            return None
        suggestion.status = SuggestionStatus.APPLIED
        suggestion.metadata.update({**(metadata or {}), "execution_id": execution_id, "apply_note": note})
        return self.create(suggestion)

    def mark_reviewed(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "", metadata: Optional[Dict[str, Any]] = None) -> SuggestionReviewRecord:
        record = SuggestionReviewRecord(
            suggestion_id=suggestion_id,
            reviewer=reviewer,
            decision=SuggestionStatus.REVIEWING.value,
            notes=notes,
            metadata={**(metadata or {}), "execution_id": execution_id},
        )
        return self.review(record)

    async def promote_to_hitl(self, suggestion_id: str, *, gate: str = "review", title: str = "", summary: str = "", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.bridge is None:
            self.bridge = SuggestionBridge(self)
        return await self.bridge.promote_to_hitl(suggestion_id, gate=gate, title=title, summary=summary, context=context)

    async def attach_replay_directive(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        if self.bridge is None:
            self.bridge = SuggestionBridge(self)
        return await self.bridge.attach_replay_directive(suggestion_id, replay)


__all__ = ["SuggestionService"]
