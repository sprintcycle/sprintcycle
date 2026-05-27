from __future__ import annotations

from sprintcycle.domain.core.evolution.activator import EvolutionActivator
from sprintcycle.domain.core.evolution.runtime_state import (
    ActivationGuardResult,
    ActivationReasonCode,
    ActivationState,
    EvolutionHealthSnapshot,
    RetryPolicyConfig,
)


def test_activation_succeeds_when_guard_passes_and_health_is_good():
    started_sessions: list[str] = []

    def guard() -> ActivationGuardResult:
        return ActivationGuardResult(allowed=True)

    def start_loop(session_id: str) -> None:
        started_sessions.append(session_id)

    activator = EvolutionActivator(
        guard_evaluator=guard,
        loop_starter=start_loop,
    )

    result = activator.activate()

    assert result.state == ActivationState.ACTIVE
    assert result.reason == ActivationReasonCode.OK
    assert started_sessions
    assert activator.health_state.state == ActivationState.ACTIVE


def test_activation_blocks_when_guard_fails():
    def guard() -> ActivationGuardResult:
        return ActivationGuardResult(
            allowed=False,
            reason=ActivationReasonCode.BLOCKED_GUARD,
            details={"missing": "dependency"},
        )

    activator = EvolutionActivator(
        guard_evaluator=guard,
        loop_starter=lambda _: None,
    )

    result = activator.activate()

    assert result.state == ActivationState.INACTIVE
    assert result.reason == ActivationReasonCode.BLOCKED_GUARD
    assert result.details["missing"] == "dependency"


def test_activation_prevents_duplicate_active_worker():
    activator = EvolutionActivator(
        guard_evaluator=lambda: ActivationGuardResult(allowed=True),
        loop_starter=lambda _: None,
    )
    first = activator.activate()
    second = activator.activate()

    assert first.state == ActivationState.ACTIVE
    assert second.reason == ActivationReasonCode.BLOCKED_ALREADY_ACTIVE


def test_transient_failure_is_retried_before_degrade():
    attempts = {"count": 0}

    def guard() -> ActivationGuardResult:
        return ActivationGuardResult(allowed=True)

    def loop_starter(_: str) -> None:
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("transient")

    activator = EvolutionActivator(
        guard_evaluator=guard,
        loop_starter=loop_starter,
        retry_config=RetryPolicyConfig(max_attempts=3),
    )

    result = activator.activate()

    assert result.state == ActivationState.ACTIVE
    assert attempts["count"] == 2


def test_persistent_failure_enters_degraded_state():
    def guard() -> ActivationGuardResult:
        return ActivationGuardResult(allowed=True)

    activator = EvolutionActivator(
        guard_evaluator=guard,
        loop_starter=lambda _: (_ for _ in ()).throw(RuntimeError("persistent")),
        retry_config=RetryPolicyConfig(max_attempts=2),
    )

    result = activator.activate()

    assert result.state == ActivationState.DEGRADED
    assert result.reason == ActivationReasonCode.RETRY_EXHAUSTED
    assert activator.health_state.degraded is True


def test_health_check_failure_degrades_activation():
    def guard() -> ActivationGuardResult:
        return ActivationGuardResult(allowed=True)

    activator = EvolutionActivator(
        guard_evaluator=guard,
        loop_starter=lambda _: None,
        health_check=type(
            "FailingHealthCheck",
            (),
            {"check": staticmethod(lambda: EvolutionHealthSnapshot(
                healthy=False,
                state=ActivationState.DEGRADED,
                reason=ActivationReasonCode.HEALTH_UNHEALTHY,
                details={"source": "test"},
            ))},
        )(),
    )

    result = activator.activate()

    assert result.state == ActivationState.DEGRADED
    assert result.reason == ActivationReasonCode.HEALTH_UNHEALTHY
    assert activator.health_state.degraded is True


def test_recovery_revalidates_and_resumes_without_duplicate_worker():
    starts: list[str] = []

    def guard() -> ActivationGuardResult:
        return ActivationGuardResult(allowed=True)

    def start_loop(session_id: str) -> None:
        starts.append(session_id)

    activator = EvolutionActivator(
        guard_evaluator=guard,
        loop_starter=start_loop,
    )
    activator.health_state.state = ActivationState.DEGRADED
    activator.health_state.degraded = True

    activator.activate()
    recovery = activator.recover()

    assert recovery.state == ActivationState.ACTIVE
    assert recovery.reason == ActivationReasonCode.RECOVERED
    assert len(set(starts)) == 1
