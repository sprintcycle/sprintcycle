"""Suggestion analysis from observability facts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .suggestion.models import (
    Suggestion,
    SuggestionImpactScope,
    SuggestionSeverity,
    SuggestionSourceType,
    SuggestionStatus,
)


@dataclass
class SuggestionAnalyzer:
    """Derive suggestions from runtime facts."""

    def analyze_events(self, execution_id: str, events: Iterable[Dict[str, Any]]) -> List[Suggestion]:
        suggestions: List[Suggestion] = []
        for event in events:
            suggestion = self._analyze_event(execution_id, event)
            if suggestion is not None:
                suggestions.append(suggestion)
        return suggestions

    def _analyze_event(self, execution_id: str, event: Dict[str, Any]) -> Optional[Suggestion]:
        event_type = str(event.get("event_type") or event.get("type") or event.get("kind") or "").lower()
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else event
        if not event_type:
            return None
        if "failed" in event_type or event_type.endswith("_error"):
            return Suggestion(
                execution_id=execution_id,
                title=self._build_title(event_type, payload, "failure detected"),
                summary=self._build_summary(event, payload, "Failure detected in execution flow."),
                source_type=SuggestionSourceType.RUNTIME,
                severity=SuggestionSeverity.HIGH,
                impact_scope=SuggestionImpactScope.EXECUTION,
                status=SuggestionStatus.OPEN,
                root_cause=str(payload.get("error") or payload.get("message") or "Runtime failure"),
                proposed_action="Inspect the failing step, reproduce the issue, and apply a targeted fix.",
                evidence=[event],
                tags=["runtime", "failure"],
                metadata={"event_type": event_type},
            )
        if "timeout" in event_type:
            return Suggestion(
                execution_id=execution_id,
                title=self._build_title(event_type, payload, "timeout detected"),
                summary=self._build_summary(event, payload, "Timeout detected in execution flow."),
                source_type=SuggestionSourceType.RUNTIME,
                severity=SuggestionSeverity.MEDIUM,
                impact_scope=SuggestionImpactScope.EXECUTION,
                status=SuggestionStatus.OPEN,
                root_cause="Step or gate exceeded the configured timeout.",
                proposed_action="Review timeout settings and add a recovery or retry strategy.",
                evidence=[event],
                tags=["runtime", "timeout"],
                metadata={"event_type": event_type},
            )
        if "hitl" in event_type or "governance" in event_type:
            return Suggestion(
                execution_id=execution_id,
                title=self._build_title(event_type, payload, "governance observation"),
                summary=self._build_summary(event, payload, "Governance or HITL observation recorded."),
                source_type=SuggestionSourceType.HITL,
                severity=SuggestionSeverity.LOW,
                impact_scope=SuggestionImpactScope.EXECUTION,
                status=SuggestionStatus.OPEN,
                root_cause=str(payload.get("summary") or payload.get("note") or "Human-in-the-loop review required"),
                proposed_action="Review the gate outcome and decide whether a correction or replay is needed.",
                evidence=[event],
                tags=["hitl", "governance"],
                metadata={"event_type": event_type},
            )
        return None

    def _build_title(self, event_type: str, payload: Dict[str, Any], fallback: str) -> str:
        step_name = str(payload.get("step_name") or payload.get("sprint_name") or payload.get("title") or "").strip()
        if step_name:
            return f"{step_name}: {fallback}"
        return f"{event_type}: {fallback}"

    def _build_summary(self, event: Dict[str, Any], payload: Dict[str, Any], fallback: str) -> str:
        bits = [fallback]
        message = payload.get("message") or payload.get("summary") or payload.get("error")
        if message:
            bits.append(str(message))
        event_id = event.get("event_id") or payload.get("event_id")
        if event_id:
            bits.append(f"event_id={event_id}")
        return " | ".join(bits)


__all__ = ["SuggestionAnalyzer"]
