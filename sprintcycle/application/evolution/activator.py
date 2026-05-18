from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from sprintcycle.domain.evolution.runtime_state import (
    ActivationDecision,
    ActivationGuardResult,
    ActivationReasonCode,
    ActivationState,
    EvolutionHealthSnapshot,
    EvolutionHealthState,
    RetryPolicyConfig,
)
from sprintcycle.infrastructure.evolution.adapters.health_check import DefaultHealthCheckAdapter, HealthCheckAdapter
from sprintcycle.infrastructure.evolution.adapters.retry_policy import DefaultRetryPolicyAdapter, RetryPolicyAdapter


LoopStarter = Callable[[str], None]
GuardEvaluator = Callable[[], ActivationGuardResult]


@dataclass(slots=True)
class EvolutionActivator:
    guard_evaluator: GuardEvaluator
    loop_starter: LoopStarter
    health_check: HealthCheckAdapter = field(default_factory=DefaultHealthCheckAdapter)
    retry_policy: RetryPolicyAdapter = field(default_factory=DefaultRetryPolicyAdapter)
    retry_config: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)
    health_state: EvolutionHealthState = field(default_factory=EvolutionHealthState)
    session_id: Optional[str] = None

    def activate(self) -> ActivationDecision:
        session_id = self._resolve_session_id()
        if self._has_active_worker(session_id):
            return ActivationDecision(
                state=ActivationState.ACTIVE,
                reason=ActivationReasonCode.BLOCKED_ALREADY_ACTIVE,
                message="activation skipped: already active",
                details={"session_id": session_id},
            )

        guard = self.guard_evaluator()
        if not guard.allowed:
            self.health_state.state = ActivationState.INACTIVE
            return ActivationDecision(
                state=ActivationState.INACTIVE,
                reason=guard.reason,
                message="activation blocked by guard",
                details=guard.details,
            )

        self.health_state.state = ActivationState.ACTIVATING
        attempts = 0
        while True:
            attempts += 1
            try:
                self.loop_starter(session_id)
                snapshot = self.health_check.check()
                self.health_state.update(snapshot)
                if not snapshot.healthy:
                    return self._degrade(snapshot, attempts)
                self.health_state.active_session_id = session_id
                return ActivationDecision(
                    state=ActivationState.ACTIVE,
                    reason=ActivationReasonCode.OK,
                    message="activation succeeded",
                    details={"attempts": attempts, "session_id": session_id},
                )
            except Exception as exc:  # noqa: BLE001
                decision = self.retry_policy.decide(attempts, self.retry_config)
                if not decision.should_retry:
                    self.health_state.state = ActivationState.DEGRADED
                    self.health_state.degraded = True
                    return ActivationDecision(
                        state=ActivationState.DEGRADED,
                        reason=ActivationReasonCode.RETRY_EXHAUSTED,
                        message="activation failed and entered degraded state",
                        details={"attempts": attempts, "error": str(exc)},
                    )
                self.health_state.consecutive_failures += 1
                self.health_state.state = ActivationState.ACTIVATING

    def check_health(self) -> EvolutionHealthSnapshot:
        snapshot = self.health_check.check()
        self.health_state.update(snapshot)
        if not snapshot.healthy and self.health_state.consecutive_failures >= self.retry_config.max_attempts:
            self.health_state.state = ActivationState.DEGRADED
            self.health_state.degraded = True
        return snapshot

    def recover(self) -> ActivationDecision:
        self.health_state.state = ActivationState.RECOVERING
        guard = self.guard_evaluator()
        if not guard.allowed:
            return ActivationDecision(
                state=ActivationState.DEGRADED,
                reason=guard.reason,
                message="recovery blocked by guard",
                details=guard.details,
            )

        snapshot = self.health_check.check()
        self.health_state.update(snapshot)
        if not snapshot.healthy:
            self.health_state.state = ActivationState.DEGRADED
            self.health_state.degraded = True
            return ActivationDecision(
                state=ActivationState.DEGRADED,
                reason=snapshot.reason,
                message="recovery failed health check",
                details=snapshot.details,
            )

        self.health_state.state = ActivationState.ACTIVE
        self.health_state.degraded = False
        self.health_state.active_session_id = self._resolve_session_id()
        return ActivationDecision(
            state=ActivationState.ACTIVE,
            reason=ActivationReasonCode.RECOVERED,
            message="recovered from degraded state",
            details={"session_id": self.health_state.active_session_id},
        )

    def _has_active_worker(self, session_id: str) -> bool:
        return self.health_state.active_session_id is not None and self.health_state.active_session_id == session_id and self.health_state.state == ActivationState.ACTIVE

    def _degrade(self, snapshot: EvolutionHealthSnapshot, attempts: int) -> ActivationDecision:
        self.health_state.state = ActivationState.DEGRADED
        self.health_state.degraded = True
        return ActivationDecision(
            state=ActivationState.DEGRADED,
            reason=snapshot.reason,
            message="activation entered degraded state after unhealthy snapshot",
            details={"attempts": attempts, **snapshot.details},
        )

    def _resolve_session_id(self) -> str:
        if self.session_id:
            return self.session_id
        self.session_id = f"evolution-{id(self):x}"
        return self.session_id
