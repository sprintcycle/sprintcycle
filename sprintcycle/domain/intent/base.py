"""
Intent 基类
定义所有意图处理器的通用接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# 使用 TYPE_CHECKING 避免循环导入
if TYPE_CHECKING:
    from ...application.sprint_orchestrator import SprintResult
    from ...application.release_plan.models import ReleasePlan
    from ...results import RunResult


@dataclass
class IntentResult:
    """意图执行结果（``release_plan`` 与根包 ``ReleasePlan`` 为同一类型）。"""

    success: bool
    release_plan: "ReleasePlan"
    completed_sprints: int = 0
    completed_tasks: int = 0
    total_sprints: int = 0
    total_tasks: int = 0
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    sprint_results: List["SprintResult"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "completed_sprints": self.completed_sprints,
            "completed_tasks": self.completed_tasks,
            "total_sprints": self.total_sprints,
            "total_tasks": self.total_tasks,
            "error": self.error,
            "details": self.details,
        }

    @classmethod
    def from_run_result(
        cls,
        release_plan: "ReleasePlan",
        run_result: "RunResult",
    ) -> "IntentResult":
        """由 ``SprintCycle.run_release_plan`` 的 ``RunResult`` 组装（``sprint_results`` 为空列表）。"""
        from ...results import RunResult

        if not isinstance(run_result, RunResult):
            raise TypeError("run_result must be RunResult")

        if run_result.pending_knowledge_confirmation:
            return cls(
                success=False,
                release_plan=release_plan,
                error=run_result.message or "知识注入待确认",
                total_sprints=run_result.total_sprints,
                total_tasks=run_result.total_tasks,
                details={
                    "pending_knowledge_confirmation": True,
                    "knowledge_injection_preview": run_result.knowledge_injection_preview,
                },
            )

        if not run_result.success:
            return cls(
                success=False,
                release_plan=release_plan,
                error=run_result.error or "执行失败",
                total_sprints=run_result.total_sprints,
                total_tasks=run_result.total_tasks,
            )

        return cls(
            success=True,
            release_plan=release_plan,
            completed_sprints=run_result.completed_sprints,
            completed_tasks=run_result.completed_tasks,
            total_sprints=run_result.total_sprints,
            total_tasks=run_result.total_tasks,
            sprint_results=[],
        )


class IntentHandler(ABC):
    """意图处理器基类"""

    @abstractmethod
    def execute(self, release_plan: "ReleasePlan") -> IntentResult:
        pass

    def validate_release_plan(self, release_plan: "ReleasePlan") -> bool:
        from ...application.release_plan.validator import ReleasePlanValidator

        result = ReleasePlanValidator().validate(release_plan)
        return result.is_valid

    def _build_result(
        self,
        success: bool,
        release_plan: "ReleasePlan",
        sprint_results: List["SprintResult"],
        error: Optional[str] = None,
    ) -> IntentResult:
        from ...execution.sprint_types import ExecutionStatus

        completed_sprints = sum(
            1 for r in sprint_results if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
        )
        completed_tasks = sum(r.success_count for r in sprint_results)

        return IntentResult(
            success=success,
            release_plan=release_plan,
            completed_sprints=completed_sprints,
            completed_tasks=completed_tasks,
            total_sprints=len(sprint_results),
            total_tasks=release_plan.total_tasks,
            error=error,
            sprint_results=sprint_results,
        )
