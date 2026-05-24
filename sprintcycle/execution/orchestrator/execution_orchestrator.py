"""Execution orchestration thin facade for backward compatibility.

This module provides a thin wrapper over SprintExecutor for legacy code paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sprintcycle.domain.models import ReleasePlan, SprintDefinition
from ..core.protocols import ExecutionContext
from .sprint_executor import SprintExecutor
from ..core.sprint_types import SprintResult


@dataclass
class ExecutionRunRequest:
    """Normalized request for an execution run."""

    execution_id: Optional[str] = None
    resume: bool = False
    mode: str = "normal"
    sprint_index_offset: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    release_plan: Optional[ReleasePlan] = None


@dataclass
class ExecutionRunResult:
    """Result returned by the orchestration layer."""

    execution_id: str
    sprint_results: List[SprintResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(
            getattr(result, "status", None) and getattr(result.status, "value", str(result.status)) == "success"
            for result in self.sprint_results
        )


class ExecutionOrchestrator:
    """Thin orchestration facade over SprintExecutor."""

    def __init__(self, executor: SprintExecutor) -> None:
        self._executor = executor

    @property
    def executor(self) -> SprintExecutor:
        return self._executor

    async def run(
        self,
        sprints: List[SprintDefinition],
        request: Optional[ExecutionRunRequest] = None,
        *,
        context: Optional[ExecutionContext | Dict[str, Any]] = None,
    ) -> ExecutionRunResult:
        req = request or ExecutionRunRequest()
        normalized_context = ExecutionContext.from_any(context).to_dict() if context is not None else {}
        normalized_context.update(req.context or {})
        execution_id = req.execution_id or normalized_context.get("execution_id")
        results = await self._executor.execute_sprints(
            sprints,
            mode=req.mode,
            context=normalized_context,
            execution_id=execution_id,
            resume=req.resume,
            release_plan=req.release_plan,
            sprint_index_offset=req.sprint_index_offset,
        )
        return ExecutionRunResult(
            execution_id=str(execution_id or getattr(self._executor, "_execution_id", "")), sprint_results=results
        )


__all__ = ["ExecutionOrchestrator", "ExecutionRunRequest", "ExecutionRunResult"]
