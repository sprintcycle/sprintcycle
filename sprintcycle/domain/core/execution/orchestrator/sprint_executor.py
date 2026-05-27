"""
Sprint 执行器 — 与 Scrum Sprint 时间盒内交付对应

顺序（或受控并行）跑完单个 SprintDefinition 的 Sprint Backlog（tasks），
聚合为 SprintResult；多 Sprint 由 SprintOrchestrator 编排。

**分层**：SprintExecutor 通过构造函数接收 StateStore 依赖，不直接依赖 Infrastructure 实现。
"""

import asyncio
import re
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set

from loguru import logger

from sprintcycle.domain.generic.models import ReleasePlan, SprintBacklogItem, SprintDefinition
from sprintcycle.domain.generic.models.release_plan.payload_keys import context_plan_id_name
from sprintcycle.domain.core.governance.hitl.types import CTX_HITL_ABORT_EXECUTION, CTX_HITL_SPRINT_ACTION
from .constants import (
    TASK_SPLIT_THRESHOLD,
    MAX_SUBTASKS,
    DEPENDENCY_KEYWORDS,
    ACTION_PATTERNS,
    DEFAULT_MAX_PARALLEL,
    DEFAULT_MAX_VERIFY_FIX_ROUNDS,
    DEFAULT_CHECKPOINT_INTERVAL,
    AGENT_TYPE_CODER,
    AGENT_TYPE_IMPLEMENT,
    AGENT_TYPE_TESTER,
    AGENT_TYPE_ARCHITECT,
    AGENT_TYPE_REGRESSION_TESTER,
)
from .strategies import (
    AgentStrategy,
    CoderStrategy,
    TesterStrategy,
    ArchitectStrategy,
    RegressionTesterStrategy,
)
from sprintcycle.domain.core.execution.core.events import EventType, ExecutionEventBackend, create_event
from ..planners.execution_planners import TaskContextBuilder
from ..hooks.governance_context import (
    CTX_GOVERNANCE_TASK_AFTER_DETAIL,
    CTX_GOVERNANCE_TASK_AFTER_FAILED,
)
from ..hooks.sprint_hooks import NoOpSprintLifecycleHooks, SprintLifecycleHooks
from ..hooks.task_hooks import NoOpTaskLifecycleHooks, TaskLifecycleHooks
from sprintcycle.domain.core.execution.core.policies import SprintFeedbackPolicy, SprintRetryPolicy
from sprintcycle.domain.core.execution.project_write import ProjectWritePlan
from sprintcycle.domain.core.execution.core.protocols import ExecutionContext
from sprintcycle.domain.generic.interfaces.types import ExecutionStatus, SprintResult, TaskResult
from ._feedback_stub import FeedbackReleasePlanStub

# TYPE_CHECKING: 仅用于类型提示，通过端口层访问
if TYPE_CHECKING:
    pass


class SprintExecutor:
    """执行单个 Sprint 的 Sprint Backlog（支持断点续传，经 StateStore）。

    **分层**：SprintExecutor 不继承 CheckpointMixin，而是直接实现断点续传功能，
    通过构造函数接收 StateStore 依赖。
    """

    def __init__(
        self,
        max_parallel: int = DEFAULT_MAX_PARALLEL,
        feedback_loop: Optional[Any] = None,
        release_plan: Optional[ReleasePlan] = None,
        error_handler: Optional[Any] = None,
        state_store: Optional[Any] = None,  # StateStore 实例，由调用方注入
        max_verify_fix_rounds: int = DEFAULT_MAX_VERIFY_FIX_ROUNDS,
        runtime_config: Optional[Any] = None,
        sprint_hooks: Optional[SprintLifecycleHooks] = None,
        task_hooks: Optional[TaskLifecycleHooks] = None,
        evolution_loop: Optional[Any] = None,
    ):
        self._strategies: Dict[str, AgentStrategy] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._max_parallel = max_parallel
        self._max_verify_fix_rounds = max(1, int(max_verify_fix_rounds))
        self._sprint_retry_policy = SprintRetryPolicy(self._max_verify_fix_rounds)
        self._sprint_feedback_policy = SprintFeedbackPolicy()
        self._runtime_config = runtime_config
        self._sprint_hooks: SprintLifecycleHooks = sprint_hooks or NoOpSprintLifecycleHooks()
        self._task_hooks: TaskLifecycleHooks = task_hooks or NoOpTaskLifecycleHooks()
        self._event_bus: Optional[ExecutionEventBackend] = None
        self._feedback_loop = feedback_loop
        self._evolution_loop = evolution_loop
        self._release_plan = release_plan
        self._sprint_count = 0
        self._error_handler = error_handler
        self._state_store = state_store
        self._execution_id: str = ""
        self._cancelled: bool = False
        self._event_cursor: int = 0
        self._checkpoint_interval = DEFAULT_CHECKPOINT_INTERVAL
        self._task_context_builder = TaskContextBuilder()
        self._project_write_plan: Optional[ProjectWritePlan] = None
        self._trace_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self._register_default_strategies()

    def _register_default_strategies(self) -> None:
        """Register default execution strategies for different agent types."""
        dry_run = self._dry_run()
        self._strategies = {
            AGENT_TYPE_CODER: CoderStrategy(
                max_verify_fix_rounds=self._max_verify_fix_rounds,
                project_write_plan=self._project_write_plan,
                dry_run=dry_run,
            ),
            AGENT_TYPE_IMPLEMENT: CoderStrategy(
                max_verify_fix_rounds=self._max_verify_fix_rounds,
                project_write_plan=self._project_write_plan,
                dry_run=dry_run,
            ),
            AGENT_TYPE_TESTER: TesterStrategy(
                project_write_plan=self._project_write_plan,
                dry_run=dry_run,
            ),
            AGENT_TYPE_ARCHITECT: ArchitectStrategy(
                project_write_plan=self._project_write_plan,
                dry_run=dry_run,
            ),
            AGENT_TYPE_REGRESSION_TESTER: RegressionTesterStrategy(
                project_write_plan=self._project_write_plan,
                dry_run=dry_run,
            ),
        }

    def set_trace_callback(self, callback: Optional[Callable[[Dict[str, Any]], None]]) -> None:
        self._trace_callback = callback

    def _emit_trace(self, kind: str, payload: Dict[str, Any]) -> None:
        if self._trace_callback is None:
            return
        try:
            self._trace_callback({"kind": kind, **payload})
        except Exception as e:
            logger.warning("trace callback failed: {}", e)

    def set_project_write_plan(self, plan: Optional[ProjectWritePlan]) -> None:
        self._project_write_plan = plan
        # Update strategies with new write plan
        dry_run = self._dry_run()
        for strategy in self._strategies.values():
            strategy.project_write_plan = plan
            strategy.dry_run = dry_run

    @property
    def project_write_plan(self) -> Optional[ProjectWritePlan]:
        return self._project_write_plan

    @property
    def state_store(self) -> Any:
        """获取状态存储（延迟初始化以避免循环依赖）"""
        if self._state_store is None:
            from sprintcycle.domain.ports.state_store import get_state_store
            self._state_store = get_state_store()
        return self._state_store

    def set_state_store(self, state_store: Any) -> None:
        """设置状态存储"""
        self._state_store = state_store
        logger.info("StateStore 已注入到 SprintExecutor")

    def set_feedback_loop(self, feedback_loop) -> None:
        self._feedback_loop = feedback_loop

    def set_release_plan(self, release_plan: ReleasePlan) -> None:
        self._release_plan = release_plan

    def set_error_handler(self, error_handler) -> None:
        self._error_handler = error_handler

    def set_sprint_hooks(self, sprint_hooks: Optional[SprintLifecycleHooks]) -> None:
        self._sprint_hooks = sprint_hooks or NoOpSprintLifecycleHooks()

    def set_task_hooks(self, task_hooks: Optional[TaskLifecycleHooks]) -> None:
        self._task_hooks = task_hooks or NoOpTaskLifecycleHooks()

    async def _invoke_task_hooks(
        self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any], task_result: TaskResult
    ) -> None:
        try:
            await self._task_hooks.on_after_task_complete(task, sprint_name, context, task_result)
        except Exception as e:
            logger.warning("task_hooks on_after_task_complete: {}", e)

    def get_feedback_history(self) -> List[Any]:
        if self._feedback_loop:
            return self._feedback_loop.get_history()
        return []

    def get_intent_evolution_events(self) -> List[Dict[str, Any]]:
        if self._evolution_loop and hasattr(self._evolution_loop, "events"):
            return self._evolution_loop.events()
        return []

    def _dry_run(self) -> bool:
        return bool(self._runtime_config and getattr(self._runtime_config, "dry_run", False))

    def _build_agent_context(self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any]):
        from .agents.base import AgentContext

        structured = self._task_context_builder.build(task, sprint_name, context)
        rid, rname = context_plan_id_name(context)
        cache_llm = True
        rc = self._runtime_config
        if rc is not None:
            cache_llm = bool(getattr(rc, "cache_llm_codegen", True))
        exec_ctx = context.get("execution_context")
        if isinstance(exec_ctx, ExecutionContext):
            release_plan_id = exec_ctx.release_plan_id or str(rid or structured.release_plan_id)
            project_goals = exec_ctx.project_goals or str(context.get("project_goals", ""))
            coding_engine = exec_ctx.coding_engine or structured.coding_engine
            quality_level = exec_ctx.quality_level or structured.quality_level
            metadata = dict(exec_ctx.metadata or {})
            codebase_context = dict(exec_ctx.codebase_context or {})
        else:
            release_plan_id = str(rid or structured.release_plan_id)
            project_goals = str(context.get("project_goals", ""))
            coding_engine = structured.coding_engine
            quality_level = structured.quality_level
            metadata = {}
            codebase_context = structured.codebase_context
        metadata.update(
            {"coding_engine": coding_engine, "quality_level": quality_level, "constraints": task.constraints or []}
        )
        if self._project_write_plan is not None:
            metadata["project_write_plan"] = self._project_write_plan.to_dict()
            metadata["write_policy"] = self._project_write_plan.write_policy
            metadata["target_path"] = self._project_write_plan.target_path
            metadata["references"] = [r.path for r in self._project_write_plan.references]
        return AgentContext(
            release_plan_id=release_plan_id,
            release_plan_name=str(rname or structured.release_plan_name),
            project_goals=project_goals,
            sprint_name=str(structured.sprint_name),
            sprint_index=int(structured.sprint_index),
            dependencies=structured.dependencies,
            codebase_context=codebase_context,
            metadata=metadata,
            config={"cache_llm_codegen": cache_llm},
        )

    def register_agent_strategy(self, agent_type: str, strategy: AgentStrategy) -> None:
        """Register a custom execution strategy for an agent type."""
        self._strategies[agent_type] = strategy

    def cancel(self) -> None:
        self._cancelled = True
        logger.info("SprintExecutor 已收到取消信号，将在下一个 Sprint 边界停止")

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def _should_split_task(self, task: SprintBacklogItem) -> bool:
        if len(task.description) >= TASK_SPLIT_THRESHOLD:
            return True
        complex_keywords = ["重构", "迁移", "优化", "重写", "implement", "refactor", "migrate", "optimize", "rewrite"]
        task_lower = task.description.lower()
        keyword_count = sum(1 for kw in complex_keywords if kw.lower() in task_lower)
        return keyword_count >= 2

    def _split_task(self, task: SprintBacklogItem) -> List[SprintBacklogItem]:
        subtasks = []
        task_text = task.description
        subtask_parts = []
        for pattern in ACTION_PATTERNS:
            matches = re.findall(pattern, task_text, re.IGNORECASE)
            subtask_parts.extend(matches)
        if len(subtask_parts) >= 2:
            for i, part in enumerate(subtask_parts[: MAX_SUBTASKS]):
                subtask = SprintBacklogItem(
                    description=part.strip(),
                    agent=task.agent,
                    target=task.target,
                    constraints=task.constraints.copy(),
                    expected_output=task.expected_output,
                    timeout=task.timeout,
                )
                subtasks.append(subtask)
        else:
            subtask = SprintBacklogItem(
                description=task_text[: TASK_SPLIT_THRESHOLD] + "..."
                if len(task_text) > TASK_SPLIT_THRESHOLD
                else task_text,
                agent=task.agent,
                target=task.target,
                constraints=task.constraints.copy(),
                expected_output=task.expected_output,
                timeout=task.timeout,
            )
            subtasks.append(subtask)
        return subtasks

    def split_sprint_tasks(self, sprint: SprintDefinition) -> SprintDefinition:
        new_sprint = SprintDefinition(name=sprint.name, goals=sprint.goals.copy(), tasks=[])
        for task in sprint.tasks:
            if self._should_split_task(task):
                subtasks = self._split_task(task)
                new_sprint.tasks.extend(subtasks)
            else:
                new_sprint.tasks.append(task)
        return new_sprint

    async def execute_sprint(
        self, sprint: SprintDefinition, context: Optional[Dict[str, Any]] = None, save_checkpoint: bool = True
    ) -> SprintResult:
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=ExecutionStatus.RUNNING)
        logger.info(f"开始执行 Sprint: {sprint.name}")
        ctx_acc: Dict[str, Any] = dict(context.to_dict() if isinstance(context, ExecutionContext) else (context or {}))
        ctx_acc.setdefault("sprint_name", sprint.name)
        ctx_acc.setdefault("execution_context", context if isinstance(context, ExecutionContext) else None)
        ctx_acc.setdefault("_sprint_coding_engine", ctx_acc.get("coding_engine", "cursor"))
        start_event = {
            "kind": "sprint_start",
            "execution_id": self._execution_id,
            "sprint_name": sprint.name,
            "timestamp": datetime.now().isoformat(),
            "payload": {"message": f"start sprint {sprint.name}"},
            "metadata": {"sprint_name": sprint.name},
        }
        self._emit_trace("sprint_start", start_event)
        await self._emit_event(
            "sprint_start",
            {"execution_id": self._execution_id, "sprint_name": sprint.name, "message": f"start sprint {sprint.name}"},
        )
        for task in sprint.tasks:
            task_start = {
                "kind": "task_start",
                "execution_id": self._execution_id,
                "sprint_name": sprint.name,
                "timestamp": datetime.now().isoformat(),
                "payload": {"agent_type": task.agent, "description": task.description},
                "metadata": {"agent_type": task.agent, "sprint_name": sprint.name},
            }
            self._emit_trace("task_start", task_start)
            await self._emit_event(
                "task_start",
                {
                    "execution_id": self._execution_id,
                    "sprint_name": sprint.name,
                    "agent_type": task.agent,
                    "description": task.description,
                },
            )
            task_result = await self._execute_task(task, sprint.name, ctx_acc)
            result.task_results.append(task_result)
            task_done = {
                "kind": "task_complete" if task_result.status == ExecutionStatus.SUCCESS else "task_failed",
                "execution_id": self._execution_id,
                "sprint_name": sprint.name,
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "agent_type": task.agent,
                    "description": task.description,
                    "status": task_result.status.value,
                    "duration": task_result.duration,
                    "error": task_result.error,
                },
                "metadata": {"agent_type": task.agent, "sprint_name": sprint.name},
            }
            self._emit_trace(task_done["kind"], task_done)
            await self._emit_event(
                "task_complete" if task_result.status == ExecutionStatus.SUCCESS else "task_failed",
                {
                    "execution_id": self._execution_id,
                    "sprint_name": sprint.name,
                    "agent_type": task.agent,
                    "description": task.description,
                    "status": task_result.status.value,
                    "duration": task_result.duration,
                    "error": task_result.error,
                },
            )
            if task_result.status == ExecutionStatus.SUCCESS:
                deps = ctx_acc.setdefault("dependencies", {})
                if task.agent in (AGENT_TYPE_CODER, AGENT_TYPE_IMPLEMENT):
                    deps["code"] = task_result.output
                if task.agent == AGENT_TYPE_ARCHITECT:
                    ctx_acc["architecture_design"] = task_result.output
        if all(r.status == ExecutionStatus.SUCCESS for r in result.task_results):
            result.status = ExecutionStatus.SUCCESS
        elif any(r.status == ExecutionStatus.FAILED for r in result.task_results):
            result.status = ExecutionStatus.FAILED
        else:
            result.status = ExecutionStatus.SUCCESS
        result.duration = time.time() - start_time
        sprint_done = {
            "kind": "sprint_complete" if result.status == ExecutionStatus.SUCCESS else "sprint_failed",
            "execution_id": self._execution_id,
            "sprint_name": sprint.name,
            "timestamp": datetime.now().isoformat(),
            "payload": {"status": result.status.value, "duration": result.duration},
            "metadata": {"sprint_name": sprint.name},
        }
        self._emit_trace(sprint_done["kind"], sprint_done)
        await self._emit_event(
            "sprint_complete" if result.status == ExecutionStatus.SUCCESS else "sprint_failed",
            {
                "execution_id": self._execution_id,
                "sprint_name": sprint.name,
                "status": result.status.value,
                "duration": result.duration,
            },
        )
        self._collect_feedback(sprint, result)
        self._persist_sprint_result(sprint, result)
        self._record_intent_evolution(sprint, result, ctx_acc)
        if save_checkpoint and self._execution_id:
            self._save_checkpoint(0, sprint.name, result)
        return result

    def _record_intent_evolution(self, sprint: SprintDefinition, result: SprintResult, ctx_acc: Dict[str, Any]) -> None:
        """Record intent evolution for the sprint (no-op by default)."""
        pass

    def _collect_feedback(self, sprint: SprintDefinition, result: SprintResult) -> None:
        if self._feedback_loop is None:
            return
        try:
            self._sprint_count += 1
            if self._release_plan:
                feedback = self._feedback_loop.collect(self._release_plan, [result])
            else:

                feedback = self._feedback_loop.collect(FeedbackReleasePlanStub(sprint_name=sprint.name), [result])
            self._feedback_loop.save(feedback)
        except Exception as e:
            logger.warning(f"收集反馈失败: {e}")

    def _persist_sprint_result(self, sprint: SprintDefinition, result: SprintResult) -> None:
        try:
            task_records = []
            for tr in result.task_results:
                task_records.append(
                    {
                        "description": tr.work_item.description,
                        "agent": tr.work_item.agent,
                        "status": tr.status.value if hasattr(tr.status, "value") else str(tr.status),
                        "output": tr.output,
                        "error": tr.error,
                        "duration": tr.duration,
                    }
                )
            execution_record = {
                "sprint_name": sprint.name,
                "status": result.status.value if hasattr(result.status, "value") else str(result.status),
                "task_results": task_records,
                "duration": result.duration,
                "timestamp": datetime.now().isoformat(),
            }
            state = self.state_store.load(self._execution_id or "default")
            if state:
                if "sprint_history" not in state.metadata:
                    state.metadata["sprint_history"] = []
                state.metadata["sprint_history"].append(execution_record)
                state.updated_at = datetime.now().isoformat()
                self.state_store.save(state)
                logger.info(f"Sprint 结果已持久化: {sprint.name}")
            else:
                logger.debug("无 StateStore 状态，跳过持久化")
        except Exception as e:
            logger.warning(f"持久化 Sprint 结果失败: {e}")

    def _log_task_execution(self, task: SprintBacklogItem, task_result: TaskResult) -> None:
        status_str = task_result.status.value if hasattr(task_result.status, "value") else str(task_result.status)
        logger.info(f"Task [{task.agent}] {task.description[:40]}... → {status_str} ({task_result.duration:.2f}s)")

    async def execute_sprints(
        self,
        sprints: List[SprintDefinition],
        mode: str = "normal",
        evolution_config: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
        resume: bool = False,
        release_plan: Optional[ReleasePlan] = None,
        sprint_index_offset: int = 0,
    ) -> List[SprintResult]:
        self._cancelled = False
        if resume and execution_id:
            return await self._resume_execution(
                execution_id, sprints, context, release_plan=release_plan, sprint_index_offset=sprint_index_offset
            )
        self._execution_id = execution_id or self._init_execution_state()
        if release_plan is not None:
            try:
                setattr(release_plan, "execution_id", self._execution_id)
            except Exception:
                pass
        if mode == "evolution":
            logger.warning("SprintExecutor mode='evolution' is removed; running as normal.")
        return await self._execute_normal_sprints(
            sprints, context or {}, release_plan=release_plan, sprint_index_offset=sprint_index_offset
        )

    async def _resume_execution(
        self,
        execution_id: str,
        sprints: List[SprintDefinition],
        context: Optional[Dict[str, Any]] = None,
        release_plan: Optional[ReleasePlan] = None,
        sprint_index_offset: int = 0,
    ) -> List[SprintResult]:
        logger.info(f"从断点恢复执行: {execution_id}")
        state = self.load_execution_state(execution_id)
        if not state:
            return []
        resume_point = self.get_resume_point(execution_id)
        if not resume_point:
            return []
        start_sprint_idx = resume_point.get("current_sprint", 0)
        self._execution_id = execution_id
        if release_plan is not None:
            try:
                setattr(release_plan, "execution_id", self._execution_id)
            except Exception:
                pass
        self.state_store.update_status(execution_id, ExecutionStatus.RUNNING)
        results: List[SprintResult] = []
        ctx = context or {}
        ctx["execution_id"] = self._execution_id
        for i, sprint in enumerate(sprints):
            if i < start_sprint_idx:
                continue
            if ctx.get(CTX_HITL_ABORT_EXECUTION):
                logger.info("HITL: 已请求中止后续 Sprint（续跑路径）")
                break
            ctx["sprint_index"] = sprint_index_offset + i
            ctx["sprint_name"] = sprint.name
            ctx["project_goals"] = " ".join(sprint.goals)
            try:
                await self._sprint_hooks.on_before_sprint(ctx["sprint_index"], sprint, ctx, release_plan)
            except Exception as e:
                logger.warning("on_before_sprint hook failed: {}", e)
            act = ctx.pop(CTX_HITL_SPRINT_ACTION, None)
            if act == "skip":
                results.append(
                    SprintResult(sprint=sprint, status=ExecutionStatus.SKIPPED, task_results=[], duration=0.0)
                )
                continue
            if act == "abort":
                results.append(
                    SprintResult(sprint=sprint, status=ExecutionStatus.CANCELLED, task_results=[], duration=0.0)
                )
                self._cancelled = True
                break
            result = await self.execute_sprint(sprint, ctx, save_checkpoint=True)
            results.append(result)
            try:
                await self._sprint_hooks.on_after_sprint(ctx["sprint_index"], sprint, result, ctx, release_plan)
            except Exception as e:
                logger.warning("on_after_sprint hook failed: {}", e)
            if result.status == ExecutionStatus.FAILED:
                break
        return results

    async def _execute_normal_sprints(
        self,
        sprints: List[SprintDefinition],
        context: Dict[str, Any],
        release_plan: Optional[ReleasePlan] = None,
        sprint_index_offset: int = 0,
    ) -> List[SprintResult]:
        results: List[SprintResult] = []
        ctx = context
        ctx["execution_id"] = self._execution_id
        for i, sprint in enumerate(sprints):
            if self._cancelled:
                logger.info(f"执行已取消，跳过剩余 Sprint (已完成 {i}/{len(sprints)})")
                break
            if ctx.get(CTX_HITL_ABORT_EXECUTION):
                logger.info("HITL: 已请求中止后续 Sprint，结束编排")
                break
            global_idx = sprint_index_offset + i
            ctx["sprint_index"] = global_idx
            ctx["sprint_name"] = sprint.name
            ctx["project_goals"] = " ".join(sprint.goals)
            try:
                await self._sprint_hooks.on_before_sprint(global_idx, sprint, ctx, release_plan)
            except Exception as e:
                logger.warning("on_before_sprint hook failed: {}", e)
            self._emit_trace(
                "sprint_phase",
                {
                    "kind": "sprint_phase",
                    "execution_id": self._execution_id,
                    "sprint_name": sprint.name,
                    "timestamp": datetime.now().isoformat(),
                    "payload": {"phase": "before_sprint", "index": global_idx},
                    "metadata": {"sprint_name": sprint.name},
                },
            )
            act = ctx.pop(CTX_HITL_SPRINT_ACTION, None)
            if act == "skip":
                results.append(
                    SprintResult(sprint=sprint, status=ExecutionStatus.SKIPPED, task_results=[], duration=0.0)
                )
                continue
            if act == "abort":
                results.append(
                    SprintResult(sprint=sprint, status=ExecutionStatus.CANCELLED, task_results=[], duration=0.0)
                )
                self._cancelled = True
                break
            result = await self.execute_sprint(sprint, ctx, save_checkpoint=True)
            results.append(result)
            self._emit_trace(
                "sprint_phase",
                {
                    "kind": "sprint_phase",
                    "execution_id": self._execution_id,
                    "sprint_name": sprint.name,
                    "timestamp": datetime.now().isoformat(),
                    "payload": {"phase": "after_sprint", "index": global_idx, "status": result.status.value},
                    "metadata": {"sprint_name": sprint.name},
                },
            )
            if result.status == ExecutionStatus.FAILED:
                logger.warning(f"Sprint 失败: {sprint.name}")
                if self._feedback_loop:
                    feedback = self._get_feedback_for_sprint(sprint, result)
                    if feedback:
                        decision = self._feedback_loop.decide(feedback)
                        retry_decision = self._sprint_retry_policy.should_retry(sprint)
                        if decision["action"] == "retry" and retry_decision.should_retry:
                            logger.info(f"Sprint {sprint.name} 根据反馈重试: {decision['reason']}")
                            result = await self._retry_with_feedback(sprint, feedback, decision, ctx)
                            results[-1] = result
                        elif decision["action"] == "abort":
                            logger.warning(f"Sprint {sprint.name} 反馈决策中止: {decision['reason']}")
                            try:
                                await self._sprint_hooks.on_after_sprint(global_idx, sprint, result, ctx, release_plan)
                            except Exception as e:
                                logger.warning("on_after_sprint hook failed: {}", e)
                            break
            if self._feedback_loop and i < len(sprints) - 1:
                feedback = self._get_feedback_for_sprint(sprint, result)
                if feedback:
                    ctx["previous_feedback"] = feedback.to_dict()
                    ctx["improvement_suggestions"] = self._feedback_loop.analyze(feedback)
            try:
                await self._sprint_hooks.on_after_sprint(global_idx, sprint, result, ctx, release_plan)
            except Exception as e:
                logger.warning("on_after_sprint hook failed: {}", e)
        return results

    def _should_retry(self, sprint: SprintDefinition) -> bool:
        decision = self._sprint_retry_policy.should_retry(sprint)
        return decision.should_retry

    async def _retry_with_feedback(
        self, sprint: SprintDefinition, feedback: Any, decision: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> SprintResult:
        object.__setattr__(sprint, "_retry_count", getattr(sprint, "_retry_count", 0) + 1)
        if context is None:
            context = {}
        context.update(self._sprint_feedback_policy.build_context(decision, feedback))
        logger.info(f"重试 Sprint {sprint.name}，携带 {len(decision.get('suggestions', []))} 条改进建议")
        result = await self.execute_sprint(sprint, context, save_checkpoint=True)
        return result

    def _get_feedback_for_sprint(self, sprint: SprintDefinition, result: SprintResult) -> Any:
        if not self._feedback_loop:
            return None
        try:
            if self._release_plan:
                return self._feedback_loop.collect(self._release_plan, [result])
            else:

                return self._feedback_loop.collect(FeedbackReleasePlanStub(sprint_name=sprint.name), [result])
        except Exception as e:
            logger.warning(f"收集反馈失败: {e}")
            return None

    def set_event_bus(self, event_bus: Optional[ExecutionEventBackend]) -> None:
        self._event_bus = event_bus

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self._event_bus:
            try:
                self._event_cursor += 1
                payload = dict(data)
                payload.setdefault("event_cursor", self._event_cursor)
                event = create_event(EventType[event_type.upper()], **payload)
                await self._event_bus.emit(event)
            except KeyError:
                pass

    async def execute_sprint_parallel(
        self,
        sprint: SprintDefinition,
        context: Optional[Dict[str, Any]] = None,
        dependency_map: Optional[Dict[int, Set[int]]] = None,
        save_checkpoint: bool = True,
    ) -> SprintResult:
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=ExecutionStatus.RUNNING)
        ctx_base = dict(context.to_dict() if isinstance(context, ExecutionContext) else (context or {}))
        ctx_base.setdefault("execution_context", context if isinstance(context, ExecutionContext) else None)
        ctx_base.setdefault("_sprint_coding_engine", ctx_base.get("coding_engine", "cursor"))
        context = ctx_base
        task_count = len(sprint.tasks)
        task_semaphore = asyncio.Semaphore(self._max_parallel)

        async def execute_with_semaphore(task: SprintBacklogItem, idx: int) -> TaskResult:
            async with task_semaphore:
                return await self._execute_task_with_event(task, sprint.name, context or {})

        async def run_task(idx: int) -> None:
            task = sprint.tasks[idx]
            task_result = await execute_with_semaphore(task, idx)
            result.task_results.append(task_result)

        task_coroutines = [run_task(i) for i in range(task_count)]
        await asyncio.gather(*task_coroutines, return_exceptions=True)

        if all(r.status == ExecutionStatus.SUCCESS for r in result.task_results):
            result.status = ExecutionStatus.SUCCESS
        elif any(r.status == ExecutionStatus.FAILED for r in result.task_results):
            result.status = ExecutionStatus.FAILED
        else:
            result.status = ExecutionStatus.SUCCESS

        result.duration = time.time() - start_time

        if save_checkpoint and self._execution_id:
            self._save_checkpoint(0, sprint.name, result)

        return result

    async def _execute_task_with_event(
        self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any]
    ) -> TaskResult:
        result = await self._execute_task(task, sprint_name, context)
        task_phase = {
            "kind": "task_phase",
            "execution_id": self._execution_id,
            "sprint_name": sprint_name,
            "timestamp": datetime.now().isoformat(),
            "payload": {
                "task": task.description[:120],
                "status": result.status.value if hasattr(result.status, "value") else str(result.status),
                "agent": task.agent,
            },
            "metadata": {"agent": task.agent, "sprint_name": sprint_name},
        }
        self._emit_trace("task_phase", task_phase)
        return result

    async def _execute_task(self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        strategy = self._strategies.get(task.agent)
        if not strategy:
            return TaskResult(
            work_item=task,
            sprint_name=sprint_name,
            status=ExecutionStatus.FAILED,
            error=f"未知的 Agent 类型: {task.agent}",
        )
        try:
            enriched_context = dict(context)
            enriched_context.setdefault("sprint_name", sprint_name)
            if self._runtime_config is not None:
                base_engine = enriched_context.get("coding_engine") or getattr(
                    self._runtime_config, "coding_engine", "cursor"
                )
                enriched_context.setdefault("_sprint_coding_engine", base_engine)
                enriched_context["coding_engine"] = enriched_context["_sprint_coding_engine"]
                enriched_context["quality_level"] = (
                    self._runtime_config.effective_quality_level()
                    if hasattr(self._runtime_config, "effective_quality_level")
                    else getattr(self._runtime_config, "quality_level", "L1")
                )
            else:
                enriched_context.setdefault("_sprint_coding_engine", enriched_context.get("coding_engine", "cursor"))
                enriched_context["coding_engine"] = enriched_context["_sprint_coding_engine"]
            if "improvement_suggestions" in context:
                suggestions = context["improvement_suggestions"]
                if suggestions:
                    enriched_context["task_guidance"] = "前序 Sprint 反馈改进建议:\n" + "\n".join(
                        f"- {s}" for s in suggestions
                    )
            if "retry_from_failure" in context:
                enriched_context["task_guidance"] = (
                enriched_context.get("task_guidance", "") + "\n[重要] 本次为失败重试，请特别注意上述问题。"
            )
            task_start = {
                "kind": "task_execute_start",
                "execution_id": self._execution_id,
                "sprint_name": sprint_name,
                "timestamp": datetime.now().isoformat(),
                "payload": {"agent": task.agent, "description": task.description},
                "metadata": {"agent": task.agent, "sprint_name": sprint_name},
            }
            self._emit_trace("task_execute_start", task_start)
            output = await strategy.execute(task, enriched_context, self._build_agent_context)
            task_result = TaskResult(
                work_item=task,
                sprint_name=sprint_name,
                status=ExecutionStatus.SUCCESS,
                output=output,
                duration=time.time() - start_time,
            )
            self._log_task_execution(task, task_result)
            await self._invoke_task_hooks(task, sprint_name, enriched_context, task_result)
            dur = time.time() - start_time
            if enriched_context.get(CTX_GOVERNANCE_TASK_AFTER_FAILED):
                detail = enriched_context.get(CTX_GOVERNANCE_TASK_AFTER_DETAIL) or "task_after 未通过"
                logger.warning(
                    "task_after 阻断任务: sprint={} agent={} desc={}",
                    sprint_name,
                    task.agent,
                    (task.description or "")[:120],
                )
                failed_phase = {
                    "kind": "task_execute_failed",
                    "execution_id": self._execution_id,
                    "sprint_name": sprint_name,
                    "timestamp": datetime.now().isoformat(),
                    "payload": {"agent": task.agent, "description": task.description, "error": str(detail)[:8000]},
                    "metadata": {"agent": task.agent, "sprint_name": sprint_name},
                }
                self._emit_trace("task_execute_failed", failed_phase)
                return TaskResult(
                    work_item=task,
                    sprint_name=sprint_name,
                    status=ExecutionStatus.FAILED,
                    output=output,
                    error=str(detail)[:8000],
                    duration=dur,
                )
            task_result.duration = dur
            task_complete = {
                "kind": "task_execute_complete",
                "execution_id": self._execution_id,
                "sprint_name": sprint_name,
                "timestamp": datetime.now().isoformat(),
                "payload": {
                    "agent": task.agent,
                    "description": task.description,
                    "status": task_result.status.value,
                    "duration": task_result.duration,
                },
                "metadata": {"agent": task.agent, "sprint_name": sprint_name},
            }
            self._emit_trace("task_execute_complete", task_complete)
            return task_result
        except Exception as e:
            failed = TaskResult(
                work_item=task,
                sprint_name=sprint_name,
                status=ExecutionStatus.FAILED,
                error=str(e),
                duration=time.time() - start_time,
            )
            await self._invoke_task_hooks(task, sprint_name, enriched_context, failed)
            failed_phase = {
                "kind": "task_execute_failed",
                "execution_id": self._execution_id,
                "sprint_name": sprint_name,
                "timestamp": datetime.now().isoformat(),
                "payload": {"agent": task.agent, "description": task.description, "error": str(e)},
                "metadata": {"agent": task.agent, "sprint_name": sprint_name},
            }
            self._emit_trace("task_execute_failed", failed_phase)
            return failed

    def _analyze_dependencies(
        self, tasks: List[SprintBacklogItem], context: Optional[Dict[str, Any]] = None
    ) -> Dict[int, Set[int]]:
        dependency_map: Dict[int, Set[int]] = {i: set() for i in range(len(tasks))}
        for i, task in enumerate(tasks):
            self._add_keyword_based_dependencies(tasks, i, task, dependency_map)
            self._add_target_path_dependencies(tasks, i, task, dependency_map)
            self._add_agent_type_dependencies(tasks, i, task, dependency_map)
        for idx in dependency_map:
            dependency_map[idx].discard(idx)
        return dependency_map

    def _add_keyword_based_dependencies(
        self, tasks: List[SprintBacklogItem], task_idx: int, task: SprintBacklogItem, dep_map: Dict[int, Set[int]]
    ) -> None:
        task_text = task.description.lower()
        for dep_kw, src_kw in DEPENDENCY_KEYWORDS:
            if dep_kw in task_text:
                for j in range(task_idx):
                    prev_text = tasks[j].description.lower()
                    prev_target = (tasks[j].target or "").lower()
                    if src_kw in prev_text or src_kw in prev_target:
                        dep_map[task_idx].add(j)
