"""
SprintCycle Release Plan 模块（工程包名 ``release_plan``）

可执行多 Sprint 计划：内存模型在 ``models`` 中为 ``ReleasePlan``、``SprintDefinition`` 等；
根包 ``from sprintcycle import ReleasePlan, ReleasePlanParser`` 与本文档一致。
"""

from .builders import (
    release_plan_from_diagnostic_slices,
    sprint_backlog_item_from_dict,
    sprint_definition_from_dict,
)
from .expand import EvolutionPath, EvolutionStrategy, expand_release_plan_for_execution
from .models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)
from .parser import ReleasePlanParseError, ReleasePlanParser, YAMLError
from .validator import ReleasePlanValidator, ValidationError, ValidationResult

__all__ = [
    "ReleasePlan",
    "ProductAnchor",
    "SprintDefinition",
    "SprintBacklogItem",
    "EvolutionParams",
    "EvolutionPath",
    "EvolutionStrategy",
    "sprint_backlog_item_from_dict",
    "sprint_definition_from_dict",
    "release_plan_from_diagnostic_slices",
    "expand_release_plan_for_execution",
    "ExecutionMode",
    "ReleasePlanParser",
    "ReleasePlanParseError",
    "YAMLError",
    "ReleasePlanValidator",
    "ValidationError",
    "ValidationResult",
]
