"""Task 状态定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


@dataclass
class TaskState:
    """任务状态数据"""
    task_id: str
    name: str
    description: str = ""
    agent_type: str = ""
    status: TaskStatus = TaskStatus.PENDING
    sprint_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None
    files_changed: Dict[str, List[str]] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_terminal(self) -> bool:
        """是否处于终态"""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)
