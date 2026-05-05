"""
Sprint 执行编排（主实现模块；类 ``SprintOrchestrator``）

**Scrum 语境**：本模块负责把 **Release Plan**（``PRD`` YAML）转为按 Sprint 顺序的**交付编排**，
不是日历「排期」。``execute_release_plan`` / ``resume_from_sprint`` 即一次 **Sprint 序列的执行**。

**主执行路径（V4.0）**：``SprintCycle.run`` / 断点续跑经 ``SprintOrchestrator.execute_release_plan``；
Normal 模式下由 ``SprintExecutor.execute_sprints`` 驱动唯一 Sprint 循环；事件与测量经生命周期钩子挂载。
详见 ``SPRINTCYCLE_PRODUCT_TECH_PLAN.md`` §4.1、§6.2、``docs/PRODUCT_TECH_V4.md``、
``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``。
"""

import asyncio
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ..config import RuntimeConfig
from ..evolution.evolution_plan_source import DiagnosticPRDSource
from ..evolution.measurement import MeasurementResult
from ..evolution.pipeline import EvolutionPipeline
from ..evolution.types import SprintContext
from ..execution.events import Event, EventBus, EventType, create_event, get_event_bus
from ..execution.feedback import FeedbackLoop
from ..execution.hooks.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks
from ..execution.knowledge.knowledge_hook import KnowledgeInjectionHook
from ..execution.sprint_executor import SprintExecutor
from ..execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from ..release_plan.models import PRD, PRDSprint, PRDTask


class _OrchestratorSprintHooks(SprintLifecycleHooks):
    """由 ``SprintOrchestrator`` 注入：在 Sprint 边界发事件、调回调、跑测量与知识卡片落盘。"""

    def __init__(self, orchestrator: "SprintOrchestrator", release_plan: PRD):
        self._orchestrator = orchestrator
        self._release_plan = release_plan

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: PRDSprint,
        context: Dict[str, Any],
        release_plan: Optional[PRD],
    ) -> None:
        self._orchestrator._callbacks["on_sprint_start"](sprint)
        await self._orchestrator._emit(
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
        release_plan: Optional[PRD],
    ) -> None:
        p = release_plan if release_plan is not None else self._release_plan
        self._orchestrator._callbacks["on_sprint_end"](result)
        if result.status == ExecutionStatus.FAILED:
            await self._orchestrator._emit(
                create_event(
                    EventType.SPRINT_FAILED,
                    sprint_number=sprint_index + 1,
                    sprint_name=sprint.name,
                    status="failed",
                    duration=result.duration,
                )
            )
        else:
            await self._orchestrator._emit(
                create_event(
                    EventType.SPRINT_COMPLETE,
                    sprint_number=sprint_index + 1,
                    sprint_name=sprint.name,
                    status="success",
                    duration=result.duration,
                )
            )
        if p is not None:
            m = await self._orchestrator._post_sprint_measurement(p)
            from ..execution.knowledge.sprint_knowledge_card import persist_sprint_outcome_card

            persist_sprint_outcome_card(
                project_path=self._orchestrator._project_root,
                config=self._orchestrator.config,
                release_plan=p,
                sprint_index=sprint_index,
                sprint=sprint,
                sprint_result=result,
                measurement=m,
            )


