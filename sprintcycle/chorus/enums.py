"""
chorus.enums - 统一枚举定义

所有枚举类型的统一存放位置，消除重复定义。

使用说明：
- 推荐直接从此模块导入枚举类型
- 为保持向后兼容，旧导入路径仍可用
"""

from enum import Enum


class ToolType(Enum):
    """工具类型枚举"""
    CURSOR = "cursor"
    CLAUDE = "claude"
    AIDER = "aider"


class AgentType(str, Enum):
    """
    Agent 类型枚举 - 合并自 models.py 和 chorus/enums.py
    
    包含所有 Agent 类型：
    - 基础类型：CODER, REVIEWER, TESTER
    - 计划类型：PLANNER, EXECUTOR, ORCHESTRATOR
    - Chorus 扩展：ARCHITECT, DIAGNOSTIC, UI_VERIFY
    """
    # 基础类型
    CODER = "coder"
    REVIEWER = "reviewer"
    TESTER = "tester"
    # 计划/执行类型
    PLANNER = "planner"
    EXECUTOR = "executor"
    ORCHESTRATOR = "orchestrator"
    # Chorus 扩展类型
    ARCHITECT = "architect"
    DIAGNOSTIC = "diagnostic"
    UI_VERIFY = "ui_verify"
    
    @classmethod
    def from_string(cls, value: str) -> "AgentType":
        """安全转换，未知类型自动映射到 CODER"""
        if not value:
            return cls.CODER
        try:
            return cls(value.lower())
        except ValueError:
            from loguru import logger
            logger.info(f"未知 agent 类型 '{value}'，自动映射到 CODER")
            return cls.CODER


class TaskStatus(str, Enum):
    """
    任务状态枚举 - 合并自 models.py, chorus/enums.py, sprint_logger.py
    
    包含所有状态：
    - 基础状态：PENDING, RUNNING
    - 结果状态：SUCCESS, COMPLETED, FAILED, SKIPPED
    - 特殊状态：RETRYING
    """
    # 基础状态
    PENDING = "pending"
    RUNNING = "running"
    # 结果状态（SUCCESS 和 COMPLETED 含义相同，保留两者兼容）
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    # 特殊状态
    RETRYING = "retrying"


class SprintStatus(str, Enum):
    """
    Sprint 状态枚举 - 合并自 models.py 和 sprint_logger.py
    
    包含所有状态：
    - 计划状态：PLANNED
    - 执行状态：IN_PROGRESS, PENDING, RUNNING
    - 结果状态：SUCCESS, COMPLETED, PARTIAL, FAILED, CANCELLED
    """
    # 计划状态
    PLANNED = "planned"
    # 执行状态
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RUNNING = "running"
    # 结果状态
    SUCCESS = "success"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewSeverity(str, Enum):
    """审查严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueSeverity(str, Enum):
    """问题严重级别"""
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class IssueType(str, Enum):
    """问题类型"""
    CODE = "code"
    STYLE = "style"
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"


class HealthStatus(str, Enum):
    """健康检查状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ErrorCategory(Enum):
    """错误类别枚举"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    UNKNOWN = "unknown"
