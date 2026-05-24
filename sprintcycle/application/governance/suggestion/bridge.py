"""Bridge execution observations to suggestion records."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .models import SuggestionStatus


class SuggestionBridge:
    def __init__(self, service: Any) -> None:
        self._service = service

    async def capture_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        execution_id = str(event.get("run_id") or event.get("execution_id") or "")
        if not execution_id:
            return {"success": False, "error": "execution_id required"}
        suggestions = self._service.analyzer.analyze_events(execution_id, [event])
        created = []
        for suggestion in suggestions:
            self._service.create(suggestion)
            created.append(suggestion.to_dict())
        return {"success": True, "data": {"execution_id": execution_id, "created": created, "total": len(created)}}

    async def promote_to_hitl(
        self,
        suggestion_id: str,
        *,
        gate: str = "review",
        title: str = "",
        summary: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        suggestion = self._service.get(suggestion_id)
        if suggestion is None:
            return {"success": False, "error": "suggestion not found"}
        suggestion.hitl_request_id = suggestion.hitl_request_id or suggestion_id
        suggestion.status = SuggestionStatus.REVIEWING
        return {
            "success": True,
            "data": {
                "suggestion_id": suggestion_id,
                "execution_id": suggestion.execution_id,
                "gate": gate,
                "title": title or suggestion.title,
                "summary": summary or suggestion.summary,
                "context": dict(context or {}),
                "hitl_request_id": suggestion.hitl_request_id,
            },
        }

    async def attach_replay_directive(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        suggestion = self._service.get(suggestion_id)
        if suggestion is None:
            return {"success": False, "error": "suggestion not found"}
        suggestion.replay_directive = dict(replay or {})
        return {
            "success": True,
            "data": {"suggestion_id": suggestion_id, "replay_directive": suggestion.replay_directive},
        }


__all__ = ["SuggestionBridge"]
