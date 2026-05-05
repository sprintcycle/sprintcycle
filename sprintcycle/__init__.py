"""
SprintCycle - 智能软件迭代框架
"""
__version__ = "0.9.2"
__author__ = "SprintCycle Team"

# 核心模块导出
from .release_plan import PRD, PRDProject, PRDSprint, PRDTask, PRDParser, PRDValidator
from .intent.runner import RunnerHandler
from .orchestration.sprint_orchestrator import ExecutionStatus, SprintOrchestrator
from .execution.sprint_types import SprintResult
from .execution import SprintExecutor
from .scrum import (
    ReleasePlan,
    SprintDefinition,
    SprintBacklogItem,
    ProductAnchor,
)

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
    "SprintOrchestrator",
    "SprintResult",
    "ExecutionStatus",
    "SprintExecutor",
    "ReleasePlan",
    "SprintDefinition",
    "SprintBacklogItem",
    "ProductAnchor",
]
