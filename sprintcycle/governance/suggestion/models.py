"""Suggestion governance models.

A suggestion is a governed, reviewable improvement proposal that may later
be promoted into an evolution request for SprintCycle itself.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional

SuggestionStatus = Literal[
    "pending",
    "under_review",
    "approved",
    "rejected",
    "promoted",
    "archived",
]

SuggestionSourceType = Literal[
    "requirement_evolution",
    "observability",
    "governance_check",
    "manual",
    "replay_analysis",
    "dashboard_feedback",
]

SuggestionSeverity = Literal["low", "medium", "high", "critical"]
SuggestionImpactScope = Literal[
    "code",
    "governance",
    "execution",
    "release_plan",
    "observability",
    "rollback",
    "documentation",
]


@dataclass(slots=True)
class Suggestion:
    suggestion_id: str
    source_type: SuggestionSourceType
    source_id: Optional[str] = None
    title: str = ""
    summary: str = ""
    details: str = ""
    impact_scope: List[SuggestionImpactScope] = field(default_factory=list)
    severity: SuggestionSeverity = "medium"
    status: SuggestionStatus = "pending"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    approved_at: Optional[str] = None
    reviewer: Optional[str] = None
    review_notes: str = ""
    linked_evolution_id: Optional[str] = None
    linked_version_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SuggestionReviewRecord:
    suggestion_id: str
    reviewer: str
    status: Literal["under_review", "approved", "rejected", "needs_more_info"]
    notes: str = ""
    reviewed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SuggestionApprovalRecord:
    suggestion_id: str
    approved_by: str
    approved_at: Optional[str] = None
    promoted: bool = False
    evolution_request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SuggestionReviewContext:
    suggestion: Suggestion
    related_evolution_id: Optional[str] = None
    related_version_id: Optional[str] = None
    risk_summary: str = ""
    impact_summary: str = ""
    recommendation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["suggestion"] = self.suggestion.to_dict()
        return data


@dataclass(slots=True)
class SuggestionOverviewResult:
    success: bool
    error: Optional[str] = None
    pending_count: int = 0
    under_review_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    promoted_count: int = 0
    archived_count: int = 0
    recent_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    source_distribution: Dict[str, int] = field(default_factory=dict)
    severity_distribution: Dict[str, int] = field(default_factory=dict)
    impact_scope_distribution: Dict[str, int] = field(default_factory=dict)
    promotion_ready: int = 0
    promotion_blocked: int = 0
    promotion_reasons: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_dashboard_payload(self) -> Dict[str, Any]:
        return {
            "counts": {
                "pending": self.pending_count,
                "under_review": self.under_review_count,
                "approved": self.approved_count,
                "rejected": self.rejected_count,
                "promoted": self.promoted_count,
                "archived": self.archived_count,
            },
            "promotion": {
                "ready": self.promotion_ready,
                "blocked": self.promotion_blocked,
                "reasons": dict(self.promotion_reasons),
            },
            "recent_suggestions": list(self.recent_suggestions[:10]),
            "source_distribution": dict(self.source_distribution),
            "severity_distribution": dict(self.severity_distribution),
            "impact_scope_distribution": dict(self.impact_scope_distribution),
        }

    def to_cli_text(self) -> str:
        lines = ["Suggestion Overview"]
        lines.append(f"  pending: {self.pending_count}")
        lines.append(f"  under_review: {self.under_review_count}")
        lines.append(f"  approved: {self.approved_count}")
        lines.append(f"  rejected: {self.rejected_count}")
        lines.append(f"  promoted: {self.promoted_count}")
        lines.append(f"  archived: {self.archived_count}")
        return "\n".join(lines)
