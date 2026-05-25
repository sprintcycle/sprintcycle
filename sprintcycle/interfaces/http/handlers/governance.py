"""Governance handler - API methods for governance operations."""

from __future__ import annotations

from typing import Any

from .services import ServiceAggregator


class GovernanceHandler:
    """Handler for governance-related API methods."""

    def __init__(self, services: ServiceAggregator):
        self._services = services

    async def governance_history(self, limit: int = 50) -> Any:
        return await self._services.governance_orchestration.history(limit=limit)

    async def governance_lifecycle(self, execution_id: str = "") -> Any:
        return await self._services.governance_orchestration.summary(execution_id=execution_id)

    async def governance_check(self, gate: str = "review") -> Any:
        return await self._services.governance_orchestration.governance_check(gate=gate)

    def architecture_check(self) -> Any:
        return self._services.governance_orchestration.architecture_check()
