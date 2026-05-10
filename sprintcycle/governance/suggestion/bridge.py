"""Bridge execution/observability events into suggestion inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import uuid4

from .models import Suggestion
from .service import SuggestionService


@dataclass
class SuggestionBridge:
    service: SuggestionService

    async def capture_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        kind = str(event.get("kind") or event.get("type") or event.get("event_type") or "")
        if kind not in {"execution_failed", "task_failed", "stage_failed", "step_failed", "error"}:
            return {"success": False, "error": "event does not require suggestion"}

        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        suggestion = Suggestion(
            suggestion_id=str(event.get("suggestion_id") or f"sg_{uuid4().hex}"),
            source_type="observability",
            source_id=str(event.get("event_id") or event.get("run_id") or data.get("run_id") or ""),
            title=f"Execution issue: {kind}",
            summary=str(data.get("message") or data.get("error") or event.get("message") or "execution issue"),
            details=str(data or event),
            impact_scope=["execution", "observability"],
            severity="high",
            metadata={
                "run_id": event.get("run_id") or data.get("run_id"),
                "kind": kind,
                "source_event": event,
            },
        )
        created = await self.service.capture_suggestion(suggestion)
        return {"success": True, "data": created.to_dict()}
