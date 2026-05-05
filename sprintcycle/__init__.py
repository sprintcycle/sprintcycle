"""
SprintCycle - 智能软件迭代框架
"""
__version__ = "0.9.2"
__author__ = "SprintCycle Team"

# 对外 API：Scrum 对齐命名（计划模型实现类名仍为 release_plan.models 中 PRD*）
from .release_plan import (
    ReleasePlanParseError,
    ReleasePlanParser,
    ReleasePlanValidator,
    ValidationError,
    ValidationResult,
)
from .intent.runner import RunnerHandler
from .orchestration.sprint_orchestrator import ExecutionStatus, SprintOrchestrator
from .execution.sprint_types import SprintResult
from .execution import SprintExecutor
from .scrum import (
    ReleasePlan,
    SprintDefinition,
    SprintBacklogItem,
    ProductAnchor,
    EvolutionParams,
    ExecutionMode,
)

VERSION = __version__

__all__ = [
    "__version__",
    "VERSION",
    "ReleasePlan",
    "ProductAnchor",
    "SprintDefinition",
    "SprintBacklogItem",
    "EvolutionParams",
    "ExecutionMode",
    "ReleasePlanParser",
    "ReleasePlanValidator",
    "ReleasePlanParseError",
    "ValidationError",
    "ValidationResult",
    "RunnerHandler",
    "SprintOrchestrator",
    "SprintResult",
    "ExecutionStatus",
    "SprintExecutor",
]
