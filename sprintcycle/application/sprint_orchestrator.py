"""
SprintOrchestrator - 统一的 Sprint 交付编排器

合并自:
- sprintcycle/application/orchestration/sprint_orchestrator.py
- sprintcycle/execution/orchestrator/sprint_orchestrator.py

本模块负责将 ReleasePlan 编排为按 Sprint 顺序执行的交付流程。
execute_release_plan 与 resume_from_sprint 是主入口。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from ..domain.verification.hooks import VerificationSprintHooks
from ..execution.events import (
    Event,
    EventType,
    ExecutionEventBackend,
    create_event,
    get_execution_event_backend,
)
from ..execution.hooks.sprint_hooks import (
    ChainedSprintHooks,
    SprintLifecycleHooks,
    _OrchestratorSprintHooks,
    _measurement_run_metadata,
)
from ..execution.hooks.task_hooks import ChainedTaskHooks, TaskLifecycleHooks
from ..execution.knowledge.knowledge_hook import KnowledgeInjectionHook
from ..execution.planners.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from ..execution.planners.expand import expand_release_plan_for_execution
from ..execution.protocols import ExecutionContext
from ..execution.skill_store import SkillStore
from ..execution.skills import SkillOrchestrator
from ..execution.sprint_executor import SprintExecutor
from ..execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from ..governance.sprint_hooks import GovernanceSprintHooks
from ..governance.task_hooks import GovernanceTaskLifecycleHooks
from ..infrastructure.config import RuntimeConfig
from ..infrastructure.integrations.langgraph.compiler import compile_intent_graph, compile_sprint_graph
from ..infrastructure.persistence.knowledge_repository import KnowledgeCardRepository
from .evolution.intent_evolution_loop import UserIntentEvolutionLoop
from .evolution.measurement import MeasurementResult
from ..execution.feedback import FeedbackLoop
from ..execution.hooks.skill_hooks import SkillLifecycleHook
from .services.lifecycle_contracts import build_lifecycle_contract

if TYPE_CHECKING:
    from ..infrastructure.integrations.phoenix.trace_runtime import PhoenixTraceRuntime


class SprintOrchestrator:
    """Sprint 交付编排（按 Release Plan 顺序执行多个 Sprint）。"""

    def __init__(
        self,
        config: Optional[RuntimeConfig] = None,
        event_bus: Optional[ExecutionEventBackend] = None,
        project_path: Optional[str] = None,
        hitl_coordinator: Optional[Any] = None,
        evolution_loop: Optional[UserIntentEvolutionLoop] = None,
    ):
        self.config = config or RuntimeConfig()
        self._project_root = os.path.abspath(project_path or ".")
        self.event_bus = event_bus
        self._hitl_coordinator = hitl_coordinator
        self._evolution_loop = evolution_loop or UserIntentEvolutionLoop(
            memory_store=None,
            feedback_loop=FeedbackLoop(),
            knowledge_repo=KnowledgeCardRepository(".sprintcycle/knowledge.db"),
        )
        self._callbacks: Dict[str, Callable] = {
            "on_task_start": self._default_on_task_start,
            "on_task_end": self._default_on_task_end,
            "on_sprint_start": self._default_on_sprint_start,
            "on_sprint_end": self._default_on_sprint_end,
        }
        self._skill_store = SkillStore()
        self._skill_orchestrator = SkillOrchestrator()
        self._last_release_finalization_result: Optional[Dict[str, Any]] = None
        self._phoenix_runtime: Optional["PhoenixTraceRuntime"] = None
        if os.environ.get("PHOENIX_ENABLED"):
            try:
                from ..infrastructure.integrations.phoenix.exporter import PhoenixExporterSpec
                from ..infrastructure.integrations.phoenix.trace_runtime import PhoenixTraceRuntime

                self._phoenix_runtime = PhoenixTraceRuntime(PhoenixExporterSpec(project_name=self._project_root))
            except ImportError:
                logger.debug("Phoenix not available")

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
        if self._phoenix_runtime is not None:
            try:
                self._phoenix_runtime.emit_trace([event.to_dict()])
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
            from ..governance.hitl.hooks import HitlTaskHooks

            hitl_th = HitlTaskHooks(self.config, self._hitl_coordinator)
            if task_hooks is not None:
                task_hooks = ChainedTaskHooks((hitl_th, task_hooks))
            else:
                task_hooks = hitl_th
        if task_hooks is not None:
            ex.set_task_hooks(task_hooks)
        return ex

    def _build_sprint_hooks(self, release_plan: ReleasePlan) -> SprintLifecycleHooks:
        parts: List[SprintLifecycleHooks] = [
            KnowledgeInjectionHook(self._project_root, self.config),
            SkillLifecycleHook(self._skill_orchestrator, self._skill_store),
        ]
        if getattr(self.config, "governance_enabled", False):
            parts.append(GovernanceSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if getattr(self.config, "verification_enabled", False):
            parts.append(VerificationSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if self._hitl_coordinator is not None:
            from ..governance.hitl.hooks import HitlSprintHooks

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
            quality_level=quality_level,
            project_goals=getattr(release_plan.project, "goals", "") if hasattr(release_plan.project, "goals") else "",
            metadata={"release_plan_name": release_plan.project.name, "release_plan": release_plan},
            codebase_context={},
        )

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
            state.metadata["release_finalization"] = (
                finalize_result.to_dict() if hasattr(finalize_result, "to_dict") else {}
            )
            store.save(state)
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
        from ..infrastructure.config.quality import resolve_effective_quality_level, runs_pytest
        from .evolution.measurement import MeasurementProvider

        quality_level = resolve_effective_quality_level(
            getattr(self.config, "quality_profile", ""),
            getattr(self.config, "quality_level", "") or "L2",
        )
        if not runs_pytest(quality_level):
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
        # 使用 intent graph 执行
        intent_runtime = compile_intent_graph(checkpointer=getattr(self.config, "checkpoint_store", None))
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
            # Fallback: 直接执行
            sprint_results = await self._execute_via_sprint_executor(to_run, max_concurrent)

        # Finalization
        try:
            from ..execution.orchestrator.finalization import ReleaseFinalizationPolicy, ReleaseFinalizationRunner

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
        # Build lifecycle contract
        completion_summary = {
            "execution_id": getattr(release_plan, "execution_id", None),
            "release_plan_name": getattr(to_run.project, "name", ""),
            "sprint_count": len(sprint_results),
            "success": success,
        }
        skill_matches = list(intent_context.get("skill_matches", [])) if isinstance(intent_context.get("skill_matches", []), list) else []
        skill_trace = dict(intent_context.get("task_skill_trace", {})) if isinstance(intent_context.get("task_skill_trace", {}), dict) else {}
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
            skill_review_checklists=list(intent_context.get("review_checklists", [])) if isinstance(intent_context.get("review_checklists", []), list) else [],
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
        # Persist state
        try:
            from ..execution.state.state_store import get_state_store

            if getattr(release_plan, "execution_id", None):
                store = get_state_store()
                state = store.load(getattr(release_plan, "execution_id", None))
                if state is not None:
                    state.metadata["release_finalization"] = completion_summary
                    state.metadata["lifecycle_contract"] = contract.to_dict()
                    state.status = "success" if success else "failed"
                    store.save(state)
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
        sprint_runtime = compile_sprint_graph(checkpointer=getattr(self.config, "checkpoint_store", None))
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
        contract = self._last_release_finalization_result if isinstance(self._last_release_finalization_result, dict) else {}
        return {
            "callbacks": list(self._callbacks.keys()),
            "event_bus": self.event_bus is not None,
            "last_release_finalization": contract.get("finalization", {}) if isinstance(contract, dict) else {},
            "last_lifecycle_contract": contract.get("lifecycle_contract", {}) if isinstance(contract, dict) else {},
            "has_execution_backbone": True,
        }
