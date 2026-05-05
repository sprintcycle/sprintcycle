"""
SprintCycle Evolution Module

v0.9.0: 统一进化管道 — ``EvolutionPipeline`` + ``EvolutionPlanSource`` + Diagnostic；人工 YAML 默认目录 **`release_plan/`**（见 ``ManualReleasePlanSource``）。
"""

# ========== Core Types ==========
from .evolution_plan_source import (
    DiagnosticReleasePlanSource,
    EvolutionPlanSource,
    EvolutionPlanSourceType,
    EvolutionReleasePlan,
    ManualReleasePlanSource,
)

# ========== Components (retained) ==========
from .measurement import (
    MeasurementProvider,
    MeasurementResult,
)
from .memory_store import (
    EvolutionMemory,
    MemoryStore,
)

# ========== Unified Pipeline (v0.9.0) ==========
from .pipeline import (
    EvolutionPipeline,
    EvolutionReleasePlanResult,
    SprintExecutionResult,
)
from .rollback_manager import (
    EvolutionRollbackManager,
    RollbackError,
    VariantBranch,
)
from .types import SprintContext

__version__ = "0.9.1"

__all__ = [
    "SprintContext",
    "EvolutionPipeline",
    "EvolutionReleasePlanResult",
    "SprintExecutionResult",
    "EvolutionPlanSource",
    "ManualReleasePlanSource",
    "DiagnosticReleasePlanSource",
    "EvolutionReleasePlan",
    "EvolutionPlanSourceType",
    "MeasurementProvider",
    "MeasurementResult",
    "MemoryStore",
    "EvolutionMemory",
    "EvolutionRollbackManager",
    "VariantBranch",
    "RollbackError",
]
