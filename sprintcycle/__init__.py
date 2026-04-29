"""
SprintCycle - AI 驱动的敏捷开发迭代框架

版本: v0.7.4
"""

__version__ = "0.7.6"
__author__ = "SprintCycle Team"

# 核心 API (用户常用)
from .server import (
    Chorus,
    SprintChain,
    Config,
    AgentType,
    TaskStatus,
    ExecutionResult,
)

# 模型
from .models import Sprint, Task, Project, Report

# 配置
from .config import SprintCycleConfig, load_config

# 工具
from .exceptions import SprintCycleError

__all__ = [
    # 版本
    "__version__",
    
    # 核心 API
    "Chorus",
    "SprintChain",
    "Config",
    "AgentType",
    "TaskStatus",
    "ExecutionResult",
    
    # 模型
    "Sprint",
    "Task",
    "Project",
    "Report",
    
    # 配置
    "SprintCycleConfig",
    "load_config",
    
    # 工具
    "SprintCycleError",
]

# 内部模块 (按需导入，不暴露在顶层)
def get_tooltype():
    from .server import ToolType
    return ToolType

def get_knowledge_base():
    from .server import KnowledgeBase
    return KnowledgeBase

def get_scheduler():
    from .scheduler import SprintScheduler
    return SprintScheduler

def get_benchmark():
    from .benchmark import BenchmarkSuite
    return BenchmarkSuite
