"""
SprintCycle Evolution Module
集成 Hermes Agent Self-Evolution (GEPA)
"""

from .types import Gene, GeneType, Variation, VariationType, SprintContext, EvolutionResult, EvolutionStage, EvolutionMetrics, FitnessDimension
from .config import EvolutionEngineConfig
from .client import GEPAClient
from .engine import EvolutionEngine

__version__ = "0.5.0"
__all__ = ["Gene", "GeneType", "Variation", "VariationType", "SprintContext", "EvolutionResult", "EvolutionStage", "EvolutionMetrics", "FitnessDimension", "EvolutionEngineConfig", "GEPAClient", "EvolutionEngine"]
