"""Canonical observability event models for SprintCycle V2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ObservabilityEvent:
    """Canonical execution event shared by execution, observability and dashboard layers."""

    event_id: str = field(default_factory=lambda: uuid4().hex)
    run_id: str = ""
    execution_id: str = ""
    kind: str = "event"
    timestamp: Optional[str] = None
    step_id: str = ""
    parent_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if not data.get("execution_id"):
            data["execution_id"] = data.get("run_id", "")
        if not data.get("run_id"):
            data["run_id"] = data.get("execution_id", "")
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ObservabilityEvent":
        payload = dict(data.get("payload", {}) or {})
        metadata = dict(data.get("metadata", {}) or {})
        return cls(
            event_id=str(data.get("event_id") or uuid4().hex),
            run_id=str(data.get("run_id") or data.get("execution_id") or ""),
            execution_id=str(data.get("execution_id") or data.get("run_id") or ""),
            kind=str(data.get("kind") or data.get("event_type") or "event"),
            timestamp=data.get("timestamp"),
            step_id=str(data.get("step_id") or data.get("step_name") or ""),
            parent_id=str(data.get("parent_id") or ""),
            payload=payload,
            metadata=metadata,
        )


@dataclass
class EventStoreSnapshot:
    """Lightweight snapshot for projections."""

    run_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


__all__ = ["ObservabilityEvent", "EventStoreSnapshot"]
