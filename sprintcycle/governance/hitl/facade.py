"""Governance-side HITL facade.

This module belongs to the governance layer and wraps the HITL service for
human-in-the-loop gates, decisions, corrections, and replay directives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ...execution.events import Event, EventType, get_execution_event_backend
from . import (
    HitlCorrection,
    HitlGate,
    HitlReplayDirective,
    HitlService,
    create_hitl_coordinator,
    evaluate_hitl_policy,
)


@dataclass
class HitlEvent:
    event_type: str
    execution_id: str
    scope: str
    title: str
    summary: str = ""
    gate: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    risk_level: str = "low"


@dataclass
class HitlGateResult:
    should_trigger: bool
    triggered: bool
    request_id: Optional[str] = None
    decision: Optional[str] = None
    policy: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HitlRequestResult:
    request_id: str
    execution_id: str
    gate: str
    status: str
    decision: Optional[str] = None
    note: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HitlFacade:
    """Governance HITL facade."""

    def __init__(self, service: Optional[HitlService], *, config: Any) -> None:
        self._service = service
        self._config = config

    @property
    def service(self) -> Optional[HitlService]:
        return self._service

    async def observe(
        self,
        *,
        event_type: str,
        execution_id: str,
        scope: str,
        title: str,
        summary: str = "",
        gate: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        risk_level: str = "low",
    ) -> None:
        event = HitlEvent(
            event_type=event_type,
            execution_id=execution_id,
            scope=scope,
            title=title,
            summary=summary,
            gate=gate,
            context=context or {},
            metadata=metadata or {},
            risk_level=risk_level,
        )
        await self._emit_observation_event(event)

    async def enter_gate(
        self,
        *,
        execution_id: str,
        gate: str,
        title: str,
        summary: str,
        context: Dict[str, Any],
        risk_level: str = "medium",
        timeout_seconds: Optional[int] = None,
    ) -> HitlGateResult:
        policy = evaluate_hitl_policy(
            gate=gate,
            context={**context, "summary": summary, "risk_level": risk_level},
            config=self._config,
        )
        result = HitlGateResult(
            should_trigger=bool(policy.should_trigger),
            triggered=False,
            policy=dict(policy.metadata or {}),
        )
        if not policy.should_trigger:
            return result
        if self._service is None:
            result.metadata["reason"] = "hitl_service_unavailable"
            return result
        request = await self._service.start_request(
            execution_id=execution_id,
            gate=HitlGate(gate),
            title=title,
            summary=summary,
            context=context,
            risk_level=policy.risk_level,
            timeout_seconds=timeout_seconds or policy.timeout_seconds,
        )
        decision = await self._service.wait_for_decision(
            execution_id=request.execution_id,
            gate=HitlGate(gate),
            title=title,
            summary=summary,
            context=context,
            risk_level=policy.risk_level,
            timeout_seconds=timeout_seconds or policy.timeout_seconds,
        )
        result.triggered = True
        result.request_id = request.request_id
        result.decision = decision.value
        result.metadata["request"] = request.to_dict()
        return result

    async def request_human_decision(
        self,
        *,
        execution_id: str,
        gate: str,
        title: str,
        summary: str,
        context: Dict[str, Any],
        risk_level: str = "medium",
        timeout_seconds: Optional[int] = None,
        wait: bool = True,
    ) -> HitlRequestResult:
        if self._service is None:
            return HitlRequestResult(
                request_id="",
                execution_id=execution_id,
                gate=gate,
                status="unavailable",
                metadata={"reason": "hitl_service_unavailable"},
            )
        request = await self._service.start_request(
            execution_id=execution_id,
            gate=HitlGate(gate),
            title=title,
            summary=summary,
            context=context,
            risk_level=risk_level,
            timeout_seconds=timeout_seconds,
        )
        decision = None
        status = request.status
        if wait:
            decision = await self._service.wait_for_decision(
                execution_id=execution_id,
                gate=HitlGate(gate),
                title=title,
                summary=summary,
                context=context,
                risk_level=risk_level,
                timeout_seconds=timeout_seconds,
            )
            status = "resolved"
        return HitlRequestResult(
            request_id=request.request_id,
            execution_id=execution_id,
            gate=gate,
            status=status,
            decision=decision.value if decision else None,
            context=context,
            metadata={"request": request.to_dict()},
        )

    async def submit_decision(
        self,
        request_id: str,
        decision: str,
        note: Optional[str] = None,
        *,
        correction: Optional[HitlCorrection] = None,
        replay: Optional[HitlReplayDirective] = None,
    ) -> Optional[Dict[str, Any]]:
        if self._service is None:
            return None
        rec = await self._service.submit_decision(
            request_id,
            decision,
            note,
            correction=correction,
            replay=replay,
        )
        return rec.to_dict() if rec else None

    async def get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        if self._service is None:
            return None
        return await self._service.get_request(request_id)

    async def list_pending(self, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self._service is None:
            return []
        return await self._service.list_pending(execution_id)

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if self._service is None:
            return []
        return await self._service.list_history(execution_id, limit)

    async def summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        pending = await self.list_pending(execution_id)
        history = await self.list_history(execution_id, limit)
        latest = history[-1] if history else None
        return {
            "execution_id": execution_id,
            "pending_count": len(pending),
            "history_count": len(history),
            "latest_request": latest,
            "has_service": self._service is not None,
        }

    async def apply_context_patch(
        self,
        *,
        request_id: str,
        context: Dict[str, Any],
        correction: Optional[HitlCorrection] = None,
        replay: Optional[HitlReplayDirective] = None,
    ) -> Dict[str, Any]:
        if self._service is None:
            return context
        current = await self._service.get_request(request_id)
        if current is None:
            return context
        if correction is not None:
            await self._service.submit_correction(request_id, correction)
        if replay is not None:
            await self._service.request_retry(request_id, replay)
        updated = await self._service.get_request(request_id)
        if updated and isinstance(updated.get("applied_context"), dict):
            return updated["applied_context"]
        return context

    async def _emit_observation_event(self, event: HitlEvent) -> None:
        bus = get_execution_event_backend()
        try:
            await bus.emit(
                Event(
                    type=EventType.GOVERNANCE_GATE,
                    data={
                        "event_type": event.event_type,
                        "execution_id": event.execution_id,
                        "scope": event.scope,
                        "title": event.title,
                        "summary": event.summary,
                        "gate": event.gate,
                        "context": event.context,
                        "metadata": event.metadata,
                        "risk_level": event.risk_level,
                    },
                )
            )
        except Exception:
            return None


def create_hitl_facade(project_path: str, config: Any) -> HitlFacade:
    coord = create_hitl_coordinator(project_path, config, get_execution_event_backend())
    service = HitlService(coord) if coord is not None else None
    return HitlFacade(service, config=config)
