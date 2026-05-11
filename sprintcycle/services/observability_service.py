"""Observability application service.

Owns trace/replay/event read paths and keeps the facade free from observability
implementation details. This layer also exposes diagnosis-oriented metadata
for failure classification and repair analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..observability.facade import ObservabilityFacade
from ..execution.state.state_store import get_state_store


@dataclass
class ObservabilityService:
    observability: ObservabilityFacade

    def record_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self.observability.record(event)

    def list_events(self) -> Dict[str, Any]:
        return self.observability.list_events()

    def trace(self, run_id: str) -> Dict[str, Any]:
        data = self.observability.to_trace_payload(run_id)
        events = list((data or {}).get("events", []) or [])
        failures = [e for e in events if str((e or {}).get("kind") or (e or {}).get("type") or "").lower().find("fail") >= 0]
        diagnostics = {
            "event_count": len(events),
            "failure_count": len(failures),
            "phase_tags": sorted({str((e or {}).get("phase") or (e or {}).get("stage") or "").strip() for e in events if str((e or {}).get("phase") or (e or {}).get("stage") or "").strip()}),
            "root_cause_tags": sorted({str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip() for e in events if str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip()}),
        }
        return {"success": True, "data": {"trace": data, "diagnostics": diagnostics}}

    def replay(self, run_id: str) -> Dict[str, Any]:
        data = self.observability.to_trace_payload(run_id)
        events = list((data or {}).get("events", []) or [])
        diagnostics = {"event_count": len(events), "latest_event": events[-1] if events else None}
        return {"success": True, "data": {"execution_id": run_id, "diagnostics": diagnostics}, "timeline": events}

    def pending(self, governance: Any, execution_id: Optional[str] = None) -> Dict[str, Any]:
        if governance is None:
            return {"success": True, "data": []}
        return {"success": True, "data": governance.list_pending(execution_id)}

    async def pending_async(self, governance: Any, execution_id: Optional[str] = None) -> Dict[str, Any]:
        if governance is None:
            return {"success": True, "data": []}
        return {"success": True, "data": await governance.list_pending(execution_id)}

    def execution_detail(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        store = get_state_store()
        state = store.load(eid)
        if state is None:
            return {"success": False, "error": f"未找到执行记录: {eid}"}
        return {"success": True, "data": {"state": state.to_dict(), "trace": self.observability.to_trace_payload(eid), "limit": limit}}


__all__ = ["ObservabilityService"]
