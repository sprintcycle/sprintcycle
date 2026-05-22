"""执行策略抽象。

用于把 SprintExecutor 中的可变决策（任务重试、Sprint 重试）从主流程中拆分出去，
以便后续扩展不同的验证/修复/反馈策略。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from sprintcycle.domain.models import SprintDefinition


@dataclass
class TaskRetryDecision:
    should_retry: bool
    reason: str = ""
    attempt: int = 0
    max_attempts: int = 1


@dataclass
class SprintRetryDecision:
    should_retry: bool
    reason: str = ""
    retry_count: int = 0
    max_retries: int = 1


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


class SprintFeedbackPolicy:
    """Sprint 反馈适配器，保留扩展点。"""

    def build_context(self, decision: Dict[str, Any], feedback: Any) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {
            "retry_feedback": feedback.to_dict() if hasattr(feedback, "to_dict") else feedback,
            "improvement_suggestions": decision.get("suggestions", []),
            "retry_from_failure": True,
        }
        return ctx
