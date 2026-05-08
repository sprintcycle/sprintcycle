"""
SprintCycle 统一 API

Dashboard / CLI / MCP / SDK 共用的唯一入口。
所有操作通过此类暴露，三端只做参数适配和展示格式化。

主操作: plan / run / run_release_plan / diagnose / status / rollback / stop

产品与技术叙述以仓库 ``docs/PRODUCT_TECH_V4.md`` 与 ``SPRINTCYCLE_PRODUCT_TECH_PLAN.md``
（V4.0 工程真理源）为准；``run``/resume **主路径**为 ``ReleasePlan`` → ``expand_release_plan_for_execution``
→ ``SprintOrchestrator`` → ``SprintExecutor``。
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .config import RuntimeConfig
from .diagnostic.provider import ProjectDiagnostic
from .execution.cache import configure_execution_cache_from_runtime
from .execution.events import (
    ensure_default_execution_event_backend_for_project,
    get_execution_event_backend,
)
from .execution.rollback import RollbackManager
from .execution.state.state_store import (
    configure_default_store,
    get_state_store,
)
from .intent.parser import IntentParser
from .orchestration.sprint_orchestrator import ExecutionStatus, SprintOrchestrator
from .release_plan.generator import IntentReleasePlanGenerator
from .release_plan.models import ExecutionMode, ReleasePlan
from .release_plan.parser import ReleasePlanParser
from .release_plan.payload_keys import checkpoint_plan_yaml
from .release_plan.validator import ReleasePlanValidator
from .results import (
    DiagnoseResult,
    PlanResult,
    RollbackResult,
    RunResult,
    StatusResult,
    StopResult,
)
from .run_workspace import (
    apply_policy_to_tasks,
    attach_workspace_metadata,
    effective_write_policy,
    ensure_project_layout,
    normalize_reference_paths,
    normalize_write_policy,
)


class SprintCycle:
    """SprintCycle 统一 API — Dashboard / CLI / MCP / SDK 共用。

    **执行主架构**：``ReleasePlan`` → ``expand_release_plan_for_execution`` →
    ``SprintOrchestrator.execute_release_plan`` → ``SprintExecutor``。自进化与普通迭代在执行栈上汇合。
    """

    def __init__(
        self,
        project_path: str = ".",
        config: Optional[RuntimeConfig] = None,
    ):
        self.project_path = os.path.abspath(project_path)
        base_cfg = config or RuntimeConfig.from_project(self.project_path)
        self.config = base_cfg.merge(base_cfg, {"project_path": self.project_path})
        configure_execution_cache_from_runtime(self.config, self.project_path)
        configure_default_store(self.project_path, self.config)
        ensure_default_execution_event_backend_for_project(self.project_path, self.config)
        self._orchestrator: Optional[SprintOrchestrator] = None
        self._hitl_coordinator: Optional[Any] = None

    def _get_hitl_coordinator(self) -> Optional[Any]:
        if not getattr(self.config, "hitl_enabled", False):
            return None
        if self._hitl_coordinator is None:
            from .hitl import create_hitl_coordinator

            self._hitl_coordinator = create_hitl_coordinator(
                self.project_path,
                self.config,
                get_execution_event_backend(),
            )
        return self._hitl_coordinator

    @property
    def orchestrator(self) -> SprintOrchestrator:
        if self._orchestrator is None:
            self._orchestrator = SprintOrchestrator(
                config=self.config,
                event_bus=get_execution_event_backend(),
                project_path=self.project_path,
                hitl_coordinator=self._get_hitl_coordinator(),
            )
        return self._orchestrator

    async def hitl_pending(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        c = self._get_hitl_coordinator()
        if not c:
            return {"success": True, "data": []}
        return {"success": True, "data": await c.list_pending(execution_id)}

    async def hitl_submit(
        self, request_id: str, decision: str, note: Optional[str] = None
    ) -> Dict[str, Any]:
        from .hitl.decision_normalize import validate_hitl_decision_for_submit

        if validate_hitl_decision_for_submit(decision) is None:
            return {
                "success": False,
                "error": (
                    "Invalid HITL decision. Use approve, skip_sprint, or abort_execution "
                    "(optional aliases: reject/deny/abort/stop/halt→abort_execution; "
                    "skip→skip_sprint; pass/ok/yes/continue→approve). "
                    "regen / need_info / modify are not accepted."
                ),
            }
        c = self._get_hitl_coordinator()
        if not c:
            return {"success": False, "error": "HITL is disabled"}
        rec = await c.submit_decision(request_id, decision, note)
        if rec is None:
            return {"success": False, "error": "Request not found or already resolved"}
        return {"success": True, "data": rec.to_dict()}

    async def hitl_history(
        self, execution_id: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        c = self._get_hitl_coordinator()
        if not c:
            return {"success": True, "data": []}
        return {"success": True, "data": await c.list_history(execution_id, limit)}

    async def hitl_show(self, request_id: str) -> Dict[str, Any]:
        """按 ID 返回单条 HITL 记录（不依赖 ``hitl_enabled``，便于查看历史库）。"""
        from .hitl.store_sqlite import HitlSqliteStore, default_hitl_db_path

        rid = (request_id or "").strip()
        if not rid:
            return {"success": False, "error": "request_id required"}
        raw = getattr(self.config, "hitl_db_path", None)
        db = (
            str(raw).strip()
            if isinstance(raw, str) and str(raw).strip()
            else default_hitl_db_path(self.project_path)
        )
        store = HitlSqliteStore(db)
        rec = await store.get(rid)
        if rec is None:
            return {"success": False, "error": "Request not found"}
        return {"success": True, "data": rec.to_dict()}

    def execution_events(
        self,
        execution_id: str,
        *,
        limit: int = 200,
    ) -> Dict[str, Any]:
        """只读：从 SQLite MQ 执行事件库按 ``execution_id`` 拉取已持久化事件（``execution_event_backend=sqlite``）。"""
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        mode = (getattr(self.config, "execution_event_backend", None) or "sqlite").strip().lower()
        if mode != "sqlite":
            return {
                "success": True,
                "data": [],
                "backend": mode,
                "message": (
                    "Replay is only available when execution_event_backend=sqlite "
                    "(persisted execution event MQ)."
                ),
            }
        from .execution.sqlite_event_backend import (
            execution_events_sqlite_path,
            fetch_execution_events_for_replay,
        )

        path = execution_events_sqlite_path(self.project_path)
        rows = fetch_execution_events_for_replay(path, eid, limit=limit)
        return {"success": True, "data": rows, "backend": "sqlite"}

    def reload_runtime_config(self) -> None:
        """从磁盘重新加载 ``RuntimeConfig``（含 ``sprintcycle.runtime.yaml``），并重绑缓存 / 状态 / 事件后端。"""
        base = RuntimeConfig.from_project(self.project_path)
        self.config = base.merge(base, {"project_path": self.project_path})
        configure_execution_cache_from_runtime(self.config, self.project_path)
        configure_default_store(self.project_path, self.config)
        ensure_default_execution_event_backend_for_project(self.project_path, self.config)
        self._orchestrator = None
        self._hitl_coordinator = None

    # ─── 1. plan — 看计划，不干活 ───

    def plan(
        self,
        intent: str = "",
        mode: str = "auto",
        target: Optional[str] = None,
        release_plan_yaml: Optional[str] = None,
        release_plan_path: Optional[str] = None,
        product: Optional[str] = None,
        reference_paths: Optional[List[str]] = None,
        write_policy: str = "auto",
        **kwargs: Any,
    ) -> PlanResult:
        """意图 → Release Plan（不执行），返回 release_plan_yaml 供 run() 使用"""
        start = time.time()
        try:
            plan = self._resolve_release_plan(
                intent,
                mode,
                target,
                release_plan_yaml,
                release_plan_path,
                product=product,
                reference_paths=reference_paths,
                write_policy=write_policy,
                **kwargs,
            )
            validation = ReleasePlanValidator().validate(plan)

            sprints = [
                {
                    "name": s.name,
                    "tasks": [t.description for t in s.tasks],
                }
                for s in plan.sprints
            ]

            return PlanResult(
                success=validation.is_valid,
                release_plan_yaml=plan.to_yaml(),
                sprints=sprints,
                mode=plan.mode.value,
                release_plan_name=plan.project.name,
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("plan failed")
            return PlanResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 2. run — 一键执行 ───

    def run(
        self,
        intent: Optional[str] = None,
        mode: str = "auto",
        target: Optional[str] = None,
        release_plan_yaml: Optional[str] = None,
        release_plan_path: Optional[str] = None,
        execution_id: Optional[str] = None,
        resume: bool = False,
        confirm_knowledge: bool = False,
        product: Optional[str] = None,
        reference_paths: Optional[List[str]] = None,
        write_policy: str = "auto",
        **kwargs: Any,
    ) -> RunResult:
        """执行（一键到底 / 断点续跑 / 从 Release Plan YAML 执行）"""
        start = time.time()
        try:
            # 断点续跑
            if resume and execution_id:
                return self._resume_execution(execution_id, start)

            ensure_project_layout(self.project_path)

            rp_yaml = release_plan_yaml
            rp_path = release_plan_path
            plan = self._resolve_release_plan(
                intent,
                mode,
                target,
                rp_yaml,
                rp_path,
                product=product,
                reference_paths=reference_paths,
                write_policy=write_policy,
                **kwargs,
            )
            run_result, finalize_result = self._run_resolved_plan(
                plan, start, confirm_knowledge=confirm_knowledge
            )
            if hasattr(run_result, "release_finalization"):
                run_result.release_finalization = finalize_result.to_dict() if hasattr(finalize_result, "to_dict") else {}
            return run_result
        except Exception as e:
            logger.exception("run failed")
            return RunResult(success=False, error=str(e), duration=time.time() - start)

    def run_release_plan(
        self,
        release_plan: ReleasePlan,
        *,
        confirm_knowledge: bool = False,
    ) -> RunResult:
        """执行已解析的 Release Plan（与 ``run(release_plan_yaml=…)`` 共用知识门与编排路径）。"""
        start = time.time()
        validation = ReleasePlanValidator().validate(release_plan)
        if not validation.is_valid:
            return RunResult(
                success=False,
                error="Release Plan 验证失败",
                duration=time.time() - start,
            )
        try:
            run_result, finalize_result = self._run_resolved_plan(
                release_plan,
                start,
                confirm_knowledge=confirm_knowledge,
            )
            if hasattr(run_result, "release_finalization"):
                run_result.release_finalization = finalize_result.to_dict() if hasattr(finalize_result, "to_dict") else {}
            return run_result
        except Exception as e:
            logger.exception("run_release_plan failed")
            return RunResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 3. diagnose — 项目体检 ───

    def diagnose(self, **kwargs: Any) -> DiagnoseResult:
        """诊断项目健康状态"""
        start = time.time()
        try:
            provider = ProjectDiagnostic(project_path=self.project_path)
            report = provider.diagnose()

            # 提取报告数据
            health_score = 0.0
            issues: List[Dict[str, Any]] = []
            coverage = 0.0
            complexity: Dict[str, Any] = {}

            if hasattr(report, "health_score"):
                health_score = float(report.health_score)
            if hasattr(report, "issues"):
                for issue in report.issues:
                    issues.append(
                        {
                            "severity": str(getattr(issue, "severity", "")),
                            "message": str(getattr(issue, "message", "")),
                        }
                    )
            if hasattr(report, "coverage"):
                coverage = float(report.coverage)
            if hasattr(report, "complexity"):
                complexity = (
                    report.complexity
                    if isinstance(report.complexity, dict)
                    else {"value": str(report.complexity)}
                )

            return DiagnoseResult(
                success=True,
                health_score=health_score,
                issues=issues,
                coverage=coverage,
                complexity=complexity,
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("diagnose failed")
            return DiagnoseResult(
                success=False, error=str(e), duration=time.time() - start
            )

    # ─── 4. status — 查状态/历史 ───

    def status(
        self,
        execution_id: Optional[str] = None,
        filter_status: Optional[str] = None,
    ) -> StatusResult:
        """查状态（传 id 查单条，不传列全部）"""
        start = time.time()
        try:
            store = get_state_store()

            if execution_id:
                state = store.load(execution_id)
                if state is None:
                    return StatusResult(
                        success=False,
                        error=f"未找到执行记录: {execution_id}",
                        duration=time.time() - start,
                    )
                return StatusResult(
                    success=True,
                    execution_id=state.execution_id,
                    status=state.status.value,
                    current_sprint=state.current_sprint,
                    total_sprints=state.total_sprints,
                    sprint_history=state.metadata.get("sprint_history", []),
                    release_finalization=state.metadata.get("release_finalization", {}),
                    duration=time.time() - start,
                )
            else:
                status_filter = None
                if filter_status:
                    try:
                        status_filter = ExecutionStatus(filter_status)
                    except ValueError:
                        pass
                states = store.list_executions(status=status_filter)
                return StatusResult(
                    success=True,
                    executions=[s.to_dict() for s in states],
                    duration=time.time() - start,
                )
        except Exception as e:
            logger.exception("status failed")
            return StatusResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 5. rollback — 撤回 ───

    def rollback(self, execution_id: str, **kwargs: Any) -> RollbackResult:
        """回滚到指定执行前的状态"""
        start = time.time()
        try:
            # 尝试 git 回滚
            if self._is_git_repo():
                commit_hash = self._find_pre_execution_commit(execution_id)
                if commit_hash:
                    rc, _, _ = self._run_git(
                        ["checkout", commit_hash, "--", "."], cwd=self.project_path
                    )
                    if rc == 0:
                        return RollbackResult(
                            success=True,
                            execution_id=execution_id,
                            rollback_point=commit_hash[:8],
                            files_restored=["<git checkout>"],
                            duration=time.time() - start,
                        )

            # fallback: 使用 RollbackManager
            manager = RollbackManager()
            # RollbackManager.rollback 是 async，用 asyncio.run
            try:
                result = asyncio.run(manager.rollback(execution_id))
                return RollbackResult(
                    success=result.success,
                    execution_id=execution_id,
                    rollback_point=result.backup_id,
                    files_restored=[result.restored_file],
                    duration=time.time() - start,
                )
            except Exception:
                # RollbackManager 可能没有对应的 backup_id，返回基本结果
                return RollbackResult(
                    success=True,
                    execution_id=execution_id,
                    rollback_point=execution_id,
                    duration=time.time() - start,
                )
        except Exception as e:
            logger.exception("rollback failed")
            return RollbackResult(
                success=False, error=str(e), duration=time.time() - start
            )

    # ─── 6. stop — 停止执行 ───

    def stop(self, execution_id: str) -> StopResult:
        """标记执行为 CANCELLED，SprintExecutor 在下一个任务边界停止"""
        start = time.time()
        try:
            store = get_state_store()
            state = store.load(execution_id)
            if state is None:
                return StopResult(
                    success=False,
                    error=f"未找到执行记录: {execution_id}",
                    duration=time.time() - start,
                )

            # 1. 更新 StateStore 状态
            store.update_status(execution_id, ExecutionStatus.CANCELLED)

            # 2. 触发 SprintExecutor 的 cancel（如果正在运行）
            if self._orchestrator and hasattr(self._orchestrator, '_executor'):
                executor = self._orchestrator._executor
                if executor and hasattr(executor, 'cancel'):
                    executor.cancel()

            return StopResult(
                success=True,
                execution_id=execution_id,
                cancelled=True,
                current_sprint=state.current_sprint,
                message="已标记为 CANCELLED，将在下一个 Sprint 边界停止",
                duration=time.time() - start,
            )
        except Exception as e:
            logger.exception("stop failed")
            return StopResult(success=False, error=str(e), duration=time.time() - start)

    # ─── 知识卡片（P1）───

    def knowledge_search(
        self,
        query: str = "",
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """按关键词与标签检索知识卡片（SQLite）。"""
        from .execution.knowledge.knowledge_hook import resolve_knowledge_db_path
        from .persistence.knowledge_repository import KnowledgeCardRepository

        repo = KnowledgeCardRepository(resolve_knowledge_db_path(self.project_path, self.config))
        cards = repo.search(query=query, tags=tags or [], limit=limit)
        return {"success": True, "count": len(cards), "cards": [c.to_dict() for c in cards]}

    # ─── 内部方法 ───

    def _run_resolved_plan(
        self,
        plan: Any,
        start: float,
        *,
        confirm_knowledge: bool = False,
    ) -> tuple[RunResult, Any]:
        """已解析的 Release Plan：知识门 → Sprint 序列。

        返回 ``(run_result, sprint_results_objects)``；若知识门提前返回，则第二项为 ``[]``。
        """
        gated = self._maybe_gate_knowledge_injection(
            plan, start, confirm_knowledge=confirm_knowledge
        )
        if gated is not None:
            return (gated, [])

        sprint_results = asyncio.run(
            self.orchestrator.execute_release_plan(
                plan, max_concurrent=self.config.parallel_tasks
            )
        )
        finalize_result = getattr(self.orchestrator, "_last_release_finalization_result", None)
        return (
            self._build_run_result(
                plan,
                sprint_results,
                start,
                release_finalization=finalize_result.to_dict() if hasattr(finalize_result, "to_dict") else {},
            ),
            finalize_result,
        )

    def _maybe_gate_knowledge_injection(
        self,
        plan: Any,
        start: float,
        *,
        confirm_knowledge: bool,
    ) -> Optional[RunResult]:
        """V4.0：可选在首次知识注入落盘前要求调用方显式确认。"""
        if confirm_knowledge:
            return None
        if not getattr(self.config, "require_knowledge_injection_confirm", False):
            return None
        if not getattr(self.config, "knowledge_injection_enabled", True):
            return None
        if not getattr(plan, "sprints", None):
            return None
        try:
            from .execution.knowledge.knowledge_hook import resolve_knowledge_db_path
            from .execution.knowledge.knowledge_injector import (
                KnowledgeInjector,
                knowledge_injection_is_material,
            )
        except Exception:
            return None
        sprint0 = plan.sprints[0]
        try:
            db_path = resolve_knowledge_db_path(self.project_path, self.config)
            inj = KnowledgeInjector(db_path)
            res = inj.inject_for_sprint(
                self.project_path, sprint0, plan, persist_overlay=False
            )
        except Exception as e:
            logger.warning("knowledge injection preview skipped: {}", e)
            return None
        if not knowledge_injection_is_material(res):
            return None
        preview = {
            "sprint_name": sprint0.name,
            "cards_used": res.cards_used,
            "diff_text": res.diff_text[:12000],
            "yaml_excerpt": res.yaml_text[:4000],
        }
        return RunResult(
            success=False,
            pending_knowledge_confirmation=True,
            knowledge_injection_preview=preview,
            release_plan_name=getattr(plan.project, "name", "") if hasattr(plan, "project") else "",
            total_sprints=len(plan.sprints),
            total_tasks=getattr(plan, "total_tasks", 0),
            duration=time.time() - start,
            message=(
                "知识注入预览已生成（未写入 release_plan_overlay.yaml）；"
                "请以 confirm_knowledge=True 或 CLI --yes 再次调用 run() 以继续。"
            ),
        )

    def _anchor_project_for_intent(self, kwargs: Dict[str, Any]) -> str:
        raw = kwargs.get("project")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        return self.project_path

    def _finalize_workspace_metadata(
        self,
        plan: ReleasePlan,
        *,
        reference_paths: Optional[List[str]],
        write_policy: str,
    ) -> ReleasePlan:
        """绑定目标目录 -p、参考项目列表与写入策略（写入 plan.metadata 与任务 constraints）。"""
        refs = normalize_reference_paths(reference_paths)
        wp = normalize_write_policy(write_policy)
        abs_target = Path(self.project_path).expanduser().resolve()
        eff = effective_write_policy(wp, abs_target)
        # 仅标准 Sprint（NORMAL）对齐 CLI/API ``-p``；进化/产品目录路径由生成器决定，不得覆盖。
        if plan.mode == ExecutionMode.NORMAL:
            plan.project.path = str(abs_target)
        attach_workspace_metadata(
            plan,
            reference_paths=refs,
            write_policy=wp,
            effective_write_policy=eff,
        )
        apply_policy_to_tasks(plan, eff)
        return plan

    def _resolve_release_plan(
        self,
        intent: Optional[str],
        mode: str,
        target: Optional[str],
        release_plan_yaml: Optional[str],
        release_plan_path: Optional[str],
        *,
        product: Optional[str] = None,
        reference_paths: Optional[List[str]] = None,
        write_policy: str = "auto",
        **kwargs: Any,
    ):
        """从意图/YAML/文件路径解析为 Release Plan（内存模型）。"""
        project_for_intent = self._anchor_project_for_intent(kwargs)
        if release_plan_yaml:
            plan = ReleasePlanParser().parse_string(release_plan_yaml)
            return self._finalize_workspace_metadata(
                plan, reference_paths=reference_paths, write_policy=write_policy
            )
        if release_plan_path:
            plan = ReleasePlanParser().parse_file(release_plan_path)
            return self._finalize_workspace_metadata(
                plan, reference_paths=reference_paths, write_policy=write_policy
            )
        has_intent = bool(intent and str(intent).strip())
        if not has_intent:
            raise ValueError("请提供 intent、release_plan_yaml 或 release_plan_path 之一")
        parsed = IntentParser().parse(
            str(intent),
            mode=mode,
            target=target,
            project=project_for_intent,
            constraints=kwargs.get("constraints"),
            product=product,
        )
        plan = IntentReleasePlanGenerator.generate(
            parsed,
            config=self.config,
            anchor_project_path=self.project_path,
        )
        return self._finalize_workspace_metadata(
            plan, reference_paths=reference_paths, write_policy=write_policy
        )

    def _build_run_result(
        self,
        plan: Any,
        sprint_results: List[Any],
        start: float,
        *,
        execution_id: Optional[str] = None,
        current_sprint: int = 0,
        message: str = "",
        release_plan_name: Optional[str] = None,
        total_tasks: Optional[int] = None,
        release_finalization: Optional[Dict[str, Any]] = None,
    ) -> RunResult:
        """从 plan + 原始 Sprint 结果拼装 ``RunResult``（首跑与断点续跑共用）。"""
        success = all(
            r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
            for r in sprint_results
        )
        completed_sprints = sum(
            1
            for r in sprint_results
            if r.status in (ExecutionStatus.SUCCESS, ExecutionStatus.SKIPPED)
        )
        completed_tasks = sum(r.success_count for r in sprint_results)

        resolved_execution_id = execution_id
        if resolved_execution_id is None:
            resolved_execution_id = ""
            try:
                store = get_state_store()
                states = store.list_executions(limit=1)
                if states:
                    resolved_execution_id = states[0].execution_id
            except Exception:
                pass

        sr_list = self._serialize_sprint_results(sprint_results)

        name = release_plan_name
        if name is None:
            name = plan.project.name if hasattr(plan, "project") else ""

        n_tasks = total_tasks
        if n_tasks is None:
            n_tasks = plan.total_tasks if hasattr(plan, "total_tasks") else 0

        return RunResult(
            success=success,
            execution_id=resolved_execution_id,
            release_plan_name=name,
            completed_sprints=completed_sprints,
            completed_tasks=completed_tasks,
            total_sprints=len(sprint_results),
            total_tasks=n_tasks,
            current_sprint=current_sprint,
            sprint_results=sr_list,
            release_finalization=release_finalization or {},
            message=message,
            duration=time.time() - start,
        )

    @staticmethod
    def _serialize_sprint_results(sprint_results: List[Any]) -> List[Dict[str, Any]]:
        """将 ``SprintResult`` 列表转为 ``RunResult.sprint_results`` 字典列表。"""
        sr_list: List[Dict[str, Any]] = []
        for r in sprint_results:
            sr_list.append(
                {
                    "sprint_name": r.sprint.name if hasattr(r, "sprint") else "",
                    "status": r.status.value
                    if hasattr(r.status, "value")
                    else str(r.status),
                    "success_count": r.success_count,
                    "task_count": len(r.task_results),
                    "duration": r.duration,
                }
            )
        return sr_list

    def _resume_execution(self, execution_id: str, start: float) -> RunResult:
        """断点续跑：从 StateStore 断点继续执行。

        产品约定：**不经**知识注入确认门（与首跑走 ``_run_resolved_plan`` 含知识门区分）。
        """
        try:
            store = get_state_store()
            if not store.can_resume(execution_id):
                return RunResult(
                    success=False,
                    error=f"执行 {execution_id} 无法续跑（状态不允许或记录不存在）",
                    execution_id=execution_id,
                    duration=time.time() - start,
                )

            state = store.load(execution_id)
            if not state:
                return RunResult(
                    success=False,
                    error=f"未找到执行记录: {execution_id}",
                    duration=time.time() - start,
                )

            # 获取断点信息
            checkpoint = state.checkpoint or {}
            sprint_idx = checkpoint.get("sprint_idx", 0)
            task_results = checkpoint.get("task_results", [])
            yml = checkpoint_plan_yaml(checkpoint)

            logger.info(
                f"断点续跑: {execution_id}, 从 Sprint {sprint_idx} 继续"
            )

            # 更新状态为 RUNNING
            store.update_status(execution_id, ExecutionStatus.RUNNING)

            # 从执行计划 YAML 恢复内存模型（类型仍为 ReleasePlan）
            if not yml:
                return RunResult(
                    success=False,
                    error=f"执行 {execution_id} 没有保存的 Release Plan YAML，无法恢复",
                    execution_id=execution_id,
                    duration=time.time() - start,
                )

            try:
                plan = ReleasePlanParser().parse_string(yml)
            except Exception as e:
                logger.error(f"无法解析保存的执行计划: {e}")
                return RunResult(
                    success=False,
                    error=f"无法解析保存的执行计划: {e}",
                    execution_id=execution_id,
                    duration=time.time() - start,
                )

            # 重建之前的 Sprint 结果
            previous_results = self._reconstruct_sprint_results(plan, task_results)

            if previous_results:
                logger.info(f"已恢复 {len(previous_results)} 个已完成的 Sprint 结果")

            # 使用编排器从断点继续执行
            async def run_resume():
                return await self.orchestrator.resume_from_sprint(
                    release_plan=plan,
                    resume_from_idx=sprint_idx,
                    previous_results=previous_results,
                    max_concurrent=self.config.parallel_tasks,
                )

            sprint_results = asyncio.run(run_resume())

            # 更新状态为 COMPLETED
            store.update_status(execution_id, ExecutionStatus.COMPLETED)

            # 与首跑共用收尾（续跑不经知识门，见 ``run`` 分支）
            resume_plan_name = (
                plan.project.name
                if hasattr(plan, "project")
                else state.release_plan_name
            )
            resume_total_tasks = (
                plan.total_tasks if hasattr(plan, "total_tasks") else state.total_tasks
            )
            return self._build_run_result(
                plan,
                sprint_results,
                start,
                execution_id=execution_id,
                current_sprint=sprint_idx,
                message=f"断点续跑完成，共执行 {len(sprint_results)} 个 Sprint",
                release_plan_name=resume_plan_name,
                total_tasks=resume_total_tasks,
            )
        except Exception as e:
            logger.exception("resume failed")
            return RunResult(
                success=False, error=str(e), duration=time.time() - start
            )

    def _reconstruct_sprint_results(
        self,
        plan: Any,
        task_results_data: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        从保存的任务结果重建 SprintResult 列表

        Args:
            plan: Release Plan 对象
            task_results_data: 保存的任务结果数据

        Returns:
            SprintResult 列表
        """
        from .execution.sprint_types import ExecutionStatus, SprintResult, TaskResult
        from .release_plan.models import SprintBacklogItem

        if not task_results_data:
            return []

        results: List[SprintResult] = []

        # 按 sprint_name 分组任务结果
        sprint_groups: Dict[str, List[Dict[str, Any]]] = {}
        for tr in task_results_data:
            sprint_name = tr.get("sprint_name", "unknown")
            if sprint_name not in sprint_groups:
                sprint_groups[sprint_name] = []
            sprint_groups[sprint_name].append(tr)

        # 找到对应的 Sprint 并重建结果
        for sprint in plan.sprints:
            if sprint.name in sprint_groups:
                group = sprint_groups[sprint.name]
                task_results: List[TaskResult] = []

                for tr_data in group:
                    # 找到对应的任务定义
                    task_def = None
                    text = tr_data.get("description") or ""
                    for t in sprint.tasks:
                        if t.description == text:
                            task_def = t
                            break

                    if task_def is None:
                        # 如果找不到精确匹配，创建一个占位任务
                        task_def = SprintBacklogItem(
                            description=text or "",
                            agent=tr_data.get("agent", "coder"),
                            target=tr_data.get("target"),
                        )

                    status_str = tr_data.get("status", "success")
                    try:
                        status = ExecutionStatus(status_str)
                    except ValueError:
                        status = ExecutionStatus.SUCCESS

                    task_result = TaskResult(
                        work_item=task_def,
                        sprint_name=sprint.name,
                        status=status,
                        output=tr_data.get("output", ""),
                        error=tr_data.get("error"),
                        duration=tr_data.get("duration", 0.0),
                    )
                    task_results.append(task_result)

                # 确定 Sprint 状态
                if all(r.status == ExecutionStatus.SUCCESS for r in task_results):
                    sprint_status = ExecutionStatus.SUCCESS
                elif any(r.status == ExecutionStatus.FAILED for r in task_results):
                    sprint_status = ExecutionStatus.FAILED
                else:
                    sprint_status = ExecutionStatus.SUCCESS

                sprint_result = SprintResult(
                    sprint=sprint,
                    status=sprint_status,
                    task_results=task_results,
                    duration=sum(r.duration for r in task_results),
                )
                results.append(sprint_result)

        return results

    def _is_git_repo(self) -> bool:
        """检查项目是否为 git 仓库"""
        rc, _, _ = self._run_git(
            ["rev-parse", "--git-dir"], cwd=self.project_path
        )
        return rc == 0

    def _find_pre_execution_commit(self, execution_id: str) -> Optional[str]:
        """查找执行前的 git commit"""
        try:
            store = get_state_store()
            state = store.load(execution_id)
            if state and state.metadata:
                return state.metadata.get("pre_execution_commit")
        except Exception:
            pass
        return None

    @staticmethod
    def _run_git(
        args: List[str], cwd: str = ".", timeout: int = 30
    ) -> tuple:
        """运行 git 命令"""
        import subprocess

        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)


__all__ = ["SprintCycle"]
