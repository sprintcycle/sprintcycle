"""Sprint 重试策略。"""

from dataclasses import dataclass

from sprintcycle.domain.generic.models import SprintDefinition


@dataclass
class SprintRetryDecision:
    should_retry: bool
    reason: str = ""
    retry_count: int = 0
    max_retries: int = 1


class SprintRetryPolicy:
    """Sprint 级反馈重试策略。"""

    def __init__(self, max_verify_fix_rounds: int = 3):
        self.max_verify_fix_rounds = max(1, int(max_verify_fix_rounds))

    def should_retry(self, sprint: SprintDefinition) -> SprintRetryDecision:
        retry_count = getattr(sprint, "_retry_count", 0)
        return SprintRetryDecision(
            should_retry=retry_count < self.max_verify_fix_rounds,
            reason=f"retry_count={retry_count}",
            retry_count=retry_count,
            max_retries=self.max_verify_fix_rounds,
        )


__all__ = [
    "SprintRetryDecision",
    "SprintRetryPolicy",
]
