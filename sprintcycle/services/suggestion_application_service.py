"""Suggestion application service.

Keeps suggestion lifecycle and promotion flows out of the SprintCycle facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..governance.facade import GovernanceFacade
from ..governance.suggestion import SuggestionFacade
from ..hooks import HookContext, HookPhase, HookPolicy, HookRegistry, HookResult


@dataclass
class SuggestionApplicationService:
    suggestion: SuggestionFacade
    governance: Optional[GovernanceFacade] = None
    hooks: Optional[HookRegistry] = None

    def _emit(self, phase: HookPhase, action: str, *, subject_id: str = "", execution_id: str = "", payload: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        if self.hooks is None:
            return
        context = HookContext(
            domain="suggestion",
            action=action,
            subject_id=subject_id,
            execution_id=execution_id,
            payload=dict(payload or {}),
            metadata=dict(metadata or {}),
        )
        self.hooks.emit(domain="suggestion", action=action, phase=phase, context=context)

    async def suggestion_review(self, suggestion_id: str) -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, "review", subject_id=suggestion_id)
        context = await self.suggestion.review_suggestion(suggestion_id)
        self._emit(HookPhase.AFTER, "review", subject_id=suggestion_id, payload=context.to_dict())
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.reviewed", {"suggestion_id": suggestion_id, "data": context.to_dict()})
        return {"success": True, "data": context.to_dict()}

    async def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        self._emit(HookPhase.BEFORE, "review_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"reviewer": reviewer, "notes": notes})
        record = await self.governance.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)
        self._emit(HookPhase.AFTER, "review_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record})
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.review_recorded", {"execution_id": execution_id, "suggestion_id": suggestion_id, "record": record})
        return {"success": True, "data": record}

    async def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        self._emit(HookPhase.BEFORE, "approve_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"approver": approver, "notes": notes})
        record = await self.governance.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)
        self._emit(HookPhase.AFTER, "approve_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record})
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.approved", {"execution_id": execution_id, "suggestion_id": suggestion_id, "approver": approver, "notes": notes})
        return {"success": True, "data": record}

    async def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        self._emit(HookPhase.BEFORE, "reject_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"rejected_by": rejected_by, "notes": notes})
        record = await self.governance.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)
        self._emit(HookPhase.AFTER, "reject_suggestion", subject_id=suggestion_id, execution_id=execution_id, payload={"record": record})
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.rejected", {"execution_id": execution_id, "suggestion_id": suggestion_id, "rejected_by": rejected_by, "notes": notes})
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
        hook_ctx = HookContext(domain="suggestion", action="promote_to_hitl", subject_id=suggestion_id, payload={"gate": gate, "title": title, "summary": summary, "context": dict(context or {})})
        if self.hooks is not None:
            results = self.hooks.emit(domain="suggestion", action="promote_to_hitl", phase=HookPhase.BEFORE, context=hook_ctx)
            if any((not r.ok or r.blocked) for r in results):
                return {"success": False, "error": "blocked by hook", "hook": [r.to_dict() for r in results]}
        request = await self.governance.promote_suggestion_to_hitl(
            suggestion_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
        )
        if self.hooks is not None:
            self.hooks.emit(domain="suggestion", action="promote_to_hitl", phase=HookPhase.AFTER, context=hook_ctx)
            self.hooks.emit_domain_event("suggestion.promoted_to_hitl", {"suggestion_id": suggestion_id, "gate": gate, "request": request})
        return {"success": True, "data": request}

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        if self.governance is None:
            return {"success": False, "error": "Governance is disabled"}
        if self.hooks is not None:
            self.hooks.emit(domain="suggestion", action="attach_replay", phase=HookPhase.BEFORE, context=HookContext(domain="suggestion", action="attach_replay", subject_id=suggestion_id, payload={"replay": dict(replay or {})}))
        request = await self.governance.attach_suggestion_replay(suggestion_id, replay)
        if self.hooks is not None:
            self.hooks.emit(domain="suggestion", action="attach_replay", phase=HookPhase.AFTER, context=HookContext(domain="suggestion", action="attach_replay", subject_id=suggestion_id, payload={"replay": dict(replay or {})}))
        return {"success": True, "data": request}

    async def suggestion_approve(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, "approve", subject_id=suggestion_id, payload={"approver": approver, "notes": notes})
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
        self._emit(HookPhase.AFTER, "approve", subject_id=suggestion_id, payload={"approval": record.to_dict(), "promotion": promoted})
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.approval_completed", {"suggestion_id": suggestion_id, "approver": approver, "promotion": promoted})
        return {"success": True, "data": {"approval": record.to_dict(), "promotion": promoted}}

    async def suggestion_reject(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, "reject", subject_id=suggestion_id, payload={"approver": approver, "notes": notes})
        record = await self.suggestion.reject_suggestion(suggestion_id, approver, notes)
        self._emit(HookPhase.AFTER, "reject", subject_id=suggestion_id, payload={"record": record.to_dict()})
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.rejection_completed", {"suggestion_id": suggestion_id, "approver": approver})
        return {"success": True, "data": record.to_dict()}

    async def suggestion_archive(self, suggestion_id: str) -> Dict[str, Any]:
        self._emit(HookPhase.BEFORE, "archive", subject_id=suggestion_id)
        await self.suggestion.archive_suggestion(suggestion_id)
        self._emit(HookPhase.AFTER, "archive", subject_id=suggestion_id)
        if self.hooks is not None:
            self.hooks.emit_domain_event("suggestion.archived", {"suggestion_id": suggestion_id})
        return {"success": True, "data": {"suggestion_id": suggestion_id, "status": "archived"}}

    async def create_suggestion_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        ctx = HookContext(domain="suggestion", action="capture_execution_event", subject_id=str(event.get("suggestion_id") or ""), execution_id=str(event.get("run_id") or event.get("execution_id") or ""), payload=dict(event or {}))
        if self.hooks is not None:
            self.hooks.emit(domain="suggestion", action="capture_execution_event", phase=HookPhase.BEFORE, context=ctx)
        result = await self.suggestion.capture_from_execution_event(event)
        if self.hooks is not None:
            self.hooks.emit(domain="suggestion", action="capture_execution_event", phase=HookPhase.AFTER, context=ctx)
            self.hooks.emit_domain_event("suggestion.captured_from_execution_event", {"event": dict(event or {}), "result": result})
        return result


__all__ = ["SuggestionApplicationService"]
