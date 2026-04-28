"""Sprint 状态定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SprintStatus(Enum):
    """Sprint 状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SprintState:
    """Sprint 状态数据"""
    sprint_id: str
    name: str
    status: SprintStatus = SprintStatus.PENDING
    goals: List[str] = field(default_factory=list)
    task_ids: List[str] = field(default_factory=list)
    completed_task_ids: List[str] = field(default_factory=list)
    failed_task_ids: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def progress(self) -> float:
        """Sprint 进度"""
        if not self.task_ids:
            return 0.0
        return len(self.completed_task_ids) / len(self.task_ids)
    
    @property
    def is_terminal(self) -> bool:
        """是否处于终态"""
        return self.status in (SprintStatus.COMPLETED, SprintStatus.FAILED, SprintStatus.CANCELLED)
