"""执行层接口协议"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sprintcycle.domain.generic.models import SprintDefinition, SprintBacklogItem


class ExecutionPlannerProtocol(ABC):
    """执行规划器接口"""
    
    @abstractmethod
    def plan_sprint(self, sprint: SprintDefinition) -> List[SprintBacklogItem]:
        """规划 Sprint"""
        ...
    
    @abstractmethod
    def estimate_effort(self, item: SprintBacklogItem) -> float:
        """估算工作量"""
        ...


class TaskExecutorProtocol(ABC):
    """任务执行器接口"""
    
    @abstractmethod
    def execute(self, task: SprintBacklogItem, context: Dict[str, Any]) -> "TaskResult":
        """执行任务"""
        ...


class TaskResult:
    """任务结果"""
    def __init__(self, success: bool, output: str, error: Optional[str] = None):
        self.success = success
        self.output = output
        self.error = error


__all__ = [
    "ExecutionPlannerProtocol",
    "TaskExecutorProtocol",
    "TaskResult",
]
