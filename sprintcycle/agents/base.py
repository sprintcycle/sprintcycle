"""
Base Agent - 所有 Agent 的基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class AgentCapability(Enum):
    """Agent 能力枚举"""
    CODING = "coding"
    REVIEW = "review"
    DESIGN = "design"
    TESTING = "testing"
    VERIFICATION = "verification"
    BROWSER_AUTOMATION = "browser_automation"
    DIAGNOSTIC = "diagnostic"
    OPTIMIZATION = "optimization"


@dataclass
class AgentConfig:
    """Agent 配置"""
    name: str
    description: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_retries: int = 3
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Agent 基类
    
    所有 Specialized Agent 都应继承此类
    """
    
    name: str = "BaseAgent"
    description: str = "Base Agent"
    capabilities: List[AgentCapability] = []
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config
        self._initialized = False
        self._execution_count = 0
        self._last_execution: Optional[datetime] = None
    
    @abstractmethod
    async def initialize(self):
        """初始化 Agent（异步）"""
        pass
    
    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务描述
            context: 执行上下文
            
        Returns:
            执行结果字典
        """
        pass
    
    async def cleanup(self):
        """清理资源"""
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def execution_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        return {
            "total_executions": self._execution_count,
            "last_execution": self._last_execution.isoformat() if self._last_execution else None
        }
    
    def _record_execution(self):
        """记录执行"""
        self._execution_count += 1
        self._last_execution = datetime.now()
    
    async def pre_execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行前钩子"""
        self._record_execution()
        return {"ready": True}
    
    async def post_execute(self, result: Dict[str, Any]):
        """执行后钩子"""
        pass
    
    def validate_task(self, task: str) -> bool:
        """验证任务是否适合此 Agent"""
        return True
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        capabilities_str = ", ".join(c.value for c in self.capabilities)
        return f"""你是 {self.name}。
        
描述: {self.description}

能力: {capabilities_str}

你擅长执行与此能力相关的任务。"""
