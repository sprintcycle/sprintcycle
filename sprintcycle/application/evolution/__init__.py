"""
SprintCycle Evolution Module

**执行主路径**在 ``SprintCycle`` + ``ReleasePlan`` + ``expand_release_plan_for_execution`` +
``SprintOrchestrator``；本包提供测量、记忆、回滚，以及进化控制面（sandbox / versioning / facade）
与意图演化闭环。

代码级边界约束
- ``evolution`` 只负责“观察、判定、沉淀”，不接管主执行链路。
- 这里可以读取 intent / feedback / memory / knowledge，但不应直接执行任务。
- 这里可以输出演化决策，但最终是否重规划、是否继续执行，必须由 ``api`` / ``orchestration`` 决定。
- 这里不应反向依赖 ``execution`` 的具体执行细节，避免把演化模块变成第二套控制平面。
- 所有学习结果必须通过显式方法写入记忆或知识库，不允许在导入时产生隐式副作用。
- 对外统一摘要契约为 ``EvolutionSummary``（位于 ``sprintcycle.results``），禁止在外部接口上扩散零散演化字段。
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

# ========== Evolution control plane ==========
from .models import (
    EvolutionMode,
    EvolutionPlan,
    EvolutionRequest,
    EvolutionStage,
    EvolutionTarget,
    PromotionResult,
    RollbackOutcome,
    SandboxBackend,
    SandboxSpec,
    ValidationResult,
    VersionArtifact,
    VersioningBackend,
)
from .controller import (
    CodeEvolutionAdapter,
    DefaultEvolutionController,
    EvolutionController,
    RequirementEvolutionAdapter,
)
from .default import create_evolution_facade
from .facade import EvolutionFacade

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
    "EvolutionMode",
    "EvolutionPlan",
    "EvolutionRequest",
    "EvolutionStage",
    "EvolutionTarget",
    "PromotionResult",
    "RollbackOutcome",
    "SandboxBackend",
    "SandboxSpec",
    "ValidationResult",
    "VersionArtifact",
    "VersioningBackend",
    "CodeEvolutionAdapter",
    "RequirementEvolutionAdapter",
    "EvolutionController",
    "DefaultEvolutionController",
    "create_evolution_facade",
    "EvolutionFacade",
]
