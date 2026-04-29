"""
Base Agent - 所有 Agent 的基类

包含:
- BaseAgent: Agent 基类（ABC）
- AgentCapability: Agent 能力枚举
- AgentConfig: Agent 配置数据类
- VerificationType: 验证类型枚举
- VerificationSeverity: 验证严重级别枚举
- VerificationResult: 验证结果数据类
- PageVerificationReport: 页面验证报告数据类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


# ============ Agent 核心定义 ============

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
    
    所有 Specialized Agent 都应继承此类并实现:
    - initialize(): 异步初始化
    - execute(): 异步执行
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
    
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        capabilities_str = ", ".join(c.value for c in self.capabilities)
        return f"""你是 {self.name}。

描述: {self.description}

能力: {capabilities_str}

你擅长执行与此能力相关的任务。"""


# ============ 验证相关类型定义 ============

class VerificationType(Enum):
    """验证类型"""
    PAGE_LOAD = "page_load"
    ELEMENT_EXISTS = "element_exists"
    TEXT_CONTENT = "text_content"
    CLICK_INTERACTION = "click_interaction"
    FORM_FILL = "form_fill"
    NAVIGATION = "navigation"
    ACCESSIBILITY = "accessibility"
    VISUAL = "visual"


class VerificationSeverity(Enum):
    """问题严重级别"""
    HIGH = "high"      # 关键功能不可用
    MEDIUM = "medium"  # 用户体验问题
    LOW = "low"        # 优化建议


@dataclass
class VerificationResult:
    """验证结果"""
    verification_type: VerificationType
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: VerificationSeverity = VerificationSeverity.LOW
    screenshot_path: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.verification_type.value,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value,
            "screenshot": self.screenshot_path,
            "suggestions": self.suggestions
        }


@dataclass
class PageVerificationReport:
    """页面验证报告"""
    url: str
    page_title: str
    load_time_ms: float
    verifications: List[VerificationResult]
    overall_score: float  # 0-100
    passed_count: int = 0
    failed_count: int = 0
    high_severity_count: int = 0
    
    def __post_init__(self):
        self.passed_count = sum(1 for v in self.verifications if v.passed)
        self.failed_count = sum(1 for v in self.verifications if not v.passed)
        self.high_severity_count = sum(1 for v in self.verifications 
                                        if not v.passed and v.severity == VerificationSeverity.HIGH)
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "page_title": self.page_title,
            "load_time_ms": self.load_time_ms,
            "verifications": [v.to_dict() for v in self.verifications],
            "overall_score": self.overall_score,
            "passed": self.passed_count,
            "failed": self.failed_count,
            "high_severity": self.high_severity_count
        }
    
    def summary(self) -> str:
        """生成摘要报告"""
        emoji = "✅" if self.overall_score >= 80 else "⚠️" if self.overall_score >= 60 else "❌"
        lines = [
            f"{emoji} **页面验证报告: {self.url}**",
            f"📊 得分: **{self.overall_score:.0f}/100**",
            f"✅ 通过: {self.passed_count} | ❌ 失败: {self.failed_count}",
            ""
        ]
        
        if self.verifications:
            lines.append("### 详细结果")
            for v in self.verifications:
                status = "✅" if v.passed else "❌"
                lines.append(f"{status} [{v.verification_type.value}] {v.message}")
                if v.suggestions:
                    for s in v.suggestions:
                        lines.append(f"   💡 {s}")
        
        return "\n".join(lines)


# Re-export from types.py for backward compatibility
__all__ = [
    # Agent core
    "BaseAgent",
    "AgentCapability",
    "AgentConfig",
    
    # Verification types (formerly in types.py)
    "VerificationType",
    "VerificationSeverity",
    "VerificationResult",
    "PageVerificationReport",
]
