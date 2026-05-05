"""
SprintCycle - 智能软件迭代框架
"""
__version__ = "0.9.2"
__author__ = "SprintCycle Team"

# 对外 API：计划模型与 Scrum 术语一致（见 release_plan.models）
from .execution import SprintExecutor
from .execution.sprint_types import SprintResult
from .intent.runner import RunnerHandler
from .orchestration.sprint_orchestrator import ExecutionStatus, SprintOrchestrator
from .release_plan import (
    ReleasePlanParseError,
    ReleasePlanParser,
    ReleasePlanValidator,
    ValidationError,
    ValidationResult,
    expand_release_plan_for_execution,
)
from .release_plan.models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
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
    "expand_release_plan_for_execution",
    "ReleasePlanParseError",
    "ValidationError",
    "ValidationResult",
    "RunnerHandler",
    "SprintOrchestrator",
    "SprintResult",
    "ExecutionStatus",
    "SprintExecutor",
]
