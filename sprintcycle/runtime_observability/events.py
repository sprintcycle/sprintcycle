"""Execution event ledger for the observability layer.

This module stores execution facts and exposes trace/replay friendly projections.
It must remain read-oriented and must not participate in governance decisions or
execution control.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ExecutionEventLedger:
    events: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event)
        self.events.append(payload)
        return {"success": True, "data": payload}

    def list_events(self) -> Dict[str, Any]:
        return {"success": True, "data": list(self.events), "total": len(self.events)}

    def list_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        rid = str(run_id)
        return [
            event
            for event in self.events
            if str(event.get("run_id") or event.get("data", {}).get("run_id") or "") == rid
        ]

    def to_trace_payload(self, run_id: str) -> Dict[str, Any]:
        from .trace import TraceProjection

        events = self.list_by_run_id(run_id)
        return TraceProjection(run_id=run_id, events=events).to_payload()

    def to_replay_payload(self, run_id: str) -> Dict[str, Any]:
        from .replay import ReplayProjection

        events = self.list_by_run_id(run_id)
        return ReplayProjection(run_id=run_id, timeline=events).to_payload()
