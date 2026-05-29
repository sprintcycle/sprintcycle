"""Observability application service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from sprintcycle.domain.ports.observability import ObservabilityFacadeProtocol
from sprintcycle.domain.ports.state_store import StateStoreProtocol
from sprintcycle.domain.core.lifecycle import (
    create_lifecycle,
    LifecycleSubstage,
    LifecycleStateMachine,
    CorrelationContext,
)
from ..execution.phase_workflow import build_observe_artifact


@dataclass
class ObservabilityService:
    observability: ObservabilityFacadeProtocol
    state_store: StateStoreProtocol

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
        
        # 使用新架构的 CorrelationContext
        correlation = CorrelationContext(
            execution_id=run_id,
            task_id=run_id,
            source="observability",
        )
        
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
        lifecycle_stage = "observing" if events else "normalized"
        lifecycle_status = "success" if not failures else "failed"
        failure_kind = root_cause_tags[0] if root_cause_tags else ("execution_error" if failures else "")
        
        lifecycle = {
            "stage": lifecycle_stage,
            "status": lifecycle_status,
            "is_healthy": not failures,
            "event_count": len(events),
            "failure_kind": failure_kind,
            "repair_ready": repair_ready,
            "correlation": correlation.to_dict(),
        }
        audit = {
            "run_id": run_id,
            "event_count": len(events),
            "failure_count": len(failures),
            "repair_ready": repair_ready,
            "root_cause_tags": root_cause_tags,
            "phase_tags": phase_tags,
        }
        
        # 使用新架构创建 lifecycle
        lifecycle_root = create_lifecycle(
            execution_id=run_id,
            task_id=run_id,
            project_path="",
            metadata={
                "source": "observability",
                "failure_kind": failure_kind,
                "delivery_refs": {"event_count": len(events)},
                "recovery_refs": {
                    "ready": repair_ready,
                    "candidate_count": len(repair_candidates),
                    "root_causes": root_cause_tags,
                    "audit": audit,
                },
                "trace": data,
                "diagnostics": diagnostics,
                "validation_refs": {
                    "trace_present": bool(events),
                    "diagnostics_present": bool(diagnostics),
                    "audit_present": True,
                },
                "output_refs": {"event_count": len(events), "root_cause_tags": root_cause_tags},
                "transition_reason": "trace inspection",
            },
        )
        
        # 转换到目标子状态
        target_substage = LifecycleSubstage.from_string(lifecycle_stage)
        if lifecycle_root.substage != target_substage:
            lifecycle_root = lifecycle_root.transition_to_substage(target_substage)
        
        # 获取字典格式
        service = LifecycleStateMachine()
        contract_dict = {
            "contract_id": lifecycle_root.contract_id,
            "execution_id": lifecycle_root.execution_id,
            "task_id": lifecycle_root.task_id,
            "project_path": lifecycle_root.project_path,
            "stage": lifecycle_root.stage.value,
            "status": lifecycle_status,
            "failure_kind": failure_kind,
            "metadata": dict(lifecycle_root.metadata),
            "delivery_refs": dict(lifecycle_root.metadata).get("delivery_refs", {}),
            "recovery_refs": dict(lifecycle_root.metadata).get("recovery_refs", {}),
            "trace": dict(lifecycle_root.metadata).get("trace", {}),
            "diagnostics": dict(lifecycle_root.metadata).get("diagnostics", {}),
            "correlation": correlation.to_dict(),
            "validation_refs": dict(lifecycle_root.metadata).get("validation_refs", {}),
            "output_refs": dict(lifecycle_root.metadata).get("output_refs", {}),
            "transition_reason": dict(lifecycle_root.metadata).get("transition_reason", ""),
            "stage_history": [
                {"from": h.from_stage, "to": h.to_stage, "at": h.at, "reason": h.reason}
                for h in lifecycle_root.stage_history
            ],
            "is_terminal": service.is_terminal(lifecycle_root.stage.value),
            "stage_index": service.stage_index(lifecycle_root.stage.value),
        }
        
        observed = build_observe_artifact(contract_dict, trace=data, diagnostics=diagnostics)
        observed_contract = observed.get("lifecycle_contract", contract_dict)
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
        state = self.state_store.load(eid)
        if state is None:
            return {"success": False, "error": f"未找到执行记录: {eid}"}
        return {
            "success": True,
            "data": {"state": state.to_dict(), "trace": self.observability.to_trace_payload(eid), "limit": limit},
        }


__all__ = ["ObservabilityService"]
