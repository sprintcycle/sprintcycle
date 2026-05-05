from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ..config import RuntimeConfig
    from ..prd.models import PRDSprint

from ..execution.sprint_types import ExecutionStatus
from .memory_store import MemoryStore
from .prd_source import EvolutionPRD, ManualPRDSource, PRDSource

logger = logging.getLogger(__name__)







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
class PRDExecutionResult:
    prd: EvolutionPRD
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
            "prd_name": self.prd.name,
            "prd_version": self.prd.version,
            "completed_sprints": self.completed_sprints,
            "total_sprints": self.total_sprints,
            "baseline_fitness": self.baseline_fitness,
            "final_fitness": self.final_fitness,
            "success": self.success,
            "improvement": self.improvement,
        }


# PipelineResult for backward compatibility
PipelineResult = PRDExecutionResult


class EvolutionPipeline:
    """统一进化管道（V4.0 §6.2）。

    主生产路径为 ``SprintCycle`` → ``TaskDispatcher`` → ``SprintExecutor.execute_sprints``。
    有 ``RuntimeConfig`` 时 ``execute_async`` 委托 ``TaskDispatcher``；无配置时为轻量占位
    执行。服务于进化实验、诊断派生 PRD 等，不与 Dispatcher 并列称为第二套「唯一编排」。
    """

    def __init__(
        self,
        project_path: str = ".",
        config: Optional["RuntimeConfig"] = None,
        memory_store: Optional[MemoryStore] = None,
        prd_source: Optional[PRDSource] = None,
    ):
        """
        初始化进化管道

        Args:
            project_path: 项目路径
            config: RuntimeConfig（统一配置）
            memory_store: 记忆存储
            prd_source: PRD 来源
        """
        self.project_path = project_path
        self._config = config
        memory_dir = getattr(config, 'evolution_cache_dir', './evolution_cache/memory') if config else './evolution_cache/memory'
        self._memory_store = memory_store or MemoryStore(storage_path=memory_dir)
        self._prd_source = prd_source or ManualPRDSource()
        self._status = ExecutionStatus.IDLE
        self._current_prd: Optional[EvolutionPRD] = None

    def execute(self, prd: EvolutionPRD) -> PRDExecutionResult:
        """
        执行单个 PRD（同步 API）。

        若在 asyncio 事件循环内调用，请改用 ``await execute_async()``；本方法在循环内会
        抛出 ``RuntimeError`` 以免阻塞事件循环。
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            if self._config is not None:
                return asyncio.run(self.execute_async(prd))
            return self._legacy_execute(prd)
        raise RuntimeError(
            "EvolutionPipeline.execute() cannot be used inside a running event loop; "
            "use await execute_async() instead."
        )

    async def execute_async(self, prd: EvolutionPRD) -> PRDExecutionResult:
        """异步执行；有 ``RuntimeConfig`` 时委托 ``TaskDispatcher``（V4.0 §6.2 选项 A）。"""
        if self._config is None:
            return self._legacy_execute(prd)
        from ..scheduler.dispatcher import TaskDispatcher
        from .prd_adapter import evolution_prd_to_prd

        self._status = ExecutionStatus.RUNNING
        self._current_prd = prd
        result = PRDExecutionResult(prd=prd)
        try:
            std_prd = evolution_prd_to_prd(prd, self.project_path or ".")
            dispatcher = TaskDispatcher(
                config=self._config,
                evolution_pipeline=None,
                project_path=std_prd.project.path,
            )
            max_c = max(1, int(self._config.parallel_tasks))
            sprint_results = await dispatcher.execute_prd(std_prd, max_concurrent=max_c)
            result.sprint_results = self._map_dispatcher_sprint_results(sprint_results)
            result.success = all(r.success for r in result.sprint_results) if result.sprint_results else True
            result.final_fitness = self._calculate_fitness(result)
            result.improvement = result.final_fitness - result.baseline_fitness
            self._status = ExecutionStatus.SUCCESS if result.success else ExecutionStatus.PARTIAL
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            result.error = str(e)
            self._status = ExecutionStatus.FAILED
        return result

    async def evolve_sprint(self, *, sprint: "PRDSprint", max_generations: int = 3) -> Any:
        """
        SprintExecutor 自进化模式入口（``SprintExecutor._execute_evolution_sprints``）。

        无 ``RuntimeConfig`` 时返回占位结果以保持兼容；有配置时委托 ``execute_async``。
        """
        class _EvoSprintResult:
            __slots__ = ("success", "execution_time")

            def __init__(self, success: bool, execution_time: float) -> None:
                self.success = success
                self.execution_time = execution_time

        if self._config is None:
            return _EvoSprintResult(True, 0.0)
        tasks_data: List[Dict[str, Any]] = []
        for t in sprint.tasks:
            tasks_data.append({"task": t.task, "agent": t.agent, "target": t.target})
        evo = EvolutionPRD(
            name=f"evolve-{sprint.name}",
            version="1.0",
            path=self.project_path or ".",
            sprints=[{"name": sprint.name, "goals": list(sprint.goals), "tasks": tasks_data}],
        )
        res = await self.execute_async(evo)
        duration = sum(r.duration for r in res.sprint_results)
        return _EvoSprintResult(bool(res.success), float(duration))

    def _legacy_execute(self, prd: EvolutionPRD) -> PRDExecutionResult:
        """无 RuntimeConfig 时的占位执行（与 v0.9.x 行为一致）。"""
        self._status = ExecutionStatus.RUNNING
        self._current_prd = prd
        result = PRDExecutionResult(prd=prd)
        try:
            for i, sprint in enumerate(prd.sprints):
                sprint_name = sprint.get("name", f"sprint_{i}")
                sprint_result = self._execute_sprint(sprint_name, sprint.get("tasks", []))
                result.sprint_results.append(sprint_result)
                if not sprint_result.success and (
                    getattr(self._config, "rollback_on_failure", True) if self._config else True
                ):
                    logger.warning(f"Sprint {i} failed, rollback")
                    break
            result.success = all(r.success for r in result.sprint_results)
            result.final_fitness = self._calculate_fitness(result)
            result.improvement = result.final_fitness - result.baseline_fitness
            self._status = ExecutionStatus.SUCCESS if result.success else ExecutionStatus.PARTIAL
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            result.error = str(e)
            self._status = ExecutionStatus.FAILED
        return result

    @staticmethod
    def _map_dispatcher_sprint_results(sprint_results: List[Any]) -> List[SprintExecutionResult]:
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
                        "task": tr.task.task,
                        "agent": tr.task.agent,
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

    def _execute_sprint(self, sprint_name: str, tasks: List[Dict[str, Any]]) -> SprintExecutionResult:
        start = datetime.now()
        result = SprintExecutionResult(sprint_name=sprint_name, success=True)

        for task in tasks:
            try:
                task_name = task.get("name", "unknown")
                task_result = self._execute_task(task_name)
                result.task_results.append(task_result)
                if not task_result.get("success", False):
                    result.success = False
            except Exception as e:
                logger.error(f"Task {task.get('name', 'unknown')} failed: {e}")
                result.task_results.append({"task": task.get("name", "unknown"), "success": False, "error": str(e)})
                result.success = False

        result.duration = (datetime.now() - start).total_seconds()
        return result

    def _execute_task(self, task_name: str) -> Dict[str, Any]:
        return {"task": task_name, "success": True}

    def _calculate_fitness(self, result: PRDExecutionResult) -> float:
        if not result.sprint_results:
            return 0.0
        success_rate = sum(1 for r in result.sprint_results if r.success) / len(result.sprint_results)
        return success_rate

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    def get_memory(self) -> MemoryStore:
        return self._memory_store
