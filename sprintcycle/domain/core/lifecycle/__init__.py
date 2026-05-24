"""生命周期子域 - 定义 LifecycleContract 和 LifecycleStateMachine"""

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
from .state_machine import (
    CorrelationContext,
    LifecycleStateMachine,
    LIFECYCLE_STAGES,
    STAGE_TRANSITIONS,
    TERMINAL_STAGES,
    build_default_correlation,
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
    "CorrelationContext",
    "LifecycleStateMachine",
    "LIFECYCLE_STAGES",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "build_default_correlation",
]
