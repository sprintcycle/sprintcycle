"""
SprintCycle Evolution Module

**执行主路径**在 ``SprintCycle`` + ``ReleasePlan`` + ``expand_release_plan_for_execution`` +
``SprintOrchestrator``；本包提供测量、记忆、回滚，以及 ``ManualReleasePlanSource`` 等（磁盘扫描与诊断辅助）。
"""

# ========== Core Types ==========
from .evolution_plan_source import (
    DiagnosticReleasePlanSource,
    EvolutionPlanSource,
    EvolutionPlanSourceType,
    ManualReleasePlanSource,
)

# ========== Components (retained) ==========
from .intent_evolution_loop import (
    IntentDriftType,
    IntentEvolutionDecision,
    IntentSnapshot,
    UserIntentEvolutionLoop,
)
from .measurement import (
    MeasurementProvider,
    MeasurementResult,
)
from .memory_store import (
    EvolutionMemory,
    MemoryStore,
)

from .rollback_manager import (
    EvolutionRollbackManager,
    RollbackError,
    VariantBranch,
)
from .types import SprintContext

__version__ = "0.9.2"

__all__ = [
    "SprintContext",
    "EvolutionPlanSource",
    "ManualReleasePlanSource",
    "DiagnosticReleasePlanSource",
    "EvolutionPlanSourceType",
    "MeasurementProvider",
    "MeasurementResult",
    "MemoryStore",
    "EvolutionMemory",
    "EvolutionRollbackManager",
    "VariantBranch",
    "RollbackError",
    "IntentDriftType",
    "IntentSnapshot",
    "IntentEvolutionDecision",
    "UserIntentEvolutionLoop",
]
