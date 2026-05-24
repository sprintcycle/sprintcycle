"""Unified hook protocol for SprintCycle.

This module defines the shared hook actions, event names, context/result
objects, and the registry/runner used by services to invoke hooks and emit
domain events consistently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional

EXECUTION_START = ("execution", "start")
EXECUTION_STARTED_EVENT = "execution.started"
EXECUTION_START_FAILED_EVENT = "execution.start_failed"
SUGGESTION_REVIEW = ("suggestion", "review")
SUGGESTION_REVIEW_SUGGESTION = ("suggestion", "review_suggestion")
SUGGESTION_APPROVE_SUGGESTION = ("suggestion", "approve_suggestion")
SUGGESTION_REJECT_SUGGESTION = ("suggestion", "reject_suggestion")
SUGGESTION_PROMOTE_TO_HITL = ("suggestion", "promote_to_hitl")
SUGGESTION_ATTACH_REPLAY = ("suggestion", "attach_replay")
SUGGESTION_ARCHIVE = ("suggestion", "archive")
SUGGESTION_CAPTURE_EXECUTION_EVENT = ("suggestion", "capture_execution_event")
SUGGESTION_REVIEWED_EVENT = "suggestion.reviewed"
SUGGESTION_REVIEW_RECORD_EVENT = "suggestion.review_recorded"
SUGGESTION_APPROVED_EVENT = "suggestion.approved"
SUGGESTION_REJECTED_EVENT = "suggestion.rejected"
SUGGESTION_PROMOTED_TO_HITL_EVENT = "suggestion.promoted_to_hitl"
SUGGESTION_APPROVAL_COMPLETED_EVENT = "suggestion.approval_completed"
SUGGESTION_REJECTION_COMPLETED_EVENT = "suggestion.rejection_completed"
SUGGESTION_ARCHIVED_EVENT = "suggestion.archived"
SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT = "suggestion.captured_from_execution_event"
GOVERNANCE_CHECK = ("governance", "check")
GOVERNANCE_CHECKED_EVENT = "governance.checked"
GOVERNANCE_CHECK_FAILED_EVENT = "governance.check_failed"

HOOK_EVENTS = {
    "execution.start": (EXECUTION_STARTED_EVENT, EXECUTION_START_FAILED_EVENT),
    "suggestion.review": (SUGGESTION_REVIEWED_EVENT,),
    "suggestion.review_suggestion": (SUGGESTION_REVIEW_RECORD_EVENT,),
    "suggestion.approve_suggestion": (SUGGESTION_APPROVED_EVENT, SUGGESTION_APPROVAL_COMPLETED_EVENT),
    "suggestion.reject_suggestion": (SUGGESTION_REJECTED_EVENT,),
    "suggestion.promote_to_hitl": (SUGGESTION_PROMOTED_TO_HITL_EVENT,),
    "suggestion.attach_replay": (),
    "suggestion.archive": (SUGGESTION_ARCHIVED_EVENT,),
    "suggestion.capture_execution_event": (SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT,),
    "governance.check": (GOVERNANCE_CHECKED_EVENT, GOVERNANCE_CHECK_FAILED_EVENT),
}

HOOK_ACTIONS = {
    "execution.start": EXECUTION_START,
    "suggestion.review": SUGGESTION_REVIEW,
    "suggestion.review_suggestion": SUGGESTION_REVIEW_SUGGESTION,
    "suggestion.approve": SUGGESTION_APPROVE_SUGGESTION,
    "suggestion.approve_suggestion": SUGGESTION_APPROVE_SUGGESTION,
    "suggestion.reject": SUGGESTION_REJECT_SUGGESTION,
    "suggestion.reject_suggestion": SUGGESTION_REJECT_SUGGESTION,
    "suggestion.promote_to_hitl": SUGGESTION_PROMOTE_TO_HITL,
    "suggestion.attach_replay": SUGGESTION_ATTACH_REPLAY,
    "suggestion.archive": SUGGESTION_ARCHIVE,
    "suggestion.capture_execution_event": SUGGESTION_CAPTURE_EXECUTION_EVENT,
    "governance.check": GOVERNANCE_CHECK,
}


def hook_action(domain: str, action: str) -> tuple[str, str]:
    key = f"{domain}.{action}"
    if key not in HOOK_ACTIONS:
        raise KeyError(f"unknown hook action: {key}")
    return HOOK_ACTIONS[key]


def hook_events(domain: str, action: str) -> tuple[str, ...]:
    return HOOK_EVENTS.get(f"{domain}.{action}", ())


class HookPhase(str, Enum):
    BEFORE = "before"
    AFTER = "after"
    FAILED = "failed"


class HookPolicy(str, Enum):
    FAIL_OPEN = "fail_open"
    FAIL_CLOSED = "fail_closed"
    COMPENSATE = "compensate"


@dataclass
class HookContext:
    domain: str
    action: str
    subject_id: str = ""
    execution_id: str = ""
    project_path: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "action": self.action,
            "subject_id": self.subject_id,
            "execution_id": self.execution_id,
            "project_path": self.project_path,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "trace_id": self.trace_id,
        }


@dataclass
class HookResult:
    ok: bool = True
    blocked: bool = False
    mutated_context: Optional[Dict[str, Any]] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "blocked": self.blocked,
            "mutated_context": self.mutated_context,
            "message": self.message,
            "data": self.data,
        }


HookHandler = Callable[[HookContext], HookResult | Dict[str, Any] | None]
EventHandler = Callable[[Dict[str, Any]], Any]


@dataclass
class HookDefinition:
    name: str
    domain: str
    action: str
    phase: HookPhase
    policy: HookPolicy = HookPolicy.FAIL_OPEN
    handler: HookHandler | None = None
    owner: str = "internal"


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: List[HookDefinition] = []
        self._event_handlers: Dict[str, List[EventHandler]] = {}

    def register(self, hook: HookDefinition) -> None:
        self._hooks.append(hook)

    def register_event_handler(self, event_name: str, handler: EventHandler) -> None:
        self._event_handlers.setdefault(event_name, []).append(handler)

    def matching(self, *, domain: str, action: str, phase: HookPhase) -> Iterable[HookDefinition]:
        return [h for h in self._hooks if h.domain == domain and h.action == action and h.phase == phase]

    def emit_domain_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        for handler in self._event_handlers.get(event_name, []):
            try:
                handler(dict(payload))
            except Exception:
                continue

    def emit(self, *, domain: str, action: str, phase: HookPhase, context: HookContext) -> List[HookResult]:
        """Convenience shortcut that creates a HookRunner and delegates."""
        runner = HookRunner(self)
        return runner.emit(domain=domain, action=action, phase=phase, context=context)


class HookRunner:
    def __init__(self, registry: HookRegistry | None) -> None:
        self.registry = registry

    def action(self, domain: str, action: str) -> tuple[str, str]:
        return hook_action(domain, action)

    def events(self, domain: str, action: str) -> tuple[str, ...]:
        return hook_events(domain, action)

    def _coerce_result(self, raw: HookResult | Dict[str, Any] | None) -> HookResult:
        if isinstance(raw, HookResult):
            return raw
        if isinstance(raw, dict):
            return HookResult(
                ok=bool(raw.get("ok", True)),
                blocked=bool(raw.get("blocked", False)),
                mutated_context=raw.get("mutated_context"),
                message=str(raw.get("message") or ""),
                data=raw.get("data"),
            )
        return HookResult()

    def _apply_mutation(self, context: HookContext, mutated: Dict[str, Any]) -> None:
        payload = mutated.get("payload")
        metadata = mutated.get("metadata")
        if payload:
            context.payload.update(dict(payload or {}))
        if metadata:
            context.metadata.update(dict(metadata or {}))

    def emit(self, *, domain: str, action: str, phase: HookPhase, context: HookContext) -> List[HookResult]:
        if self.registry is None:
            return []
        results: List[HookResult] = []
        for hook in self.registry.matching(domain=domain, action=action, phase=phase):
            if hook.handler is None:
                continue
            try:
                raw = hook.handler(context)
                result = self._coerce_result(raw)
            except Exception as exc:
                result = HookResult(
                    ok=False,
                    blocked=phase == HookPhase.BEFORE and hook.policy == HookPolicy.FAIL_CLOSED,
                    message=str(exc),
                )
            results.append(result)
            if result.mutated_context:
                self._apply_mutation(context, dict(result.mutated_context))
            if (
                phase == HookPhase.BEFORE
                and hook.policy == HookPolicy.FAIL_CLOSED
                and (not result.ok or result.blocked)
            ):
                break
        return results

    def before(self, domain: str, action: str, context: HookContext) -> List[HookResult]:
        return self.emit(domain=domain, action=action, phase=HookPhase.BEFORE, context=context)

    def after(self, domain: str, action: str, context: HookContext) -> List[HookResult]:
        return self.emit(domain=domain, action=action, phase=HookPhase.AFTER, context=context)

    def failed(self, domain: str, action: str, context: HookContext) -> List[HookResult]:
        return self.emit(domain=domain, action=action, phase=HookPhase.FAILED, context=context)

    def event(self, domain: str, action: str, event_name: str, payload: Dict[str, Any]) -> None:
        if self.registry is None:
            return
        if event_name in hook_events(domain, action):
            self.registry.emit_domain_event(event_name, payload)


__all__ = [
    "EXECUTION_START",
    "EXECUTION_STARTED_EVENT",
    "EXECUTION_START_FAILED_EVENT",
    "HOOK_ACTIONS",
    "HOOK_EVENTS",
    "GOVERNANCE_CHECK",
    "GOVERNANCE_CHECKED_EVENT",
    "GOVERNANCE_CHECK_FAILED_EVENT",
    "HookContext",
    "HookDefinition",
    "HookHandler",
    "HookPhase",
    "HookPolicy",
    "HookRegistry",
    "HookResult",
    "HookRunner",
    "SUGGESTION_APPROVE_SUGGESTION",
    "SUGGESTION_APPROVAL_COMPLETED_EVENT",
    "SUGGESTION_APPROVED_EVENT",
    "SUGGESTION_ARCHIVE",
    "SUGGESTION_ARCHIVED_EVENT",
    "SUGGESTION_ATTACH_REPLAY",
    "SUGGESTION_CAPTURE_EXECUTION_EVENT",
    "SUGGESTION_CAPTURED_FROM_EXECUTION_EVENT",
    "SUGGESTION_PROMOTE_TO_HITL",
    "SUGGESTION_PROMOTED_TO_HITL_EVENT",
    "SUGGESTION_REJECT_SUGGESTION",
    "SUGGESTION_REJECTION_COMPLETED_EVENT",
    "SUGGESTION_REJECTED_EVENT",
    "SUGGESTION_REVIEW",
    "SUGGESTION_REVIEWED_EVENT",
    "SUGGESTION_REVIEW_RECORD_EVENT",
    "hook_action",
    "hook_events",
]
