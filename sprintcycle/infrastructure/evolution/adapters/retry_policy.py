from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from sprintcycle.domain.evolution.runtime_state import ActivationReasonCode, RetryDecision, RetryPolicyConfig


class RetryPolicyAdapter(Protocol):
    def decide(self, attempt: int, config: RetryPolicyConfig) -> RetryDecision:
        ...


@dataclass(slots=True)
class DefaultRetryPolicyAdapter:
    config: RetryPolicyConfig = field(default_factory=RetryPolicyConfig)

    def decide(self, attempt: int, config: RetryPolicyConfig | None = None) -> RetryDecision:
        policy = config or self.config
        should_retry = attempt < policy.max_attempts
        delay = min(
            policy.backoff_seconds * (policy.backoff_multiplier ** max(attempt - 1, 0)),
            policy.max_backoff_seconds,
        )
        return RetryDecision(
            should_retry=should_retry,
            attempt=attempt,
            reason=ActivationReasonCode.RETRYING_TRANSIENT_FAILURE if should_retry else ActivationReasonCode.RETRY_EXHAUSTED,
            delay_seconds=delay if should_retry else 0.0,
            details={"max_attempts": policy.max_attempts},
        )
