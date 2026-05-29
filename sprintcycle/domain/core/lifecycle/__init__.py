"""生命周期子域 - Lifecycle subdomain.

这是新架构的核心入口，完全使用 DDD 模式实现。

**状态机层次结构:**
- ExecutionStateMachine: 任务/执行级别的运行时状态管理
- LifecycleStateMachine: 业务生命周期阶段管理

两者形成层次关系，ExecutionStateMachine 作为 LifecycleStateMachine 的内部组件。
"""

from .models import (
    LifecycleContract,
    STAGE_EVIDENCE_SCHEMA,
    STAGE_EVIDENCE_TRUTHY_KEYS,
    FAILURE_KIND_BY_STAGE,
    STAGE_EVIDENCE_KEYS,
    CANONICAL_EVIDENCE_KEYS,
    TERMINAL_STATUSES,
    REQUIRED_EVIDENCE_SECTIONS,
    REQUIRED_STAGE_SEQUENCE,
    RECOVERY_STAGE_TARGETS,
    ensure_lifecycle_evidence,
    next_stage,
    normalize_lifecycle_metadata,
    validate_lifecycle_evidence,
    build_lifecycle_state_machine,
)

from .values import (
    StageEvidence,
    StageHistoryEntry,
    CorrelationContext,
    GovernanceRef,
    EvolutionRef,
    RuntimeRef,
    LifecycleEvidence,
    FailureInfo,
)

from .services import (
    ExecutionStatus,
    EXECUTION_TRANSITIONS,
    TASK_TRANSITIONS,
    StateTransition,
    ExecutionStateMachine,
    summarize_execution_state_machine,
    LIFECYCLE_STAGES,
    STAGE_TRANSITIONS,
    TERMINAL_STAGES,
    FAILURE_STAGES,
    RECOVERY_STAGES,
    RECOVERY_TARGETS,
    REPAIR_ROUTE_BY_STAGE,
    CORRELATION_KEY_FIELDS,
    validate_transition,
)

from .state_machine import (
    LifecycleStateMachine,
    get_lifecycle_state_machine,
    build_default_correlation,
)

from .lifecycle_root import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
)

from .mapper import (
    LifecycleMapper,
    map_contract_to_root,
    map_root_to_contract,
)

__all__ = [
    # Execution State Machine (Runtime States)
    "ExecutionStatus",
    "EXECUTION_TRANSITIONS",
    "TASK_TRANSITIONS",
    "StateTransition",
    "ExecutionStateMachine",
    "summarize_execution_state_machine",
    # Lifecycle Models (DTOs)
    "LifecycleContract",
    "STAGE_EVIDENCE_SCHEMA",
    "STAGE_EVIDENCE_TRUTHY_KEYS",
    "FAILURE_KIND_BY_STAGE",
    "STAGE_EVIDENCE_KEYS",
    "CANONICAL_EVIDENCE_KEYS",
    "TERMINAL_STATUSES",
    "REQUIRED_EVIDENCE_SECTIONS",
    "REQUIRED_STAGE_SEQUENCE",
    "RECOVERY_STAGE_TARGETS",
    "ensure_lifecycle_evidence",
    "next_stage",
    "normalize_lifecycle_metadata",
    "validate_lifecycle_evidence",
    "build_lifecycle_state_machine",
    # Value Objects
    "StageEvidence",
    "StageHistoryEntry",
    "CorrelationContext",
    "GovernanceRef",
    "EvolutionRef",
    "RuntimeRef",
    "LifecycleEvidence",
    "FailureInfo",
    # Lifecycle State Machine
    "LifecycleStateMachine",
    "LIFECYCLE_STAGES",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "RECOVERY_TARGETS",
    "REPAIR_ROUTE_BY_STAGE",
    "CORRELATION_KEY_FIELDS",
    "get_lifecycle_state_machine",
    "build_default_correlation",
    "validate_transition",
    # Lifecycle Root Aggregate
    "LifecycleRoot",
    "LifecycleStage",
    "LifecycleStatus",
    "create_lifecycle",
    # Mapper
    "LifecycleMapper",
    "map_contract_to_root",
    "map_root_to_contract",
]