"""
SprintOrchestrator - 统一的 Sprint 交付编排器

本模块负责将 ReleasePlan 编排为按 Sprint 顺序执行的交付流程。
execute_release_plan 与 resume_from_sprint 是主入口。

**分层**：所有基础设施依赖通过依赖注入提供，不直接依赖 Infrastructure。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from sprintcycle.domain.supporting.verification.hooks import VerificationSprintHooks
from sprintcycle.domain.core.execution.core.events import (
    Event,
    EventType,
    ExecutionEventBackend,
    create_event,
    get_execution_event_backend,
)
from sprintcycle.domain.core.execution.core.feedback import FeedbackLoop
from sprintcycle.domain.core.execution.hooks.skill_hooks import SkillLifecycleHook
from sprintcycle.domain.core.execution.hooks.sprint_hooks import (
    ChainedSprintHooks,
    SprintLifecycleHooks,
    _measurement_run_metadata,
    _OrchestratorSprintHooks,
)
from sprintcycle.domain.core.execution.hooks.task_hooks import ChainedTaskHooks, TaskLifecycleHooks
from sprintcycle.domain.core.execution.planners.expand import expand_release_plan_for_execution
from sprintcycle.domain.generic.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from sprintcycle.domain.core.execution.core.protocols import ExecutionContext
from sprintcycle.domain.core.execution.agents.skill_store import SkillStore
from sprintcycle.domain.core.execution.agents.skills import SkillOrchestrator
from sprintcycle.domain.core.execution.orchestrator.sprint_executor import SprintExecutor
from sprintcycle.domain.generic.interfaces import ExecutionStatus, SprintResult, TaskResult
from sprintcycle.domain.core.governance.hooks.sprint_hooks import GovernanceSprintHooks
from sprintcycle.domain.core.governance.hooks.task_hooks import GovernanceTaskLifecycleHooks
from sprintcycle.domain.core.evolution.intent_evolution_loop import UserIntentEvolutionLoop
from sprintcycle.domain.core.evolution.measurement import MeasurementResult
from sprintcycle.domain.generic.interfaces.protocols import OrchestrationProtocol
from sprintcycle.application.services.lifecycle.lifecycle_contracts import build_lifecycle_contract
from sprintcycle.domain.generic.ports.orchestration import (
    OrchestrationDependencies,
    RuntimeConfigPort,
)


class SprintOrchestrator:
    """Sprint 交付编排（按 Release Plan 顺序执行多个 Sprint）。"""

    def __init__(
        self,
        dependencies: Optional[OrchestrationDependencies] = None,
        event_bus: Optional[ExecutionEventBackend] = None,
        project_path: Optional[str] = None,
        hitl_coordinator: Optional[Any] = None,
        evolution_loop: Optional[UserIntentEvolutionLoop] = None,
    ):
        self._dependencies = dependencies
        self.config: RuntimeConfigPort = dependencies.runtime_config if dependencies else self._create_default_config()
        self._project_root = os.path.abspath(project_path or ".")
        self.event_bus = event_bus
        self._hitl_coordinator = hitl_coordinator
        self._evolution_loop = evolution_loop or self._create_evolution_loop()
        self._callbacks: Dict[str, Callable] = {
            "on_task_start": self._default_on_task_start,
            "on_task_end": self._default_on_task_end,
            "on_sprint_start": self._default_on_sprint_start,
            "on_sprint_end": self._default_on_sprint_end,
        }
        self._skill_store = SkillStore()
        self._skill_orchestrator = SkillOrchestrator()
        self._last_release_finalization_result: Optional[Dict[str, Any]] = None

    def _create_default_config(self) -> RuntimeConfigPort:
        """创建默认配置（仅在未提供依赖时使用）"""
        from sprintcycle.application.factories.orchestration import RuntimeConfigAdapter
        return RuntimeConfigAdapter()

    def _create_evolution_loop(self) -> UserIntentEvolutionLoop:
        """创建演化循环"""
        knowledge_repo = self._dependencies.knowledge_repository if self._dependencies else None
        if knowledge_repo is None:
            from sprintcycle.application.factories.orchestration import KnowledgeRepositoryAdapter
            knowledge_repo = KnowledgeRepositoryAdapter(".sprintcycle/knowledge.db")
        return UserIntentEvolutionLoop(
            memory_store=None,
            feedback_loop=FeedbackLoop(),
            knowledge_repo=knowledge_repo,
        )

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
        trace_runtime = self._dependencies.trace_runtime if self._dependencies else None
        if trace_runtime is not None:
            try:
                trace_runtime.emit_trace([event.to_dict()])
            except Exception as e:
                logger.debug("Failed to emit trace event: {}", e)

    def _make_sprint_executor(self, max_concurrent: int) -> SprintExecutor:
        feedback_loop: Optional[FeedbackLoop] = None
        if not getattr(self.config, "dry_run", False):
            feedback_loop = FeedbackLoop()
        ex = SprintExecutor(
            max_parallel=max_concurrent,
            max_verify_fix_rounds=int(self.config.max_verify_fix_rounds),
            runtime_config=self.config,
            feedback_loop=feedback_loop,
            evolution_loop=self._evolution_loop,
        )
        ex.set_event_bus(self._get_event_bus())
        task_hooks: Optional[TaskLifecycleHooks] = None
        if getattr(self.config, "governance_enabled", False) and getattr(
            self.config, "governance_task_hooks_enabled", False
        ):
            task_hooks = GovernanceTaskLifecycleHooks(self.config, self._project_root, self._get_event_bus())
        if self._hitl_coordinator is not None and getattr(self.config, "hitl_enabled", False):
            from sprintcycle.domain.core.governance.hitl.hooks import HitlTaskHooks

            hitl_th = HitlTaskHooks(self.config, self._hitl_coordinator)
            if task_hooks is not None:
                task_hooks = ChainedTaskHooks((hitl_th, task_hooks))
            else:
                task_hooks = hitl_th
        if task_hooks is not None:
            ex.set_task_hooks(task_hooks)
        return ex

    def _build_sprint_hooks(self, release_plan: ReleasePlan) -> SprintLifecycleHooks:
        knowledge_hook = self._dependencies.knowledge_injection_hook if self._dependencies else None
        if knowledge_hook is None:
            from sprintcycle.application.factories.orchestration import KnowledgeInjectionHookAdapter
            knowledge_hook = KnowledgeInjectionHookAdapter(self._project_root, self.config)

        parts: List[SprintLifecycleHooks] = [
            knowledge_hook,
            SkillLifecycleHook(self._skill_orchestrator, self._skill_store),
        ]
        if getattr(self.config, "governance_enabled", False):
            parts.append(GovernanceSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if getattr(self.config, "verification_enabled", False):
            parts.append(VerificationSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if self._hitl_coordinator is not None:
            from sprintcycle.domain.core.governance.hitl.hooks import HitlSprintHooks

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
        return ExecutionContext(
            project_path=proj,
            release_plan_id=str(meta.get("id", "")),
            coding_engine=getattr(self.config, "coding_engine", "cursor"),
            quality_level=getattr(self.config, "quality_level", "L2"),
            project_goals=getattr(release_plan.project, "goals", "") if hasattr(release_plan.project, "goals") else "",
            metadata={"release_plan_name": release_plan.project.name, "release_plan": release_plan},
            codebase_context={},
        )

    def _persist_release_finalization(self, release_plan: ReleasePlan, finalize_result: Any) -> None:
        try:
            state_store = self._dependencies.state_store if self._dependencies else None
            if state_store is None:
                from sprintcycle.application.factories.orchestration import StateStoreAdapter
                state_store = StateStoreAdapter()

            eid = getattr(release_plan, "execution_id", None)
            if not eid:
                return
            state = state_store.load(eid)
            if state is None:
                return
            state.metadata["release_finalization"] = (
                finalize_result.to_dict() if hasattr(finalize_result, "to_dict") else {}
            )
            state_store.save(state)
        except Exception as e:
            logger.debug("persist release finalization failed: {}", e)

    async def _post_sprint_measurement(
        self,
        release_plan: ReleasePlan,
        *,
        sprint_index: int = 0,
        sprint: Optional[SprintDefinition] = None,
        sprint_result: Optional[SprintResult] = None,
    ) -> Optional[MeasurementResult]:
        from sprintcycle.domain.core.evolution.measurement import MeasurementProvider

        quality_level = self._resolve_effective_quality_level()
        if not self._runs_pytest(quality_level):
            return None
        raw_root = release_plan.project.path or self._project_root
        try:
            repo = str(Path(raw_root).resolve())
        except Exception:
            repo = raw_root or "."
        prov = MeasurementProvider(repo_path=repo, runtime_config=self.config)
        m = prov.measure_all()
        m.details["run_metadata"] = _measurement_run_metadata(
            self.config,
            release_plan=release_plan,
            sprint_index=sprint_index,
            sprint=sprint,
            sprint_result=sprint_result,
        )
        if not prov.check_quality_gate(m):
            logger.warning(
                "Sprint 后质量测量未通过: level=%s overall=%.2f",
                quality_level,
                m.overall,
            )
        return m

    def _resolve_effective_quality_level(self) -> str:
        """解析有效质量级别（通过依赖注入）"""
        quality_config = self._dependencies.quality_config if self._dependencies else None
        if quality_config is None:
            from sprintcycle.application.factories.orchestration import QualityConfigAdapter
            quality_config = QualityConfigAdapter()
        return quality_config.resolve_effective_quality_level(
            getattr(self.config, "quality_profile", ""),
            getattr(self.config, "quality_level", "") or "L2",
        )

    def _runs_pytest(self, quality_level: str) -> bool:
        """检查是否需要运行 pytest（通过依赖注入）"""
        quality_config = self._dependencies.quality_config if self._dependencies else None
        if quality_config is None:
            from sprintcycle.application.factories.orchestration import QualityConfigAdapter
            quality_config = QualityConfigAdapter()
        return quality_config.runs_pytest(quality_level)

    def _compile_intent_graph(self, **kwargs: Any) -> Any:
        """编译意图图（通过依赖注入）"""
        graph_compiler = self._dependencies.graph_compiler if self._dependencies else None
        if graph_compiler is None:
            from sprintcycle.application.factories.orchestration import GraphCompilerAdapter
            graph_compiler = GraphCompilerAdapter()
        return graph_compiler.compile_intent_graph(**kwargs)

    def _compile_sprint_graph(self, **kwargs: Any) -> Any:
        """编译 Sprint 图（通过依赖注入）"""
        graph_compiler = self._dependencies.graph_compiler if self._dependencies else None
        if graph_compiler is None:
            from sprintcycle.application.factories.orchestration import GraphCompilerAdapter
            graph_compiler = GraphCompilerAdapter()
        return graph_compiler.compile_sprint_graph(**kwargs)

    async def execute_release_plan(self, release_plan: ReleasePlan, max_concurrent: int = 3) -> List[SprintResult]:
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
        self._emit_trace_event(
            create_event(
                EventType.EXECUTION_START,
                execution_id=getattr(release_plan, "execution_id", None),
                message="trace:start",
                sprint_name=to_run.project.name,
                sprint_number=0,
            )
        )
        intent_runtime = self._compile_intent_graph(checkpointer=getattr(self.config, "checkpoint_store", None))
        intent_graph = intent_runtime.graph
        intent_context = {
            "project_path": self._project_root,
            "runtime_config": self.config.to_dict() if hasattr(self.config, "to_dict") else {},
            "release_plan": to_run,
            "release_plan_id": getattr(release_plan, "execution_id", None),
        }
        intent_state = {
            "intent": getattr(to_run.project, "name", ""),
            "context": intent_context,
            "release_plan": to_run,
            "status": "pending",
            "attempt": 1,
            "metadata": {
                "execution_id": getattr(release_plan, "execution_id", None),
                "checkpointer": getattr(self.config, "checkpoint_store", None),
            },
        }
        intent_result = await intent_graph.ainvoke(intent_state)
        sprint_results: List[SprintResult] = []
        for sprint_state in intent_result.get("sprint_results", []):
            sprint_payload = sprint_state.get(
                "final_result", sprint_state.get("execution_result", sprint_state.get("sprint_result", {}))
            )
            sprint_name = sprint_payload.get("sprint_name", sprint_state.get("sprint", {}).get("name", ""))
            sprint_status = sprint_payload.get("status", "success")
            raw_task_results = sprint_payload.get("task_results", []) or []
            task_results = []
            for tr in raw_task_results:
                if isinstance(tr, dict):
                    work_item_raw = tr.get("work_item", {})
                    if isinstance(work_item_raw, dict):
                        work_item = SprintBacklogItem(
                            description=work_item_raw.get("description", ""),
                            agent=work_item_raw.get("agent", ""),
                        )
                    else:
                        work_item = work_item_raw
                    task_results.append(
                        TaskResult(
                            work_item=work_item,
                            sprint_name=tr.get("sprint_name", sprint_name),
                            status=ExecutionStatus(tr.get("status", "success")),
                            output=tr.get("output", ""),
                            duration=float(tr.get("duration", 0.0)),
                        )
                    )
            sprint_results.append(
                SprintResult(
                    sprint=type("SprintStub", (), {"name": sprint_name, "goals": []})(),
                    status=ExecutionStatus.SUCCESS
                    if sprint_status in ("success", "skipped")
                    else ExecutionStatus.FAILED,
                    task_results=task_results,
                    duration=float(sprint_payload.get("duration", 0.0)),
                )
            )
        if not sprint_results:
            sprint_results = await self._execute_via_sprint_executor(to_run, max_concurrent)

        try:
            from sprintcycle.domain.core.execution.orchestrator.finalization import (
                ReleaseFinalizationPolicy,
                ReleaseFinalizationRunner,
            )

            runner = ReleaseFinalizationRunner(
                ReleaseFinalizationPolicy(), sprint_executor_factory=self._make_sprint_executor
            )
            finalize_result = await runner.run(
                to_run, sprint_results, context={"execution_id": getattr(release_plan, "execution_id", None)}
            )
            self._last_release_finalization_result = finalize_result
            self._persist_release_finalization(release_plan, finalize_result)
        except Exception as e:
            logger.debug("Finalization skipped: {}", e)

        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in sprint_results)
        completion_summary = {
            "execution_id": getattr(release_plan, "execution_id", None),
            "release_plan_name": getattr(to_run.project, "name", ""),
            "sprint_count": len(sprint_results),
            "success": success,
        }
        skill_matches = (
            list(intent_context.get("skill_matches", []))
            if isinstance(intent_context.get("skill_matches", []), list)
            else []
        )
        skill_trace = (
            dict(intent_context.get("task_skill_trace", {}))
            if isinstance(intent_context.get("task_skill_trace", {}), dict)
            else {}
        )
        contract = build_lifecycle_contract(
            execution_id=getattr(release_plan, "execution_id", ""),
            task_id=getattr(release_plan, "execution_id", "") or getattr(to_run.project, "name", ""),
            project_path=self._project_root,
            stage="delivering",
            status="success" if success else "failed",
            metadata={"release_plan": to_run.project.name, "execution_id": getattr(release_plan, "execution_id", None)},
            delivery_refs={"delivery_summary": completion_summary},
            evolution_refs={"finalization": completion_summary.get("finalization", {})},
            skill_refs=list(skill_matches),
            skill_matches=list(skill_matches),
            skill_review_checklists=list(intent_context.get("review_checklists", []))
            if isinstance(intent_context.get("review_checklists", []), list)
            else [],
            skill_trace=skill_trace,
        )
        complete_event = create_event(
            EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED,
            execution_id=getattr(release_plan, "execution_id", None),
            message="ReleasePlan 执行完成",
            sprint_name=to_run.project.name,
            sprint_number=len(sprint_results),
            status="success" if success else "failed",
        )
        await self._emit(complete_event)
        self._emit_trace_event(complete_event)
        try:
            state_store = self._dependencies.state_store if self._dependencies else None
            if state_store is None:
                from sprintcycle.application.factories.orchestration import StateStoreAdapter
                state_store = StateStoreAdapter()

            if getattr(release_plan, "execution_id", None):
                state = state_store.load(getattr(release_plan, "execution_id", None))
                if state is not None:
                    state.metadata["release_finalization"] = completion_summary
                    state.metadata["lifecycle_contract"] = contract.to_dict()
                    state.status = "success" if success else "failed"
                    state_store.save(state)
        except Exception as e:
            logger.debug("persist sprint orchestration lifecycle failed: {}", e)
        self._last_release_finalization_result = {
            "finalization": completion_summary,
            "lifecycle_contract": contract.to_dict(),
        }
        return sprint_results

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
        self._emit_trace_event(
            create_event(
                EventType.EXECUTION_START,
                execution_id=getattr(release_plan, "execution_id", None),
                message="trace:resume:start",
                sprint_name=to_run.project.name,
                sprint_number=resume_from_idx,
            )
        )
        sprint_runtime = self._compile_sprint_graph(checkpointer=getattr(self.config, "checkpoint_store", None))
        results = list(previous_results)
        for sprint_index, sprint in enumerate(to_run.sprints[resume_from_idx:], start=resume_from_idx):
            sprint_state = {
                "sprint": sprint,
                "context": {
                    "project_name": to_run.project.name,
                    "project_path": self._project_root,
                    "runtime_config": self.config.to_dict() if hasattr(self.config, "to_dict") else {},
                    "sprint_executor": self._make_sprint_executor(max_concurrent),
                },
                "attempt": 1,
                "status": "pending",
                "metadata": {
                    "execution_id": getattr(release_plan, "execution_id", None),
                    "checkpointer": getattr(self.config, "checkpoint_store", None),
                    "resume_from_idx": resume_from_idx,
                    "sprint_index": sprint_index,
                },
            }
            graph_result = await sprint_runtime.graph.ainvoke(sprint_state)
            final_result = dict(
                graph_result.get(
                    "final_sprint_result", graph_result.get("final_result", graph_result.get("sprint_result", {}))
                )
                or {}
            )
            if not final_result:
                final_result = {
                    "sprint_name": getattr(sprint, "name", ""),
                    "status": graph_result.get("status", "failed"),
                    "task_results": [],
                }
            results.append(
                SprintResult(
                    sprint=sprint,
                    status=ExecutionStatus.SUCCESS
                    if str(final_result.get("status", "success")).lower() in ("success", "skipped")
                    else ExecutionStatus.FAILED,
                    task_results=[],
                    duration=float(final_result.get("duration", 0.0)),
                )
            )
        success = all(r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED) for r in results)
        complete_event = create_event(
            EventType.EXECUTION_COMPLETE if success else EventType.EXECUTION_FAILED,
            execution_id=getattr(release_plan, "execution_id", None),
            message="断点续跑完成",
            sprint_name=to_run.project.name,
            sprint_number=len(results),
            status="success" if success else "failed",
        )
        await self._emit(complete_event)
        self._emit_trace_event(complete_event)
        return results

    async def _execute_via_sprint_executor(self, release_plan: ReleasePlan, max_concurrent: int) -> List[SprintResult]:
        """通过 SprintExecutor 直接执行（无 intent graph）"""
        ex = self._make_sprint_executor(max_concurrent)
        ex.set_release_plan(release_plan)
        ex.set_sprint_hooks(self._build_sprint_hooks(release_plan))
        ctx = self._base_runner_context(release_plan)
        return await ex.execute_sprints(
            release_plan.sprints, mode="normal", context=ctx, release_plan=release_plan, sprint_index_offset=0
        )

    def _default_on_task_start(self, task: SprintBacklogItem) -> None:
        pass

    def _default_on_task_end(self, result: TaskResult) -> None:
        if result.status == ExecutionStatus.FAILED:
            logger.error(f"   ❌ 任务失败: {result.error}")
        elif result.status == ExecutionStatus.SUCCESS:
            logger.debug("   ✅ 任务成功")

    def _default_on_sprint_start(self, sprint: SprintDefinition) -> None:
        pass

    def _default_on_sprint_end(self, result: SprintResult) -> None:
        if result.status == ExecutionStatus.FAILED:
            logger.warning("Sprint 失败率较高")

    def get_summary(self) -> Dict[str, Any]:
        contract = (
            self._last_release_finalization_result if isinstance(self._last_release_finalization_result, dict) else {}
        )
        return {
            "callbacks": list(self._callbacks.keys()),
            "event_bus": self.event_bus is not None,
            "last_release_finalization": contract.get("finalization", {}) if isinstance(contract, dict) else {},
            "last_lifecycle_contract": contract.get("lifecycle_contract", {}) if isinstance(contract, dict) else {},
            "has_execution_backbone": True,
        }