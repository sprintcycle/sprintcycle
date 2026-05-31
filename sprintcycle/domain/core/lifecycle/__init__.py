"""Lifecycle domain module - SprintCycle's core lifecycle orchestration.

This module provides:
1. **State Management**: Unified state machine for execution and lifecycle states
2. **Aggregate Root**: LifecycleRoot as the single source of lifecycle truth
3. **Value Objects**: Evidence, correlation, and cross-domain references
4. **Request Builders**: Data classes for parameter grouping

**Architecture:**
- LifecycleRoot: Aggregate root managing lifecycle state
- LifecycleStateMachine: Unified state machine for both execution and business stages
- StageEvidence: Immutable evidence collection per stage
- CorrelationContext: Cross-request correlation tracking
- Governance/Evolution/RuntimeRef: Cross-subdomain references

**Design Principles:**
- DDD: Rich domain model with behavior
- Immutable: Value objects are frozen dataclasses
- Unified: Single state machine handles both execution and lifecycle contexts
- Single Source of Truth: LifecycleRoot is the sole aggregate root
"""

from .lifecycle_root import (
    LifecycleRoot,
    LifecycleStatus,
    create_lifecycle,
)
from .state_machine import (
    LifecycleStateMachine,
    LifecyclePhase,
    LifecycleSubstage,
    ExecutionStatus,
    LIFECYCLE_STAGES,
    SUBSTAGE_TRANSITIONS,
    TERMINAL_STAGES,
    FAILURE_STAGES,
    RECOVERY_STAGES,
    RECOVERY_TARGETS,
    PHASE_SUBSTAGES,
    CORRELATION_KEY_FIELDS,
    FAILURE_KIND_BY_STAGE,
    get_lifecycle_state_machine,
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
from .requests import (
    BuildLifecycleRequest,
    BuildLifecycleRequestBuilder,
    TransitionRequest,
    TransitionRequestBuilder,
    WebLifecycleRequest,
    WebLifecycleRequestBuilder,
    RecoveryRequest,
    RecoveryRequestBuilder,
)
from .models import (
    STAGE_EVIDENCE_SCHEMA,
    STAGE_EVIDENCE_TRUTHY_KEYS,
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
from .services import (
    StateTransition,
)


__all__ = [
    # Core Aggregate
    "LifecycleRoot",
    "LifecycleStatus",
    "create_lifecycle",

    # State Machine
    "LifecycleStateMachine",
    "LifecyclePhase",
    "LifecycleSubstage",
    "ExecutionStatus",

    # Configuration Constants
    "LIFECYCLE_STAGES",
    "SUBSTAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "FAILURE_STAGES",
    "RECOVERY_STAGES",
    "RECOVERY_TARGETS",
    "PHASE_SUBSTAGES",
    "CORRELATION_KEY_FIELDS",
    "FAILURE_KIND_BY_STAGE",

    # Value Objects
    "StageEvidence",
    "StageHistoryEntry",
    "CorrelationContext",
    "GovernanceRef",
    "EvolutionRef",
    "RuntimeRef",
    "LifecycleEvidence",
    "FailureInfo",

    # Request Builders
    "BuildLifecycleRequest",
    "BuildLifecycleRequestBuilder",
    "TransitionRequest",
    "TransitionRequestBuilder",
    "WebLifecycleRequest",
    "WebLifecycleRequestBuilder",
    "RecoveryRequest",
    "RecoveryRequestBuilder",

    # Evidence Schema
    "STAGE_EVIDENCE_SCHEMA",
    "STAGE_EVIDENCE_TRUTHY_KEYS",
    "STAGE_EVIDENCE_KEYS",
    "CANONICAL_EVIDENCE_KEYS",
    "TERMINAL_STATUSES",
    "REQUIRED_EVIDENCE_SECTIONS",
    "REQUIRED_STAGE_SEQUENCE",
    "RECOVERY_STAGE_TARGETS",

    # Helper Functions
    "get_lifecycle_state_machine",
    "ensure_lifecycle_evidence",
    "next_stage",
    "normalize_lifecycle_metadata",
    "validate_lifecycle_evidence",

    # Domain Services
    "StateTransition",
]
