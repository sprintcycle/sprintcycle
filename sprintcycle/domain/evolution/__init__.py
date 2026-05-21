"""
Domain Evolution - 版本演进领域模型

包含版本控制、演进策略、回滚管理等核心领域逻辑。
"""

from .activator import EvolutionActivator
from .context import EvolutionContext
from .controller import EvolutionController
from .default import DefaultEvolutionService
from .facade import EvolutionFacade
from .intent_evolution_loop import UserIntentEvolutionLoop
from .measurement import MeasurementResult
from .memory_store import MemoryStore
from .models import (
    EvolutionRequest,
    EvolutionTarget,
    RollbackOutcome,
    VersionArtifact,
)
from .rollback_manager import (
    EvolutionRollbackManager,
    HAS_GIT_ROLLBACK,
    RollbackConfig,
    RollbackError,
)
from .types import SprintContext

__all__ = [
    # Core
    "EvolutionController",
    "EvolutionFacade",
    "EvolutionActivator",
    # Service
    "DefaultEvolutionService",
    # Intent Loop
    "UserIntentEvolutionLoop",
    # Context & Types
    "EvolutionContext",
    "SprintContext",
    # Models
    "EvolutionRequest",
    "EvolutionTarget",
    "RollbackOutcome",
    "VersionArtifact",
    # Measurement
    "MeasurementResult",
    # Memory
    "MemoryStore",
    # Rollback
    "EvolutionRollbackManager",
    "RollbackConfig",
    "RollbackError",
    "HAS_GIT_ROLLBACK",
]
