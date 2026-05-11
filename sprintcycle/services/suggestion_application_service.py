"""Suggestion application service.

Keeps suggestion lifecycle and promotion flows out of the SprintCycle facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..governance.facade import GovernanceFacade
from ..governance.suggestion import SuggestionFacade
from ..hooks import (
    HookContext,
    HookPhase,
    HookRegistry,
    HookResult,
    HookRouter,
    SUGGESTION_APPROVE_SUGGESTION,
    SUGGESTION_APPROVAL_COMPLETED_EVENT,
    SUGGESTION_APPROVED_EVENT,
    SUGGESTION_ARCHIVED_EVENT,
    SUGGESTION_ATTACH_REPLAY,
    SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT,
    SUGGESTION_CAPTURE_EXECUTION_EVENT,
    SUGGESTION_PROMOTE_TO_HITL,
    SUGGESTION_PROMOTED_TO_HITL_EVENT,
    SUGGESTION_REJECT_SUGGESTION,
    SUGGESTION_REJECTION_COMPLETED_EVENT,
    SUGGESTION_REJECTED_EVENT,
    SUGGESTION_REVIEW,
    SUGGESTION_REVIEWED_EVENT,
    SUGGESTION_REVIEW_RECORD_EVENT,
)


@dataclass
class SuggestionApplicationService:
    suggestion: SuggestionFacade
    governance: Optional[GovernanceFacade] = None
    hooks: Optional[HookRegistry] = None

    def __post_init__(self) -> None:
        self._hooks = HookRouter(self.hooks)

    def _emit(self, phase: HookPhase, action: str, *, subject_id: str = "", execution_id: str = "", payload: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> list[HookResult]:
        domain, normalized_action = self._hooks.action("suggestion", action)
        context = HookContext(
            domain=domain,
            action=normalized_action,
            subject_id=subject_id,
            execution_id=execution_id,
            payload=dict(payload or {}),
            metadata=dict(metadata or {}),
        )
        if phase == HookPhase.BEFORE:
            return self._hooks.before(domain, normalized_action, context)
        if phase == HookPhase.AFTER:
            return self._hooks.after(domain, normalized_action, context)
        return self._hooks.failed(domain, normalized_action, context)

    async def suggestion_review(self, suggestion_id: str) -> Dict[str, Any]:
        before = self._emit(HookPhase.BEFORE, SUGGESTION_REVIEW[1], subject_id=suggestion_id)
        if any((not r.ok or r.blocked) for r in before):
            result = next((r for r in before if not r.ok or r.blocked), None)
            return {"success": False, "error": result.message if result and result.message else "blocked by hook", "hook": [r.to_dict() for r in before]}
        context = await self.suggestion.review_suggestion(suggestion_id)
        self._emit(HookPhase.AFTER, "review", subject_id=suggestion_id, payload=context.to_dict())
        self._hooks.event("suggestion", "review", SUGGESTION_REVIEWED_EVENT, {"suggestion_id": suggestion_id, "data": context.to_dict()})
        return {"success": True, "data": context.to_dict()}

    async def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        before = self._emit(HookPhase.BEFORE, "review_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"reviewer": reviewer, "notes": notes})
        if any((not r.ok or r.blocked) for r in before):
            result = next((r for r in before if not r.ok or r.blocked), None)
            return {"success": False, "error": result.message if result and result.message else "blocked by hook", "hook": [r.to_dict() for r in before]}
        record = await self.governance.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)
        self._emit(HookPhase.AFTER, "review_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record})
        self._hooks.event("suggestion", "review_suggestion", SUGGESTION_REVIEW_RECORD_EVENT, {"execution_id": execution_id, "suggestion_id": suggestion_id, "record": record})
        return {"success": True, "data": record}

    async def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        before = self._emit(HookPhase.BEFORE, SUGGESTION_APPROVE_SUGGESTION[1], subject_id=suggestion_id, execution_id=execution_id, payload={"approver": approver, "notes": notes})
        if any((not r.ok or r.blocked) for r in before):
            result = next((r for r in before if not r.ok or r.blocked), None)
            return {"success": False, "error": result.message if result and result.message else "blocked by hook", "hook": [r.to_dict() for r in before]}
        record = await self.governance.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)
        self._emit(HookPhase.AFTER, SUGGESTION_APPROVE_SUGGESTION[1], subject_id=suggestion_id, execution_id=execution_id, payload={"record": record})
        self._hooks.event("suggestion", "approve_suggestion", SUGGESTION_APPROVED_EVENT, {"execution_id": execution_id, "suggestion_id": suggestion_id, "approver": approver, "notes": notes})
        return {"success": True, "data": record}

    async def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        before = self._emit(HookPhase.BEFORE, "reject_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"rejected_by": rejected_by, "notes": notes})
        if any((not r.ok or r.blocked) for r in before):
            result = next((r for r in before if not r.ok or r.blocked), None)
            return {"success": False, "error": result.message if result and result.message else "blocked by hook", "hook": [r.to_dict() for r in before]}
        record = await self.governance.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)
        self._emit(HookPhase.AFTER, "reject_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record})
        self._hooks.event("suggestion", "reject_suggestion", SUGGESTION_REJECTED_EVENT, {"execution_id": execution_id, "suggestion_id": suggestion_id, "rejected_by": rejected_by, "notes": notes})
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
        hook_ctx = HookContext(domain="suggestion", action=SUGGESTION_PROMOTE_TO_HITL[1], subject_id=suggestion_id, payload={"gate": gate, "title": title, "summary": summary, "context": dict(context or {})})
        results = self._hooks.before(SUGGESTION_PROMOTE_TO_HITL[0], SUGGESTION_PROMOTE_TO_HITL[1], hook_ctx)
        if any((not r.ok or r.blocked) for r in results):
            return {"success": False, "error": "blocked by hook", "hook": [r.to_dict() for r in results]}
        request = await self.governance.promote_suggestion_to_hitl(
            suggestion_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
        )
        self._hooks.after(SUGGESTION_PROMOTE_TO_HITL[0], SUGGESTION_PROMOTE_TO_HITL[1], hook_ctx)
        self._hooks.event("suggestion", "promote_to_hitl", SUGGESTION_PROMOTED_TO_HITL_EVENT, {"suggestion_id": suggestion_id, "gate": gate, "request": request})
        return {"success": True, "data": request}

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        attach_ctx = HookContext(domain=SUGGESTION_ATTACH_REPLAY[0], action=SUGGESTION_ATTACH_REPLAY[1], subject_id=suggestion_id, payload={"replay": dict(replay or {})})
        self._hooks.before(SUGGESTION_ATTACH_REPLAY[0], SUGGESTION_ATTACH_REPLAY[1], attach_ctx)
        request = await self.governance.attach_suggestion_replay(suggestion_id, replay)
        self._hooks.after(SUGGESTION_ATTACH_REPLAY[0], SUGGESTION_ATTACH_REPLAY[1], attach_ctx)
        return {"success": True, "data": request}

    async def suggestion_approve(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, SUGGESTION_APPROVE_SUGGESTION[1], subject_id=suggestion_id, payload={"approver": approver, "notes": notes})
        record = await self.suggestion.approve_suggestion(suggestion_id, approver, notes)
        promoted: Dict[str, Any] | None = None
        if self.governance is not None:
            try:
                request = await self.governance.promote_suggestion_to_hitl(
                    suggestion_id,
                    gate="review",
                    title="",
                    summary=notes,
                    context={"approver": approver, "notes": notes, "source": "suggestion_approval"},
                )
                promoted = request.get("data", request) if isinstance(request, dict) else {"request_id": getattr(request, "request_id", None)}
            except Exception:
                promoted = None
        self._emit(HookPhase.AFTER, SUGGESTION_APPROVE_SUGGESTION[1], subject_id=suggestion_id, payload={"approval": record.to_dict(), "promotion": promoted})
        self._hooks.event("suggestion", "approve", SUGGESTION_APPROVAL_COMPLETED_EVENT, {"suggestion_id": suggestion_id, "approver": approver, "promotion": promoted})
        return {"success": True, "data": {"approval": record.to_dict(), "promotion": promoted}}

    async def suggestion_reject(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, SUGGESTION_REJECT_SUGGESTION[1], subject_id=suggestion_id, payload={"approver": approver, "notes": notes})
        record = await self.suggestion.reject_suggestion(suggestion_id, approver, notes)
        self._emit(HookPhase.AFTER, SUGGESTION_REJECT_SUGGESTION[1], subject_id=suggestion_id, payload={"record": record.to_dict()})
        self._hooks.event("suggestion", "reject", SUGGESTION_REJECTION_COMPLETED_EVENT, {"suggestion_id": suggestion_id, "approver": approver})
        return {"success": True, "data": record.to_dict()}

    async def suggestion_archive(self, suggestion_id: str) -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, SUGGESTION_ARCHIVE[1], subject_id=suggestion_id)
        await self.suggestion.archive_suggestion(suggestion_id)
        self._emit(HookPhase.AFTER, SUGGESTION_ARCHIVE[1], subject_id=suggestion_id)
        self._hooks.event("suggestion", "archive", SUGGESTION_ARCHIVED_EVENT, {"suggestion_id": suggestion_id})
        return {"success": True, "data": {"suggestion_id": suggestion_id, "status": "archived"}}

    async def create_suggestion_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        ctx = HookContext(domain=SUGGESTION_CAPTURE_EXECUTION_EVENT[0], action=SUGGESTION_CAPTURE_EXECUTION_EVENT[1], subject_id=str(event.get("suggestion_id") or ""), execution_id=str(event.get("run_id") or event.get("execution_id") or ""), payload=dict(event or {}))
        self._hooks.before(SUGGESTION_CAPTURE_EXECUTION_EVENT[0], SUGGESTION_CAPTURE_EXECUTION_EVENT[1], ctx)
        result = await self.suggestion.capture_from_execution_event(event)
        self._hooks.after(SUGGESTION_CAPTURE_EXECUTION_EVENT[0], SUGGESTION_CAPTURE_EXECUTION_EVENT[1], ctx)
        self._hooks.event("suggestion", "capture_execution_event", SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT, {"event": dict(event or {}), "result": result})
        return result


__all__ = ["SuggestionApplicationService"]
