"""
SprintCycle Evolution Runtime State

Explicit runtime state primitives for the self-evolution activation lifecycle.
The activator imports these types to keep orchestration decisions observable
without embedding domain policy.
"""

from .runtime_state import (
    ActivationDecision,
    ActivationGuardResult,
    ActivationReasonCode,
    ActivationState,
    EvolutionHealthSnapshot,
    EvolutionHealthState,
    RetryDecision,
    RetryPolicyConfig,
)

__all__ = [
    "ActivationDecision",
    "ActivationGuardResult",
    "ActivationReasonCode",
    "ActivationState",
    "EvolutionHealthSnapshot",
    "EvolutionHealthState",
    "RetryDecision",
    "RetryPolicyConfig",
]
