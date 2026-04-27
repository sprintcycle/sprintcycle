"""Sprint 模型定义"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SprintStatus(Enum):
    """Sprint 状态"""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class SprintConfig:
    """Sprint 配置"""
    name: str
    goals: List[str]
    duration_days: int = 7
    auto_approve: bool = True
    verification_enabled: bool = True
    knowledge_injection: bool = True


@dataclass
class Sprint:
    """Sprint 模型"""
    index: int
    name: str
    goals: List[str]
    status: SprintStatus = SprintStatus.PENDING
    session_id: Optional[str] = None
    proposal_id: Optional[str] = None
    task_ids: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    verification_result: Optional[dict] = None
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "goals": self.goals,
            "status": self.status.value,
            "session_id": self.session_id,
            "proposal_id": self.proposal_id,
            "task_ids": self.task_ids,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }
