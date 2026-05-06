"""
Sprint 执行编排（主实现模块；类 ``SprintOrchestrator``）

**Scrum 语境**：本模块负责把 **Release Plan**（``ReleasePlan`` YAML）转为按 Sprint 顺序的**交付编排**，
不是日历「排期」。``execute_release_plan`` / ``resume_from_sprint`` 即一次 **Sprint 序列的执行**。

**主执行路径（唯一推荐）**：``ReleasePlan`` → ``expand_release_plan_for_execution``（自进化 YAML 在此并入）
→ ``SprintOrchestrator.execute_release_plan`` → ``SprintExecutor.execute_sprints``（``mode=normal``）。
``SprintCycle.run`` / 断点续跑经本模块。
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ..config import RuntimeConfig
from ..evolution.measurement import MeasurementResult
from ..execution.events import (
    Event,
    EventType,
    ExecutionEventBackend,
    create_event,
    get_execution_event_backend,
)
from ..execution.feedback import FeedbackLoop
from ..execution.hooks.sprint_hooks import ChainedSprintHooks, SprintLifecycleHooks
from ..execution.hooks.task_hooks import ChainedTaskHooks, TaskLifecycleHooks
from ..execution.knowledge.knowledge_hook import KnowledgeInjectionHook
from ..execution.sprint_executor import SprintExecutor
from ..execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
from ..governance.sprint_hooks import GovernanceSprintHooks
from ..governance.task_hooks import GovernanceTaskLifecycleHooks
from ..prompt_sources import compute_prompt_sources_fingerprint
from ..release_plan.expand import expand_release_plan_for_execution
from ..release_plan.models import ReleasePlan, SprintBacklogItem, SprintDefinition


def _measurement_run_metadata(
    config: RuntimeConfig,
    *,
    release_plan: Optional[ReleasePlan] = None,
    sprint_index: int = 0,
    sprint: Optional[SprintDefinition] = None,
    sprint_result: Optional[SprintResult] = None,
) -> Dict[str, Any]:
    """F-3 v1–v4：配置指纹 + LLM 环境轨道 + Sprint/任务摘要 + 稳定 prompt 模板全文摘要（无用户任务正文）。"""
    env_model = os.environ.get("LLM_MODEL") or ""
    ev_p = os.environ.get("EVOLUTION_LLM_PROVIDER") or ""
    ev_m = os.environ.get("EVOLUTION_LLM_MODEL") or ""
    fp_src: Dict[str, Any] = {
        "llm_provider": config.llm_provider,
        "llm_model": config.llm_model,
        "coding_engine": config.coding_engine,
        "quality_level": config.effective_quality_level(),
        "dry_run": bool(getattr(config, "dry_run", False)),
        "test_command": config.test_command,
        "llm_model_env": env_model,
        "evolution_llm_provider_env": ev_p,
        "evolution_llm_model_env": ev_m,
    }
    fp = hashlib.sha256(
        json.dumps(fp_src, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    out: Dict[str, Any] = {
        "llm_provider": config.llm_provider,
        "llm_model": config.llm_model,
        "coding_engine": config.coding_engine,
        "quality_level": config.effective_quality_level(),
        "dry_run": fp_src["dry_run"],
        "project_path": getattr(config, "project_path", ".") or ".",
        "config_fingerprint": fp,
    }
    if env_model:
        out["llm_model_env"] = env_model
    if ev_p:
        out["evolution_llm_provider_env"] = ev_p
    if ev_m:
        out["evolution_llm_model_env"] = ev_m

    if release_plan is not None:
        out["release_plan_name"] = release_plan.project.name
        eid = getattr(release_plan, "execution_id", None)
        meta = getattr(release_plan, "metadata", None) or {}
        out["execution_id"] = str(eid) if eid is not None else str(meta.get("id", "") or "")

    if sprint is not None:
        out["sprint_index"] = int(sprint_index)
        out["sprint_name"] = sprint.name

    if sprint_result is not None:
        lines: List[Dict[str, Any]] = []
        for tr in sprint_result.task_results:
            wi = tr.work_item
            st = tr.status.value if hasattr(tr.status, "value") else str(tr.status)
            lines.append(
                {
                    "agent": wi.agent,
                    "description_preview": (wi.description or "")[:240],
                    "status": st,
                }
            )
        out["task_outcome_digest"] = hashlib.sha256(
            json.dumps(lines, ensure_ascii=False).encode("utf-8")
        ).hexdigest()[:16]

    ctx_bind: Dict[str, Any] = {
        "config_fingerprint": out.get("config_fingerprint"),
        "sprint_index": out.get("sprint_index"),
        "sprint_name": out.get("sprint_name"),
        "release_plan_name": out.get("release_plan_name"),
        "execution_id": out.get("execution_id"),
        "task_outcome_digest": out.get("task_outcome_digest"),
    }
    pf = compute_prompt_sources_fingerprint()
    out["prompt_source_digests"] = pf["prompt_source_digests"]
    out["prompt_sources_aggregate_sha256"] = pf["prompt_sources_aggregate_sha256"]
    out["prompt_sources_schema"] = pf["prompt_sources_schema"]

    ctx_bind["prompt_sources_aggregate_sha256"] = out["prompt_sources_aggregate_sha256"]
    out["measurement_context_hash"] = hashlib.sha256(
        json.dumps(ctx_bind, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    return out


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
            m = await self._orchestrator._post_sprint_measurement(
                p,
                sprint_index=sprint_index,
                sprint=sprint,
                sprint_result=result,
            )
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
        event_bus: Optional[ExecutionEventBackend] = None,
        project_path: Optional[str] = None,
        hitl_coordinator: Optional[Any] = None,
    ):
        self.config = config or RuntimeConfig()
        self._project_root = os.path.abspath(project_path or ".")
        self.event_bus = event_bus
        self._hitl_coordinator = hitl_coordinator
        self._callbacks: Dict[str, Callable] = {
            "on_task_start": self._default_on_task_start,
            "on_task_end": self._default_on_task_end,
            "on_sprint_start": self._default_on_sprint_start,
            "on_sprint_end": self._default_on_sprint_end,
        }

    def _get_event_bus(self) -> ExecutionEventBackend:
        if self.event_bus is None:
            self.event_bus = get_execution_event_backend()
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
        task_hooks: Optional[TaskLifecycleHooks] = None
        if getattr(self.config, "governance_enabled", False) and getattr(
            self.config, "governance_task_hooks_enabled", False
        ):
            task_hooks = GovernanceTaskLifecycleHooks(
                self.config, self._project_root, self._get_event_bus()
            )
        if self._hitl_coordinator is not None and getattr(self.config, "hitl_enabled", False):
            from ..hitl.hooks import HitlTaskHooks

            hitl_th = HitlTaskHooks(self.config, self._hitl_coordinator)
            if task_hooks is not None:
                # ChainedTaskHooks 逆序调用 on_after：后注册先执行 → (hitl, gov) 则先治理后人机
                task_hooks = ChainedTaskHooks((hitl_th, task_hooks))
            else:
                task_hooks = hitl_th
        if task_hooks is not None:
            ex.set_task_hooks(task_hooks)
        return ex

    def _build_sprint_hooks(self, release_plan: ReleasePlan) -> SprintLifecycleHooks:
        # 顺序：知识注入 → 治理（Planning/Review）→ 编排事件与测量（见 governance/sprint_hooks 模块注释）
        parts: List[SprintLifecycleHooks] = [
            KnowledgeInjectionHook(self._project_root, self.config),
        ]
        if getattr(self.config, "governance_enabled", False):
            parts.append(GovernanceSprintHooks(self._project_root, self.config, self._get_event_bus()))
        if self._hitl_coordinator is not None:
            from ..hitl.hooks import HitlSprintHooks

            parts.append(HitlSprintHooks(self.config, self._hitl_coordinator))
        parts.append(_OrchestratorSprintHooks(self, release_plan))
        return ChainedSprintHooks(tuple(parts))

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

    async def _post_sprint_measurement(
        self,
        release_plan: ReleasePlan,
        *,
        sprint_index: int = 0,
        sprint: Optional[SprintDefinition] = None,
        sprint_result: Optional[SprintResult] = None,
    ) -> Optional[MeasurementResult]:
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
        # F-3：测量结果附带运行期模型/引擎元数据 + Sprint/任务绑定摘要（v3）
        m.details["run_metadata"] = _measurement_run_metadata(
            self.config,
            release_plan=release_plan,
            sprint_index=sprint_index,
            sprint=sprint,
            sprint_result=sprint_result,
        )
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
            "callbacks": list(self._callbacks.keys()),
            "event_bus": self.event_bus is not None,
        }
