"""
任务调度器

根据 PRD 创建 Sprint 任务，分配给对应 agent，跟踪执行状态
"""

import asyncio
import logging
import os
import time
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from pathlib import Path

from ..prd.models import PRD, PRDSprint, PRDTask
from ..evolution.pipeline import EvolutionPipeline
from ..evolution.prd_source import DiagnosticPRDSource
from ..config import RuntimeConfig
from ..evolution.types import SprintContext
from ..execution.events import EventBus, EventType, Event, get_event_bus, create_event
from ..execution.sprint_types import ExecutionStatus, TaskResult, SprintResult
from ..execution.sprint_executor import SprintExecutor
from ..execution.feedback import FeedbackLoop
from ..execution.knowledge_hook import KnowledgeInjectionHook
from ..execution.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks

logger = logging.getLogger(__name__)


class _DispatcherSprintHooks(SprintLifecycleHooks):
    """将 Sprint 边界事件、回调与测量挂到 SprintExecutor 钩子链上。"""

    def __init__(self, dispatcher: "TaskDispatcher", prd: PRD):
        self._dispatcher = dispatcher
        self._prd = prd

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        self._dispatcher._callbacks["on_sprint_start"](sprint)
        await self._dispatcher._emit(
            create_event(
                EventType.SPRINT_START,
                sprint_number=sprint_index + 1,
                sprint_name=sprint.name,
                message=f"开始 Sprint: {sprint.name}",
            )
        )

    async def on_after_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        result: SprintResult,
        context: Dict[str, Any],
        prd: Optional[PRD],
    ) -> None:
        p = prd if prd is not None else self._prd
        self._dispatcher._callbacks["on_sprint_end"](result)
        if result.status == ExecutionStatus.FAILED:
            await self._dispatcher._emit(
                create_event(
                    EventType.SPRINT_FAILED,
                    sprint_number=sprint_index + 1,
                    sprint_name=sprint.name,
                    status="failed",
                    duration=result.duration,
                )
            )
        else:
            await self._dispatcher._emit(
                create_event(
                    EventType.SPRINT_COMPLETE,
                    sprint_number=sprint_index + 1,
                    sprint_name=sprint.name,
                    status="success",
                    duration=result.duration,
                )
            )
        if p is not None:
            await self._dispatcher._post_sprint_measurement(p)


