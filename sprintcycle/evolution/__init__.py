"""
SprintCycle Evolution Module

v0.9.0: 统一进化管道 — EvolutionPipeline + PRDSource + Diagnostic
"""

# ========== Core Types ==========
from .types import (
    Gene, GeneType, Variation, VariationType,
    SprintContext, EvolutionResult, EvolutionStage,
    EvolutionMetrics, FitnessDimension,
    FitnessScore,
)

# ========== GEPA Engine (Active) ==========
from .gepa_engine import (
    GEPAEngine,
    GEPAConfig,
    EvolutionStatus,
    EvolutionError,
    ConvergenceError,
    QualityGateError,
    VariationError,
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

# ========== Components ==========
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

from .variation_engine_new import (
    VariationEngine,
    VariationConfig,
    GeneratedVariant,
    VariationStrategy,
)

from .selection_engine import (
    SelectionEngine,
    SelectionConfig,
    EvaluatedVariant,
)

from .inheritance_engine import (
    InheritanceEngine,
    InheritanceGene,
    EvolutionCycle,
    CodeVariant,
    GeneMemoryStore,
    InheritanceError,
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
    # GEPA Engine
    "GEPAEngine", "GEPAConfig", "EvolutionStatus",
    "EvolutionError", "ConvergenceError", "QualityGateError", "VariationError",
    # Unified Pipeline
    "EvolutionPipeline", "PipelineConfig", "PipelineResult",
    "PRDSource", "ManualPRDSource", "DiagnosticPRDSource", "EvolutionPRD",
    # Components
    "MeasurementProvider", "MeasurementResult", "MeasurementConfig",
    "MemoryStore", "EvolutionMemory", "MemoryConfig",
    "VariationEngine", "VariationConfig", "GeneratedVariant", "VariationStrategy",
    "SelectionEngine", "SelectionConfig", "EvaluatedVariant",
    "InheritanceEngine", "InheritanceGene", "EvolutionCycle", "CodeVariant",
    "GeneMemoryStore", "InheritanceError",
    "EvolutionRollbackManager", "VariantBranch", "RollbackError",
    # Config
    "EvolutionEngineConfig",
]
