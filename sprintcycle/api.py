"""
SprintCycle 统一 API

Dashboard / CLI / MCP / SDK 共用的唯一入口。
所有操作通过此类暴露，三端只做参数适配和展示格式化。

主操作: plan / run / run_release_plan / diagnose / status / rollback / stop

产品与技术叙述以仓库 ``docs/PRODUCT_TECH_V4.md`` 与 ``SPRINTCYCLE_PRODUCT_TECH_PLAN.md``
（V4.0 工程真理源）为准；``run``/resume **主路径**为 ``ReleasePlan`` → ``expand_release_plan_for_execution``
→ ``SprintOrchestrator`` → ``SprintExecutor``。

代码级边界约束
- ``api`` 是意图演化的观察与编排入口，不是演化规则的实现中心。
- ``api`` 可以记录初始意图、修正意图、返回演化阶段，但不应把演化逻辑散落到多个业务分支。
- ``api`` 负责把 evolution 上下文传给 ``release_plan`` / ``orchestration``，不负责直接修改执行器内部状态。
- 是否重规划、是否继续执行、是否回滚，由 ``api`` 汇总信号后作出明确决策，不允许由底层模块偷偷触发主链路切换。
- ``api`` 不应依赖 ``evolution`` 的内部存储实现，只依赖显式接口，保证演化能力可替换、可测试、可隔离。
- 对外只输出统一演化摘要 ``EvolutionSummary``，不要在 ``PlanResult`` / ``RunResult`` 上散落额外演化字段。
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
from .execution.state import summarize_state_machine
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
    EvolutionIndexResult,
    EvolutionOverviewResult,
    EvolutionSummary,
    EvolutionVersionListResult,
    EvolutionVersionSummary,
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
from .evolution import MemoryStore, UserIntentEvolutionLoop
from .governance.facade import GovernanceFacade, create_governance_facade
from .persistence.knowledge_repository import KnowledgeCardRepository
from .versioning.interface import get_version_manifest_summary
from .versioning.sqlite_registry import SQLiteVersionRegistry


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
        self._governance: Optional[GovernanceFacade] = None
        self._evolution_registry = SQLiteVersionRegistry(
            root_dir=str(getattr(getattr(self.config, "evolution_versioning", None), "root_dir", None) or ".sprintcycle/versioning")
        )
        self._memory_store = MemoryStore(runtime_config=self.config)
        self._knowledge_repo = KnowledgeCardRepository(self._resolve_knowledge_db_path())
        self._intent_evolution_loop = UserIntentEvolutionLoop(
            memory_store=self._memory_store,
            feedback_loop=None,
            knowledge_repo=self._knowledge_repo,
        )

    @property
    def intent_evolution_loop(self) -> UserIntentEvolutionLoop:
        return self._intent_evolution_loop

    async def get_evolution_version(self, version_id: str) -> EvolutionVersionSummary:
        """查询单个演化版本摘要。"""
        payload = await get_version_manifest_summary(self._evolution_registry, version_id)
        return EvolutionVersionSummary(
            success=bool(payload.get("success")),
            error=payload.get("error"),
            version_id=payload.get("version_id", ""),
            target=payload.get("target", ""),
            commit_hash=payload.get("commit_hash", ""),
            tag=payload.get("tag", ""),
            branch=payload.get("branch", ""),
            manifest_path=payload.get("manifest_path", ""),
            sandbox_id=payload.get("sandbox_id", ""),
            metadata=dict(payload.get("metadata", {}) or {}),
        )

    async def list_evolution_versions(self, target: Optional[str] = None, limit: int = 20) -> EvolutionVersionListResult:
        """列出演化版本历史。"""
        versions = await self._evolution_registry.list_versions(target=target, limit=limit)
        return EvolutionVersionListResult(
            success=True,
            target=target or "",
            versions=[
                EvolutionVersionSummary(
                    success=True,
                    version_id=v.version_id,
                    target=v.target,
                    commit_hash=v.commit_hash or "",
                    tag=v.tag or "",
                    branch=v.branch or "",
                    manifest_path=v.manifest_path or "",
                    sandbox_id=v.sandbox_id or "",
                    metadata=dict(v.metadata or {}),
                )
                for v in versions
            ],
            total=len(versions),
        )

    async def export_evolution_index(self) -> EvolutionIndexResult:
        """导出演化版本索引。"""
        index = await self._evolution_registry.export_manifest_index()
        return EvolutionIndexResult(success=True, index=index)

    async def evolution_overview(self) -> EvolutionOverviewResult:
        """演化总览：active、recent candidate、索引与沙盒状态。"""
        active_versions: Dict[str, Dict[str, Any]] = {}
        for target in ("code", "requirement"):
            active = await self._evolution_registry.get_active(target)
            if active is not None:
                active_versions[target] = active.to_dict()

        recent = await self._evolution_registry.list_versions(limit=5)
        index = await self._evolution_registry.export_manifest_index()
        totals = {
            "versions": len(recent),
            "code_active": 1 if "code" in active_versions else 0,
            "requirement_active": 1 if "requirement" in active_versions else 0,
        }
        sandbox_status: Dict[str, Any] = {}
        try:
            sandbox_status = {
                "available": True,
                "backend": getattr(getattr(self.config, "evolution_sandbox", None), "backend", "worktree"),
                "root_dir": getattr(getattr(self.config, "evolution_sandbox", None), "root_dir", ".sprintcycle/evolution"),
            }
        except Exception:
            sandbox_status = {"available": False}
        return EvolutionOverviewResult(
            success=True,
            active_versions=active_versions,
            recent_candidates=[
                EvolutionVersionSummary(
                    success=True,
                    version_id=v.version_id,
                    target=v.target,
                    commit_hash=v.commit_hash or "",
                    tag=v.tag or "",
                    branch=v.branch or "",
                    manifest_path=v.manifest_path or "",
                    sandbox_id=v.sandbox_id or "",
                    metadata=dict(v.metadata or {}),
                )
                for v in recent
            ],
            index=index,
            totals=totals,
            sandbox_status=sandbox_status,
        )

    def evolution_overview_cli(self) -> str:
        """CLI 友好的演化总览文本。"""
        return asyncio.run(self.evolution_overview()).to_cli_text()

    def evolution_overview_dashboard(self) -> Dict[str, Any]:
        """Dashboard 首屏友好的演化总览 payload。"""
        return asyncio.run(self.evolution_overview()).to_dashboard_payload()

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        """治理检查薄入口：仅做编排，不承载规则实现。"""
        from .governance.arch_guard.config import ArchGuardConfig
        from .governance.arch_guard.engine import ArchGuardEngine
        from .governance.arch_guard.reporter import GovernanceReportAdapter

        start = time.time()
        try:
            cfg = ArchGuardConfig.from_runtime_config(self.config, self.project_path)
            engine = ArchGuardEngine(cfg)
            context: Dict[str, Any] = dict(kwargs.get("context") or {})
            if gate == "planning":
                release_plan = kwargs.get("release_plan")
                if release_plan is None:
                    return {"success": False, "error": "planning gate requires release_plan"}
                report = asyncio.run(
                    engine.run_planning_gate(self.project_path, release_plan=release_plan, context=context)
                )
            else:
                report = asyncio.run(engine.run_review_gate(self.project_path, context=context))
            gov = GovernanceReportAdapter.to_governance_report(report)
            return {
                "success": True,
                "gate": gate,
                "data": gov.to_dict(),
                "duration": time.time() - start,
            }
        except Exception as e:
            logger.exception("governance_check failed")
            return {"success": False, "error": str(e), "duration": time.time() - start}

    def _resolve_knowledge_db_path(self) -> str:
        from .execution.knowledge.knowledge_hook import resolve_knowledge_db_path

        return resolve_knowledge_db_path(self.project_path, self.config)

    def _get_governance(self) -> Optional[GovernanceFacade]:
        if self._governance is None:
            self._governance = create_governance_facade(self.project_path, self.config)
        return self._governance

    @property
    def orchestrator(self) -> SprintOrchestrator:
        if self._orchestrator is None:
            self._orchestrator = SprintOrchestrator(
                config=self.config,
                event_bus=get_execution_event_backend(),
                project_path=self.project_path,
                hitl_coordinator=None,
                evolution_loop=self._intent_evolution_loop,
            )
        return self._orchestrator

    async def observability_pending(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        gov = self._get_governance()
        if gov is None:
            return {"success": True, "data": []}
        return {"success": True, "data": await gov.list_pending(execution_id)}


    async def observability_submit(
        self, request_id: str, decision: str, note: Optional[str] = None, correction: Optional[Dict[str, Any]] = None, replay: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        gov = self._get_governance()
        if not gov:
            return {"success": False, "error": "Governance is disabled"}
        rec = await gov.submit_decision(request_id, decision, note, correction=correction, replay=replay)
        if rec is None:
            return {"success": False, "error": "Request not found or already resolved"}
        return {"success": True, "data": rec}

    async def observability_history(
        self, execution_id: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        gov = self._get_governance()
        if gov is None:
            return {"success": True, "data": []}
        return {"success": True, "data": await gov.list_history(execution_id, limit)}

    async def observability_summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        gov = self._get_governance()
        if gov is None:
            return {"success": True, "data": {"has_service": False, "pending_count": 0, "history_count": 0}}
        return {"success": True, "data": await gov.summary(execution_id, limit)}

    async def observability_show(self, request_id: str) -> Dict[str, Any]:
        """按 ID 返回单条观测/治理记录。"""
        gov = self._get_governance()
        if gov is None:
            return {"success": False, "error": "Governance is disabled"}
        rid = (request_id or "").strip()
        if not rid:
            return {"success": False, "error": "request_id required"}
        rec = await gov.get_request(rid)
        if rec is None:
            return {"success": False, "error": "Request not found"}
        return {"success": True, "data": rec}

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

    def replay_execution(self, execution_id: str, *, limit: int = 500) -> Dict[str, Any]:
        """基于事件与状态快照生成可回放视图。"""
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        store = get_state_store()
        state = store.load(eid)
        if state is None:
            return {"success": False, "error": f"未找到执行记录: {eid}"}
        timeline = self.execution_events(eid, limit=limit)
        events = timeline.get("data", []) if isinstance(timeline, dict) else []
        summary = {
            "execution_id": eid,
            "status": state.status.value,
            "current_sprint": state.current_sprint,
            "total_sprints": state.total_sprints,
            "completed_tasks": state.completed_tasks,
            "total_tasks": state.total_tasks,
            "last_stable_state": state.last_stable_state,
            "event_cursor": state.event_cursor,
            "replay_version": state.replay_version,
            "event_count": len(events),
            "latest_event": events[-1] if events else None,
        }
        return {"success": True, "data": summary, "timeline": events}

    def execution_detail(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        """执行详情：状态、恢复点、回放、状态机摘要一次性返回。"""
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        store = get_state_store()
        state = store.load(eid)
        if state is None:
            return {"success": False, "error": f"未找到执行记录: {eid}"}
        checkpoint = state.checkpoint or {}
        resume_point = store.get_resume_point(eid) or {}
        replay = self.replay_execution(eid, limit=limit)
        detail = {
            "state": state.to_dict(),
            "checkpoint": checkpoint,
            "resume_point": resume_point,
            "replay": replay.get("data", {}),
            "timeline": replay.get("timeline", []),
            "state_machine": summarize_state_machine(),
            "can_resume": store.can_resume(eid),
            "last_stable_state": state.last_stable_state,
            "event_cursor": state.event_cursor,
        }
        return {"success": True, "data": detail}

    def resume_execution(self, execution_id: str) -> Dict[str, Any]:
        """控制台恢复入口：按记录的断点继续执行。"""
        eid = (execution_id or "").strip()
        if not eid:
            return {"success": False, "error": "execution_id required"}
        store = get_state_store()
        state = store.load(eid)
        if state is None:
            return {"success": False, "error": f"未找到执行记录: {eid}"}
        if not store.can_resume(eid):
            return {"success": False, "error": f"执行 {eid} 当前不可恢复"}
        checkpoint = state.checkpoint or {}
        yml = checkpoint.get("release_plan_yaml") or checkpoint.get("release_plan")
        if not yml:
            return {"success": False, "error": "缺少 release plan checkpoint，无法恢复"}
        try:
            plan = ReleasePlanParser().parse_string(str(yml))
        except Exception as e:
            return {"success": False, "error": f"无法解析 checkpoint: {e}"}
        results = asyncio.run(
            self.orchestrator.resume_from_sprint(
                plan,
                int(checkpoint.get("sprint_idx", 0) or 0),
                [],
                max_concurrent=self.config.parallel_tasks,
            )
        )
        return {"success": True, "data": {"execution_id": eid, "results": [r.to_dict() for r in results]}}

    def console_overview(self, *, limit: int = 20) -> Dict[str, Any]:
        """控制台总览：当前执行、可恢复执行、最近事件与状态机摘要。"""
        store = get_state_store()
        states = store.list_executions(limit=max(1, int(limit)))
        executions = [s.to_dict() for s in states]
        recoverable = [s.to_dict() for s in states if store.can_resume(s.execution_id)]
        running = [s.to_dict() for s in states if str(s.status.value) == "running"]
        latest = executions[0] if executions else None
        recent_events: List[Dict[str, Any]] = []
        if latest and latest.get("execution_id"):
            try:
                recent_events = self.execution_events(str(latest["execution_id"]), limit=20).get("data", [])
            except Exception:
                recent_events = []
        return {
            "success": True,
            "data": {
                "executions": executions,
                "running_executions": running,
                "recoverable_executions": recoverable,
                "primary_execution": latest,
                "recent_events": recent_events,
                "state_machine": summarize_state_machine(),
            },
        }

    def reload_runtime_config(self) -> None:
        """从磁盘重新加载 ``RuntimeConfig``（含 ``sprintcycle.runtime.yaml``），并重绑缓存 / 状态 / 事件后端。"""
        base = RuntimeConfig.from_project(self.project_path)
        self.config = base.merge(base, {"project_path": self.project_path})
        configure_execution_cache_from_runtime(self.config, self.project_path)
        configure_default_store(self.project_path, self.config)
        ensure_default_execution_event_backend_for_project(self.project_path, self.config)
        self._orchestrator = None

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
            if intent:
                self._intent_evolution_loop.start(
                    str(intent),
                    mode=mode,
                    target=target,
                    phase="plan",
                    source="plan",
                )
            validation = ReleasePlanValidator().validate(plan)

            sprints = [
                {
                    "name": s.name,
                    "tasks": [t.description for t in s.tasks],
                }
                for s in plan.sprints
            ]

            evo_summary = dict(getattr(plan, "metadata", {}).get("evolution_summary", {}) or {})
            return PlanResult(
                success=validation.is_valid,
                release_plan_yaml=plan.to_yaml(),
                sprints=sprints,
                mode=plan.mode.value,
                release_plan_name=plan.project.name,
                duration=time.time() - start,
                evolution=EvolutionSummary(
                    stage=str(evo_summary.get("stage", "")),
                    signals=list(evo_summary.get("signals", []) or []),
                    context=dict(evo_summary.get("context", {}) or {}),
                ),
            )
        except Exception as e:
            logger.exception("plan failed")
            return PlanResult(success=False, error=str(e), duration=time.time() - start)
