"""任务重试策略。"""

from dataclasses import dataclass


@dataclass
class TaskRetryDecision:
    should_retry: bool
    reason: str = ""
    attempt: int = 0
    max_attempts: int = 1


class TaskRetryPolicy:
    """任务级验证-修复策略。"""

    def __init__(self, max_verify_fix_rounds: int = 3):
        self.max_verify_fix_rounds = max(1, int(max_verify_fix_rounds))

    def should_retry(self, attempt: int, last_error: str) -> TaskRetryDecision:
        max_attempts = self.max_verify_fix_rounds
        remaining = attempt < max_attempts - 1
        return TaskRetryDecision(
            should_retry=remaining,
            reason=last_error,
            attempt=attempt + 1,
            max_attempts=max_attempts,
        )


__all__ = [
    "TaskRetryDecision",
    "TaskRetryPolicy",
]
