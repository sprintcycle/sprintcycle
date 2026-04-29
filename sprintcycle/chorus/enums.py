"""
chorus.enums - 枚举定义
"""
from enum import Enum


class ToolType(Enum):
    """工具类型枚举"""
    CURSOR = "cursor"
    CLAUDE = "claude"
    AIDER = "aider"


class AgentType(Enum):
    """Agent 类型枚举"""
    CODER = "coder"
    REVIEWER = "reviewer"
    ARCHITECT = "architect"
    TESTER = "tester"
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


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
