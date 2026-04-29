"""
SprintCycle - 智能软件迭代框架
"""
__version__ = "0.7.0"
__author__ = "SprintCycle Team"

# 核心模块导出
from .prd import PRD, PRDProject, PRDSprint, PRDTask, PRDParser, PRDValidator
from .intent.runner import RunnerHandler
from .scheduler import TaskDispatcher, SprintResult, ExecutionStatus
from .execution import SprintExecutor

VERSION = __version__

__all__ = [
    "__version__",
    "VERSION",
    "PRD",
    "PRDProject",
    "PRDSprint",
    "PRDTask",
    "PRDParser",
    "PRDValidator",
    "RunnerHandler",
    "TaskDispatcher",
    "SprintResult",
    "ExecutionStatus",
    "SprintExecutor",
]
