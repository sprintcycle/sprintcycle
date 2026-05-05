"""
Sprint 执行器 — 与 Scrum **Sprint** 时间盒内交付对应

顺序（或受控并行）跑完单个 ``SprintDefinition`` / ``SprintDefinition`` 的 **Sprint Backlog**（``tasks``），
聚合为 ``SprintResult``；多 Sprint 由 ``SprintOrchestrator`` 编排。断点续跑通过 ``StateStore``。

Scrum 命名对照见 ``docs/DESIGN_SCRUM_NAMING_MIGRATION.md``。
"""

import asyncio
import re
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger

from ..release_plan.models import ReleasePlan, EvolutionParams, SprintDefinition, SprintBacklogItem
from .hooks.sprint_hooks import NoOpSprintLifecycleHooks, SprintLifecycleHooks
from .sprint_types import ExecutionStatus, SprintResult, TaskResult
from .state.checkpoint import CheckpointMixin
from .state.state_store import StateStore, get_state_store
from .state.wire_compat import context_plan_id_name


class SprintExecutor(CheckpointMixin):
    """
    执行单个 **Sprint** 的 Sprint Backlog（支持断点续传，经 ``StateStore``）。
    """

    def __init__(
        self,
        max_parallel: int = 3,
        feedback_loop: Optional[Any] = None,
        release_plan: Optional[ReleasePlan] = None,
        evolution_engine: Optional[Any] = None,
        error_handler: Optional[Any] = None,
        state_store: Optional[StateStore] = None,
        max_verify_fix_rounds: int = 3,
        runtime_config: Optional[Any] = None,
        sprint_hooks: Optional[SprintLifecycleHooks] = None,
    ):
        self._agent_executors: Dict[str, Callable] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._max_parallel = max_parallel
        self._max_verify_fix_rounds = max(1, int(max_verify_fix_rounds))
        self._runtime_config = runtime_config
        self._sprint_hooks: SprintLifecycleHooks = sprint_hooks or NoOpSprintLifecycleHooks()
        self._event_bus = None
        self._feedback_loop = feedback_loop
        self._release_plan = release_plan
        self._sprint_count = 0
        self._evolution_engine = evolution_engine
        self._error_handler = error_handler
        self._state_store = state_store
        self._execution_id: str = ""
        self._cancelled: bool = False
        self._checkpoint_interval = 1
        self._register_default_executors()

    @property
    def state_store(self) -> StateStore:
        if self._state_store is None:
            self._state_store = get_state_store()
        return self._state_store

    def set_state_store(self, state_store: StateStore) -> None:
        self._state_store = state_store
        logger.info("StateStore 已注入到 SprintExecutor")

    def set_feedback_loop(self, feedback_loop) -> None:
        self._feedback_loop = feedback_loop

    def set_release_plan(self, release_plan: ReleasePlan) -> None:
        self._release_plan = release_plan

    def set_evolution_engine(self, evolution_engine) -> None:
        self._evolution_engine = evolution_engine

    def set_error_handler(self, error_handler) -> None:
        self._error_handler = error_handler

    def set_sprint_hooks(self, sprint_hooks: Optional[SprintLifecycleHooks]) -> None:
        """注册 Sprint 生命周期钩子（None 表示使用无操作实现）。"""
        self._sprint_hooks = sprint_hooks or NoOpSprintLifecycleHooks()

    def get_feedback_history(self) -> List[Any]:
        if self._feedback_loop:
            return self._feedback_loop.get_history()
        return []


    def _register_default_executors(self) -> None:
        self._agent_executors = {
            "coder": self._execute_coder_task,
            "implement": self._execute_coder_task,
            "tester": self._execute_tester_task,
            "architect": self._execute_architect_task,
            "regression_tester": self._execute_regression_tester_task,
        }

    def _dry_run(self) -> bool:
        return bool(self._runtime_config and getattr(self._runtime_config, "dry_run", False))

    def _build_agent_context(self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any]):
        from .agents.base import AgentContext

        deps = dict(context.get("dependencies") or {})
        cb: Dict[str, Any] = {
            "project_path": str(context.get("project_path", ".")),
        }
        for key in ("architecture_design", "modules", "tech_stack", "issues", "code"):
            if key in context:
                cb[key] = context[key]
        if context.get("task_guidance"):
            cb["task_guidance"] = context["task_guidance"]
        if context.get("verify_fix_notes"):
            vn = str(context["verify_fix_notes"]).strip()
            if vn:
                prev = (cb.get("task_guidance") or "").strip()
                extra = "\n\n[Coder 验证-修复 — 上一轮失败]\n" + vn
                cb["task_guidance"] = (prev + extra).strip() if prev else extra.strip()
        if context.get("release_plan_overlay_yaml"):
            cb["release_plan_overlay"] = context["release_plan_overlay_yaml"]
        locked_engine = str(
            context.get("_sprint_coding_engine") or context.get("coding_engine", "aider")
        )
        rid, rname = context_plan_id_name(context)
        return AgentContext(
            release_plan_id=str(rid),
            release_plan_name=str(rname),
            project_goals=str(context.get("project_goals", "")),
            sprint_name=str(context.get("sprint_name", sprint_name)),
            sprint_index=int(context.get("sprint_index", 0)),
            dependencies=deps,
            codebase_context=cb,
            metadata={
                "coding_engine": locked_engine,
                "quality_level": context.get("quality_level", "L1"),
                "constraints": task.constraints or [],
            },
        )

    def register_agent_executor(self, agent_type: str, executor: Callable):
        self._agent_executors[agent_type] = executor

    def cancel(self) -> None:
        """标记执行为取消状态，SprintExecutor 在下一个 Sprint 边界停止"""
        self._cancelled = True
        logger.info("🛑 SprintExecutor 已收到取消信号，将在下一个 Sprint 边界停止")

    @property
    def is_cancelled(self) -> bool:
        """检查是否已被取消"""
        return self._cancelled

    TASK_SPLIT_THRESHOLD = 500
    MAX_SUBTASKS = 5

    def _should_split_task(self, task: SprintBacklogItem) -> bool:
        if len(task.description) >= self.TASK_SPLIT_THRESHOLD:
            return True
        complex_keywords = ["重构", "迁移", "优化", "重写", "implement", "refactor", "migrate", "optimize", "rewrite"]
        task_lower = task.description.lower()
        keyword_count = sum(1 for kw in complex_keywords if kw.lower() in task_lower)
        return keyword_count >= 2

    def _split_task(self, task: SprintBacklogItem) -> List[SprintBacklogItem]:
        subtasks = []
        task_text = task.description
        action_patterns = [
            r"实现[^\s，,。]+", r"添加[^\s，,。]+", r"修改[^\s，,。]+",
            r"修复[^\s，,。]+", r"优化[^\s，,。]+", r"创建[^\s，,。]+",
        ]
        subtask_parts = []
        for pattern in action_patterns:
            matches = re.findall(pattern, task_text, re.IGNORECASE)
            subtask_parts.extend(matches)

        if len(subtask_parts) >= 2:
            for i, part in enumerate(subtask_parts[:self.MAX_SUBTASKS]):
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
                description=task_text[:self.TASK_SPLIT_THRESHOLD] + "..." if len(task_text) > self.TASK_SPLIT_THRESHOLD else task_text,
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

    async def execute_sprint(self, sprint: SprintDefinition, context: Optional[Dict[str, Any]] = None, save_checkpoint: bool = True) -> SprintResult:
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=ExecutionStatus.RUNNING)
        logger.info(f"开始执行 Sprint: {sprint.name}")

        ctx_acc: Dict[str, Any] = dict(context or {})
        ctx_acc.setdefault("sprint_name", sprint.name)
        ctx_acc.setdefault(
            "_sprint_coding_engine",
            ctx_acc.get("coding_engine", "aider"),
        )

        for task in sprint.tasks:
            task_result = await self._execute_task(task, sprint.name, ctx_acc)
            result.task_results.append(task_result)
            if task_result.status == ExecutionStatus.SUCCESS:
                deps = ctx_acc.setdefault("dependencies", {})
                if task.agent in ("coder", "implement"):
                    deps["code"] = task_result.output
                if task.agent == "architect":
                    ctx_acc["architecture_design"] = task_result.output

        if all(r.status == ExecutionStatus.SUCCESS for r in result.task_results):
            result.status = ExecutionStatus.SUCCESS
        elif any(r.status == ExecutionStatus.FAILED for r in result.task_results):
            result.status = ExecutionStatus.FAILED
        else:
            result.status = ExecutionStatus.SUCCESS

        result.duration = time.time() - start_time
        self._collect_feedback(sprint, result)
        self._persist_sprint_result(sprint, result)

        if save_checkpoint and self._execution_id:
            self._save_checkpoint(0, sprint.name, result)

        return result

    def _collect_feedback(self, sprint: SprintDefinition, result: SprintResult) -> None:
        if self._feedback_loop is None:
            return
        try:
            self._sprint_count += 1
            if self._release_plan:
                feedback = self._feedback_loop.collect(self._release_plan, [result])
            else:
                class _FeedbackReleasePlanStub:
                    def __init__(self):
                        self.id = f"sprint-{self._sprint_count}"
                        self.project = type("obj", (), {"name": sprint.name})()
                feedback = self._feedback_loop.collect(_FeedbackReleasePlanStub(), [result])
            self._feedback_loop.save(feedback)
        except Exception as e:
            logger.warning(f"收集反馈失败: {e}")

    def _persist_sprint_result(self, sprint: SprintDefinition, result: SprintResult) -> None:
        """持久化 Sprint 执行结果到 StateStore"""
        try:
            # 构建执行记录
            task_records = []
            for tr in result.task_results:
                task_records.append({
                    "description": tr.work_item.description,
                    "agent": tr.work_item.agent,
                    "status": tr.status.value if hasattr(tr.status, "value") else str(tr.status),
                    "output": tr.output,
                    "error": tr.error,
                    "duration": tr.duration,
                })

            execution_record = {
                "sprint_name": sprint.name,
                "status": result.status.value if hasattr(result.status, "value") else str(result.status),
                "task_results": task_records,
                "duration": result.duration,
                "timestamp": datetime.now().isoformat(),
            }

            # 通过 StateStore 的 metadata 持久化
            state = self.state_store.load(self._execution_id or "default")
            if state:
                if "sprint_history" not in state.metadata:
                    state.metadata["sprint_history"] = []
                state.metadata["sprint_history"].append(execution_record)
                state.updated_at = datetime.now().isoformat()
                self.state_store.save(state)
                logger.info(f"📝 Sprint 结果已持久化: {sprint.name}")
            else:
                logger.debug("无 StateStore 状态，跳过持久化")
        except Exception as e:
            logger.warning(f"持久化 Sprint 结果失败: {e}")

    def _log_task_execution(self, task: SprintBacklogItem, task_result: TaskResult) -> None:
        """记录单个 Task 执行日志"""
        status_str = task_result.status.value if hasattr(task_result.status, "value") else str(task_result.status)
        logger.info(
            f"📋 Task [{task.agent}] {task.description[:40]}... → {status_str} "
            f"({task_result.duration:.2f}s)"
        )

    async def execute_sprints(
        self,
        sprints: List[SprintDefinition],
        mode: str = "normal",
        evolution_config: Optional[EvolutionParams] = None,
        context: Optional[Dict[str, Any]] = None,
        execution_id: Optional[str] = None,
        resume: bool = False,
        release_plan: Optional[ReleasePlan] = None,
        sprint_index_offset: int = 0,
    ) -> List[SprintResult]:
        self._cancelled = False  # 重置取消标志
        if resume and execution_id:
            return await self._resume_execution(
                execution_id, sprints, context, release_plan=release_plan, sprint_index_offset=sprint_index_offset
            )
        self._execution_id = execution_id or self._init_execution_state()
        if mode == "evolution" and self._evolution_engine:
            return await self._execute_evolution_sprints(sprints, evolution_config, context or {})
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
        self.state_store.update_status(execution_id, ExecutionStatus.RUNNING)
        results: List[SprintResult] = []
        ctx = context or {}
        for i, sprint in enumerate(sprints):
            if i < start_sprint_idx:
                continue
            ctx["sprint_index"] = sprint_index_offset + i
            ctx["sprint_name"] = sprint.name
            ctx["project_goals"] = " ".join(sprint.goals)
            try:
                await self._sprint_hooks.on_before_sprint(ctx["sprint_index"], sprint, ctx, release_plan)
            except Exception as e:
                logger.warning("on_before_sprint hook failed: {}", e)
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
        for i, sprint in enumerate(sprints):
            if self._cancelled:
                logger.info(f"🛑 执行已取消，跳过剩余 Sprint (已完成 {i}/{len(sprints)})")
                break

            global_idx = sprint_index_offset + i
            ctx["sprint_index"] = global_idx
            ctx["sprint_name"] = sprint.name
            ctx["project_goals"] = " ".join(sprint.goals)

            try:
                await self._sprint_hooks.on_before_sprint(global_idx, sprint, ctx, release_plan)
            except Exception as e:
                logger.warning("on_before_sprint hook failed: {}", e)

            result = await self.execute_sprint(sprint, ctx, save_checkpoint=True)
            results.append(result)

            if result.status == ExecutionStatus.FAILED:
                logger.warning(f"Sprint 失败: {sprint.name}")
                if self._feedback_loop:
                    feedback = self._get_feedback_for_sprint(sprint, result)
                    if feedback:
                        decision = self._feedback_loop.decide(feedback)
                        if decision["action"] == "retry" and self._should_retry(sprint):
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
        """Sprint 失败后反馈闭环重试次数上限（与 max_verify_fix_rounds 对齐，默认 3）"""
        retry_count = getattr(sprint, "_retry_count", 0)
        return retry_count < self._max_verify_fix_rounds

    async def _retry_with_feedback(self, sprint: SprintDefinition, feedback: Any, decision: Dict[str, Any], context: Optional[Dict[str, Any]]) -> SprintResult:
        """根据反馈重试 Sprint"""
        object.__setattr__(sprint, '_retry_count', getattr(sprint, '_retry_count', 0) + 1)
        if context is None:
            context = {}
        context["retry_feedback"] = feedback.to_dict()
        context["improvement_suggestions"] = decision.get("suggestions", [])
        context["retry_from_failure"] = True
        logger.info(f"重试 Sprint {sprint.name}，携带 {len(decision.get('suggestions', []))} 条改进建议")
        result = await self.execute_sprint(sprint, context, save_checkpoint=True)
        return result

    def _get_feedback_for_sprint(self, sprint: SprintDefinition, result: SprintResult) -> Any:
        """收集 Sprint 的反馈（复用已有逻辑）"""
        if not self._feedback_loop:
            return None
        try:
            if self._release_plan:
                return self._feedback_loop.collect(self._release_plan, [result])
            else:
                class _FeedbackReleasePlanStub:
                    def __init__(self):
                        self.id = "sprint-feedback"
                        self.project = type("obj", (), {"name": sprint.name})()
                return self._feedback_loop.collect(_FeedbackReleasePlanStub(), [result])
        except Exception as e:
            logger.warning(f"收集反馈失败: {e}")
            return None

    async def _execute_evolution_sprints(self, sprints: List[SprintDefinition], evolution_config: Optional[EvolutionParams], context: Optional[Dict[str, Any]] = None) -> List[SprintResult]:
        results = []
        max_generations = evolution_config.iterations if evolution_config else 3
        for sprint in sprints:
            assert self._evolution_engine is not None
            result = await self._evolution_engine.evolve_sprint(sprint=sprint, max_generations=max_generations)
            sprint_result = self._convert_evolution_result(sprint, result)
            results.append(sprint_result)
            if self._execution_id:
                self._save_checkpoint(0, sprint.name, sprint_result)
        return results

    def _convert_evolution_result(self, sprint: SprintDefinition, evo_result: Any) -> SprintResult:
        success = evo_result.success if hasattr(evo_result, "success") else True
        sprint_result = SprintResult(
            sprint=sprint,
            status=ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED,
            duration=evo_result.execution_time if hasattr(evo_result, "execution_time") else 0.0,
        )
        return sprint_result

    def set_event_bus(self, event_bus) -> None:
        self._event_bus = event_bus

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self._event_bus:
            from .events import Event, EventType
            try:
                event = Event(type=EventType[event_type.upper()], data=data)
                await self._event_bus.emit(event)
            except KeyError:
                pass

    async def execute_sprint_parallel(self, sprint: SprintDefinition, context: Optional[Dict[str, Any]] = None, dependency_map: Optional[Dict[int, Set[int]]] = None, save_checkpoint: bool = True) -> SprintResult:
        start_time = time.time()
        result = SprintResult(sprint=sprint, status=ExecutionStatus.RUNNING)
        ctx_base = dict(context or {})
        ctx_base.setdefault(
            "_sprint_coding_engine",
            ctx_base.get("coding_engine", "aider"),
        )
        context = ctx_base
        task_count = len(sprint.tasks)
        completed: Set[int] = set()
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

    async def _execute_task_with_event(self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any]) -> TaskResult:
        result = await self._execute_task(task, sprint_name, context)
        return result

    async def _execute_task(self, task: SprintBacklogItem, sprint_name: str, context: Dict[str, Any]) -> TaskResult:
        start_time = time.time()
        executor = self._agent_executors.get(task.agent)
        if not executor:
            return TaskResult(work_item=task, sprint_name=sprint_name, status=ExecutionStatus.FAILED, error=f"未知的 Agent 类型: {task.agent}")
        try:
            # 注入反馈闭环信息到 task context
            enriched_context = dict(context)
            enriched_context.setdefault("sprint_name", sprint_name)
            if self._runtime_config is not None:
                base_engine = enriched_context.get("coding_engine") or getattr(
                    self._runtime_config, "coding_engine", "aider"
                )
                enriched_context.setdefault("_sprint_coding_engine", base_engine)
                enriched_context["coding_engine"] = enriched_context["_sprint_coding_engine"]
                enriched_context["quality_level"] = (
                    self._runtime_config.effective_quality_level()
                    if hasattr(self._runtime_config, "effective_quality_level")
                    else getattr(self._runtime_config, "quality_level", "L1")
                )
            else:
                enriched_context.setdefault(
                    "_sprint_coding_engine",
                    enriched_context.get("coding_engine", "aider"),
                )
                enriched_context["coding_engine"] = enriched_context["_sprint_coding_engine"]
            if "improvement_suggestions" in context:
                suggestions = context["improvement_suggestions"]
                if suggestions:
                    enriched_context["task_guidance"] = (
                        "前序 Sprint 反馈改进建议:\n"
                        + "\n".join(f"- {s}" for s in suggestions)
                    )
            if "retry_from_failure" in context:
                enriched_context["task_guidance"] = enriched_context.get("task_guidance", "") + (
                    "\n[重要] 本次为失败重试，请特别注意上述问题。"
                )
            output = await executor(task, enriched_context)
            task_result = TaskResult(work_item=task, sprint_name=sprint_name, status=ExecutionStatus.SUCCESS, output=output, duration=time.time() - start_time)
            self._log_task_execution(task, task_result)
            return task_result
        except Exception as e:
            return TaskResult(work_item=task, sprint_name=sprint_name, status=ExecutionStatus.FAILED, error=str(e), duration=time.time() - start_time)

    async def _execute_coder_task(self, task: SprintBacklogItem, context: Dict[str, Any]) -> str:
        if self._dry_run():
            return f"[dry_run] 完成: {task.description[:120]}"
        from .agents.coder_base import CoderAgent

        work = dict(context)
        max_r = self._max_verify_fix_rounds
        last_msg = "CoderAgent 执行失败"
        for attempt in range(max_r):
            ctx = self._build_agent_context(task, work.get("sprint_name", ""), work)
            agent = CoderAgent()
            res = await agent.execute(task.description, ctx)
            if res.success:
                return res.output or ""
            last_msg = res.error or last_msg
            if attempt >= max_r - 1:
                raise RuntimeError(last_msg)
            prev = (work.get("verify_fix_notes") or "").strip()
            work["verify_fix_notes"] = (
                prev + f"\n[attempt {attempt + 1}/{max_r}] {last_msg}"
            ).strip()

    async def _execute_tester_task(self, task: SprintBacklogItem, context: Dict[str, Any]) -> str:
        if self._dry_run():
            return f"[dry_run] 测试完成: {task.description[:80]}"
        from .agents.tester import TesterAgent

        ctx = self._build_agent_context(task, context.get("sprint_name", ""), context)
        agent = TesterAgent()
        res = await agent.execute(task.description, ctx)
        if not res.success:
            raise RuntimeError(res.error or "TesterAgent 执行失败")
        return res.output or ""

    async def _execute_architect_task(self, task: SprintBacklogItem, context: Dict[str, Any]) -> str:
        if self._dry_run():
            summary = f"[dry_run] 架构设计: {task.description[:80]}"
            context["architecture_design"] = summary
            return summary
        from .agents.architect import ArchitectureAgent

        ctx = self._build_agent_context(task, context.get("sprint_name", ""), context)
        agent = ArchitectureAgent()
        res = await agent.execute(task.description, ctx)
        if not res.success:
            raise RuntimeError(res.error or "ArchitectureAgent 执行失败")
        arch = ctx.codebase_context.get("architecture_design") or res.output or ""
        if arch:
            context["architecture_design"] = arch
        return str(arch)

    async def _execute_regression_tester_task(self, task: SprintBacklogItem, context: Dict[str, Any]) -> str:
        if self._dry_run():
            return f"[dry_run] 回归测试完成: {task.description[:80]}"
        await asyncio.sleep(0.05)
        return f"回归测试完成: {task.description[:80]}"


    def _analyze_dependencies(
        self,
        tasks: List[SprintBacklogItem],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[int, Set[int]]:
        """
        分析任务间的依赖关系
        
        Args:
            tasks: 任务列表
            context: 执行上下文
            
        Returns:
            Dict[int, Set[int]]: 任务索引到其依赖任务索引集合的映射
        """
        dependency_map: Dict[int, Set[int]] = {i: set() for i in range(len(tasks))}

        # 对每个任务分析依赖
        for i, task in enumerate(tasks):
            self._add_keyword_based_dependencies(tasks, i, task, dependency_map)
            self._add_target_path_dependencies(tasks, i, task, dependency_map)
            self._add_agent_type_dependencies(tasks, i, task, dependency_map)

        # 移除自引用
        for idx in dependency_map:
            dependency_map[idx].discard(idx)

        return dependency_map

    def _add_keyword_based_dependencies(
        self,
        tasks: List[SprintBacklogItem],
        task_idx: int,
        task: SprintBacklogItem,
        dep_map: Dict[int, Set[int]]
    ) -> None:
        """基于关键词分析依赖关系"""
        dependency_keywords = [
            ("测试", "实现"), ("test", "implement"),
            ("verify", "build"), ("build", "compile"),
            ("集成", "单元"), ("integration", "unit"),
            ("端到端", "模块"), ("e2e", "module"),
            ("部署", "构建"), ("deploy", "build"),
        ]

        task_text = task.description.lower()

        for dep_kw, src_kw in dependency_keywords:
            if dep_kw in task_text:
                for j in range(task_idx):
                    prev_text = tasks[j].description.lower()
                    prev_target = (tasks[j].target or "").lower()
                    if src_kw in prev_text or src_kw in prev_target:
                        dep_map[task_idx].add(j)

    def _add_target_path_dependencies(
        self,
        tasks: List[SprintBacklogItem],
        task_idx: int,
        task: SprintBacklogItem,
        dep_map: Dict[int, Set[int]]
    ) -> None:
        """基于target文件路径分析依赖关系"""
        if not task.target:
            return

        task_ext = task.target.lower().split('.')[-1] if '.' in task.target.lower() else ''
        code_extensions = {'py', 'ts', 'js', 'go', 'java'}

        if task_ext not in code_extensions:
            return

        for j in range(task_idx):
            prev_task = tasks[j]
            if not prev_task.target:
                continue

            prev_ext = prev_task.target.lower().split('.')[-1] if '.' in prev_task.target.lower() else ''
            if prev_ext == task_ext:
                dep_map[task_idx].add(j)

    def _add_agent_type_dependencies(
        self,
        tasks: List[SprintBacklogItem],
        task_idx: int,
        task: SprintBacklogItem,
        dep_map: Dict[int, Set[int]]
    ) -> None:
        """基于任务类型/agent分析依赖关系"""
        task_text = task.description.lower()

        # Agent类型依赖: 测试任务依赖实现任务
        if task.agent == "tester":
            for j in range(task_idx):
                if tasks[j].agent in ["coder", "implement"]:
                    dep_map[task_idx].add(j)

        # 任务文本依赖规则
        dep_rules = [
            (["build", "编译"], ["compile", "编译"]),
            (["deploy", "部署"], ["build", "构建"]),
        ]

        for target_kws, source_kws in dep_rules:
            if any(kw in task_text for kw in target_kws):
                for j in range(task_idx):
                    prev_text = tasks[j].description.lower()
                    if any(kw in prev_text for kw in source_kws):
                        dep_map[task_idx].add(j)


    def _extract_file_paths(self, text: str) -> List[str]:
        """从文本中提取文件路径"""
        import re
        patterns = [
            r'(?:from|import|include|require)\s+["\']([^"\']+)["\']',
            r'[\'"][\./]*([\w/]+\.[\w]+)[\'"]',
            r'path:\s*["\']?([^"\'\s]+)["\']?',
            r'file:\s*["\']?([^"\'\s]+)["\']?',
        ]

        paths = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            paths.extend(matches)

        return list(set(paths))

    def get_execution_order(self, tasks: List[SprintBacklogItem]) -> List[List[int]]:
        """
        获取任务的拓扑排序执行顺序
        
        Args:
            tasks: 任务列表
            
        Returns:
            List[List[int]]: 分批执行的任务索引列表
            例如: [[0, 1], [2], [3, 4]] 表示任务分三批执行
        """
        dependency_map = self._analyze_dependencies(tasks)

        # 计算每个任务的入度
        in_degree = {i: len(deps) for i, deps in dependency_map.items()}
        remaining = set(range(len(tasks)))

        batches: List[List[int]] = []

        while remaining:
            # 找到入度为0的任务
            ready = [i for i in remaining if in_degree.get(i, 0) == 0]

            if not ready:
                # 存在循环依赖，随机选择一个
                ready = [min(remaining)]

            batches.append(ready)

            # 更新入度
            for task_idx in ready:
                remaining.discard(task_idx)
                for other_idx, deps in dependency_map.items():
                    if task_idx in deps:
                        in_degree[other_idx] -= 1

        return batches