class TaskDispatcher:
    """任务调度器 - 解析 PRD、分配任务、跟踪状态"""
    
    def __init__(
        self,
        config: Optional[RuntimeConfig] = None,
        evolution_pipeline: Optional[EvolutionPipeline] = None,
        event_bus: Optional[EventBus] = None,
        project_path: Optional[str] = None,
    ):
        self.config = config or RuntimeConfig()
        self._project_root = os.path.abspath(project_path or ".")
        self.evolution_pipeline = evolution_pipeline
        self.event_bus = event_bus
        self._callbacks: Dict[str, Callable] = {
            "on_task_start": self._default_on_task_start,
            "on_task_end": self._default_on_task_end,
            "on_sprint_start": self._default_on_sprint_start,
            "on_sprint_end": self._default_on_sprint_end,
        }
    
    def _get_event_bus(self) -> EventBus:
        if self.event_bus is None:
            self.event_bus = get_event_bus()
        return self.event_bus
    
    async def _emit(self, event: Event) -> None:
        try:
            await self._get_event_bus().emit(event)
        except Exception as e:
            logger.warning(f"Failed to emit event: {e}")

    def _make_sprint_executor(self, max_concurrent: int) -> SprintExecutor:
        feedback_loop: Optional[FeedbackLoop] = None
        if not getattr(self.config, "dry_run", False):
            feedback_loop = FeedbackLoop()
        ex = SprintExecutor(
            max_parallel=max_concurrent,
            max_verify_fix_rounds=int(self.config.max_verify_fix_rounds),
            runtime_config=self.config,
            feedback_loop=feedback_loop,
        )
        ex.set_event_bus(self._get_event_bus())
        return ex

    def _build_sprint_hooks(self, prd: PRD) -> SprintLifecycleHooks:
        return ChainedSprintHooks(
            (
                KnowledgeInjectionHook(self._project_root, self.config),
                _DispatcherSprintHooks(self, prd),
            )
        )

    def _base_runner_context(self, prd: PRD) -> Dict[str, Any]:
        """每 Sprint 的索引/目标由 SprintExecutor 在编排循环内写入 context。"""
        raw = (prd.project.path or self._project_root or ".").strip()
        try:
            proj = str(Path(raw).resolve())
        except Exception:
            proj = raw or "."
        meta = getattr(prd, "metadata", None) or {}
        return {
            "project_path": proj,
            "prd_name": prd.project.name,
            "prd_id": str(meta.get("id", "")),
            "coding_engine": self.config.coding_engine,
            "quality_level": self.config.quality_level,
        }

    async def _post_sprint_measurement(self, prd: PRD) -> None:
        """每个 Sprint 结束后按 quality_level 运行测量（与 RuntimeConfig 一致）。"""
        from ..config.quality import runs_pytest
        from ..evolution.measurement import MeasurementProvider

        if not runs_pytest(self.config.quality_level):
            return
        raw_root = prd.project.path or self._project_root
        try:
            repo = str(Path(raw_root).resolve())
        except Exception:
            repo = raw_root or "."
        prov = MeasurementProvider(repo_path=repo, runtime_config=self.config)
        m = prov.measure_all()
        if not prov.check_quality_gate(m):
            logger.warning(
                "Sprint 后质量测量未通过: level=%s overall=%.2f correctness=%.2f details=%s",
                self.config.quality_level,
                m.overall,
                m.correctness,
                m.details,
            )
    
    async def execute_prd(self, prd: PRD, max_concurrent: int = 3) -> List[SprintResult]:
        await self._emit(create_event(EventType.EXECUTION_START, execution_id=getattr(prd, 'execution_id', None), message=f"开始执行 PRD: {prd.project.name}", sprint_name=prd.project.name, sprint_number=0))
        logger.info(f"🚀 开始执行 PRD: {prd.project.name} | 模式: {prd.mode.value} | Sprint: {len(prd.sprints)} | 任务: {prd.total_tasks}")
        results = await (self._execute_evolution_mode(prd) if prd.is_evolution_mode else self._execute_normal_mode(prd, max_concurrent))
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        await self._emit(create_event(EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED, execution_id=getattr(prd, 'execution_id', None), message="PRD 执行完成", sprint_name=prd.project.name, sprint_number=len(results), status="success" if success else "failed"))
        total_success = sum(r.success_count for r in results)
        total_tasks = sum(len(r.task_results) for r in results)
        logger.info(f"\n📊 PRD 执行完成: 任务={total_tasks} 成功={total_success} 失败={total_tasks - total_success} 耗时={sum(r.duration for r in results):.2f}s")
        return results
    
    async def resume_from_sprint(self, prd: PRD, resume_from_idx: int, previous_results: List[SprintResult], max_concurrent: int = 3) -> List[SprintResult]:
        await self._emit(create_event(EventType.EXECUTION_START, execution_id=getattr(prd, 'execution_id', None), message=f"断点续跑: 从 Sprint {resume_from_idx} 继续", sprint_name=prd.project.name, sprint_number=resume_from_idx))
        logger.info(f"🔄 断点续跑: 从 Sprint {resume_from_idx} 继续 | PRD: {prd.project.name} | 已有: {len(previous_results)} | 待执行: {len(prd.sprints) - resume_from_idx}")
        results = list(previous_results)
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_prd(prd)
        ex.set_sprint_hooks(self._build_sprint_hooks(prd))
        ctx = self._base_runner_context(prd)
        tail = await ex.execute_sprints(
            prd.sprints[resume_from_idx:],
            mode="normal",
            context=ctx,
            prd=prd,
            sprint_index_offset=resume_from_idx,
        )
        results.extend(tail)
        for sprint_result in tail:
            if sprint_result.status == ExecutionStatus.FAILED and sprint_result.failed_count > sprint_result.success_count:
                logger.warning(f"⚠️  Sprint '{sprint_result.sprint.name}' 失败率较高")
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        await self._emit(create_event(EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED, execution_id=getattr(prd, 'execution_id', None), message="断点续跑完成", sprint_name=prd.project.name, sprint_number=len(results), status="success" if success else "failed"))
        return results
    
    async def _execute_normal_mode(self, prd: PRD, max_concurrent: int) -> List[SprintResult]:
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_prd(prd)
        ex.set_sprint_hooks(self._build_sprint_hooks(prd))
        ctx = self._base_runner_context(prd)
        return await ex.execute_sprints(
            prd.sprints,
            mode="normal",
            context=ctx,
            prd=prd,
            sprint_index_offset=0,
        )
    
    @staticmethod
    def _infer_evolution_strategy(goals: List[str]) -> str:
        goals_text = " ".join(goals).lower()
        if any(kw in goals_text for kw in ["性能", "速度", "performance", "latency", "吞吐"]): return "performance"
        elif any(kw in goals_text for kw in ["可读", "可维护", "readability", "maintainability", "文档"]): return "readability"
        elif any(kw in goals_text for kw in ["重构", "拆分", "refactor", "架构"]): return "refactoring"
        return "quality"
    
    async def _execute_evolution_mode(self, prd: PRD) -> List[SprintResult]:
        if not prd.evolution:
            logger.error("❌ 自进化模式缺少 evolution 配置")
            return []
        if not self.evolution_pipeline:
            self.evolution_pipeline = EvolutionPipeline(".", prd_source=DiagnosticPRDSource())
        strategy = self._infer_evolution_strategy(prd.evolution.goals)
        logger.info(f"🧬 自进化策略: {strategy} | 目标: {prd.evolution.goals}")
        results: List[SprintResult] = []
        for target in prd.evolution.targets:
            sprint = PRDSprint(name=f"进化: {target}", goals=prd.evolution.goals, tasks=[
                PRDTask(task=f"架构设计: {target}", agent="architect", target=target),
                PRDTask(task=f"进化 {target}", agent="evolver", target=target),
                PRDTask(task=f"验证进化结果: {target}", agent="tester", target=target),
                PRDTask(task=f"回归测试: {target}", agent="regression_tester", target=target),
            ])
            results.append(await self._execute_evolution_task(sprint, prd, SprintContext(sprint_id=f"evo-{int(time.time())}", sprint_number=1, goal="; ".join(prd.evolution.goals) if prd.evolution.goals else "优化代码", constraints={"dimensions": getattr(self.config, "eval_dimensions", ["correctness", "performance"]), "strategy": strategy}), target))
        return results
    
    async def _execute_sprint(self, sprint: PRDSprint, prd: PRD, max_concurrent: int, sprint_number: int = 1) -> SprintResult:
        start_time = datetime.now()
        self._callbacks["on_sprint_start"](sprint)
        await self._emit(create_event(EventType.SPRINT_START, sprint_number=sprint_number, sprint_name=sprint.name, message=f"开始 Sprint: {sprint.name}"))
        logger.info(f"\n📦 开始 Sprint: {sprint.name}" + (f" | 🎯 {' '.join(sprint.goals)}" if sprint.goals else ""))
        processed_results = await self._run_tasks_concurrent(sprint, prd, max_concurrent, sprint_number)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        status = self._determine_sprint_status(processed_results)
        sprint_result = SprintResult(sprint=sprint, status=status, task_results=processed_results, duration=duration, start_time=start_time, end_time=end_time)
        self._callbacks["on_sprint_end"](sprint_result)
        logger.info(f"   完成: {sprint_result.success_count}/{len(sprint.tasks)} 成功 ({duration:.2f}s)")
        return sprint_result
    
    async def _run_tasks_concurrent(self, sprint: PRDSprint, prd: PRD, max_concurrent: int, sprint_number: int = 1) -> List[TaskResult]:
        semaphore = asyncio.Semaphore(max_concurrent)
        async def execute_with_semaphore(task: PRDTask, task_idx: int) -> TaskResult:
            async with semaphore:
                return await self._execute_task(task, sprint.name, prd, task_idx, sprint_number)
        task_results = await asyncio.gather(*[execute_with_semaphore(t, i) for i, t in enumerate(sprint.tasks)], return_exceptions=True)
        return self._process_task_results(sprint, task_results)
    
    def _process_task_results(self, sprint: PRDSprint, task_results: List[Any]) -> List[TaskResult]:
        processed_results: List[TaskResult] = []
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                processed_results.append(TaskResult(task=sprint.tasks[i], sprint_name=sprint.name, status=ExecutionStatus.FAILED, error=str(result)))
            else:
                processed_results.append(result)  # type: ignore[arg-type]
        return processed_results
    
    def _determine_sprint_status(self, results: List[TaskResult]) -> ExecutionStatus:
        if all(r.status == ExecutionStatus.SUCCESS for r in results): return ExecutionStatus.SUCCESS
        if all(r.status in (ExecutionStatus.SKIPPED, ExecutionStatus.SUCCESS) for r in results): return ExecutionStatus.SUCCESS
        failed = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
        return ExecutionStatus.FAILED if failed > len(results) / 2 else ExecutionStatus.SUCCESS
    
    async def _execute_evolution_task(self, sprint: PRDSprint, prd: PRD, context: SprintContext, target: str) -> SprintResult:
        start_time = datetime.now()
        self._callbacks["on_sprint_start"](sprint)
        logger.info(f"\n🧬 开始自进化: {target}")
        task_result = TaskResult(task=sprint.tasks[0], sprint_name=sprint.name, status=ExecutionStatus.RUNNING, start_time=start_time)
        try:
            target_path = Path(prd.project.path) / target
            if not target_path.exists(): raise FileNotFoundError(f"目标文件不存在: {target_path}")
            assert self.evolution_pipeline is not None
            from sprintcycle.evolution.prd_source import EvolutionPRD
            evo_prd = EvolutionPRD(name=f"evo-{sprint.tasks[0].agent}", version="1.0", path=prd.project.path)
            evo_prd.sprints = [{"name": "evolution", "tasks": [sprint.tasks[0].task]}]
            evo_result = self.evolution_pipeline.execute(evo_prd)
            task_result.status = ExecutionStatus.SUCCESS if evo_result.success else ExecutionStatus.FAILED
            task_result.output = f"进化执行完成: {evo_result.completed_sprints} 个Sprint" if evo_result.success else ""
            task_result.error = evo_result.error or "未知错误" if not evo_result.success else None
        except Exception as e:
            task_result.status = ExecutionStatus.FAILED
            task_result.error = str(e)
            logger.exception(f"进化失败: {target}")
        task_result.end_time = datetime.now()
        task_result.duration = ((task_result.end_time or datetime.now()) - (task_result.start_time or datetime.now())).total_seconds()
        end_time = datetime.now()
        sprint_result = SprintResult(sprint=sprint, status=task_result.status, task_results=[task_result], duration=(end_time - start_time).total_seconds(), start_time=start_time, end_time=end_time)
        self._callbacks["on_sprint_end"](sprint_result)
        return sprint_result
    
    async def _execute_task(self, task: PRDTask, sprint_name: str, prd: PRD, task_index: int, sprint_number: int) -> TaskResult:
        start_time = datetime.now()
        self._callbacks["on_task_start"](task)
        await self._emit(create_event(EventType.TASK_START, sprint_number=sprint_number, sprint_name=sprint_name, agent_type=task.agent, task=task.task, message=f"开始任务: {task.task[:50]}..." if len(task.task) > 50 else f"开始任务: {task.task}"))
        result = TaskResult(task=task, sprint_name=sprint_name, status=ExecutionStatus.RUNNING, start_time=start_time)
        try:
            logger.info(f"   📋 {task.agent}: {task.task[:60]}...")
            if task.agent == "evolver": result = await self._execute_evolver_task(task, prd, result)
            elif task.agent == "tester": result = await self._execute_tester_task(task, prd, result)
            else: result = await self._execute_coder_task(task, prd, result)
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"任务超时 ({task.timeout}s)"
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            logger.exception(f"任务执行失败")
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds() if result.start_time else 0.0
        self._callbacks["on_task_end"](result)
        if result.status == ExecutionStatus.FAILED:
            await self._emit(create_event(EventType.TASK_FAILED, sprint_number=sprint_number, sprint_name=sprint_name, agent_type=task.agent, task=task.task, status="failed", error=result.error, duration=result.duration))
        else:
            await self._emit(create_event(EventType.TASK_COMPLETE, sprint_number=sprint_number, sprint_name=sprint_name, agent_type=task.agent, task=task.task, status="success" if result.status == ExecutionStatus.SUCCESS else "skipped", duration=result.duration))
        return result
    
    async def _execute_coder_task(self, task: PRDTask, prd: PRD, result: TaskResult) -> TaskResult:
        await asyncio.sleep(0.1)
        result.status = ExecutionStatus.SUCCESS
        result.output = f"Coder 任务完成: {task.task[:50]}..."
        return result
    
    async def _execute_evolver_task(self, task: PRDTask, prd: PRD, result: TaskResult) -> TaskResult:
        if not task.target:
            result.status = ExecutionStatus.FAILED
            result.error = "evolver 任务必须指定 target"
            return result
        if not self.evolution_pipeline:
            self.evolution_pipeline = EvolutionPipeline(".", config=self.config, prd_source=DiagnosticPRDSource())
        try:
            from sprintcycle.evolution.prd_source import EvolutionPRD
            evo_prd = EvolutionPRD(name=f"evolution-{task.target}", version="1.0", path=".", goals=[task.task], sprints=[{"name": f"evo-{task.target}", "tasks": [{"name": task.target}]}])
            evo_result = self.evolution_pipeline.execute(evo_prd)
            result.status = ExecutionStatus.SUCCESS if evo_result.success else ExecutionStatus.FAILED
            result.output = f"进化执行完成: {evo_result.completed_sprints} 个Sprint" if evo_result.success else ""
            result.error = evo_result.error if not evo_result.success else None
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
        return result
    
    async def _execute_tester_task(self, task: PRDTask, prd: PRD, result: TaskResult) -> TaskResult:
        await asyncio.sleep(0.1)
        result.status = ExecutionStatus.SUCCESS
        result.output = f"Tester 任务完成: {task.task[:50]}..."
        return result
    
    def _default_on_task_start(self, task: PRDTask) -> None: pass
    def _default_on_task_end(self, result: TaskResult) -> None:
        if result.status == ExecutionStatus.FAILED: logger.error(f"   ❌ 任务失败: {result.error}")
        elif result.status == ExecutionStatus.SUCCESS: logger.info(f"   ✅ 任务成功")
    def _default_on_sprint_start(self, sprint: PRDSprint) -> None: pass
    def _default_on_sprint_end(self, result: SprintResult) -> None:
        if result.status == ExecutionStatus.FAILED: logger.warning(f"   ⚠️  Sprint 失败率较高")
    
    def get_summary(self) -> Dict[str, Any]:
        return {"evolution_pipeline": self.evolution_pipeline is not None, "callbacks": list(self._callbacks.keys()), "event_bus": self.event_bus is not None}
