"""生命周期子域 - Lifecycle subdomain.

This module provides the canonical lifecycle management for SprintCycle.

**Key Concepts:**
- LifecycleRoot: Aggregate root for lifecycle management
- LifecycleStage: Enum for stage values
- LifecycleStateMachineService: Domain service for state transitions
- LifecycleContract: Contract model (maintained for compatibility)

**Event-Driven Architecture:**
Events flow between subdomains:
- StageTransitioned: Published when lifecycle transitions
- RecoveryTriggered: Published when recovery is initiated
"""

# Import models
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
    build_lifecycle_machine,
    build_lifecycle_contract,
)

# Import state machine
from .state_machine import (
    LifecycleStateMachine,
    build_default_correlation,
)

# Import new value objects
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

# Import new domain service
from .services import (
    LifecycleStateMachineService,
    LIFECYCLE_STAGES,
    STAGE_TRANSITIONS,
    TERMINAL_STAGES,
    FAILURE_STAGES,
    RECOVERY_STAGES,
    RECOVERY_TARGETS,
    REPAIR_ROUTE_BY_STAGE,
    CORRELATION_KEY_FIELDS,
    FAILURE_KIND_BY_STAGE as SERVICE_FAILURE_KIND_BY_STAGE,
    get_lifecycle_state_machine_service,
)

# Import new aggregate root
from .lifecycle_root import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
)

__all__ = [
    # Models
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
    "build_lifecycle_machine",
    "build_lifecycle_contract",
    # State machine
    "LifecycleStateMachine",
    "build_default_correlation",
    # Value objects
    "StageEvidence",
    "StageHistoryEntry",
    "CorrelationContext",
    "GovernanceRef",
    "EvolutionRef",
    "RuntimeRef",
    "LifecycleEvidence",
    "FailureInfo",
    # Domain service
    "LifecycleStateMachineService",
    "LIFECYCLE_STAGES",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "RECOVERY_TARGETS",
    "REPAIR_ROUTE_BY_STAGE",
    "CORRELATION_KEY_FIELDS",
    "SERVICE_FAILURE_KIND_BY_STAGE",
    "get_lifecycle_state_machine_service",
    # Aggregate root
    "LifecycleRoot",
    "LifecycleStage",
    "LifecycleStatus",
    "create_lifecycle",
]
