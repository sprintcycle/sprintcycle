"""
Domain Models - 核心领域模型

包含 ReleasePlan、SprintDefinition、SprintBacklogItem 等核心领域对象。
"""

from .release_plan_models import (
    ExecutionMode,
    EvolutionParams,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)

# Re-export for backwards compatibility
from .sprint_models import (
    SprintBacklogItem as SprintBacklogItemExec,
    SprintDefinition as SprintDefinitionExec,
)

__all__ = [
    # Core Models
    "ExecutionMode",
    "EvolutionParams",
    "ProductAnchor",
    "ReleasePlan",
    "SprintBacklogItem",
    "SprintDefinition",
    # Legacy aliases
    "SprintBacklogItemExec",
    "SprintDefinitionExec",
]
