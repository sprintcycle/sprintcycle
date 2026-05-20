"""Suggestion reviewer.

Builds context for human approval.
"""

from __future__ import annotations

from .models import SuggestionReviewContext
from .store import SuggestionStore


class SuggestionReviewer:
    def __init__(self, store: SuggestionStore) -> None:
        self._store = store

    async def build_review_context(self, suggestion_id: str) -> SuggestionReviewContext:
        suggestion = await self._store.get(suggestion_id)
        if suggestion is None:
            raise KeyError(f"suggestion not found: {suggestion_id}")
        risk_summary = f"severity={suggestion.severity}, scopes={','.join(suggestion.impact_scope or [])}"
        impact_summary = suggestion.summary or suggestion.details[:120]
        recommendation = "approve for promotion" if suggestion.severity in {"high", "critical"} else "review manually"
        return SuggestionReviewContext(
            suggestion=suggestion,
            related_evolution_id=suggestion.linked_evolution_id,
            related_version_id=suggestion.linked_version_id,
            risk_summary=risk_summary,
            impact_summary=impact_summary,
            recommendation=recommendation,
            metadata={"source_type": suggestion.source_type},
        )
