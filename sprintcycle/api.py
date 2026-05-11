"""
SprintCycle public API.

This module exposes the main coordination layer for CLI, dashboard, MCP, and
SDK usage. It handles request normalization, thin delegation, result assembly,
and compatibility adapters where legacy behavior still exists.

The current runtime flow centers on `SprintCycle` coordinating execution,
governance, suggestion, observability, and platform summary services.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .config import RuntimeConfig
from .deployment.runtime_registry import RuntimeRegistry
from .execution.cache import configure_execution_cache_from_runtime
from .execution.events import (
    ensure_default_execution_event_backend_for_project,
    get_execution_event_backend,
)
from .execution.state import summarize_state_machine
from .execution.state.state_store import (
    configure_default_store,
    get_state_store,
)
from .execution_core import ExecutionContext, create_execution_engine
from .orchestration.sprint_orchestrator import SprintOrchestrator
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
from .hooks import HookRegistry
from .run_workspace import (
    apply_policy_to_tasks,
    attach_workspace_metadata,
    effective_write_policy,
    ensure_project_layout,
    normalize_reference_paths,
    normalize_write_policy,
)
from .evolution import MemoryStore, UserIntentEvolutionLoop
from .fitness import FitnessEvaluator
from .governance.facade import GovernanceFacade, create_governance_facade
from .governance.policy.gates import GateResult, pre_run_gate
from .governance.suggestion import SuggestionFacade, create_suggestion_facade
from .persistence.knowledge_repository import KnowledgeCardRepository
from .versioning.interface import get_version_manifest_summary
from .versioning.sqlite_registry import SQLiteVersionRegistry
from .observability.facade import ObservabilityFacade
from .services.execution_lifecycle_service import ExecutionLifecycleService
from .services.governance_orchestration_service import GovernanceOrchestrationService
from .services.observability_service import ObservabilityService
from .services.platform_summary_service import PlatformSummaryService
from .services.suggestion_application_service import SuggestionApplicationService
from .platform.overview import build_platform_overview
from .integrations.langgraph.runtime import LangGraphRuntimeAdapter, LangGraphRuntimeSpec
from .integrations.phoenix.runtime import PhoenixRuntimeAdapter, PhoenixRuntimeSpec
from .integrations.phoenix.exporter import PhoenixExporterSpec
from .integrations.langgraph.graph import build_default_langgraph_graph_spec
from .platform.views import PlatformComposeView, PlatformSpecView
from .dashboard.view_service import DashboardViewService
from .dashboard.workbench import DashboardWorkbenchService
from .dashboard.views.architecture_view import ArchitectureView
from .dashboard.views.deploy_view import DeployView
from .dashboard.views.fix_view import FixView
from .dashboard.views.fitness_view import FitnessView
from .dashboard.views.governance_view import GovernanceView


class SprintCycle:
    """SprintCycle 统一 API — Dashboard / CLI / MCP / SDK 共用。

    **执行主架构**：``ReleasePlan`` → ``SprintOrchestrator.execute_release_plan`` → ``SprintExecutor``。
    自进化与普通迭代在执行栈上汇合。
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
        self._suggestion: SuggestionFacade = create_suggestion_facade(
            project_path=self.project_path,
            config=self.config,
            evolution_facade=None,
        )
        self._memory_store = MemoryStore(runtime_config=self.config)
        self._knowledge_repo = KnowledgeCardRepository(self._resolve_knowledge_db_path())
        self._intent_evolution_loop = UserIntentEvolutionLoop(
            memory_store=self._memory_store,
            feedback_loop=None,
            knowledge_repo=self._knowledge_repo,
        )
        self._execution_engine = create_execution_engine()
        self._observability = ObservabilityFacade()
        self._runtime_registry = RuntimeRegistry()
        self._hooks = HookRegistry()
        self._execution_service = ExecutionLifecycleService(
            project_path=self.project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            hooks=self._hooks,
        )
        self._observability_service = ObservabilityService(observability=self._observability)
        self._dashboard_views = DashboardViewService(project_path=self.project_path)
        self._dashboard_workbench = DashboardWorkbenchService(view_service=self._dashboard_views)
        self._platform_summary = PlatformSummaryService(
            project_path=self.project_path,
            dashboard_views=self._dashboard_views,
            dashboard_workbench=self._dashboard_workbench,
        )
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=self.project_path,
            config=self.config,
            governance=self._get_governance(),
            hooks=self._hooks,
        )
        self._suggestion_application = SuggestionApplicationService(suggestion=self._suggestion, governance=self._get_governance())
        self._fitness = FitnessEvaluator()

    @property
    def intent_evolution_loop(self) -> UserIntentEvolutionLoop:
        return self._intent_evolution_loop

    @property
    def suggestion(self) -> SuggestionFacade:
        return self._suggestion

    @property
    def execution_engine(self):
        return self._execution_engine

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

    def _suggestion_overview(self) -> Any:
        return asyncio.run(self._suggestion.overview())

    def suggestion_overview(self) -> Dict[str, Any]:
        return self._suggestion_overview().to_dict()

    def suggestion_overview_cli(self) -> str:
        return self._suggestion_overview().to_cli_text()

    def suggestion_overview_dashboard(self) -> Dict[str, Any]:
        return self._suggestion_overview().to_dashboard_payload()

    async def suggestion_review(self, suggestion_id: str) -> Dict[str, Any]:
        context = await self._suggestion.review_suggestion(suggestion_id)
        return {"success": True, "data": context.to_dict()}

    async def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    async def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)

    async def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)

    async def promote_suggestion_to_hitl(
        self,
        suggestion_id: str,
        *,
        gate: str = "review",
        title: str = "",
        summary: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return await self._suggestion_application.promote_suggestion_to_hitl(
            suggestion_id,
            gate=gate,
            title=title,
            summary=summary,
            context=context,
        )

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        return await self._suggestion_application.attach_suggestion_replay(suggestion_id, replay)

    async def suggestion_approve(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_approve(suggestion_id, approver, notes)

    async def suggestion_reject(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_reject(suggestion_id, approver, notes)

    async def suggestion_archive(self, suggestion_id: str) -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_archive(suggestion_id)

    def _management_overview_payload(self) -> Dict[str, Any]:
        return {
            "evolution": self.evolution_overview_dashboard(),
            "suggestion": self.suggestion_overview_dashboard(),
            "project_path": self.project_path,
        }

    def management_overview(self) -> Dict[str, Any]:
        return {"success": True, "data": self._management_overview_payload()}

    def management_overview_cli(self) -> str:
        evo = self.evolution_overview_cli()
        sug = self.suggestion_overview_cli()
        return "\n".join(["Management Overview", "", "[Evolution]", evo, "", "[Suggestion]", sug])

    def management_overview_dashboard(self) -> Dict[str, Any]:
        return self._management_overview_payload()

    def platform_spec(self) -> Dict[str, Any]:
        """Return the aggregated V2 platform composition spec."""
        return {"success": True, "data": build_platform_spec(project_name=self.project_path).to_dict()}

    async def start_execution_run(self, task_id: str, **kwargs: Any) -> Dict[str, Any]:
        return await self._execution_service.start_execution_run(task_id, **kwargs)

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        return self._governance_orchestration.governance_check(gate=gate, **kwargs)

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
        return await self._governance_orchestration.pending(execution_id=execution_id)

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
        return await self._governance_orchestration.history(execution_id=execution_id, limit=limit)

    async def observability_summary(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        return await self._governance_orchestration.summary(execution_id=execution_id, limit=limit)

    async def observability_show(self, request_id: str) -> Dict[str, Any]:
        return await self._governance_orchestration.show(request_id)

    def record_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._observability_service.record_event(event)

    def list_recorded_execution_events(self) -> Dict[str, Any]:
        return self._observability_service.list_events()

    def observability_trace(self, run_id: str) -> Dict[str, Any]:
        return self._observability_service.trace(run_id)

    def observability_replay(self, run_id: str) -> Dict[str, Any]:
        return self._observability_service.replay(run_id)

    def record_observation_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._observability_service.record_event(event)

    async def create_suggestion_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return await self._suggestion_application.create_suggestion_from_execution_event(event)

    def register_runtime(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._runtime_registry.register(payload)

    def _fitness_payload(self) -> Dict[str, Any]:
        return self._platform_summary.fitness_payload(self._observability, self._runtime_registry, self._suggestion)

    def platform_overview(self) -> Dict[str, Any]:
        return self._platform_summary.platform_overview()

    def _execution_detail_payload(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_detail(execution_id, limit=limit)

    def fitness_view(self) -> Dict[str, Any]:
        payload = self._fitness.evaluate(self._fitness_payload())
        return self._platform_summary.fitness_view(payload)

    def deploy_view(self) -> Dict[str, Any]:
        payload = self._runtime_registry.list()
        return self._platform_summary.deploy_view(payload)

    def _suggestion_overview_payload(self) -> Dict[str, Any]:
        overview = asyncio.run(self._suggestion.overview())
        return self._dashboard_views.suggestion_overview_payload(overview)

    def _suggestion_list_payload(self, limit: int = 20) -> Dict[str, Any]:
        suggestions = asyncio.run(self._suggestion.list_suggestions(limit=limit))
        return self._dashboard_views.suggestion_list_payload(suggestions)

    def runtime_latest(self) -> Dict[str, Any]:
        return self._execution_service.runtime_latest()

    def runtime_update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        return self._execution_service.runtime_update(runtime_id, **changes)

    def governance_view(self) -> Dict[str, Any]:
        overview = self._suggestion_overview_payload()
        return self._platform_summary.governance_view(overview)

    def fix_view(self) -> Dict[str, Any]:
        return self._platform_summary.fix_view(self._suggestion_list_payload(limit=20))

    def architecture_check(self) -> Dict[str, Any]:
        from .governance.arch_guard.architecture_checker import check_architecture

        result = check_architecture(self.project_path)
        return ArchitectureView(payload=result.to_dict()).to_payload()

    def evaluate_fitness(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._fitness.evaluate(payload)

    def execution_events(
        self,
        execution_id: str,
        *,
        limit: int = 200,
    ) -> Dict[str, Any]:
        return self._execution_service.execution_events(execution_id, limit=limit)

    def replay_execution(self, execution_id: str, *, limit: int = 500) -> Dict[str, Any]:
        return self._execution_service.replay_execution(execution_id, limit=limit)

    def execution_detail(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_detail(execution_id, limit=limit)

    def _resume_execution_payload(self, execution_id: str) -> Dict[str, Any]:
        eid = (execution_id or "").strip()
        return {"success": False, "error": f"resume is removed in V2 for execution_id={eid}"}

    def resume_execution(self, execution_id: str) -> Dict[str, Any]:
        """兼容入口：V2 中已移除实际 resume 执行能力。"""
        return self._resume_execution_payload(execution_id)

    def console_overview(self, *, limit: int = 20) -> Dict[str, Any]:
        trace_payload = None
        store = get_state_store()
        states = store.list_executions(limit=max(1, int(limit)))
        executions = [s.to_dict() for s in states]
        latest = executions[0] if executions else None
        if latest and latest.get("execution_id"):
            trace_payload = self.observability_trace(str(latest["execution_id"])).get("data", {})
        return self._platform_summary.console_overview(trace_payload=trace_payload, limit=limit)

    def reload_runtime_config(self) -> None:
        """从磁盘重新加载 ``RuntimeConfig``（含 ``sprintcycle.runtime.yaml``）。"""
        base = RuntimeConfig.from_project(self.project_path)
        self.config = base.merge(base, {"project_path": self.project_path})
        configure_execution_cache_from_runtime(self.config, self.project_path)
        configure_default_store(self.project_path, self.config)
        ensure_default_execution_event_backend_for_project(self.project_path, self.config)
        self._orchestrator = None
        self._execution_engine = create_execution_engine()
        self._execution_service = ExecutionLifecycleService(
            project_path=self.project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
        )
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=self.project_path,
            config=self.config,
            governance=self._get_governance(),
        )

    # ─── 1. plan — 看计划，不干活 ───
