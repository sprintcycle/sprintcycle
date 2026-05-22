"""Observability application service.

Owns trace/replay/event read paths and keeps the facade free from observability
implementation details. This layer also exposes diagnosis-oriented metadata
for failure classification and repair analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ...execution.state.state_store import get_state_store
from sprintcycle.infrastructure.observability.facade import ObservabilityFacade
from .lifecycle_contracts import build_lifecycle_contract
from .lifecycle_state_machine import build_default_correlation
from .phase_workflow import build_observe_artifact


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
        failures = [
            e for e in events if str((e or {}).get("kind") or (e or {}).get("type") or "").lower().find("fail") >= 0
        ]
        phase_tags = sorted(
            {
                str((e or {}).get("phase") or (e or {}).get("stage") or "").strip()
                for e in events
                if str((e or {}).get("phase") or (e or {}).get("stage") or "").strip()
            }
        )
        root_cause_tags = sorted(
            {
                str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip()
                for e in events
                if str((e or {}).get("root_cause") or (e or {}).get("failure_kind") or "").strip()
            }
        )
        correlation = build_default_correlation(
            {"execution_id": run_id, "metadata": {"source": "observability"}}
        ).to_dict()
        repair_ready = bool(failures or root_cause_tags)
        repair_candidates = [
            e
            for e in events
            if str(
                (e or {}).get("repair_hint") or (e or {}).get("root_cause") or (e or {}).get("failure_kind") or ""
            ).strip()
        ]
        diagnostics = {
            "event_count": len(events),
            "failure_count": len(failures),
            "phase_tags": phase_tags,
            "root_cause_tags": root_cause_tags,
            "failure_rate": round((len(failures) / len(events)) * 100, 2) if events else 0.0,
            "observability_ready": bool(events),
            "repair_ready": repair_ready,
            "repair_candidate_count": len(repair_candidates),
        }
        lifecycle = {
            "stage": "observing" if events else "normalized",
            "status": "success" if not failures else "failed",
            "is_healthy": not failures,
            "event_count": len(events),
            "failure_kind": root_cause_tags[0] if root_cause_tags else ("execution_error" if failures else ""),
            "repair_ready": repair_ready,
            "correlation": correlation,
        }
        audit = {
            "run_id": run_id,
            "event_count": len(events),
            "failure_count": len(failures),
            "repair_ready": repair_ready,
            "root_cause_tags": root_cause_tags,
            "phase_tags": phase_tags,
        }
        contract = build_lifecycle_contract(
            execution_id=run_id,
            task_id=run_id,
            project_path="",
            stage=lifecycle["stage"],
            status=lifecycle["status"],
            metadata={"source": "observability"},
            failure_kind=lifecycle["failure_kind"],
            delivery_refs={"event_count": len(events)},
            recovery_refs={
                "ready": repair_ready,
                "candidate_count": len(repair_candidates),
                "root_causes": root_cause_tags,
                "audit": audit,
            },
            trace=data,
            diagnostics=diagnostics,
            correlation=correlation,
            validation_refs={
                "trace_present": bool(events),
                "diagnostics_present": bool(diagnostics),
                "audit_present": True,
            },
            output_refs={"event_count": len(events), "root_cause_tags": root_cause_tags},
            transition_reason="trace inspection",
        )
        observed = build_observe_artifact(contract.to_dict(), trace=data, diagnostics=diagnostics)
        observed_contract = observed.get("lifecycle_contract", contract.to_dict())
        observed_contract.setdefault("validation_refs", {})["audit_present"] = True
        observed_contract.setdefault("evidence", {}).setdefault("stages", {}).setdefault("observe", {})["audit"] = audit
        observed_contract.setdefault("evidence", {}).setdefault("recovery", {})["audit"] = audit
        return {
            "success": True,
            "data": {
                "trace": data,
                "diagnostics": diagnostics,
                "lifecycle": lifecycle,
                "repair": {
                    "ready": repair_ready,
                    "candidate_count": len(repair_candidates),
                    "root_causes": root_cause_tags,
                },
                "observe": observed.get("observe", {}),
                "lifecycle_contract": observed_contract,
                "audit": audit,
            },
        }

    def replay(self, run_id: str) -> Dict[str, Any]:
        data = self.observability.to_trace_payload(run_id)
        events = list((data or {}).get("events", []) or [])
        diagnostics = {"event_count": len(events), "latest_event": events[-1] if events else None}
        lifecycle = {
            "stage": "observing" if events else "normalized",
            "status": "success" if events else "pending",
            "is_healthy": True if events else False,
        }
        return {
            "success": True,
            "data": {"execution_id": run_id, "diagnostics": diagnostics, "lifecycle": lifecycle},
            "timeline": events,
        }

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
        return {
            "success": True,
            "data": {"state": state.to_dict(), "trace": self.observability.to_trace_payload(eid), "limit": limit},
        }


__all__ = ["ObservabilityService"]
