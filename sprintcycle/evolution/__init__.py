"""
SprintCycle Evolution Module

v0.9.0: 统一进化管道 — EvolutionPipeline + PRDSource + Diagnostic
GEPA standalone engine removed, all evolution via EvolutionPipeline。
v0.9.1: 精简 Config 类，删除未使用的枚举
"""

# ========== Core Types ==========
from .types import (
    Gene, Variation,
    SprintContext, EvolutionResult, EvolutionStage,
    EvolutionMetrics,
    FitnessScore,
)

# ========== Unified Pipeline (v0.9.0) ==========
from .pipeline import (
    EvolutionPipeline,
    PipelineResult,
)
from .prd_source import (
    PRDSource,
    ManualPRDSource,
    DiagnosticPRDSource,
    EvolutionPRD,
)

# ========== Components (retained) ==========
from .measurement import (
    MeasurementProvider,
    MeasurementResult,
)

from .memory_store import (
    MemoryStore,
    EvolutionMemory,
)

from .rollback_manager import (
    EvolutionRollbackManager,
    VariantBranch,
    RollbackError,
)

# ========== Config (backward compat) ==========
# MeasurementConfig, MemoryConfig removed in v0.9.1 - use RuntimeConfig fields instead
# RollbackConfig removed in v0.9.1 - use parameters or RuntimeConfig instead

__version__ = "0.9.1"

__all__ = [
    # Core Types
    "Gene", "Variation",
    "SprintContext", "EvolutionResult", "EvolutionStage",
    "EvolutionMetrics",
    "FitnessScore",
    # Unified Pipeline
    "EvolutionPipeline", "PipelineResult",
    "PRDSource", "ManualPRDSource", "DiagnosticPRDSource", "EvolutionPRD",
    # Components
    "MeasurementProvider", "MeasurementResult",
    "MemoryStore", "EvolutionMemory",
    "EvolutionRollbackManager", "VariantBranch", "RollbackError",
]
