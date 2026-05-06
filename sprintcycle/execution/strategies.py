"""
执行策略 — 仅保留 ``NormalStrategy``（与 ``SprintCycle`` 主路径一致）。

历史 ``ExecutionEngine`` / ``EvolutionStrategy`` 已移除；自进化 YAML 请使用
``expand_release_plan_for_execution`` 后走编排器。
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger

from ..release_plan.models import ReleasePlan
from .sprint_executor import ExecutionStatus, SprintExecutor, SprintResult


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    release_plan: ReleasePlan
    sprint_results: List[SprintResult] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None

    @property
    def completed_sprints(self) -> int:
        return sum(1 for r in self.sprint_results if r.status == ExecutionStatus.SUCCESS)

    @property
    def total_sprints(self) -> int:
        return len(self.sprint_results)

    @property
    def completed_tasks(self) -> int:
        return sum(r.success_count for r in self.sprint_results)

    @property
    def total_tasks(self) -> int:
        return sum(len(r.task_results) for r in self.sprint_results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "completed_sprints": self.completed_sprints,
            "total_sprints": self.total_sprints,
            "completed_tasks": self.completed_tasks,
            "total_tasks": self.total_tasks,
            "duration": self.duration,
            "error": self.error,
        }


class ExecutionStrategy(ABC):
    """执行策略基类：共享 ``SprintExecutor``。"""

    def __init__(self, sprint_executor: SprintExecutor):
        self.sprint_executor = sprint_executor

    @abstractmethod
    async def execute(self, release_plan: ReleasePlan) -> ExecutionResult:
        pass


class NormalStrategy(ExecutionStrategy):
    """标准 Sprint 顺序交付。"""

    async def execute(self, release_plan: ReleasePlan) -> ExecutionResult:
        start_time = time.time()
        logger.info(f"📋 Normal 策略执行: {release_plan.project.name}")

        self.sprint_executor.set_release_plan(release_plan)
        sprint_results = await self.sprint_executor.execute_sprints(
            release_plan.sprints, mode="normal", release_plan=release_plan, sprint_index_offset=0
        )

        success = all(r.status == ExecutionStatus.SUCCESS for r in sprint_results)

        duration = time.time() - start_time
        logger.info(f"{'✅' if success else '❌'} Normal 策略完成 ({duration:.2f}s)")

        return ExecutionResult(
            success=success,
            release_plan=release_plan,
            sprint_results=sprint_results,
            duration=duration,
            error=None if success else "部分 Sprint 失败",
        )


def get_strategy(
    mode: Any,
    sprint_executor: SprintExecutor,
) -> ExecutionStrategy:
    """始终返回 ``NormalStrategy``（``mode`` 参数忽略，保留签名供极少旧代码）。"""
    return NormalStrategy(sprint_executor)
