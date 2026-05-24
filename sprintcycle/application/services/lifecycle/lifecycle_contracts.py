"""Lifecycle contract helpers for web-triggered execution chains.

This module re-exports from domain layer to maintain imports for existing code.
"""

from sprintcycle.domain.core.lifecycle.models import (
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

__all__ = [
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
]
