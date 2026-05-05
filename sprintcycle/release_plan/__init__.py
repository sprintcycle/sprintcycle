"""
SprintCycle Release Plan 模块（工程包名 ``release_plan``）

可执行多 Sprint 计划：内存模型在 ``models`` 中仍以 ``PRD`` 等类名实现；
**对外推荐**使用 ``sprintcycle`` 根包或 ``sprintcycle.scrum`` 的 Scrum 对等名
（``ReleasePlan``、``ReleasePlanParser`` 等）。
"""

from .models import PRD, ExecutionMode, PRDEvolutionParams, PRDProject, PRDSprint, PRDTask
from .parser import (
    PRDParseError,
    PRDParser,
    ReleasePlanParseError,
    ReleasePlanParser,
    YAMLError,
)
from .validator import PRDValidator, ReleasePlanValidator, ValidationError, ValidationResult

__all__ = [
    "PRD",
    "PRDProject",
    "PRDSprint",
    "PRDTask",
    "PRDEvolutionParams",
    "ExecutionMode",
    "PRDParser",
    "PRDParseError",
    "ReleasePlanParser",
    "ReleasePlanParseError",
    "YAMLError",
    "PRDValidator",
    "ReleasePlanValidator",
    "ValidationError",
    "ValidationResult",
]
