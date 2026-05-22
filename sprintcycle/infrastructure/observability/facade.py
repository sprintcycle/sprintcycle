"""Observability facade for the V2 execution pipeline.

The facade is intentionally thin: it normalizes canonical events and exposes
run-level trace snapshots for the UI and platform layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from sprintcycle.infrastructure.integrations.phoenix.trace_runtime import PhoenixTraceRuntime
from .event_models import EventStoreSnapshot, ObservabilityEvent


@dataclass
class ObservabilityFacade:
    events: List[Dict[str, Any]]

    def __init__(self) -> None:
        self.events = []
        self._phoenix = PhoenixTraceRuntime()

    def trace(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Record a trace event."""
        return self.record(*args, **kwargs)

    def record(self, event: Dict[str, Any] | ObservabilityEvent | str) -> Dict[str, Any]:
        if isinstance(event, str):
            payload = {"event_type": "log", "message": event}
        elif isinstance(event, ObservabilityEvent):
            payload = event.to_dict()
        else:
            payload = ObservabilityEvent.from_dict(event).to_dict()
        self.events.append(payload)
        return {"success": True, "data": payload}

    record_event = record

    def list_events(self) -> Dict[str, Any]:
        return {"success": True, "data": list(self.events), "total": len(self.events)}

    def list_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        rid = str(run_id)
        return [event for event in self.events if str(event.get("run_id") or event.get("execution_id") or "") == rid]

    def snapshot(self, run_id: str) -> EventStoreSnapshot:
        return EventStoreSnapshot(run_id=run_id, events=self.list_by_run_id(run_id))

    def to_trace_payload(self, run_id: str) -> Dict[str, Any]:
        events = self.list_by_run_id(run_id)
        phoenix_trace = self._phoenix.emit_trace(events)
        return {
            "run_id": run_id,
            "execution_id": run_id,
            "total": len(events),
            "events": events,
            "phoenix_trace": phoenix_trace,
        }

    def to_replay_payload(self, run_id: str) -> Dict[str, Any]:
        events = self.list_by_run_id(run_id)
        return {
            "run_id": run_id,
            "execution_id": run_id,
            "total": len(events),
            "timeline": events,
        }
