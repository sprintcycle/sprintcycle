"""Execution subdomain aggregates.

This module provides DDD aggregates for the Execution subdomain:
- ReleasePlanAggregate: Manages multi-sprint execution
- SprintAggregate: Manages single sprint execution
- TaskResult: Value object for task execution results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from sprintcycle.domain.generic.interfaces.types import ExecutionStatus


# =============================================================================
# Value Objects
# =============================================================================


@dataclass(frozen=True)
class TaskResult:
    """
    Task execution result value object.

    Immutable representation of a single task's execution outcome.
    """

    task_id: str
    description: str
    agent: str
    status: ExecutionStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description[:100] + "..." if len(self.description) > 100 else self.description,
            "agent": self.agent,
            "status": self.status.value,
            "output": self.output[:500] if len(self.output) > 500 else self.output,
            "error": self.error,
            "duration": self.duration,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


@dataclass(frozen=True)
class SprintResult:
    """
    Sprint execution result value object.

    Immutable representation of a single sprint's execution outcome.
    """

    sprint_id: str
    sprint_name: str
    status: ExecutionStatus
    task_results: Tuple[TaskResult, ...]
    duration: float = 0.0
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == ExecutionStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.task_results if r.status == ExecutionStatus.FAILED)

    @property
    def success_rate(self) -> float:
        if not self.task_results:
            return 0.0
        return self.success_count / len(self.task_results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_id": self.sprint_id,
            "sprint_name": self.sprint_name,
            "status": self.status.value,
            "task_count": len(self.task_results),
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": self.success_rate,
            "duration": self.duration,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "task_results": [r.to_dict() for r in self.task_results],
        }


# =============================================================================
# Sprint Aggregate
# =============================================================================


class SprintAggregate:
    """
    Sprint aggregate root.

    Manages the execution lifecycle of a single sprint, including:
    - Task execution tracking
    - Sprint status management
    - Results aggregation

    **Immutable Updates:**
    All state-modifying methods return new instances.
    """

    def __init__(
        self,
        sprint_id: str,
        sprint_name: str,
        tasks: Tuple[Dict[str, Any], ...],
        status: ExecutionStatus = ExecutionStatus.PENDING,
        task_results: Tuple[TaskResult, ...] = (),
        current_task_index: int = 0,
        started_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
    ):
        self._sprint_id = sprint_id
        self._sprint_name = sprint_name
        self._tasks = tasks
        self._status = status
        self._task_results = task_results
        self._current_task_index = current_task_index
        self._started_at = started_at
        self._ended_at = ended_at

    # Identity
    @property
    def sprint_id(self) -> str:
        return self._sprint_id

    @property
    def sprint_name(self) -> str:
        return self._sprint_name

    # State
    @property
    def status(self) -> ExecutionStatus:
        return self._status

    @property
    def is_terminal(self) -> bool:
        return self._status in (
            ExecutionStatus.SUCCESS,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        )

    @property
    def is_running(self) -> bool:
        return self._status == ExecutionStatus.RUNNING

    # Task management
    @property
    def pending_tasks(self) -> List[Dict[str, Any]]:
        """Get list of tasks not yet executed."""
        completed = len(self._task_results)
        return list(self._tasks[completed:])

    @property
    def total_tasks(self) -> int:
        return len(self._tasks)

    @property
    def completed_tasks(self) -> int:
        return len(self._task_results)

    @property
    def current_task_index(self) -> int:
        return self._current_task_index

    @property
    def current_task(self) -> Optional[Dict[str, Any]]:
        """Get the current task to execute."""
        if self._current_task_index < len(self._tasks):
            return self._tasks[self._current_task_index]
        return None

    @property
    def success_rate(self) -> float:
        if not self._task_results:
            return 0.0
        success = sum(1 for r in self._task_results if r.status == ExecutionStatus.SUCCESS)
        return success / len(self._task_results)

    # Commands
    def start(self) -> "SprintAggregate":
        """Start the sprint."""
        if self._status != ExecutionStatus.PENDING:
            raise ValueError(f"Cannot start sprint in status: {self._status}")
        return SprintAggregate(
            sprint_id=self._sprint_id,
            sprint_name=self._sprint_name,
            tasks=self._tasks,
            status=ExecutionStatus.RUNNING,
            task_results=self._task_results,
            current_task_index=self._current_task_index,
            started_at=datetime.now(),
            ended_at=None,
        )

    def record_task_result(self, result: TaskResult) -> "SprintAggregate":
        """Record a task result and advance to next task."""
        new_results = self._task_results + (result,)
        new_index = self._current_task_index + 1

        # Determine sprint status
        new_status = self._status
        if new_index >= len(self._tasks):
            all_success = all(r.status == ExecutionStatus.SUCCESS for r in new_results)
            new_status = ExecutionStatus.SUCCESS if all_success else ExecutionStatus.COMPLETED

        terminal_statuses = {"success", "failed", "cancelled"}
        is_terminal = new_status.value in terminal_statuses

        return SprintAggregate(
            sprint_id=self._sprint_id,
            sprint_name=self._sprint_name,
            tasks=self._tasks,
            status=new_status,
            task_results=new_results,
            current_task_index=new_index,
            started_at=self._started_at,
            ended_at=datetime.now() if is_terminal else None,
        )

    def complete(self, status: ExecutionStatus = ExecutionStatus.SUCCESS) -> "SprintAggregate":
        """Complete the sprint with given status."""
        if self._status not in (ExecutionStatus.RUNNING, ExecutionStatus.PENDING):
            raise ValueError(f"Cannot complete sprint in status: {self._status}")
        return SprintAggregate(
            sprint_id=self._sprint_id,
            sprint_name=self._sprint_name,
            tasks=self._tasks,
            status=status,
            task_results=self._task_results,
            current_task_index=self._current_task_index,
            started_at=self._started_at,
            ended_at=datetime.now(),
        )

    def to_result(self) -> SprintResult:
        """Convert to SprintResult value object."""
        return SprintResult(
            sprint_id=self._sprint_id,
            sprint_name=self._sprint_name,
            status=self._status,
            task_results=self._task_results,
            duration=(self._ended_at - self._started_at).total_seconds() if self._started_at and self._ended_at else 0.0,
            started_at=self._started_at.isoformat() if self._started_at else None,
            ended_at=self._ended_at.isoformat() if self._ended_at else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_id": self._sprint_id,
            "sprint_name": self._sprint_name,
            "status": self._status.value,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": len(self.pending_tasks),
            "current_task_index": self._current_task_index,
            "success_rate": self.success_rate,
            "is_terminal": self.is_terminal,
        }


# =============================================================================
# ReleasePlan Aggregate
# =============================================================================


class ReleasePlanAggregate:
    """
    ReleasePlan aggregate root.

    Manages the execution of a complete release plan with multiple sprints:
    - Sprint orchestration
    - Overall success rate calculation
    - Governance coordination

    **Immutable Updates:**
    All state-modifying methods return new instances.
    """

    def __init__(
        self,
        release_plan_id: str,
        project_name: str,
        project_path: str,
        sprints: Tuple[SprintAggregate, ...],
        mode: str = "normal",
        sprint_results: Tuple[SprintResult, ...] = (),
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self._release_plan_id = release_plan_id
        self._project_name = project_name
        self._project_path = project_path
        self._sprints = sprints
        self._mode = mode
        self._sprint_results = sprint_results
        self._started_at = started_at
        self._completed_at = completed_at

    # Identity
    @property
    def release_plan_id(self) -> str:
        return self._release_plan_id

    @property
    def project_name(self) -> str:
        return self._project_name

    @property
    def project_path(self) -> str:
        return self._project_path

    # State
    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_terminal(self) -> bool:
        """All sprints completed."""
        return all(s.is_terminal for s in self._sprints)

    @property
    def is_running(self) -> bool:
        """Any sprint is running."""
        return any(s.is_running for s in self._sprints)

    # Sprint management
    @property
    def sprints(self) -> Tuple[SprintAggregate, ...]:
        return self._sprints

    @property
    def sprint_count(self) -> int:
        return len(self._sprints)

    @property
    def total_tasks(self) -> int:
        return sum(s.total_tasks for s in self._sprints)

    @property
    def completed_tasks(self) -> int:
        return sum(s.completed_tasks for s in self._sprints)

    @property
    def overall_success_rate(self) -> float:
        """Calculate overall success rate across all sprints."""
        if not self._sprint_results:
            return 0.0
        total_success = sum(r.success_count for r in self._sprint_results)
        total_tasks = sum(len(r.task_results) for r in self._sprint_results)
        if total_tasks == 0:
            return 0.0
        return total_success / total_tasks

    @property
    def current_sprint(self) -> Optional[SprintAggregate]:
        """Get the current sprint (first non-terminal)."""
        for sprint in self._sprints:
            if not sprint.is_terminal:
                return sprint
        return None

    @property
    def sprint_results(self) -> Tuple[SprintResult, ...]:
        return self._sprint_results

    # Commands
    def start(self) -> "ReleasePlanAggregate":
        """Start the release plan."""
        if self._started_at:
            raise ValueError("Release plan already started")
        return ReleasePlanAggregate(
            release_plan_id=self._release_plan_id,
            project_name=self._project_name,
            project_path=self._project_path,
            sprints=self._sprints,
            mode=self._mode,
            sprint_results=self._sprint_results,
            started_at=datetime.now(),
            completed_at=None,
        )

    def record_sprint_result(self, result: SprintResult) -> "ReleasePlanAggregate":
        """Record a sprint result."""
        new_results = self._sprint_results + (result,)
        return ReleasePlanAggregate(
            release_plan_id=self._release_plan_id,
            project_name=self._project_name,
            project_path=self._project_path,
            sprints=self._sprints,
            mode=self._mode,
            sprint_results=new_results,
            started_at=self._started_at,
            completed_at=datetime.now() if all(s.is_terminal for s in self._sprints) else None,
        )

    def complete(self) -> "ReleasePlanAggregate":
        """Complete the release plan."""
        return ReleasePlanAggregate(
            release_plan_id=self._release_plan_id,
            project_name=self._project_name,
            project_path=self._project_path,
            sprints=self._sprints,
            mode=self._mode,
            sprint_results=self._sprint_results,
            started_at=self._started_at,
            completed_at=datetime.now(),
        )

    def to_governance_input(self) -> Dict[str, Any]:
        """Convert to governance subdomain input format."""
        return {
            "release_plan_id": self._release_plan_id,
            "project_name": self._project_name,
            "project_path": self._project_path,
            "sprint_count": self.sprint_count,
            "total_tasks": self.total_tasks,
            "overall_success_rate": self.overall_success_rate,
            "sprint_results": [s.to_dict() for s in self._sprint_results],
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "release_plan_id": self._release_plan_id,
            "project_name": self._project_name,
            "project_path": self._project_path,
            "mode": self._mode,
            "sprint_count": self.sprint_count,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "overall_success_rate": self.overall_success_rate,
            "is_terminal": self.is_terminal,
            "is_running": self.is_running,
            "current_sprint": self.current_sprint.to_dict() if self.current_sprint else None,
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_sprint_aggregate(
    sprint_name: str,
    tasks: List[Dict[str, Any]],
) -> SprintAggregate:
    """Create a new SprintAggregate from task definitions."""
    return SprintAggregate(
        sprint_id=f"sprint-{uuid4()}",
        sprint_name=sprint_name,
        tasks=tuple(tasks),
        status=ExecutionStatus.PENDING,
        task_results=(),
        current_task_index=0,
    )


def create_release_plan_aggregate(
    project_name: str,
    project_path: str,
    sprint_definitions: List[Dict[str, Any]],
    mode: str = "normal",
) -> ReleasePlanAggregate:
    """Create a new ReleasePlanAggregate from sprint definitions."""
    sprints = tuple(
        create_sprint_aggregate(sprint["name"], sprint.get("tasks", []))
        for sprint in sprint_definitions
    )
    return ReleasePlanAggregate(
        release_plan_id=f"release-{uuid4()}",
        project_name=project_name,
        project_path=project_path,
        sprints=sprints,
        mode=mode,
    )


__all__ = [
    "TaskResult",
    "SprintResult",
    "SprintAggregate",
    "ReleasePlanAggregate",
    "create_sprint_aggregate",
    "create_release_plan_aggregate",
]
