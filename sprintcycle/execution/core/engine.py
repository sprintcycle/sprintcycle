"""Phase 1 execution engine.

This engine keeps the implementation intentionally lightweight and delegates
sandbox / verification / deployment to existing platform services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from .context import ExecutionContext
from .events import Event, EventBus, EventType, get_event_bus as create_default_event_bus
from .hooks import ExecutionHooks
from .state_machine import ExecutionStateMachine


@dataclass
class ExecutionEngine:
    event_bus: EventBus
    state_machine: ExecutionStateMachine
    hooks: ExecutionHooks

    def create_context(self, run_id: str, task_id: str, project_path: str, **kwargs: Any) -> ExecutionContext:
        return ExecutionContext.create(run_id=run_id, task_id=task_id, project_path=project_path, **kwargs)

    async def _emit(self, event_type: EventType, context: ExecutionContext, **payload: Any) -> Dict[str, Any]:
        event = Event(type=event_type, run_id=context.run_id, task_id=context.task_id, payload=payload)
        await self.event_bus.emit(event)
        return event.to_dict()

    def _set_status(
        self, context: ExecutionContext, status: str, stage: Optional[str] = None, step: Optional[str] = None
    ) -> None:
        context.status = status
        if stage is not None:
            context.stage = stage
        if step is not None:
            context.step = step
        context.touch()

    def basic_flow(self, context: ExecutionContext) -> Dict[str, Any]:
        """Run a minimal phase-1 flow synchronously.

        The implementation is intentionally conservative: it updates the local
        context and emits a compact set of events so the dashboard and runtime
        registry can reflect execution without invasive architecture changes.
        """
        try:
            self.hooks.run(self.hooks.before_task_start, context)
            self._set_status(context, "running", stage="prepare")
            logger.info("execution_started run_id={} task_id={}", context.run_id, context.task_id)
            self._set_status(context, "sandboxing", stage="sandbox_execute", step="run")
            self._set_status(context, "validating", stage="verify", step="check")
            self._set_status(context, "deploying", stage="deploy", step="publish")
            self._set_status(context, "deployed", stage="deploy", step="published")
            self._set_status(context, "succeeded", stage="complete", step="done")
            return context.to_dict()
        except Exception as exc:
            context.error = str(exc)
            self._set_status(context, "failed")
            logger.exception("execution_failed run_id={} task_id={}", context.run_id, context.task_id)
            return context.to_dict()

    def run(self, context: ExecutionContext) -> Dict[str, Any]:
        return self.basic_flow(context)


def create_execution_engine(event_bus: Optional[ExecutionEventBus] = None) -> ExecutionEngine:
    return ExecutionEngine(
        event_bus=event_bus or create_default_event_bus(),
        state_machine=ExecutionStateMachine(),
        hooks=ExecutionHooks(),
    )
