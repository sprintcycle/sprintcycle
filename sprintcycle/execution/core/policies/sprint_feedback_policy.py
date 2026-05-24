"""Sprint 反馈策略。"""

from typing import Any, Dict


class SprintFeedbackPolicy:
    """Sprint 反馈适配器，保留扩展点。"""

    def build_context(self, decision: Dict[str, Any], feedback: Any) -> Dict[str, Any]:
        ctx: Dict[str, Any] = {
            "retry_feedback": feedback.to_dict() if hasattr(feedback, "to_dict") else feedback,
            "improvement_suggestions": decision.get("suggestions", []),
            "retry_from_failure": True,
        }
        return ctx


__all__ = [
    "SprintFeedbackPolicy",
]
