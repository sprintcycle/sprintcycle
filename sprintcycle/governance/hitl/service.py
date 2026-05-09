"""HITL 应用服务。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .coordinator import HitlCoordinator
from .decision_normalize import validate_hitl_decision_for_submit
from .types import HitlCorrection, HitlGate, HitlReplayDirective


class HitlService:
    def __init__(self, coordinator: HitlCoordinator) -> None:
        self._coord = coordinator

    async def start_request(
        self,
        *,
        execution_id: str,
        gate: HitlGate,
        title: str,
        summary: str,
        context: Dict[str, Any],
        risk_level: str = "medium",
        timeout_seconds: Optional[int] = None,
    ):
        return await self._coord.create_request(
            execution_id=execution_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
            risk_level=risk_level,
            timeout_seconds=timeout_seconds,
        )

    async def approve(self, request_id: str, note: Optional[str] = None):
        return await self._submit(request_id, "approve", note)

    async def reject(self, request_id: str, note: Optional[str] = None):
        return await self._submit(request_id, "reject", note)

    async def modify(self, request_id: str, note: Optional[str] = None, correction: Optional[HitlCorrection] = None):
        return await self._submit(request_id, "modify", note, correction=correction)

    async def request_changes(
        self,
        request_id: str,
        note: Optional[str] = None,
        correction: Optional[HitlCorrection] = None,
    ):
        return await self._submit(request_id, "request_changes", note, correction=correction)

    async def retry(self, request_id: str, replay: HitlReplayDirective, note: Optional[str] = None):
        return await self._submit(request_id, "retry", note, replay=replay)

    async def resume(self, request_id: str, note: Optional[str] = None):
        return await self._submit(request_id, "resume", note)

    async def get_request(self, request_id: str):
        return await self._coord.get_request(request_id)

    async def list_pending(self, execution_id: Optional[str] = None):
        return await self._coord.list_pending(execution_id)

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50):
        return await self._coord.list_history(execution_id, limit)

    async def _submit(
        self,
        request_id: str,
        decision: str,
        note: Optional[str],
        *,
        correction: Optional[HitlCorrection] = None,
        replay: Optional[HitlReplayDirective] = None,
    ):
        canon = validate_hitl_decision_for_submit(decision)
        if canon is None:
            return None
        return await self._coord.submit_decision(request_id, canon, note, correction=correction, replay=replay)
