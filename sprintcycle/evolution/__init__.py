"""
SprintCycle Evolution Module

GEPA 自进化引擎 — 统一入口
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

# ========== Deprecated (kept for backward compatibility) ==========
from .config import EvolutionEngineConfig  # deprecated: use GEPAConfig
from .client import GEPAClient  # deprecated: use GEPAEngine
from .engine import EvolutionEngine  # deprecated: use GEPAEngine

__version__ = "0.8.1"

__all__ = [
    # Core Types
    "Gene", "GeneType", "Variation", "VariationType",
    "SprintContext", "EvolutionResult", "EvolutionStage",
    "EvolutionMetrics", "FitnessDimension",
    "FitnessScore",
    # GEPA Engine
    "GEPAEngine", "GEPAConfig", "EvolutionStatus",
    "EvolutionError", "ConvergenceError", "QualityGateError", "VariationError",
    # Components
    "MeasurementProvider", "MeasurementResult", "MeasurementConfig",
    "MemoryStore", "EvolutionMemory", "MemoryConfig",
    "VariationEngine", "VariationConfig", "GeneratedVariant", "VariationStrategy",
    "SelectionEngine", "SelectionConfig", "EvaluatedVariant",
    "InheritanceEngine", "InheritanceGene", "EvolutionCycle", "CodeVariant",
    "GeneMemoryStore", "InheritanceError",
    "EvolutionRollbackManager", "VariantBranch", "RollbackError",
    # Deprecated
    "EvolutionEngineConfig", "GEPAClient", "EvolutionEngine",
]