class SprintOrchestrator:
    """Sprint 交付编排（Scrum：按 Release Plan 顺序执行多个 Sprint）。"""

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

    def _build_sprint_hooks(self, release_plan: PRD) -> SprintLifecycleHooks:
        return ChainedSprintHooks(
            (
                KnowledgeInjectionHook(self._project_root, self.config),
                _OrchestratorSprintHooks(self, release_plan),
            )
        )

    def _base_runner_context(self, release_plan: PRD) -> Dict[str, Any]:
        """每 Sprint 的索引/目标由 SprintExecutor 在编排循环内写入 context。"""
        raw = (release_plan.project.path or self._project_root or ".").strip()
        try:
            proj = str(Path(raw).resolve())
        except Exception:
            proj = raw or "."
        meta = getattr(release_plan, "metadata", None) or {}
        return {
            "project_path": proj,
            "release_plan_name": release_plan.project.name,
            "release_plan_id": str(meta.get("id", "")),
            "coding_engine": self.config.coding_engine,
            "quality_level": self.config.effective_quality_level(),
        }

    async def _post_sprint_measurement(self, release_plan: PRD) -> Optional[MeasurementResult]:
        """每个 Sprint 结束后按 quality_level 运行测量（与 RuntimeConfig 一致）。返回测量结果供知识卡片等复用。"""
        from ..config.quality import runs_pytest
        from ..evolution.measurement import MeasurementProvider

        if not runs_pytest(self.config.effective_quality_level()):
            return None
        raw_root = release_plan.project.path or self._project_root
        try:
            repo = str(Path(raw_root).resolve())
        except Exception:
            repo = raw_root or "."
        prov = MeasurementProvider(repo_path=repo, runtime_config=self.config)
        m = prov.measure_all()
        if not prov.check_quality_gate(m):
            logger.warning(
                "Sprint 后质量测量未通过: level=%s overall=%.2f correctness=%.2f details=%s",
                self.config.effective_quality_level(),
                m.overall,
                m.correctness,
                m.details,
            )
        return m

    async def execute_release_plan(self, release_plan: PRD, max_concurrent: int = 3) -> List[SprintResult]:
        await self._emit(create_event(EventType.EXECUTION_START, execution_id=getattr(release_plan, 'execution_id', None), message=f"开始执行 PRD: {release_plan.project.name}", sprint_name=release_plan.project.name, sprint_number=0))
        logger.info(f"🚀 开始执行 PRD: {release_plan.project.name} | 模式: {release_plan.mode.value} | Sprint: {len(release_plan.sprints)} | 任务: {release_plan.total_tasks}")
        results = await (self._execute_evolution_mode(release_plan) if release_plan.is_evolution_mode else self._execute_normal_mode(release_plan, max_concurrent))
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        await self._emit(create_event(EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED, execution_id=getattr(release_plan, 'execution_id', None), message="PRD 执行完成", sprint_name=release_plan.project.name, sprint_number=len(results), status="success" if success else "failed"))
        total_success = sum(r.success_count for r in results)
        total_tasks = sum(len(r.task_results) for r in results)
        logger.info(f"\n📊 PRD 执行完成: 任务={total_tasks} 成功={total_success} 失败={total_tasks - total_success} 耗时={sum(r.duration for r in results):.2f}s")
        return results

    async def resume_from_sprint(self, release_plan: PRD, resume_from_idx: int, previous_results: List[SprintResult], max_concurrent: int = 3) -> List[SprintResult]:
        await self._emit(create_event(EventType.EXECUTION_START, execution_id=getattr(release_plan, 'execution_id', None), message=f"断点续跑: 从 Sprint {resume_from_idx} 继续", sprint_name=release_plan.project.name, sprint_number=resume_from_idx))
        logger.info(f"🔄 断点续跑: 从 Sprint {resume_from_idx} 继续 | PRD: {release_plan.project.name} | 已有: {len(previous_results)} | 待执行: {len(release_plan.sprints) - resume_from_idx}")
        results = list(previous_results)
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_release_plan(release_plan)
        ex.set_sprint_hooks(self._build_sprint_hooks(release_plan))
        ctx = self._base_runner_context(release_plan)
        tail = await ex.execute_sprints(
            release_plan.sprints[resume_from_idx:],
            mode="normal",
            context=ctx,
            release_plan=release_plan,
            sprint_index_offset=resume_from_idx,
        )
        results.extend(tail)
        for sprint_result in tail:
            if sprint_result.status == ExecutionStatus.FAILED and sprint_result.failed_count > sprint_result.success_count:
                logger.warning(f"⚠️  Sprint '{sprint_result.sprint.name}' 失败率较高")
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        await self._emit(create_event(EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED, execution_id=getattr(release_plan, 'execution_id', None), message="断点续跑完成", sprint_name=release_plan.project.name, sprint_number=len(results), status="success" if success else "failed"))
        return results

    async def _execute_normal_mode(self, release_plan: PRD, max_concurrent: int) -> List[SprintResult]:
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_release_plan(release_plan)
        ex.set_sprint_hooks(self._build_sprint_hooks(release_plan))
        ctx = self._base_runner_context(release_plan)
        return await ex.execute_sprints(
            release_plan.sprints,
            mode="normal",
            context=ctx,
            release_plan=release_plan,
            sprint_index_offset=0,
        )

    @staticmethod
    def _infer_evolution_strategy(goals: List[str]) -> str:
        goals_text = " ".join(goals).lower()
        if any(kw in goals_text for kw in ["性能", "速度", "performance", "latency", "吞吐"]): return "performance"
        elif any(kw in goals_text for kw in ["可读", "可维护", "readability", "maintainability", "文档"]): return "readability"
        elif any(kw in goals_text for kw in ["重构", "拆分", "refactor", "架构"]): return "refactoring"
        return "quality"

    async def _execute_evolution_mode(self, release_plan: PRD) -> List[SprintResult]:
        if not release_plan.evolution:
            logger.error("❌ 自进化模式缺少 evolution 配置")
            return []
        if not self.evolution_pipeline:
            self.evolution_pipeline = EvolutionPipeline(
                self._project_root, config=self.config, plan_source=DiagnosticPRDSource()
            )
        strategy = self._infer_evolution_strategy(release_plan.evolution.goals)
        logger.info(f"🧬 自进化策略: {strategy} | 目标: {release_plan.evolution.goals}")
        results: List[SprintResult] = []
        for target in release_plan.evolution.targets:
            sprint = PRDSprint(name=f"进化: {target}", goals=release_plan.evolution.goals, tasks=[
                PRDTask(description=f"架构设计: {target}", agent="architect", target=target),
                PRDTask(description=f"进化 {target}", agent="evolver", target=target),
                PRDTask(description=f"验证进化结果: {target}", agent="tester", target=target),
                PRDTask(description=f"回归测试: {target}", agent="regression_tester", target=target),
            ])
            results.append(await self._execute_evolution_task(sprint, release_plan, SprintContext(sprint_id=f"evo-{int(time.time())}", sprint_number=1, goal="; ".join(release_plan.evolution.goals) if release_plan.evolution.goals else "优化代码", constraints={"dimensions": getattr(self.config, "eval_dimensions", ["correctness", "performance"]), "strategy": strategy}), target))
        return results

    async def _execute_sprint(self, sprint: PRDSprint, release_plan: PRD, max_concurrent: int, sprint_number: int = 1) -> SprintResult:
        start_time = datetime.now()
        self._callbacks["on_sprint_start"](sprint)
        await self._emit(create_event(EventType.SPRINT_START, sprint_number=sprint_number, sprint_name=sprint.name, message=f"开始 Sprint: {sprint.name}"))
        logger.info(f"\n📦 开始 Sprint: {sprint.name}" + (f" | 🎯 {' '.join(sprint.goals)}" if sprint.goals else ""))
        processed_results = await self._run_tasks_concurrent(sprint, release_plan, max_concurrent, sprint_number)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        status = self._determine_sprint_status(processed_results)
        sprint_result = SprintResult(sprint=sprint, status=status, task_results=processed_results, duration=duration, start_time=start_time, end_time=end_time)
        self._callbacks["on_sprint_end"](sprint_result)
        logger.info(f"   完成: {sprint_result.success_count}/{len(sprint.tasks)} 成功 ({duration:.2f}s)")
        return sprint_result

    async def _run_tasks_concurrent(self, sprint: PRDSprint, release_plan: PRD, max_concurrent: int, sprint_number: int = 1) -> List[TaskResult]:
        semaphore = asyncio.Semaphore(max_concurrent)
        async def execute_with_semaphore(task: PRDTask, task_idx: int) -> TaskResult:
            async with semaphore:
                return await self._execute_task(task, sprint.name, release_plan, task_idx, sprint_number)
        task_results = await asyncio.gather(*[execute_with_semaphore(t, i) for i, t in enumerate(sprint.tasks)], return_exceptions=True)
        return self._process_task_results(sprint, task_results)

    def _process_task_results(self, sprint: PRDSprint, task_results: List[Any]) -> List[TaskResult]:
        processed_results: List[TaskResult] = []
        for i, result in enumerate(task_results):
            if isinstance(result, Exception):
                processed_results.append(TaskResult(work_item=sprint.tasks[i], sprint_name=sprint.name, status=ExecutionStatus.FAILED, error=str(result)))
            else:
                processed_results.append(result)  # type: ignore[arg-type]
        return processed_results

    def _determine_sprint_status(self, results: List[TaskResult]) -> ExecutionStatus:
        if all(r.status == ExecutionStatus.SUCCESS for r in results): return ExecutionStatus.SUCCESS
        if all(r.status in (ExecutionStatus.SKIPPED, ExecutionStatus.SUCCESS) for r in results): return ExecutionStatus.SUCCESS
        failed = sum(1 for r in results if r.status == ExecutionStatus.FAILED)
        return ExecutionStatus.FAILED if failed > len(results) / 2 else ExecutionStatus.SUCCESS

    async def _execute_evolution_task(self, sprint: PRDSprint, release_plan: PRD, context: SprintContext, target: str) -> SprintResult:
        start_time = datetime.now()
        self._callbacks["on_sprint_start"](sprint)
        logger.info(f"\n🧬 开始自进化: {target}")
        task_result = TaskResult(work_item=sprint.tasks[0], sprint_name=sprint.name, status=ExecutionStatus.RUNNING, start_time=start_time)
        try:
            target_path = Path(release_plan.project.path) / target
            if not target_path.exists(): raise FileNotFoundError(f"目标文件不存在: {target_path}")
            assert self.evolution_pipeline is not None
            from sprintcycle.evolution.evolution_plan_source import EvolutionReleasePlan

            evo_plan = EvolutionReleasePlan(
                name=f"evo-{sprint.tasks[0].agent}", version="1.0", path=release_plan.project.path
            )
            evo_plan.sprints = [{"name": "evolution", "tasks": [sprint.tasks[0].description]}]
            evo_result = await self.evolution_pipeline.execute_async(evo_plan)
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

    async def _execute_task(self, task: PRDTask, sprint_name: str, release_plan: PRD, task_index: int, sprint_number: int) -> TaskResult:
        start_time = datetime.now()
        self._callbacks["on_task_start"](task)
        await self._emit(create_event(EventType.TASK_START, sprint_number=sprint_number, sprint_name=sprint_name, agent_type=task.agent, description=task.description, message=f"开始任务: {task.description[:50]}..." if len(task.description) > 50 else f"开始任务: {task.description}"))
        result = TaskResult(work_item=task, sprint_name=sprint_name, status=ExecutionStatus.RUNNING, start_time=start_time)
        try:
            logger.info(f"   📋 {task.agent}: {task.description[:60]}...")
            if task.agent == "evolver": result = await self._execute_evolver_task(task, release_plan, result)
            elif task.agent == "tester": result = await self._execute_tester_task(task, release_plan, result)
            else: result = await self._execute_coder_task(task, release_plan, result)
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"任务超时 ({task.timeout}s)"
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            logger.exception("任务执行失败")
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds() if result.start_time else 0.0
        self._callbacks["on_task_end"](result)
        if result.status == ExecutionStatus.FAILED:
            await self._emit(create_event(EventType.TASK_FAILED, sprint_number=sprint_number, sprint_name=sprint_name, agent_type=task.agent, description=task.description, status="failed", error=result.error, duration=result.duration))
        else:
            await self._emit(create_event(EventType.TASK_COMPLETE, sprint_number=sprint_number, sprint_name=sprint_name, agent_type=task.agent, description=task.description, status="success" if result.status == ExecutionStatus.SUCCESS else "skipped", duration=result.duration))
        return result

    async def _execute_coder_task(self, task: PRDTask, release_plan: PRD, result: TaskResult) -> TaskResult:
        await asyncio.sleep(0.1)
        result.status = ExecutionStatus.SUCCESS
        result.output = f"Coder 任务完成: {task.description[:50]}..."
        return result

    async def _execute_evolver_task(self, task: PRDTask, release_plan: PRD, result: TaskResult) -> TaskResult:
        if not task.target:
            result.status = ExecutionStatus.FAILED
            result.error = "evolver 任务必须指定 target"
            return result
        if not self.evolution_pipeline:
            self.evolution_pipeline = EvolutionPipeline(
                ".", config=self.config, plan_source=DiagnosticPRDSource()
            )
        try:
            from sprintcycle.evolution.evolution_plan_source import EvolutionReleasePlan

            evo_plan = EvolutionReleasePlan(
                name=f"evolution-{task.target}",
                version="1.0",
                path=".",
                goals=[task.description],
                sprints=[
                    {
                        "name": f"evo-{task.target}",
                        "tasks": [
                            {
                                "description": task.description,
                                "agent": "evolver",
                                "target": task.target,
                            }
                        ],
                    }
                ],
            )
            evo_result = await self.evolution_pipeline.execute_async(evo_plan)
            result.status = ExecutionStatus.SUCCESS if evo_result.success else ExecutionStatus.FAILED
            result.output = f"进化执行完成: {evo_result.completed_sprints} 个Sprint" if evo_result.success else ""
            result.error = evo_result.error if not evo_result.success else None
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
        return result

    async def _execute_tester_task(self, task: PRDTask, release_plan: PRD, result: TaskResult) -> TaskResult:
        await asyncio.sleep(0.1)
        result.status = ExecutionStatus.SUCCESS
        result.output = f"Tester 任务完成: {task.description[:50]}..."
        return result

    def _default_on_task_start(self, task: PRDTask) -> None: pass
    def _default_on_task_end(self, result: TaskResult) -> None:
        if result.status == ExecutionStatus.FAILED: logger.error(f"   ❌ 任务失败: {result.error}")
        elif result.status == ExecutionStatus.SUCCESS: logger.info("   ✅ 任务成功")
    def _default_on_sprint_start(self, sprint: PRDSprint) -> None: pass
    def _default_on_sprint_end(self, result: SprintResult) -> None:
        if result.status == ExecutionStatus.FAILED: logger.warning("   ⚠️  Sprint 失败率较高")

    def get_summary(self) -> Dict[str, Any]:
        return {"evolution_pipeline": self.evolution_pipeline is not None, "callbacks": list(self._callbacks.keys()), "event_bus": self.event_bus is not None}
