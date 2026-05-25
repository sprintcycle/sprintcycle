"""HITL handler - API methods for human-in-the-loop operations."""

from __future__ import annotations

from typing import Any, Optional

from .services import ServiceAggregator


class HitlHandler:
    """Handler for HITL (Human-in-the-Loop) related API methods."""

    def __init__(self, services: ServiceAggregator):
        self._services = services

    def hitl_pending(self, execution_id: Optional[str] = None) -> Any:
        return self._services.execution_lifecycle.hitl_pending(execution_id)

    def hitl_history(self, execution_id: Optional[str] = None, limit: int = 50) -> Any:
        return self._services.execution_lifecycle.hitl_history(execution_id, limit)

    def hitl_show(self, request_id: str) -> Any:
        return self._services.execution_lifecycle.hitl_show(request_id)

    def hitl_submit(self, request_id: str, decision: str, note: Optional[str] = None) -> Any:
        return self._services.execution_lifecycle.hitl_submit(request_id, decision, note)
