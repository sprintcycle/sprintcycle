from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional


class ActivationState(str, Enum):
    INACTIVE = "inactive"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEGRADED = "degraded"
    RECOVERING = "recovering"


class ActivationReasonCode(str, Enum):
    OK = "ok"
    BLOCKED_GUARD = "blocked_guard"
    BLOCKED_ALREADY_ACTIVE = "blocked_already_active"
    BLOCKED_CONCURRENT_SESSION = "blocked_concurrent_session"
    RETRYING_TRANSIENT_FAILURE = "retrying_transient_failure"
    RETRY_EXHAUSTED = "retry_exhausted"
    HEALTH_UNHEALTHY = "health_unhealthy"
    DEGRADED_BY_FAILURES = "degraded_by_failures"
    RECOVERED = "recovered"


@dataclass(slots=True)
class ActivationGuardResult:
    allowed: bool
    reason: ActivationReasonCode = ActivationReasonCode.OK
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RetryPolicyConfig:
    max_attempts: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 30.0


@dataclass(slots=True)
class RetryDecision:
    should_retry: bool
    attempt: int
    reason: ActivationReasonCode
    delay_seconds: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvolutionHealthSnapshot:
    healthy: bool
    state: ActivationState
    reason: ActivationReasonCode = ActivationReasonCode.OK
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvolutionHealthState:
    state: ActivationState = ActivationState.INACTIVE
    last_snapshot: Optional[EvolutionHealthSnapshot] = None
    consecutive_failures: int = 0
    degraded: bool = False
    active_session_id: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    def update(self, snapshot: EvolutionHealthSnapshot) -> None:
        self.last_snapshot = snapshot
        self.state = snapshot.state
        self.degraded = snapshot.state == ActivationState.DEGRADED
        if snapshot.healthy:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1


@dataclass(slots=True)
class ActivationDecision:
    state: ActivationState
    reason: ActivationReasonCode
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "state": self.state.value,
            "reason": self.reason.value,
            "message": self.message,
            "details": self.details,
        }
