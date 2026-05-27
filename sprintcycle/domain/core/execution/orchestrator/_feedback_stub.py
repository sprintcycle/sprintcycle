"""Feedback Release Plan Stub - 用于反馈循环中生成假计划。"""

from sprintcycle.domain.generic.models import ReleasePlan


class FeedbackReleasePlanStub:
    """生成假 Release Plan 用于反馈收集。

    用于在反馈循环中没有真实 release_plan 时生成假计划。
    """

    def __init__(self, sprint_name: str = "feedback-sprint", sprint_id: str = None):
        self.id = sprint_id or f"sprint-{sprint_name}"
        self.project = type("obj", (), {"name": sprint_name})()

    @property
    def sprints(self) -> list:
        return []

    def to_dict(self) -> dict:
        return {"project": {"name": self.project.name}, "sprints": []}


def create_feedback_stub() -> ReleasePlan:
    """创建用于反馈收集的空 ReleasePlan。"""
    return FeedbackReleasePlanStub()  # type: ignore
