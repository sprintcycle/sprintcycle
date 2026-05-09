"""Suggestion governance module."""

from .facade import SuggestionFacade, create_suggestion_facade
from .models import (
    Suggestion,
    SuggestionApprovalRecord,
    SuggestionImpactScope,
    SuggestionOverviewResult,
    SuggestionReviewContext,
    SuggestionReviewRecord,
    SuggestionSeverity,
    SuggestionSourceType,
    SuggestionStatus,
)

__all__ = [
    "SuggestionFacade",
    "create_suggestion_facade",
    "Suggestion",
    "SuggestionApprovalRecord",
    "SuggestionImpactScope",
    "SuggestionOverviewResult",
    "SuggestionReviewContext",
    "SuggestionReviewRecord",
    "SuggestionSeverity",
    "SuggestionSourceType",
    "SuggestionStatus",
]
