"""Suggestion application service.

Owns suggestion review, approval, rejection, archive, replay attachment, and
execution-event capture flows, including hook emission and governance
integration where applicable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...governance.facade import GovernanceFacade
from ...governance.suggestion import SuggestionFacade
from ...governance.versioning.registry import VersionRegistry
from ...hooks import (
    SUGGESTION_APPROVAL_COMPLETED_EVENT,
    SUGGESTION_APPROVE_SUGGESTION,
    SUGGESTION_APPROVED_EVENT,
    SUGGESTION_ARCHIVE,
    SUGGESTION_ARCHIVED_EVENT,
    SUGGESTION_ATTACH_REPLAY,
    SUGGESTION_CAPTURE_EXECUTION_EVENT,
    SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT,
    SUGGESTION_PROMOTE_TO_HITL,
    SUGGESTION_PROMOTED_TO_HITL_EVENT,
    SUGGESTION_REJECT_SUGGESTION,
    SUGGESTION_REJECTED_EVENT,
    SUGGESTION_REJECTION_COMPLETED_EVENT,
    SUGGESTION_REVIEW,
    SUGGESTION_REVIEW_RECORD_EVENT,
    SUGGESTION_REVIEWED_EVENT,
    HookContext,
    HookPhase,
    HookRegistry,
    HookResult,
    HookRunner,
)
from ..evolution.models import VersionArtifact
from .lifecycle_contracts import build_lifecycle_contract
from .lifecycle_state_machine import build_default_correlation
from .promotion_policy import PromotionPolicy


@dataclass
class SuggestionApplicationService:
    suggestion: SuggestionFacade
    governance: Optional[GovernanceFacade] = None
    version_registry: Optional[VersionRegistry] = None
    promotion_policy: Optional[PromotionPolicy] = None
    hooks: Optional[HookRegistry] = None

    def __post_init__(self) -> None:
        self._hooks = HookRunner(self.hooks)
        self._promotion_policy = self.promotion_policy or PromotionPolicy()

    def _hook_context(
        self,
        action: str,
        *,
        subject_id: str = "",
        execution_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HookContext:
        domain, normalized_action = self._hooks.action("suggestion", action)
        return HookContext(
            domain=domain,
            action=normalized_action,
            subject_id=subject_id,
            execution_id=execution_id,
            payload=dict(payload or {}),
            metadata=dict(metadata or {}),
        )

    def _emit(
        self,
        phase: HookPhase,
        action: str,
        *,
        subject_id: str = "",
        execution_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[HookResult]:
        context = self._hook_context(
            action, subject_id=subject_id, execution_id=execution_id, payload=payload, metadata=metadata
        )
        return self._hooks.emit(domain=context.domain, action=context.action, phase=phase, context=context)

    def _ensure_before(
        self,
        action: str,
        *,
        subject_id: str = "",
        execution_id: str = "",
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[HookContext, Dict[str, Any] | None]:
        context = self._hook_context(
            action, subject_id=subject_id, execution_id=execution_id, payload=payload, metadata=metadata
        )
        results = self._hooks.before(context.domain, context.action, context)
        if any((not r.ok or r.blocked) for r in results):
            result = next((r for r in results if not r.ok or r.blocked), None)
            return context, {
                "success": False,
                "error": result.message if result and result.message else "blocked by hook",
                "hook": [r.to_dict() for r in results],
            }
        return context, None

    async def suggestion_review(self, suggestion_id: str) -> Dict[str, Any]:
        _, blocked = self._ensure_before(SUGGESTION_REVIEW[1], subject_id=suggestion_id)
        if blocked is not None:
            return blocked
        context = await self.suggestion.review_suggestion(suggestion_id)
        self._hooks.after(
            "suggestion",
            SUGGESTION_REVIEW[1],
            self._hook_context(SUGGESTION_REVIEW[1], subject_id=suggestion_id, payload=context.to_dict()),
        )
        self._hooks.event(
            "suggestion",
            "review",
            SUGGESTION_REVIEWED_EVENT,
            {"suggestion_id": suggestion_id, "data": context.to_dict()},
        )
        return {"success": True, "data": context.to_dict()}

    async def review_suggestion(
        self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        _, blocked = self._ensure_before(
            "review_suggestion",
            subject_id=suggestion_id,
            execution_id=execution_id,
            payload={"reviewer": reviewer, "notes": notes},
        )
        if blocked is not None:
            return blocked
        record = await self.governance.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)
        self._hooks.after(
            "suggestion",
            "review_suggestion",
            self._hook_context(
                "review_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record}
            ),
        )
        self._hooks.event(
            "suggestion",
            "review_suggestion",
            SUGGESTION_REVIEW_RECORD_EVENT,
            {"execution_id": execution_id, "suggestion_id": suggestion_id, "record": record},
        )
        return {"success": True, "data": record}

    async def approve_suggestion(
        self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        _, blocked = self._ensure_before(
            SUGGESTION_APPROVE_SUGGESTION[1],
            subject_id=suggestion_id,
            execution_id=execution_id,
            payload={"approver": approver, "notes": notes},
        )
        if blocked is not None:
            return blocked
        record = await self.governance.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)
        self._hooks.after(
            "suggestion",
            SUGGESTION_APPROVE_SUGGESTION[1],
            self._hook_context(
                SUGGESTION_APPROVE_SUGGESTION[1],
                subject_id=suggestion_id,
                execution_id=execution_id,
                payload={"record": record},
            ),
        )
        self._hooks.event(
            "suggestion",
            "approve_suggestion",
            SUGGESTION_APPROVED_EVENT,
            {"execution_id": execution_id, "suggestion_id": suggestion_id, "approver": approver, "notes": notes},
        )
        return {"success": True, "data": record}

    async def reject_suggestion(
        self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        _, blocked = self._ensure_before(
            "reject_suggestion",
            subject_id=suggestion_id,
            execution_id=execution_id,
            payload={"rejected_by": rejected_by, "notes": notes},
        )
        if blocked is not None:
            return blocked
        record = await self.governance.reject_suggestion(
            execution_id, suggestion_id, rejected_by=rejected_by, notes=notes
        )
        self._hooks.after(
            "suggestion",
            "reject_suggestion",
            self._hook_context(
                "reject_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record}
            ),
        )
        self._hooks.event(
            "suggestion",
            "reject_suggestion",
            SUGGESTION_REJECTED_EVENT,
            {"execution_id": execution_id, "suggestion_id": suggestion_id, "rejected_by": rejected_by, "notes": notes},
        )
        return {"success": True, "data": record}

    async def promote_suggestion_to_hitl(
        self,
        suggestion_id: str,
        *,
        gate: str = "review",
        title: str = "",
        summary: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        _, blocked = self._ensure_before(
            SUGGESTION_PROMOTE_TO_HITL[1],
            subject_id=suggestion_id,
            payload={"gate": gate, "title": title, "summary": summary, "context": dict(context or {})},
        )
        if blocked is not None:
            return blocked
        request = await self.governance.promote_suggestion_to_hitl(
            suggestion_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
        )
        self._hooks.after(
            "suggestion",
            SUGGESTION_PROMOTE_TO_HITL[1],
            self._hook_context(SUGGESTION_PROMOTE_TO_HITL[1], subject_id=suggestion_id, payload={"request": request}),
        )
        self._hooks.event(
            "suggestion",
            "promote_to_hitl",
            SUGGESTION_PROMOTED_TO_HITL_EVENT,
            {"suggestion_id": suggestion_id, "gate": gate, "request": request},
        )
        return {"success": True, "data": request}

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        _, blocked = self._ensure_before(
            SUGGESTION_ATTACH_REPLAY[1], subject_id=suggestion_id, payload={"replay": dict(replay or {})}
        )
        if blocked is not None:
            return blocked
        request = await self.governance.attach_suggestion_replay(suggestion_id, replay)
        self._hooks.after(
            "suggestion",
            SUGGESTION_ATTACH_REPLAY[1],
            self._hook_context(SUGGESTION_ATTACH_REPLAY[1], subject_id=suggestion_id, payload={"request": request}),
        )
        return {"success": True, "data": request}

    async def suggestion_approve(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        hook_ctx, blocked = self._ensure_before(
            SUGGESTION_APPROVE_SUGGESTION[1], subject_id=suggestion_id, payload={"approver": approver, "notes": notes}
        )
        if blocked is not None:
            return blocked
        record = await self.suggestion.approve_suggestion(suggestion_id, approver, notes)
        promoted: Dict[str, Any] | None = None
        policy_result: Dict[str, Any] | None = None
        if self.governance is not None:
            try:
                request = await self.governance.promote_suggestion_to_hitl(
                    suggestion_id,
                    gate="review",
                    title="",
                    summary=notes,
                    context={"approver": approver, "notes": notes, "source": "suggestion_approval"},
                )
                promoted = (
                    request.get("data", request)
                    if isinstance(request, dict)
                    else {"request_id": getattr(request, "request_id", None)}
                )
            except Exception:
                promoted = None
        if self.version_registry is not None:
            suggestion = await self.suggestion.get_suggestion(suggestion_id)
            runtime = dict((suggestion.metadata or {}).get("runtime", {}) if suggestion else {})
            governance = {"approved": True, "status": "approved", "approver": approver, "notes": notes}
            lifecycle_contract = {
                "completion_score": 100.0 if suggestion and suggestion.status == "approved" else 0.0,
                "trace": dict((suggestion.metadata or {}).get("trace", {}) if suggestion else {}),
                "diagnostics": dict((suggestion.metadata or {}).get("diagnostics", {}) if suggestion else {}),
                "recovery": dict((suggestion.metadata or {}).get("repair", {}) if suggestion else {}),
                "suggestion": {"approved": True, "suggestion_id": suggestion_id},
                "health": {"completion_score": 100.0},
            }
            policy_result = self._promotion_policy.evaluate(lifecycle_contract, runtime=runtime, governance=governance)
            if policy_result.get("allowed") and suggestion is not None:
                artifact = VersionArtifact(
                    version_id=f"version_from_{suggestion_id}",
                    target="code",
                    source_suggestion_id=suggestion_id,
                    promotion_guard={"policy": policy_result, "approver": approver, "notes": notes},
                    metadata={
                        "source": "suggestion_approval",
                        "correlation": build_default_correlation({"suggestion_id": suggestion_id}).to_dict(),
                    },
                )
                await self.version_registry.register(artifact)
        self._emit(
            HookPhase.AFTER,
            SUGGESTION_APPROVE_SUGGESTION[1],
            subject_id=suggestion_id,
            payload={"approval": record.to_dict(), "promotion": promoted, "promotion_policy": policy_result},
        )
        self._hooks.event(
            "suggestion",
            "approve_suggestion",
            SUGGESTION_APPROVAL_COMPLETED_EVENT,
            {
                "suggestion_id": suggestion_id,
                "approver": approver,
                "promotion": promoted,
                "promotion_policy": policy_result,
            },
        )
        return {
            "success": True,
            "data": {"approval": record.to_dict(), "promotion": promoted, "promotion_policy": policy_result},
        }

    async def suggestion_reject(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        _, blocked = self._ensure_before(
            SUGGESTION_REJECT_SUGGESTION[1], subject_id=suggestion_id, payload={"approver": approver, "notes": notes}
        )
        if blocked is not None:
            return blocked
        record = await self.suggestion.reject_suggestion(suggestion_id, approver, notes)
        self._hooks.after(
            "suggestion",
            SUGGESTION_REJECT_SUGGESTION[1],
            self._hook_context(
                SUGGESTION_REJECT_SUGGESTION[1], subject_id=suggestion_id, payload={"record": record.to_dict()}
            ),
        )
        self._hooks.event(
            "suggestion",
            "reject",
            SUGGESTION_REJECTION_COMPLETED_EVENT,
            {"suggestion_id": suggestion_id, "approver": approver},
        )
        return {"success": True, "data": record.to_dict()}

    async def suggestion_archive(self, suggestion_id: str) -> Dict[str, Any]:
        _, blocked = self._ensure_before(SUGGESTION_ARCHIVE[1], subject_id=suggestion_id)
        if blocked is not None:
            return blocked
        await self.suggestion.archive_suggestion(suggestion_id)
        self._hooks.after(
            "suggestion", SUGGESTION_ARCHIVE[1], self._hook_context(SUGGESTION_ARCHIVE[1], subject_id=suggestion_id)
        )
        self._hooks.event("suggestion", "archive", SUGGESTION_ARCHIVED_EVENT, {"suggestion_id": suggestion_id})
        return {"success": True, "data": {"suggestion_id": suggestion_id, "status": "archived"}}

    async def create_suggestion_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        normalized_event = dict(event or {})
        execution_id = str(normalized_event.get("run_id") or normalized_event.get("execution_id") or "")
        _, blocked = self._ensure_before(
            SUGGESTION_CAPTURE_EXECUTION_EVENT[1],
            subject_id=str(normalized_event.get("suggestion_id") or ""),
            execution_id=execution_id,
            payload=normalized_event,
        )
        if blocked is not None:
            return blocked
        normalized_event.setdefault("source", "execution")
        normalized_event.setdefault(
            "kind", normalized_event.get("kind") or normalized_event.get("type") or "execution_event"
        )
        normalized_event.setdefault(
            "root_cause", normalized_event.get("root_cause") or normalized_event.get("failure_kind") or ""
        )
        result = await self.suggestion.capture_from_execution_event(normalized_event)
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=str(normalized_event.get("task_id") or execution_id),
            project_path=str(normalized_event.get("project_path") or ""),
            stage="suggesting",
            status="success",
            metadata={"source": "execution_event", "root_cause": normalized_event.get("root_cause", "")},
            suggestion_refs=[result.to_dict() if hasattr(result, "to_dict") else dict(result or {})],
            governance_refs={"source": "execution_event_capture", "governed": bool(self.governance is not None)},
            evolution_refs={"candidate": True, "source": "execution_event"},
            recovery_refs={"root_cause": normalized_event.get("root_cause", ""), "execution_id": execution_id},
        )
        self._hooks.after(
            "suggestion",
            SUGGESTION_CAPTURE_EXECUTION_EVENT[1],
            self._hook_context(
                SUGGESTION_CAPTURE_EXECUTION_EVENT[1],
                subject_id=str(normalized_event.get("suggestion_id") or ""),
                execution_id=execution_id,
                payload={"event": normalized_event, "result": result, "lifecycle_contract": contract.to_dict()},
            ),
        )
        self._hooks.event(
            "suggestion",
            "capture_execution_event",
            SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT,
            {
                "event": normalized_event,
                "result": result,
                "source": "execution",
                "root_cause": normalized_event.get("root_cause", ""),
                "lifecycle_contract": contract.to_dict(),
            },
        )
        return {
            "success": True,
            "data": {
                "suggestion": result.to_dict() if hasattr(result, "to_dict") else result,
                "lifecycle_contract": contract.to_dict(),
            },
        }


__all__ = ["SuggestionApplicationService"]
