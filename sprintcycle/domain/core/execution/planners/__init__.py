"""
Execution Planners - 执行层计划模块

本模块提供发布计划构建和扩展功能。
核心数据模型已移动到 sprintcycle.domain.models。
本模块重新导出以保持向后兼容。
"""

from sprintcycle.domain.generic.models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)

from .execution_planners import TaskContextBuilder, SprintContextBuilder, SprintLoopResultPolicy
from .builders import (
    release_plan_from_diagnostic_slices,
    sprint_backlog_item_from_dict,
    sprint_definition_from_dict,
)
from .expand import EvolutionPath, EvolutionStrategy, expand_release_plan_for_execution
from .parser import ReleasePlanParseError, ReleasePlanParser, YAMLError
from .strategies import ExecutionResult, ExecutionStrategy, NormalStrategy, get_strategy
from .validator import ReleasePlanValidator, ValidationError, ValidationResult
from .work_item_splitter import WorkItemSplitter, IntentWorkItem

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
    "TaskContextBuilder", "SprintContextBuilder", "SprintLoopResultPolicy",
    "ExecutionResult", "ExecutionStrategy", "NormalStrategy", "get_strategy",
    "WorkItemSplitter", "IntentWorkItem"
]

