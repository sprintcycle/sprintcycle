"""Execution core for SprintCycle domain layer.

Domain primitives for execution:
- ExecutionContext: 单次任务运行的执行上下文
- ExecutionState: 执行状态标识符
- ExecutionStateMachine: 轻量级状态机
"""

from sprintcycle.domain.execution.core.context import ExecutionContext
from sprintcycle.domain.execution.core.events import Event as ExecutionEvent, EventBus as ExecutionEventBus, get_event_bus as create_default_event_bus
from sprintcycle.domain.execution.core.state_machine import ExecutionState, ExecutionStateMachine

__all__ = [
    "ExecutionContext",
    "ExecutionEvent",
    "ExecutionEventBus",
    "ExecutionState",
    "ExecutionStateMachine",
    "create_default_event_bus",
]
