"""Unified lifecycle state machine for SprintCycle.

This module re-exports from domain layer to maintain imports for existing code.
"""

from sprintcycle.domain.core.lifecycle.state_machine import (
    CorrelationContext,
    LifecycleStateMachine,
    LIFECYCLE_STAGES,
    STAGE_TRANSITIONS,
    TERMINAL_STAGES,
    build_default_correlation,
)

__all__ = [
    "CorrelationContext",
    "LifecycleStateMachine",
    "LIFECYCLE_STAGES",
    "STAGE_TRANSITIONS",
    "TERMINAL_STAGES",
    "build_default_correlation",
]
