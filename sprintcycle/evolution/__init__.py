"""
SprintCycle Evolution Module

v0.9.0: 统一进化管道 — EvolutionPipeline + PRDSource + Diagnostic
GEPA独立引擎已移除，所有进化通过EvolutionPipeline执行。
"""

# ========== Core Types ==========
from .types import (
    Gene, GeneType, Variation, VariationType,
    SprintContext, EvolutionResult, EvolutionStage,
    EvolutionMetrics, FitnessDimension,
    FitnessScore,
)

# ========== Unified Pipeline (v0.9.0) ==========
from .pipeline import (
    EvolutionPipeline,
    PipelineConfig,
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
    MeasurementConfig,
)

from .memory_store import (
    MemoryStore,
    EvolutionMemory,
    MemoryConfig,
)

from .rollback_manager import (
    EvolutionRollbackManager,
    VariantBranch,
    RollbackError,
)

# ========== Config (backward compat) ==========
from .config import EvolutionEngineConfig  # deprecated: use RuntimeConfig

__version__ = "0.9.0"

__all__ = [
    # Core Types
    "Gene", "GeneType", "Variation", "VariationType",
    "SprintContext", "EvolutionResult", "EvolutionStage",
    "EvolutionMetrics", "FitnessDimension",
    "FitnessScore",
    # Unified Pipeline
    "EvolutionPipeline", "PipelineConfig", "PipelineResult",
    "PRDSource", "ManualPRDSource", "DiagnosticPRDSource", "EvolutionPRD",
    # Components
    "MeasurementProvider", "MeasurementResult", "MeasurementConfig",
    "MemoryStore", "EvolutionMemory", "MemoryConfig",
    "EvolutionRollbackManager", "VariantBranch", "RollbackError",
    # Config
    "EvolutionEngineConfig",
]
