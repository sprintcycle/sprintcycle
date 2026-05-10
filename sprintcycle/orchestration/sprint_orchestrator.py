"""
Sprint 执行编排（主实现模块；类 ``SprintOrchestrator``）

本模块负责将 ``ReleasePlan`` 编排为按 Sprint 顺序执行的交付流程。
``execute_release_plan`` 与 ``resume_from_sprint`` 是主入口，``SprintCycle.run`` 也会经此模块。
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ..config import RuntimeConfig
from ..evolution.measurement import MeasurementResult
from .finalization import ReleaseFinalizationPolicy, ReleaseFinalizationRunner
from .policies import SprintEvaluator, SprintMeasurementPolicy, SprintPersistencePolicy
from ..execution.events import (
    Event,
    EventType,
    ExecutionEventBackend,
    create_event,
    get_execution_event_backend,
)
from ..execution.protocols import ExecutionContext, SkillTrace
from ..execution.feedback import FeedbackLoop
from ..execution.hooks.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks
from ..execution.hooks.skill_hooks import SkillLifecycleHook
from ..execution.skills import SkillOrchestrator
from ..execution.skill_store import SkillStore
from ..execution.hooks.task_hooks import ChainedTaskHooks, TaskLifecycleHooks
from ..execution.knowledge.knowledge_hook import KnowledgeInjectionHook
from ..execution.sprint_executor import SprintExecutor
from ..execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from ..governance.sprint_hooks import GovernanceSprintHooks
from ..governance.task_hooks import GovernanceTaskLifecycleHooks
from ..verification.hooks import VerificationSprintHooks
from ..prompt_sources import compute_prompt_sources_fingerprint
from ..release_plan.expand import expand_release_plan_for_execution
from ..release_plan.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from ..evolution.intent_evolution_loop import UserIntentEvolutionLoop
from ..evolution.intent_evolution_loop import UserIntentEvolutionLoop
from ..evolution.memory_store import MemoryStore
from ..persistence.knowledge_repository import KnowledgeCardRepository
from ..integrations.langgraph.runtime import LangGraphRuntimeAdapter
from ..integrations.phoenix.trace_runtime import PhoenixTraceRuntime
from ..integrations.phoenix.exporter import PhoenixExporterSpec


class SprintOrchestrator:
    """Sprint 交付编排（Scrum：按 Release Plan 顺序执行多个 Sprint）。"""

    def __init__(self, config: Optional[RuntimeConfig] = None, event_bus: Optional[ExecutionEventBackend] = None, project_path: Optional[str] = None, hitl_coordinator: Optional[Any] = None, evolution_loop: Optional[UserIntentEvolutionLoop] = None):
        self.config = config or RuntimeConfig()
        self._project_root = os.path.abspath(project_path or ".")
        self.event_bus = event_bus
        self._hitl_coordinator = hitl_coordinator
        self._evolution_loop = evolution_loop or UserIntentEvolutionLoop(memory_store=MemoryStore(runtime_config=self.config), feedback_loop=FeedbackLoop(), knowledge_repo=KnowledgeCardRepository(".sprintcycle/knowledge.db"))
        self._callbacks: Dict[str, Callable] = {
            "on_task_start": self._default_on_task_start,
            "on_task_end": self._default_on_task_end,
            "on_sprint_start": self._default_on_sprint_start,
            "on_sprint_end": self._default_on_sprint_end,
        }
        self._sprint_evaluator = SprintEvaluator()
        self._sprint_measurement_policy = SprintMeasurementPolicy()
        self._sprint_persistence_policy = SprintPersistencePolicy()
        self._release_finalization_runner = ReleaseFinalizationRunner(ReleaseFinalizationPolicy(), sprint_executor_factory=self._make_sprint_executor)
        self._skill_store = SkillStore()
        self._skill_orchestrator = SkillOrchestrator()
        self._last_release_finalization_result = None
        self._langgraph_runtime = LangGraphRuntimeAdapter()
        self._phoenix_runtime = PhoenixTraceRuntime(PhoenixExporterSpec(project_name=self._project_root))

    def _get_event_bus(self) -> ExecutionEventBackend:
        if self.event_bus is None:
            self.event_bus = get_execution_event_backend()
        return self.event_bus

    async def _emit(self, event: Event) -> None:
        try:
            await self._get_event_bus().emit(event)
        except Exception as e:
            logger.warning(f"Failed to emit event: {e}")

    def _emit_trace_event(self, event: Event) -> None:
        try:
            self._phoenix_runtime.emit_trace([event.to_dict()])
        except Exception as e:
            logger.warning("Failed to emit trace event: {}", e)

    def _emit_execution_phase(self, event_type: EventType, message: str, release_plan: ReleasePlan, sprint_name: str, sprint_number: int, status: Optional[str] = None) -> Event:
        event = create_event(
            event_type,
            execution_id=getattr(release_plan, "execution_id", None),
            message=message,
            sprint_name=sprint_name,
            sprint_number=sprint_number,
            status=status,
        )
        return event

    def _make_sprint_executor(self, max_concurrent: int) -> SprintExecutor:
        feedback_loop: Optional[FeedbackLoop] = None
        if not getattr(self.config, "dry_run", False):
            feedback_loop = FeedbackLoop()
        ex = SprintExecutor(max_parallel=max_concurrent, max_verify_fix_rounds=int(self.config.max_verify_fix_rounds), runtime_config=self.config, feedback_loop=feedback_loop, evolution_loop=self._evolution_loop)
        ex.set_event_bus(self._get_event_bus())
        task_hooks: Optional[TaskLifecycleHooks] = None
        if getattr(self.config, "governance_enabled", False) and getattr(self.config, "governance_task_hooks_enabled", False):
            task_hooks = GovernanceTaskLifecycleHooks(self.config, self._project_root, self._get_event_bus())
        if self._hitl_coordinator is not None and getattr(self.config, "hitl_enabled", False):
            from ..hitl.hooks import HitlTaskHooks
            hitl_th = HitlTaskHooks(self.config, self._hitl_coordinator)
            if task_hooks is not None:
                task_hooks = ChainedTaskHooks((hitl_th, task_hooks))
            else:
                task_hooks = hitl_th
        if task_hooks is not None:
            ex.set_task_hooks(task_hooks)
        return ex

    def _build_sprint_hooks(self, release_plan: ReleasePlan) -> SprintLifecycleHooks:
        parts: List[SprintLifecycleHooks] = [KnowledgeInjectionHook(self._project_root, self.config), SkillLifecycleHook(self._skill_orchestrator, self._skill_store)]
        if getattr(self.config, "governance_enabled", False):
            parts.append(GovernanceSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if getattr(self.config, "verification_enabled", False):
            parts.append(VerificationSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if self._hitl_coordinator is not None:
            from ..hitl.hooks import HitlSprintHooks
            parts.append(HitlSprintHooks(self.config, self._hitl_coordinator))
        parts.append(_OrchestratorSprintHooks(self, release_plan))
        return ChainedSprintHooks(tuple(parts))

    def _base_runner_context(self, release_plan: ReleasePlan) -> ExecutionContext:
        raw = (release_plan.project.path or self._project_root or ".").strip()
        try:
            proj = str(Path(raw).resolve())
        except Exception:
            proj = raw or "."
        meta = getattr(release_plan, "metadata", None) or {}
        return ExecutionContext(project_path=proj, release_plan_id=str(meta.get("id", "")), coding_engine=getattr(self.config, "coding_engine", "cursor"), quality_level=self.config.effective_quality_level(), project_goals=getattr(release_plan.project, "goals", "") if hasattr(release_plan.project, "goals") else "", metadata={"release_plan_name": release_plan.project.name, "release_plan": release_plan}, codebase_context={})

    def _persist_release_finalization(self, release_plan: ReleasePlan, finalize_result: Any) -> None:
        try:
            from ..execution.state.state_store import get_state_store
            eid = getattr(release_plan, "execution_id", None)
            if not eid:
                return
            store = get_state_store()
            state = store.load(eid)
            if state is None:
                return
            state.metadata["release_finalization"] = finalize_result.to_dict() if hasattr(finalize_result, "to_dict") else {}
            store.save(state)
        except Exception as e:
            logger.warning("persist release finalization failed: {}", e)

    async def _post_sprint_measurement(self, release_plan: ReleasePlan, *, sprint_index: int = 0, sprint: Optional[SprintDefinition] = None, sprint_result: Optional[SprintResult] = None) -> Optional[MeasurementResult]:
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
        m.details["run_metadata"] = _measurement_run_metadata(self.config, release_plan=release_plan, sprint_index=sprint_index, sprint=sprint, sprint_result=sprint_result)
        if not prov.check_quality_gate(m):
            logger.warning("Sprint 后质量测量未通过: level=%s overall=%.2f correctness=%.2f details=%s", self.config.effective_quality_level(), m.overall, m.correctness, m.details)
        return m

    async def execute_release_plan(self, release_plan: ReleasePlan, max_concurrent: int = 3) -> List[SprintResult]:
        to_run = expand_release_plan_for_execution(release_plan)
        await self._emit(self._emit_execution_phase(EventType.EXECUTION_START, f"开始执行 ReleasePlan: {to_run.project.name}", release_plan, to_run.project.name, 0))
        self._emit_trace_event(self._emit_execution_phase(EventType.EXECUTION_START, "trace:start", release_plan, to_run.project.name, 0))
        self._langgraph_runtime.build()
        results = await self._execute_normal_mode(to_run, max_concurrent)
        finalize_result = await self._release_finalization_runner.run(to_run, results, context={"execution_id": getattr(release_plan, "execution_id", None)})
        self._last_release_finalization_result = finalize_result
        self._persist_release_finalization(release_plan, finalize_result)
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        complete_event = self._emit_execution_phase(EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED, "ReleasePlan 执行完成", release_plan, to_run.project.name, len(results), status="success" if success else "failed")
        await self._emit(complete_event)
        self._emit_trace_event(complete_event)
        return results

    async def resume_from_sprint(self, release_plan: ReleasePlan, resume_from_idx: int, previous_results: List[SprintResult], max_concurrent: int = 3) -> List[SprintResult]:
        to_run = expand_release_plan_for_execution(release_plan)
        await self._emit(self._emit_execution_phase(EventType.EXECUTION_START, f"断点续跑: 从 Sprint {resume_from_idx} 继续", release_plan, to_run.project.name, resume_from_idx))
        self._emit_trace_event(self._emit_execution_phase(EventType.EXECUTION_START, "trace:resume:start", release_plan, to_run.project.name, resume_from_idx))
        results = list(previous_results)
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_release_plan(to_run)
        ex.set_sprint_hooks(self._build_sprint_hooks(to_run))
        ctx = self._base_runner_context(to_run)
        tail = await ex.execute_sprints(to_run.sprints[resume_from_idx:], mode="normal", context=ctx, release_plan=to_run, sprint_index_offset=resume_from_idx)
        results.extend(tail)
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        complete_event = self._emit_execution_phase(EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED, "断点续跑完成", release_plan, to_run.project.name, len(results), status="success" if success else "failed")
        await self._emit(complete_event)
        self._emit_trace_event(complete_event)
        return results

    async def _execute_via_sprint_executor(self, release_plan: ReleasePlan, max_concurrent: int) -> List[SprintResult]:
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_release_plan(release_plan)
        ex.set_sprint_hooks(self._build_sprint_hooks(release_plan))
        ctx = self._base_runner_context(release_plan)
        return await ex.execute_sprints(release_plan.sprints, mode="normal", context=ctx, release_plan=release_plan, sprint_index_offset=0)

    async def _execute_normal_mode(self, release_plan: ReleasePlan, max_concurrent: int) -> List[SprintResult]:
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
            logger.warning("Sprint 失败率较高")

    def get_summary(self) -> Dict[str, Any]:
        return {"callbacks": list(self._callbacks.keys()), "event_bus": self.event_bus is not None}
