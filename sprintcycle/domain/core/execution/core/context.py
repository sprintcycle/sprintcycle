"""执行上下文类型。

用于替代 SprintExecutor / SprintOrchestrator 中散落的 dict context，
保留兼容字段，同时给 task / sprint 两层循环提供更明确的结构化输入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sprintcycle.domain.generic.models import ReleasePlan


@dataclass
class TaskExecutionContext:
    project_path: str = "."
    sprint_name: str = ""
    sprint_index: int = 0
    coding_engine: str = "cursor"
    quality_level: str = "L1"
    release_plan: Optional[ReleasePlan] = None
    release_plan_name: str = ""
    release_plan_id: str = ""
    architecture_design: Optional[str] = None
    dependencies: Dict[str, Any] = field(default_factory=dict)
    codebase_context: Dict[str, Any] = field(default_factory=dict)
    task_guidance: str = ""
    verify_fix_notes: str = ""
    improvement_suggestions: list[str] = field(default_factory=list)
    retry_from_failure: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)

    def to_agent_context_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "project_path": self.project_path,
            "sprint_name": self.sprint_name,
            "sprint_index": self.sprint_index,
            "coding_engine": self.coding_engine,
            "quality_level": self.quality_level,
            "release_plan": self.release_plan,
            "release_plan_name": self.release_plan_name,
            "release_plan_id": self.release_plan_id,
            "architecture_design": self.architecture_design,
            "dependencies": self.dependencies,
            "task_guidance": self.task_guidance,
            "verify_fix_notes": self.verify_fix_notes,
            "improvement_suggestions": self.improvement_suggestions,
            "retry_from_failure": self.retry_from_failure,
            "config": self.config,
            "metadata": self.metadata,
        }
        data.update(self.codebase_context)
        return data

    def copy_with(self, **kwargs: Any) -> "TaskExecutionContext":
        data = self.__dict__.copy()
        data.update(kwargs)
        return TaskExecutionContext(**data)


@dataclass
class SprintExecutionContext:
    project_path: str = "."
    release_plan: Optional[ReleasePlan] = None
    release_plan_name: str = ""
    release_plan_id: str = ""
    coding_engine: str = "aider"
    quality_level: str = "L1"
    execution_id: str = ""
    sprint_name: str = ""
    sprint_index: int = 0
    project_goals: str = ""
    previous_feedback: Dict[str, Any] = field(default_factory=dict)
    improvement_suggestions: list[str] = field(default_factory=list)
    retry_feedback: Dict[str, Any] = field(default_factory=dict)
    retry_from_failure: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "project_path": self.project_path,
            "release_plan": self.release_plan,
            "release_plan_name": self.release_plan_name,
            "release_plan_id": self.release_plan_id,
            "coding_engine": self.coding_engine,
            "quality_level": self.quality_level,
            "execution_id": self.execution_id,
            "sprint_name": self.sprint_name,
            "sprint_index": self.sprint_index,
            "project_goals": self.project_goals,
            "previous_feedback": self.previous_feedback,
            "improvement_suggestions": self.improvement_suggestions,
            "retry_feedback": self.retry_feedback,
            "retry_from_failure": self.retry_from_failure,
        }
        data.update(self.extra)
        return data

    def copy_with(self, **kwargs: Any) -> "SprintExecutionContext":
        data = self.__dict__.copy()
        data.update(kwargs)
        return SprintExecutionContext(**data)


__all__ = ["TaskExecutionContext", "SprintExecutionContext"]
