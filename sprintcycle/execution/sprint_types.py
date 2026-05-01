"""
Sprint Execution Types - 统一执行状态与结果类型

v0.9.1: 合并 TaskStatus/ExecutionStatus → ExecutionStatus
        合并 dispatcher_types 中的 TaskResult/SprintResult
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

from ..prd.models import PRDTask, PRDSprint


class ExecutionStatus(Enum):
    """统一执行状态枚举（v0.9.2: 合并 ExecutionStateStatus + PipelineStatus）"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    # 从 ExecutionStateStatus 合并
    COMPLETED = "completed"
    PAUSED = "paused"
    # 从 PipelineStatus 合并
    IDLE = "idle"
    PARTIAL = "partial"


# Backward compat aliases — will be removed in v1.0
TaskStatus = ExecutionStatus
ExecutionStateStatus = ExecutionStatus
PipelineStatus = ExecutionStatus


@dataclass
class TaskResult:
    """任务执行结果"""
    task: PRDTask
    sprint_name: str
    status: ExecutionStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task.task[:100] + "..." if len(self.task.task) > 100 else self.task.task,
            "agent": self.task.agent,
            "target": self.task.target,
            "status": self.status.value,
            "output": self.output[:500] if self.output else "",
            "error": self.error,
            "duration": self.duration,
        }


@dataclass
class SprintResult:
    """Sprint 执行结果"""
    sprint: PRDSprint
    status: ExecutionStatus
    task_results: List[TaskResult] = field(default_factory=list)
    duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
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
            "sprint_name": self.sprint.name,
            "status": self.status.value,
            "total_tasks": len(self.task_results),
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "success_rate": self.success_rate,
            "duration": self.duration,
            "task_results": [r.to_dict() for r in self.task_results],
        }
