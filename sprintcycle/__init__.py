"""
SprintCycle - 智能软件迭代框架
"""

__version__ = "0.9.2"
__author__ = "SprintCycle Team"

VERSION = __version__

from .domain.generic.models import (
    EvolutionParams,
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)
from .domain.generic.models.release_plan.parser import ReleasePlanParser
from .application.sprint_orchestrator import SprintOrchestrator

__all__ = [
    "__version__",
    "VERSION",
    "__author__",
    "EvolutionParams",
    "ExecutionMode",
    "ProductAnchor",
    "ReleasePlan",
    "SprintBacklogItem",
    "SprintDefinition",
    "ReleasePlanParser",
    "SprintOrchestrator",
]
