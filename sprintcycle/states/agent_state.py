"""Agent 状态定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentState:
    """Agent 状态数据"""
    agent_id: str
    agent_type: str
    status: AgentStatus = AgentStatus.IDLE
    current_task_id: Optional[str] = None
    completed_task_ids: List[str] = field(default_factory=list)
    failed_task_ids: List[str] = field(default_factory=list)
    total_duration_seconds: float = 0
    last_active_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_available(self) -> bool:
        """是否可用"""
        return self.status == AgentStatus.IDLE
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = len(self.completed_task_ids) + len(self.failed_task_ids)
        if total == 0:
            return 0.0
        return len(self.completed_task_ids) / total
