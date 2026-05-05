"""
Evolution pipeline — 与主线执行类型的边界（读此段再接 UI/API）

**何时用本模块的结果类型**

- ``EvolutionReleasePlanResult`` / ``SprintExecutionResult``：仅表示 **进化管道**
  一次 run 的聚合（轻量 dict Sprint、fitness 占位、``SprintExecutionResult.task_results`` 为 dict 列表）。
  用于 ``EvolutionPipeline.execute`` / ``execute_async``、实验与诊断闭环。

**何时用主线 execution 类型**

- ``SprintResult`` / ``TaskResult``（``execution.sprint_types``）：**SprintOrchestrator / SprintExecutor**
  对真实 Sprint Backlog 的执行产物（含 ``work_item: PRDTask``、``ExecutionStatus``）。
- ``RunResult``（``SprintCycle.run``）：CLI / MCP / Dashboard 面向用户的 **一次交付 run** 摘要。

**不要**把 ``EvolutionReleasePlanResult.to_dict()`` 与 ``RunResult.to_dict()`` 当作同一 schema 拼接；
若委托编排器，应经 ``release_plan_adapter.evolution_release_plan_to_prd`` 再进主线，UI 展示执行层结果请用 ``SprintResult`` / ``RunResult``。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from ..config import RuntimeConfig
    from ..release_plan.models import PRDSprint

from ..execution.sprint_types import ExecutionStatus
from .evolution_plan_source import (
    EvolutionPlanSource,
    EvolutionReleasePlan,
    ManualPRDSource,
)
from .memory_store import MemoryStore


@dataclass
class SprintExecutionResult:
    sprint_name: str
    success: bool
    task_results: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sprint_name": self.sprint_name,
            "success": self.success,
            "task_results": self.task_results,
            "duration": self.duration,
            "error": self.error,
        }


@dataclass
class EvolutionReleasePlanResult:
    """进化管道对单次 ``EvolutionReleasePlan`` 执行的聚合结果（非 ``RunResult``）。"""
    release_plan: EvolutionReleasePlan
    sprint_results: List[SprintExecutionResult] = field(default_factory=list)
    baseline_fitness: float = 0.0
    final_fitness: float = 0.0
    success: bool = False
    improvement: float = 0.0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def completed_sprints(self) -> int:
        return sum(1 for r in self.sprint_results if r.success)

    @property
    def total_sprints(self) -> int:
        return len(self.sprint_results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "release_plan_name": self.release_plan.name,
            "release_plan_version": self.release_plan.version,
            "completed_sprints": self.completed_sprints,
            "total_sprints": self.total_sprints,
            "baseline_fitness": self.baseline_fitness,
            "final_fitness": self.final_fitness,
            "success": self.success,
            "improvement": self.improvement,
        }


class EvolutionPipeline:
    """统一进化管道（V4.0 §6.2）。

    主生产路径为 ``SprintCycle`` → ``SprintOrchestrator`` → ``SprintExecutor.execute_sprints``。
    有 ``RuntimeConfig`` 时 ``execute_async`` 委托编排器；无配置时为轻量占位执行。
    """

    def __init__(
        self,
        project_path: str = ".",
        config: Optional["RuntimeConfig"] = None,
        memory_store: Optional[MemoryStore] = None,
        plan_source: Optional[EvolutionPlanSource] = None,
    ):
        self.project_path = project_path
        self._config = config
        memory_dir = (
            getattr(config, "evolution_cache_dir", "./evolution_cache/memory")
            if config
            else "./evolution_cache/memory"
        )
        self._memory_store = memory_store or MemoryStore(storage_path=memory_dir)
        self._plan_source = plan_source or ManualPRDSource()
        self._status = ExecutionStatus.IDLE
        self._current_release_plan: Optional[EvolutionReleasePlan] = None

    def execute(self, release_plan: EvolutionReleasePlan) -> EvolutionReleasePlanResult:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            if self._config is not None:
                return asyncio.run(self.execute_async(release_plan))
            return self._legacy_execute(release_plan)
        raise RuntimeError(
            "EvolutionPipeline.execute() cannot be used inside a running event loop; "
            "use await execute_async() instead."
        )

    async def execute_async(
        self, release_plan: EvolutionReleasePlan
    ) -> EvolutionReleasePlanResult:
        if self._config is None:
            return self._legacy_execute(release_plan)
        from ..orchestration.sprint_orchestrator import SprintOrchestrator
        from .release_plan_adapter import evolution_release_plan_to_prd

        self._status = ExecutionStatus.RUNNING
        self._current_release_plan = release_plan
        result = EvolutionReleasePlanResult(release_plan=release_plan)
        try:
            std_prd = evolution_release_plan_to_prd(release_plan, self.project_path or ".")
            orchestrator = SprintOrchestrator(
                config=self._config,
                evolution_pipeline=None,
                project_path=std_prd.project.path,
            )
            max_c = max(1, int(self._config.parallel_tasks))
            sprint_results = await orchestrator.execute_release_plan(
                std_prd, max_concurrent=max_c
            )
            result.sprint_results = self._map_orchestrator_sprint_results(sprint_results)
            result.success = (
                all(r.success for r in result.sprint_results)
                if result.sprint_results
                else True
            )
            result.final_fitness = self._calculate_fitness(result)
            result.improvement = result.final_fitness - result.baseline_fitness
            self._status = (
                ExecutionStatus.SUCCESS if result.success else ExecutionStatus.PARTIAL
            )
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            result.error = str(e)
            self._status = ExecutionStatus.FAILED
        return result

    async def evolve_sprint(self, *, sprint: "PRDSprint", max_generations: int = 3) -> Any:
        class _EvoSprintResult:
            __slots__ = ("success", "execution_time")

            def __init__(self, success: bool, execution_time: float) -> None:
                self.success = success
                self.execution_time = execution_time

        if self._config is None:
            return _EvoSprintResult(True, 0.0)
        tasks_data: List[Dict[str, Any]] = []
        for t in sprint.tasks:
            tasks_data.append(
                {"description": t.description, "agent": t.agent, "target": t.target}
            )
        evo = EvolutionReleasePlan(
            name=f"evolve-{sprint.name}",
            version="1.0",
            path=self.project_path or ".",
            sprints=[
                {
                    "name": sprint.name,
                    "goals": list(sprint.goals),
                    "tasks": tasks_data,
                }
            ],
        )
        res = await self.execute_async(evo)
        duration = sum(r.duration for r in res.sprint_results)
        return _EvoSprintResult(bool(res.success), float(duration))

    def _legacy_execute(
        self, release_plan: EvolutionReleasePlan
    ) -> EvolutionReleasePlanResult:
        self._status = ExecutionStatus.RUNNING
        self._current_release_plan = release_plan
        result = EvolutionReleasePlanResult(release_plan=release_plan)
        try:
            for i, sprint in enumerate(release_plan.sprints):
                sprint_name = sprint.get("name", f"sprint_{i}")
                sprint_result = self._execute_sprint(
                    sprint_name, sprint.get("tasks", [])
                )
                result.sprint_results.append(sprint_result)
                if not sprint_result.success and (
                    getattr(self._config, "rollback_on_failure", True)
                    if self._config
                    else True
                ):
                    logger.warning(f"Sprint {i} failed, rollback")
                    break
            result.success = all(r.success for r in result.sprint_results)
            result.final_fitness = self._calculate_fitness(result)
            result.improvement = result.final_fitness - result.baseline_fitness
            self._status = (
                ExecutionStatus.SUCCESS if result.success else ExecutionStatus.PARTIAL
            )
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            result.error = str(e)
            self._status = ExecutionStatus.FAILED
        return result

    @staticmethod
    def _map_orchestrator_sprint_results(
        sprint_results: List[Any],
    ) -> List[SprintExecutionResult]:
        from ..execution.sprint_types import SprintResult

        out: List[SprintExecutionResult] = []
        for sr in sprint_results:
            if not isinstance(sr, SprintResult):
                continue
            ok = sr.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
            tr_list: List[Dict[str, Any]] = []
            for tr in sr.task_results:
                tr_list.append(
                    {
                        "description": tr.work_item.description,
                        "agent": tr.work_item.agent,
                        "success": tr.status == ExecutionStatus.SUCCESS,
                        "error": tr.error,
                    }
                )
            out.append(
                SprintExecutionResult(
                    sprint_name=sr.sprint.name,
                    success=ok,
                    task_results=tr_list,
                    duration=float(sr.duration),
                )
            )
        return out

    def _execute_sprint(
        self, sprint_name: str, tasks: List[Dict[str, Any]]
    ) -> SprintExecutionResult:
        start = datetime.now()
        result = SprintExecutionResult(sprint_name=sprint_name, success=True)

        for work in tasks:
            try:
                if isinstance(work, str):
                    task_name = work
                else:
                    task_name = str(work.get("description", "unknown"))
                task_result = self._execute_task(task_name)
                result.task_results.append(task_result)
                if not task_result.get("success", False):
                    result.success = False
            except Exception as e:
                label = work if isinstance(work, str) else work.get("description", "unknown")
                logger.error(f"Sprint Backlog item {label} failed: {e}")
                result.task_results.append(
                    {"description": str(label), "success": False, "error": str(e)}
                )
                result.success = False

        result.duration = (datetime.now() - start).total_seconds()
        return result

    def _execute_task(self, task_name: str) -> Dict[str, Any]:
        return {"description": task_name, "success": True}

    def _calculate_fitness(self, result: EvolutionReleasePlanResult) -> float:
        if not result.sprint_results:
            return 0.0
        success_rate = sum(1 for r in result.sprint_results if r.success) / len(
            result.sprint_results
        )
        return success_rate

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    def get_memory(self) -> MemoryStore:
        return self._memory_store
