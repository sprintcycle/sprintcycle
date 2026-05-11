"""Unified hook protocol for SprintCycle.

The protocol standardizes before/after/failed hooks and domain events so the
system can avoid ad-hoc hook-like calls scattered across services.

Semantics
- Who can hook: code registered in HookRegistry, typically internal services,
  bootstrap/composition roots, or approved plugins.
- Timing: before_* runs before the main action, after_* runs on success,
  on_*_failed runs on failure, emit_domain_event publishes domain events.
- Failure policy:
  - fail_closed: block the main flow when a before hook fails or blocks.
  - fail_open: log/observe and continue.
  - compensate: use a follow-up action in the caller or subscriber.
- Flow impact: only before hooks with fail_closed are allowed to stop the main
  flow by default.
- Return consumption: before hooks are consumed by the caller; after/failed
  hooks are generally telemetry side effects; domain events are observed by
  subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional


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

    def emit(self, *, domain: str, action: str, phase: HookPhase, context: HookContext) -> List[HookResult]:
        results: List[HookResult] = []
        for hook in self.matching(domain=domain, action=action, phase=phase):
            if hook.handler is None:
                continue
            raw = hook.handler(context)
            result = raw if isinstance(raw, HookResult) else HookResult(**raw) if isinstance(raw, dict) else HookResult()
            results.append(result)
            if phase == HookPhase.BEFORE and hook.policy == HookPolicy.FAIL_CLOSED and (not result.ok or result.blocked):
                break
        return results

    def emit_domain_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        for handler in self._event_handlers.get(event_name, []):
            handler(dict(payload))


__all__ = [
    "EventHandler",
    "HookContext",
    "HookDefinition",
    "HookHandler",
    "HookPhase",
    "HookPolicy",
    "HookRegistry",
    "HookResult",
]
