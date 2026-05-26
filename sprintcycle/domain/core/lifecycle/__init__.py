"""生命周期子域 - Lifecycle subdomain.

This module provides the canonical lifecycle management for SprintCycle.

**Key Concepts:**
- LifecycleRoot: Aggregate root for lifecycle management
- LifecycleStage: Enum for stage values
- LifecycleStateMachineService: Domain service for state transitions

**Event-Driven Architecture:**
Events flow between subdomains:
- StageTransitioned: Published when lifecycle transitions
- RecoveryTriggered: Published when recovery is initiated
"""

# Import core business constants from models (keep business logic intact)
from .models import (
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
)

# Import value objects
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

# Import domain service
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
    get_lifecycle_state_machine_service,
)

# Import aggregate root
from .lifecycle_root import (
    LifecycleRoot,
    LifecycleStage,
    LifecycleStatus,
    create_lifecycle,
)

# Compatibility: Build lifecycle contract using new architecture
def build_lifecycle_contract(*args, **kwargs):
    """
    Create a lifecycle contract.
    
    DEPRECATED: Use create_lifecycle() instead.
    This is maintained for backward compatibility.
    """
    return create_lifecycle(*args, **kwargs)

# Compatibility: Build state machine using new architecture
def build_lifecycle_state_machine():
    """
    Build lifecycle state machine.
    
    DEPRECATED: Use LifecycleStateMachineService instead.
    This is maintained for backward compatibility.
    """
    return LifecycleStateMachineService()

build_lifecycle_machine = build_lifecycle_state_machine

# Compatibility: Build default correlation
def build_default_correlation(payload=None):
    """
    Build default correlation context.
    
    DEPRECATED: Use CorrelationContext directly.
    This is maintained for backward compatibility.
    """
    service = LifecycleStateMachineService()
    return service.build_default_correlation(payload)

__all__ = [
    # Core business constants (keep business logic)
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
    "get_lifecycle_state_machine_service",
    # Aggregate root (NEW ARCHITECTURE - PRIMARY API)
    "LifecycleRoot",
    "LifecycleStage",
    "LifecycleStatus",
    "create_lifecycle",
    # Compatibility functions (DEPRECATED)
    "build_lifecycle_contract",
    "build_lifecycle_state_machine",
    "build_lifecycle_machine",
    "build_default_correlation",
]
