"""HITL 应用服务。"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .coordinator import HitlCoordinator
from .decision_normalize import validate_hitl_decision_for_submit
from .types import HitlGate


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

    async def modify(self, request_id: str, note: Optional[str] = None):
        return await self._submit(request_id, "request_changes", note)

    async def resume(self, request_id: str, note: Optional[str] = None):
        return await self._submit(request_id, "approve", note)

    async def _submit(self, request_id: str, decision: str, note: Optional[str]):
        canon = validate_hitl_decision_for_submit(decision)
        if canon is None:
            return None
        return await self._coord.submit_decision(request_id, canon, note)
