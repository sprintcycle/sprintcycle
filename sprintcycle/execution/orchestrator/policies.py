"""Sprint 编排层策略。

将 Sprint 级评估、测量与持久化从 SprintOrchestrator 中拆分，便于替换与测试。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ...domain.evolution.measurement import MeasurementResult
from ...application.release_plan.models import ReleasePlan, SprintDefinition
from ..sprint_types import ExecutionStatus, SprintResult


@dataclass
class SprintEvaluationResult:
    success: bool
    should_continue: bool = True
    should_retry: bool = False
    reason: str = ""


class SprintEvaluator:
    def evaluate(self, result: SprintResult) -> SprintEvaluationResult:
        if result.status == ExecutionStatus.FAILED:
            return SprintEvaluationResult(
                success=False, should_continue=True, should_retry=True, reason="sprint_failed"
            )
        return SprintEvaluationResult(success=True, should_continue=True, should_retry=False, reason="ok")


class SprintMeasurementPolicy:
    async def measure(
        self,
        orchestrator: Any,
        release_plan: ReleasePlan,
        sprint_index: int,
        sprint: Optional[SprintDefinition],
        sprint_result: Optional[SprintResult],
    ) -> Optional[MeasurementResult]:
        return await orchestrator._post_sprint_measurement(
            release_plan,
            sprint_index=sprint_index,
            sprint=sprint,
            sprint_result=sprint_result,
        )


class SprintPersistencePolicy:
    def persist(
        self,
        orchestrator: Any,
        release_plan: ReleasePlan,
        sprint_index: int,
        sprint: SprintDefinition,
        sprint_result: SprintResult,
        measurement: Optional[MeasurementResult],
    ) -> None:
        from ..knowledge.sprint_knowledge_card import persist_sprint_outcome_card

        persist_sprint_outcome_card(
            project_path=orchestrator._project_root,
            config=orchestrator.config,
            release_plan=release_plan,
            sprint_index=sprint_index,
            sprint=sprint,
            sprint_result=sprint_result,
            measurement=measurement,
        )


__all__ = ["SprintEvaluator", "SprintMeasurementPolicy", "SprintPersistencePolicy", "SprintEvaluationResult"]
