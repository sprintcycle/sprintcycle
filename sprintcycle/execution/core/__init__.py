"""Execution core for SprintCycle phase 1.

Provides a lightweight orchestration layer that keeps the main architecture
non-invasive while exposing a single internal entry point for task execution.
"""

from __future__ import annotations

from .context import ExecutionContext
from .engine import ExecutionEngine, create_execution_engine
from .events import Event as ExecutionEvent, EventBus as ExecutionEventBus, get_event_bus as create_default_event_bus
from .hooks import ExecutionHooks
from .state_machine import ExecutionState, ExecutionStateMachine

__all__ = [
    "ExecutionContext",
    "ExecutionEngine",
    "ExecutionEvent",
    "ExecutionEventBus",
    "ExecutionHooks",
    "ExecutionState",
    "ExecutionStateMachine",
    "create_default_event_bus",
    "create_execution_engine",
]
