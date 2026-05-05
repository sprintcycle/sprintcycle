"""
Sprint 执行编排（主实现模块；类 ``SprintOrchestrator``）

**Scrum 语境**：本模块负责把 **Release Plan**（``ReleasePlan`` YAML）转为按 Sprint 顺序的**交付编排**，
不是日历「排期」。``execute_release_plan`` / ``resume_from_sprint`` 即一次 **Sprint 序列的执行**。

**主执行路径**：``SprintCycle.run`` / 断点续跑经 ``SprintOrchestrator.execute_release_plan``；
自进化模式在入口由 ``expand_release_plan_for_execution`` 展开为与普通模式相同的 ``sprints``，
随后统一由 ``SprintExecutor.execute_sprints`` 驱动。
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ..config import RuntimeConfig
from ..evolution.measurement import MeasurementResult
from ..evolution.pipeline import EvolutionPipeline
from ..execution.events import Event, EventBus, EventType, create_event, get_event_bus
from ..execution.feedback import FeedbackLoop
from ..execution.hooks.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks
from ..execution.knowledge.knowledge_hook import KnowledgeInjectionHook
from ..execution.sprint_executor import SprintExecutor
from ..execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from ..release_plan.expand import expand_release_plan_for_execution
from ..release_plan.models import ReleasePlan, SprintDefinition, SprintBacklogItem


class _OrchestratorSprintHooks(SprintLifecycleHooks):
    """由 ``SprintOrchestrator`` 注入：在 Sprint 边界发事件、调回调、跑测量与知识卡片落盘。"""

    def __init__(self, orchestrator: "SprintOrchestrator", release_plan: ReleasePlan):
        self._orchestrator = orchestrator
        self._release_plan = release_plan

    async def on_before_sprint(
        self,
        sprint_index: int,
        sprint: SprintDefinition,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
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
        sprint: SprintDefinition,
        result: SprintResult,
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan],
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

    def _build_sprint_hooks(self, release_plan: ReleasePlan) -> SprintLifecycleHooks:
        return ChainedSprintHooks(
            (
                KnowledgeInjectionHook(self._project_root, self.config),
                _OrchestratorSprintHooks(self, release_plan),
            )
        )

    def _base_runner_context(self, release_plan: ReleasePlan) -> Dict[str, Any]:
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

    async def _post_sprint_measurement(self, release_plan: ReleasePlan) -> Optional[MeasurementResult]:
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

    async def execute_release_plan(self, release_plan: ReleasePlan, max_concurrent: int = 3) -> List[SprintResult]:
        original_mode = release_plan.mode.value
        to_run = expand_release_plan_for_execution(release_plan)
        await self._emit(
            create_event(
                EventType.EXECUTION_START,
                execution_id=getattr(release_plan, "execution_id", None),
                message=f"开始执行 ReleasePlan: {to_run.project.name}",
                sprint_name=to_run.project.name,
                sprint_number=0,
            )
        )
        logger.info(
            f"🚀 开始执行 ReleasePlan: {to_run.project.name} | 原始模式: {original_mode} | "
            f"执行 Sprint 数: {len(to_run.sprints)} | 任务: {to_run.total_tasks}"
        )
        results = await self._execute_normal_mode(to_run, max_concurrent)
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        await self._emit(
            create_event(
                EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED,
                execution_id=getattr(release_plan, "execution_id", None),
                message="ReleasePlan 执行完成",
                sprint_name=to_run.project.name,
                sprint_number=len(results),
                status="success" if success else "failed",
            )
        )
        total_success = sum(r.success_count for r in results)
        total_tasks = sum(len(r.task_results) for r in results)
        logger.info(
            f"\n📊 ReleasePlan 执行完成: 任务={total_tasks} 成功={total_success} "
            f"失败={total_tasks - total_success} 耗时={sum(r.duration for r in results):.2f}s"
        )
        return results

    async def resume_from_sprint(
        self,
        release_plan: ReleasePlan,
        resume_from_idx: int,
        previous_results: List[SprintResult],
        max_concurrent: int = 3,
    ) -> List[SprintResult]:
        to_run = expand_release_plan_for_execution(release_plan)
        await self._emit(
            create_event(
                EventType.EXECUTION_START,
                execution_id=getattr(release_plan, "execution_id", None),
                message=f"断点续跑: 从 Sprint {resume_from_idx} 继续",
                sprint_name=to_run.project.name,
                sprint_number=resume_from_idx,
            )
        )
        logger.info(
            f"🔄 断点续跑: 从 Sprint {resume_from_idx} 继续 | ReleasePlan: {to_run.project.name} | "
            f"已有: {len(previous_results)} | 待执行: {len(to_run.sprints) - resume_from_idx}"
        )
        results = list(previous_results)
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_release_plan(to_run)
        ex.set_sprint_hooks(self._build_sprint_hooks(to_run))
        ctx = self._base_runner_context(to_run)
        tail = await ex.execute_sprints(
            to_run.sprints[resume_from_idx:],
            mode="normal",
            context=ctx,
            release_plan=to_run,
            sprint_index_offset=resume_from_idx,
        )
        results.extend(tail)
        for sprint_result in tail:
            if sprint_result.status == ExecutionStatus.FAILED and sprint_result.failed_count > sprint_result.success_count:
                logger.warning(f"⚠️  Sprint '{sprint_result.sprint.name}' 失败率较高")
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        await self._emit(
            create_event(
                EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED,
                execution_id=getattr(release_plan, "execution_id", None),
                message="断点续跑完成",
                sprint_name=to_run.project.name,
                sprint_number=len(results),
                status="success" if success else "failed",
            )
        )
        return results

    async def _execute_via_sprint_executor(
        self, release_plan: ReleasePlan, max_concurrent: int
    ) -> List[SprintResult]:
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

    async def _execute_normal_mode(
        self, release_plan: ReleasePlan, max_concurrent: int
    ) -> List[SprintResult]:
        """与 ``_execute_via_sprint_executor`` 相同（保留名称供测试与外部补丁）。"""
        return await self._execute_via_sprint_executor(release_plan, max_concurrent)

    def _default_on_task_start(self, task: SprintBacklogItem) -> None:
        pass

    def _default_on_task_end(self, result: TaskResult) -> None:
        if result.status == ExecutionStatus.FAILED:
            logger.error(f"   ❌ 任务失败: {result.error}")
        elif result.status == ExecutionStatus.SUCCESS:
            logger.info("   ✅ 任务成功")

    def _default_on_sprint_start(self, sprint: SprintDefinition) -> None:
        pass

    def _default_on_sprint_end(self, result: SprintResult) -> None:
        if result.status == ExecutionStatus.FAILED:
            logger.warning("   ⚠️  Sprint 失败率较高")

    def get_summary(self) -> Dict[str, Any]:
        return {
            "evolution_pipeline": self.evolution_pipeline is not None,
            "callbacks": list(self._callbacks.keys()),
            "event_bus": self.event_bus is not None,
        }
