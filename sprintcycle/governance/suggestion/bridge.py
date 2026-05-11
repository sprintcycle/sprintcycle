"""Compatibility bridge for suggestion event capture."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .service import SuggestionService


@dataclass
class SuggestionBridge:
    service: SuggestionService

    async def capture_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return await self.service.capture_from_execution_event(event)
