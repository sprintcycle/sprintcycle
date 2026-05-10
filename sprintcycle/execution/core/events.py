"""Minimal execution event model and in-memory event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4


class ExecutionEventType(str, Enum):
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    STAGE_STARTED = "stage_started"
    STAGE_FINISHED = "stage_finished"
    STEP_STARTED = "step_started"
    STEP_FINISHED = "step_finished"
    TASK_SUCCEEDED = "task_succeeded"
    TASK_FAILED = "task_failed"
    TASK_DEPLOYED = "task_deployed"


@dataclass
class ExecutionEvent:
    type: ExecutionEventType
    run_id: str
    task_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }


EventHandler = Callable[[ExecutionEvent], Awaitable[None] | None]


class ExecutionEventBus:
    def __init__(self) -> None:
        self._handlers: Dict[ExecutionEventType, List[EventHandler]] = {}
        self.events: List[ExecutionEvent] = []

    def on(self, event_type: ExecutionEventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def emit(self, event: ExecutionEvent) -> ExecutionEvent:
        self.events.append(event)
        for handler in self._handlers.get(event.type, []):
            result = handler(event)
            if hasattr(result, "__await__"):
                await result  # type: ignore[misc]
        return event

    def list_events(self) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self.events]


_DEFAULT_EVENT_BUS = ExecutionEventBus()


def create_default_event_bus() -> ExecutionEventBus:
    return _DEFAULT_EVENT_BUS
