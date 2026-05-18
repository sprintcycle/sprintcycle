from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from sprintcycle.domain.evolution.runtime_state import (
    ActivationReasonCode,
    ActivationState,
    EvolutionHealthSnapshot,
)


class HealthCheckAdapter(Protocol):
    def check(self) -> EvolutionHealthSnapshot:
        ...


@dataclass(slots=True)
class DefaultHealthCheckAdapter:
    healthy: bool = True
    metadata: dict[str, str] = field(default_factory=lambda: {"adapter": "default_health_check"})

    def check(self) -> EvolutionHealthSnapshot:
        return EvolutionHealthSnapshot(
            healthy=self.healthy,
            state=ActivationState.ACTIVE if self.healthy else ActivationState.DEGRADED,
            reason=ActivationReasonCode.OK if self.healthy else ActivationReasonCode.HEALTH_UNHEALTHY,
            details=dict(self.metadata),
        )
