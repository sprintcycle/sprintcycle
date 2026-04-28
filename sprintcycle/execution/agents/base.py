"""
Agent 执行器基类 - 定义 Agent 执行器抽象架构

包含：
- AgentContext: 执行上下文
- AgentResult: 执行结果（含 feedback 字段）
- AgentExecutor: 抽象基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class AgentType(Enum):
    """Agent 类型枚举"""
    CODER = "coder"
    EVOLVER = "evolver"
    TESTER = "tester"
    REVIEWER = "reviewer"
    CUSTOM = "custom"


@dataclass
class AgentContext:
    """Agent 执行上下文"""
    prd_id: str = ""
    prd_name: str = ""
    project_goals: str = ""
    sprint_name: str = ""
    sprint_index: int = 0
    iteration: int = 1
    dependencies: Dict[str, Any] = field(default_factory=dict)
    codebase_context: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    feedback_history: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_feedback(self, feedback: str) -> None:
        self.feedback_history.append(feedback)
    
    def get_dependency(self, key: str, default: Any = None) -> Any:
        return self.dependencies.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "prd_id": self.prd_id,
            "prd_name": self.prd_name,
            "sprint_name": self.sprint_name,
            "sprint_index": self.sprint_index,
            "iteration": self.iteration,
            "dependencies": self.dependencies,
            "feedback_history": self.feedback_history,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    artifacts: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    feedback: Optional[str] = None
    agent_type: AgentType = AgentType.CUSTOM
    task_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def add_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value
    
    def add_metric(self, key: str, value: Any) -> None:
        self.metrics[key] = value
    
    def set_feedback(self, feedback: str) -> None:
        self.feedback = feedback
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "duration": self.duration,
            "artifacts": self.artifacts,
            "metrics": self.metrics,
            "feedback": self.feedback,
            "agent_type": self.agent_type.value,
            "task_name": self.task_name,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_error(cls, error: str, agent_type: AgentType = AgentType.CUSTOM) -> "AgentResult":
        return cls(
            success=False,
            error=error,
            agent_type=agent_type,
        )


class AgentExecutor(ABC):
    """Agent 执行器抽象基类"""
    
    def __init__(self):
        self._name = self.__class__.__name__
    
    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        pass
    
    async def execute(self, task: str, context: AgentContext) -> AgentResult:
        import logging
        logger = logging.getLogger(self._name)
        
        if not self._validate(task):
            return AgentResult.from_error(
                f"任务验证失败: {task[:50]}...",
                self.agent_type
            )
        
        await self._before_execute(task, context)
        
        import time
        start_time = time.time()
        
        try:
            result = await self._do_execute(task, context)
            result.duration = time.time() - start_time
            result.agent_type = self.agent_type
            result.task_name = task
            logger.info(f"Agent {self.agent_type.value} 执行成功")
        except Exception as e:
            logger.error(f"Agent {self.agent_type.value} 执行失败: {e}")
            result = AgentResult.from_error(str(e), self.agent_type)
            result.duration = time.time() - start_time
            result.task_name = task
        
        await self._after_execute(result, context)
        return result
    
    def _validate(self, task: str) -> bool:
        if not task or not task.strip():
            return False
        return True
    
    async def _before_execute(self, task: str, context: AgentContext) -> None:
        pass
    
    async def _after_execute(self, result: AgentResult, context: AgentContext) -> None:
        if result.feedback and context:
            context.add_feedback(result.feedback)
    
    @abstractmethod
    async def _do_execute(self, task: str, context: AgentContext) -> AgentResult:
        pass


__all__ = [
    "AgentType",
    "AgentContext",
    "AgentResult",
    "AgentExecutor",
]
