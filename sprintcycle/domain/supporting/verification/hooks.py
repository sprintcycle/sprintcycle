from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from sprintcycle.domain.generic.interfaces import Event, EventType, ExecutionEventBackendProtocol

from sprintcycle.domain.generic.models import ReleasePlan, SprintDefinition
from .config import VerificationConfig
from .engine import VerificationEngine
from .reporter import VerificationReportAdapter


class VerificationSprintHooks:
    """验证钩子 - 使用协议接口"""
    
    def __init__(self, project_path: str, config: Any, event_bus: Optional[ExecutionEventBackendProtocol] = None):
        self._project_path = project_path
        self._config = config
        self._event_bus = event_bus

    def _enabled(self) -> bool:
        return bool(getattr(self._config, "verification_enabled", True))

    def _build_context(
        self,
        *,
        sprint_index: int,
        sprint: SprintDefinition,
        release_plan: Optional[ReleasePlan] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        context = {
            "sprint_index": sprint_index,
            "sprint": sprint,
            "release_plan": release_plan,
            "project_path": self._project_path,
        }
        context.update(kwargs)
        return context

    def on_sprint_completed(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        release_plan: Optional[ReleasePlan] = None,
        **kwargs: Any,
    ) -> None:
        if not self._enabled():
            return

        logger.info("Running verification for sprint {}", sprint_index)
        context = self._build_context(
            sprint_index=sprint_index,
            sprint=sprint,
            release_plan=release_plan,
            **kwargs,
        )
        engine = VerificationEngine(config=self._config)
        report = engine.verify(context)
        
        adapter = VerificationReportAdapter()
        adapter.adapt(report)

        if self._event_bus:
            event = Event(
                event_type=EventType.SPRINT_COMPLETED,
                timestamp=__import__("datetime").datetime.now(),
                data={"sprint_index": sprint_index, "report": report.to_dict()},
                source="verification",
            )
            self._event_bus.publish(event)


__all__ = ["VerificationSprintHooks"]
