"""Dashboard-facing projections and view models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SuggestionCardViewModel:
    suggestion_id: str
    execution_id: str
    title: str
    summary: str
    severity: str = "medium"
    status: str = "open"
    impact_scope: str = "task"
    source_type: str = "runtime"
    root_cause: str = ""
    proposed_action: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SuggestionCardViewModel":
        return cls(
            suggestion_id=str(data.get("suggestion_id", "")),
            execution_id=str(data.get("execution_id", "")),
            title=str(data.get("title", "")),
            summary=str(data.get("summary", "")),
            severity=str(data.get("severity", "medium")),
            status=str(data.get("status", "open")),
            impact_scope=str(data.get("impact_scope", "task")),
            source_type=str(data.get("source_type", "runtime")),
            root_cause=str(data.get("root_cause", "")),
            proposed_action=str(data.get("proposed_action", "")),
            tags=list(data.get("tags", []) or []),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass
class SuggestionBoardViewModel:
    execution_id: str
    total: int = 0
    open_count: int = 0
    approved_count: int = 0
    rejected_count: int = 0
    suggestions: List[SuggestionCardViewModel] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "total": self.total,
            "open_count": self.open_count,
            "approved_count": self.approved_count,
            "rejected_count": self.rejected_count,
            "suggestions": [item.__dict__ for item in self.suggestions],
        }


@dataclass
class HitlRequestViewModel:
    request_id: str
    execution_id: str
    gate: str
    status: str
    decision: Optional[str] = None
    note: Optional[str] = None
    title: str = ""
    summary: str = ""
    risk_level: str = "medium"
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HitlRequestViewModel":
        return cls(
            request_id=str(data.get("request_id", "")),
            execution_id=str(data.get("execution_id", "")),
            gate=str(data.get("gate", "")),
            status=str(data.get("status", "")),
            decision=data.get("decision"),
            note=data.get("note"),
            title=str(data.get("title", "")),
            summary=str(data.get("summary", "")),
            risk_level=str(data.get("risk_level", "medium")),
            context=dict(data.get("context", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass
class DashboardProjectionBundle:
    execution_id: str
    trace: Dict[str, Any] = field(default_factory=dict)
    replay: Dict[str, Any] = field(default_factory=dict)
    suggestions: Dict[str, Any] = field(default_factory=dict)
    hitl: Dict[str, Any] = field(default_factory=dict)
    deployment: Dict[str, Any] = field(default_factory=dict)
    fitness: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "trace": self.trace,
            "replay": self.replay,
            "suggestions": self.suggestions,
            "hitl": self.hitl,
            "deployment": self.deployment,
            "fitness": self.fitness,
        }


__all__ = [
    "DashboardProjectionBundle",
    "HitlRequestViewModel",
    "SuggestionBoardViewModel",
    "SuggestionCardViewModel",
]
