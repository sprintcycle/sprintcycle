"""
Sprint Models - 执行层 Sprint 模型扩展

复用 domain.models 的核心类型并添加执行层专属方法。
"""

from typing import Any, Dict, List

from .release_plan_models import (
    EvolutionParams as _BaseEvolutionParams,
    ExecutionMode,
    ProductAnchor as _BaseProductAnchor,
    ReleasePlan as _BaseReleasePlan,
    SprintBacklogItem as _BaseSprintBacklogItem,
    SprintDefinition as _BaseSprintDefinition,
)
from .release_plan_models import (
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
    EvolutionParams,
)

from .constraint_spec import ConstraintSpec
from .task_spec import TaskSpec
from .verification_strategy import VerificationStrategySpec

__all__ = [
    "ExecutionMode",
    "ProductAnchor",
    "ReleasePlan",
    "SprintBacklogItem",
    "SprintDefinition",
    "EvolutionParams",
    "ConstraintSpec",
    "TaskSpec",
    "VerificationStrategySpec",
]
