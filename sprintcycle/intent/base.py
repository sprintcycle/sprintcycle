"""
Intent 基类

定义所有意图处理器的通用接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..prd.models import PRD
from ..scheduler.dispatcher import SprintResult


@dataclass
class IntentResult:
    """意图执行结果"""
    success: bool
    prd: PRD
    completed_sprints: int = 0
    completed_tasks: int = 0
    total_sprints: int = 0
    total_tasks: int = 0
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    sprint_results: List[SprintResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "completed_sprints": self.completed_sprints,
            "completed_tasks": self.completed_tasks,
            "total_sprints": self.total_sprints,
            "total_tasks": self.total_tasks,
            "error": self.error,
            "details": self.details,
        }


class IntentHandler(ABC):
    """意图处理器基类"""
    
    def __init__(self):
        from ..scheduler.dispatcher import TaskDispatcher
        self.dispatcher = TaskDispatcher()
    
    @abstractmethod
    def execute(self, prd: PRD) -> IntentResult:
        """执行意图"""
        pass
    
    def validate_prd(self, prd: PRD) -> bool:
        """验证 PRD"""
        from ..prd.validator import PRDValidator
        result = PRDValidator().validate(prd)
        return result.is_valid
    
    def _build_result(
        self,
        success: bool,
        prd: PRD,
        sprint_results: List[SprintResult],
        error: Optional[str] = None,
    ) -> IntentResult:
        """构建执行结果"""
        completed_sprints = sum(
            1 for r in sprint_results 
            if r.status.value in ("success", "skipped")
        )
        completed_tasks = sum(r.success_count for r in sprint_results)
        
        return IntentResult(
            success=success,
            prd=prd,
            completed_sprints=completed_sprints,
            completed_tasks=completed_tasks,
            total_sprints=len(sprint_results),
            total_tasks=prd.total_tasks,
            error=error,
            sprint_results=sprint_results,
        )
