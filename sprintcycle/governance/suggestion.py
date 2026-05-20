"""Suggestion domain for problem discovery and repair proposals."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SuggestionStatus(str, Enum):
    OPEN = "open"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    CLOSED = "closed"


class SuggestionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SuggestionSourceType(str, Enum):
    TEST = "test"
    RUNTIME = "runtime"
    REVIEW = "review"
    HITL = "hitl"
    EVALUATION = "evaluation"
    MANUAL = "manual"


class SuggestionImpactScope(str, Enum):
    TASK = "task"
    SPRINT = "sprint"
    EXECUTION = "execution"
    DEPLOYMENT = "deployment"
    PROJECT = "project"


@dataclass
class Suggestion:
    suggestion_id: str = field(default_factory=lambda: uuid4().hex)
    execution_id: str = ""
    title: str = ""
    summary: str = ""
    source_type: SuggestionSourceType = SuggestionSourceType.RUNTIME
    severity: SuggestionSeverity = SuggestionSeverity.MEDIUM
    impact_scope: SuggestionImpactScope = SuggestionImpactScope.TASK
    status: SuggestionStatus = SuggestionStatus.OPEN
    root_cause: str = ""
    proposed_action: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    hitl_request_id: str = ""
    replay_directive: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["source_type"] = self.source_type.value
        data["severity"] = self.severity.value
        data["impact_scope"] = self.impact_scope.value
        data["status"] = self.status.value
        return data


@dataclass
class SuggestionReviewContext:
    execution_id: str
    suggestion_id: str
    reviewer: str = ""
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SuggestionReviewRecord:
    suggestion_id: str
    reviewer: str
    decision: str
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuggestionApprovalRecord:
    suggestion_id: str
    approved_by: str
    note: str = ""
    applied: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuggestionOverviewResult:
    execution_id: str
    suggestions: List[Suggestion] = field(default_factory=list)
    total: int = 0
    open_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "suggestions": [item.to_dict() for item in self.suggestions],
            "total": self.total,
            "open_count": self.open_count,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
        }


class SuggestionFacade:
    """In-memory suggestion facade for the governance layer."""

    def __init__(self) -> None:
        self._suggestions: Dict[str, Suggestion] = {}
        self._reviews: List[SuggestionReviewRecord] = []
        self._approvals: List[SuggestionApprovalRecord] = []

    def create(self, suggestion: Suggestion) -> Suggestion:
        self._suggestions[suggestion.suggestion_id] = suggestion
        return suggestion

    def get(self, suggestion_id: str) -> Optional[Suggestion]:
        return self._suggestions.get(suggestion_id)

    def list(self, execution_id: Optional[str] = None) -> List[Suggestion]:
        items = list(self._suggestions.values())
        if execution_id is None:
            return items
        return [item for item in items if item.execution_id == execution_id]

    def review(self, record: SuggestionReviewRecord) -> SuggestionReviewRecord:
        self._reviews.append(record)
        suggestion = self._suggestions.get(record.suggestion_id)
        if suggestion is not None:
            if record.decision == SuggestionStatus.APPROVED.value:
                suggestion.status = SuggestionStatus.APPROVED
            elif record.decision == SuggestionStatus.REJECTED.value:
                suggestion.status = SuggestionStatus.REJECTED
            elif record.decision in (SuggestionStatus.OPEN.value, SuggestionStatus.REVIEWING.value):
                suggestion.status = SuggestionStatus.REVIEWING
        return record

    def approve(self, record: SuggestionApprovalRecord) -> SuggestionApprovalRecord:
        self._approvals.append(record)
        suggestion = self._suggestions.get(record.suggestion_id)
        if suggestion is not None:
            suggestion.status = SuggestionStatus.APPROVED
        return record

    def overview(self, execution_id: Optional[str] = None) -> SuggestionOverviewResult:
        suggestions = self.list(execution_id)
        total = len(suggestions)
        open_count = sum(1 for item in suggestions if item.status == SuggestionStatus.OPEN)
        approved_count = sum(1 for item in suggestions if item.status == SuggestionStatus.APPROVED)
        rejected_count = sum(1 for item in suggestions if item.status == SuggestionStatus.REJECTED)
        return SuggestionOverviewResult(
            execution_id=execution_id or "",
            suggestions=suggestions,
            total=total,
            open_count=open_count,
            approved_count=approved_count,
            rejected_count=rejected_count,
        )


class SuggestionBridge:
    """Bridge execution observations to suggestion records."""

    def __init__(self, service: Any) -> None:
        self._service = service

    async def capture_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        execution_id = str(event.get("run_id") or event.get("execution_id") or "")
        if not execution_id:
            return {"success": False, "error": "execution_id required"}
        suggestions = self._service.analyzer.analyze_events(execution_id, [event])
        created = []
        for suggestion in suggestions:
            self._service.create(suggestion)
            created.append(suggestion.to_dict())
        return {"success": True, "data": {"execution_id": execution_id, "created": created, "total": len(created)}}

    async def promote_to_hitl(
        self,
        suggestion_id: str,
        *,
        gate: str = "review",
        title: str = "",
        summary: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        suggestion = self._service.get(suggestion_id)
        if suggestion is None:
            return {"success": False, "error": "suggestion not found"}
        suggestion.hitl_request_id = suggestion.hitl_request_id or suggestion_id
        suggestion.status = SuggestionStatus.REVIEWING
        return {
            "success": True,
            "data": {
                "suggestion_id": suggestion_id,
                "execution_id": suggestion.execution_id,
                "gate": gate,
                "title": title or suggestion.title,
                "summary": summary or suggestion.summary,
                "context": dict(context or {}),
                "hitl_request_id": suggestion.hitl_request_id,
            },
        }

    async def attach_replay_directive(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        suggestion = self._service.get(suggestion_id)
        if suggestion is None:
            return {"success": False, "error": "suggestion not found"}
        suggestion.replay_directive = dict(replay or {})
        return {
            "success": True,
            "data": {"suggestion_id": suggestion_id, "replay_directive": suggestion.replay_directive},
        }


def create_suggestion_facade() -> SuggestionFacade:
    return SuggestionFacade()


__all__ = [
    "Suggestion",
    "SuggestionApprovalRecord",
    "SuggestionBridge",
    "SuggestionFacade",
    "SuggestionImpactScope",
    "SuggestionOverviewResult",
    "SuggestionReviewContext",
    "SuggestionReviewRecord",
    "SuggestionSeverity",
    "SuggestionSourceType",
    "SuggestionStatus",
    "create_suggestion_facade",
]
