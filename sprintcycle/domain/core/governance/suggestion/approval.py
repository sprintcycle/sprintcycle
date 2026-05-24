"""Suggestion approval helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from .models import SuggestionApprovalRecord, SuggestionReviewRecord
from sprintcycle.infrastructure.governance.suggestion_store import SuggestionStore


class SuggestionApprovalService:
    def __init__(self, store: SuggestionStore) -> None:
        self._store = store

    async def approve(self, suggestion_id: str, approver: str, notes: str = "") -> SuggestionApprovalRecord:
        suggestion = await self._store.update_status(suggestion_id, "approved")
        suggestion.approved_at = datetime.now(timezone.utc).isoformat()
        suggestion.reviewer = approver
        suggestion.review_notes = notes
        await self._store.save(suggestion)
        record = SuggestionApprovalRecord(
            suggestion_id=suggestion_id,
            approved_by=approver,
            approved_at=suggestion.approved_at,
            promoted=False,
            metadata={"notes": notes},
        )
        await self._store.append_approval(record)
        return record

    async def reject(self, suggestion_id: str, approver: str, notes: str = "") -> SuggestionReviewRecord:
        suggestion = await self._store.update_status(suggestion_id, "rejected")
        suggestion.reviewer = approver
        suggestion.review_notes = notes
        suggestion.reviewed_at = datetime.now(timezone.utc).isoformat()
        await self._store.save(suggestion)
        record = SuggestionReviewRecord(
            suggestion_id=suggestion_id,
            reviewer=approver,
            status="rejected",
            notes=notes,
            reviewed_at=suggestion.reviewed_at,
        )
        await self._store.append_review(record)
        return record

    async def archive(self, suggestion_id: str) -> None:
        await self._store.update_status(suggestion_id, "archived")
