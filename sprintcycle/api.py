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
from .services.lifecycle_evolution_service import LifecycleEvolutionService
from .services.observability_service import ObservabilityService
from .services.phase_workflow import build_decompose_artifact, build_plan_artifact, build_prepare_artifact
from .services.platform_summary_service import PlatformSummaryService
from .services.promotion_policy import PromotionPolicy
from .services.repair_orchestration_service import RepairOrchestrationService
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
        self._repair_orchestration = RepairOrchestrationService(observability=self._observability)
        self._promotion_policy = PromotionPolicy()
        self._lifecycle_evolution = LifecycleEvolutionService(
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            promotion_policy=self._promotion_policy,
        )
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

    def promotion_readiness(self) -> Dict[str, Any]:
        overview = self._suggestion_overview().to_dashboard_payload()
        promotion = overview.get("promotion", {}) if isinstance(overview, dict) else {}
        ready = int(promotion.get("ready", 0)) if isinstance(promotion, dict) else 0
        blocked = int(promotion.get("blocked", 0)) if isinstance(promotion, dict) else 0
        total = ready + blocked
        return {
            "success": True,
            "data": {
                "ready": ready,
                "blocked": blocked,
                "total": total,
                "ready_rate": round((ready / total) * 100, 2) if total else 0.0,
                "reasons": dict(promotion.get("reasons", {}) if isinstance(promotion, dict) else {}),
            },
        }

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

    def plan_task(self, execution_id: str, task_id: str, *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        contract = build_lifecycle_contract(
            execution_id=execution_id,
            task_id=task_id,
            project_path=project_path or self.project_path,
            stage="normalized",
            status="pending",
            metadata={"source": "web", "phase": "plan"},
            input_refs={"execution_id": execution_id, "task_id": task_id, "objective": objective},
        )
        return build_plan_artifact(contract, objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies)

    def prepare_task(self, contract_payload: Dict[str, Any], *, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None) -> Dict[str, Any]:
        return build_prepare_artifact(contract_payload, checks=checks, blockers=blockers)

    def decompose_task(self, contract_payload: Dict[str, Any], *, subtasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return build_decompose_artifact(contract_payload, subtasks=subtasks)

    def run_phase_workflow(self, execution_id: str, task_id: str, *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None, subtasks: Optional[List[Dict[str, Any]]] = None, project_path: Optional[str] = None) -> Dict[str, Any]:
        plan_result = self.plan_task(execution_id, task_id, objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies, project_path=project_path)
        prepared_result = self.prepare_task(plan_result.get("lifecycle_contract", {}), checks=checks, blockers=blockers)
        decomposed_result = self.decompose_task(prepared_result.get("lifecycle_contract", {}), subtasks=subtasks)
        return {
            "success": True,
            "data": {
                "plan": plan_result.get("plan", {}),
                "prepare": prepared_result.get("prepare", {}),
                "decompose": decomposed_result.get("decompose", {}),
                "lifecycle_contract": decomposed_result.get("lifecycle_contract", {}),
            },
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

    def plan_task(self, execution_contract: Dict[str, Any], *, objective: str = "", success_criteria: Optional[List[str]] = None, risks: Optional[List[str]] = None, dependencies: Optional[List[str]] = None, version: str = "v1") -> Dict[str, Any]:
        contract = build_lifecycle_contract(
            execution_id=str(execution_contract.get("execution_id") or execution_contract.get("task_id") or ""),
            task_id=str(execution_contract.get("task_id") or execution_contract.get("execution_id") or ""),
            project_path=str(execution_contract.get("project_path") or self.project_path),
            stage=str(execution_contract.get("stage") or "normalized"),
            status=str(execution_contract.get("status") or "pending"),
            metadata=dict(execution_contract.get("metadata") or {}),
            input_refs=dict(execution_contract.get("input_refs") or {}),
            output_refs=dict(execution_contract.get("output_refs") or {}),
            validation_refs=dict(execution_contract.get("validation_refs") or {}),
            trace=dict(execution_contract.get("trace") or {}),
            diagnostics=dict(execution_contract.get("diagnostics") or {}),
        )
        return build_plan_artifact(contract, objective=objective, success_criteria=success_criteria, risks=risks, dependencies=dependencies, version=version)

    def prepare_task(self, contract_payload: Dict[str, Any], *, checks: Optional[Dict[str, Any]] = None, blockers: Optional[List[str]] = None) -> Dict[str, Any]:
        return build_prepare_artifact(contract_payload, checks=checks, blockers=blockers)

    def decompose_task(self, contract_payload: Dict[str, Any], *, subtasks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        return build_decompose_artifact(contract_payload, subtasks=subtasks)

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
        return {"success": True, "data": {"record": rec, "lifecycle": {"stage": "governing", "status": "success", "decision": decision, "request_id": request_id}}}

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

    def repair_execution(self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._repair_orchestration.repair_and_verify(execution_id, repair_plan=repair_plan)

    def diagnose_execution(self, execution_id: str) -> Dict[str, Any]:
        return self._repair_orchestration.diagnose(execution_id)

    def evaluate_promotion(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        contract = self._lifecycle_evolution.build_contract(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)
        runtime = self.runtime_lifecycle(execution_id).get("data", {}).get("runtime", {})
        return self._lifecycle_evolution.evaluate_promotion(contract, runtime=runtime, governance=governance)

    def promote_versioned_evolution(self, execution_id: str, *, project_path: str = "", suggestion: Optional[Dict[str, Any]] = None, governance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._lifecycle_evolution.promote(execution_id, project_path=project_path, suggestion=suggestion, governance=governance)

    async def suggestion_lifecycle_from_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        result = await self._suggestion_application.create_suggestion_from_execution_event(event)
        data = result.get("data", {}) if isinstance(result, dict) else {}
        contract = data.get("lifecycle_contract", {}) if isinstance(data, dict) else {}
        suggestion_payload = data.get("suggestion", {}) if isinstance(data, dict) else {}
        evolution_refs = {
            "candidate": bool(suggestion_payload),
            "evolution_ready": bool(suggestion_payload),
            "source_execution_id": contract.get("execution_id", "") if isinstance(contract, dict) else "",
            "root_cause": contract.get("metadata", {}).get("root_cause", "") if isinstance(contract, dict) else "",
        }
        closure_score = 100.0 if suggestion_payload else 0.0
        return {"success": bool(result.get("success", False)) if isinstance(result, dict) else False, "data": {"suggestion": suggestion_payload, "lifecycle_contract": contract, "evolution_refs": evolution_refs, "lifecycle": {"stage": contract.get("stage", "suggesting") if isinstance(contract, dict) else "suggesting", "status": contract.get("status", "success") if isinstance(contract, dict) else "success", "closure_score": closure_score}, "health": {"closure_score": closure_score, "is_healthy": bool(suggestion_payload)}}}

    def register_runtime(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._runtime_registry.register(payload)

    def _fitness_payload(self) -> Dict[str, Any]:
        return self._platform_summary.fitness_payload(self._observability, self._runtime_registry, self._suggestion)

    def platform_overview(self) -> Dict[str, Any]:
        overview = self._platform_summary.platform_overview()
        data = overview.get("data", {}) if isinstance(overview, dict) else {}
        summary = data.get("summary", {}) if isinstance(data, dict) else {}
        data["closure_score"] = float(summary.get("closure_score", 100.0)) if isinstance(summary, dict) else 100.0
        repair = self.diagnose_execution(self.project_path if False else "") if False else {}
        promotion = self.evaluate_promotion(self.project_path if False else "", project_path=self.project_path, governance={}) if False else {}
        data["lifecycle"] = {
            "stage": "normalized",
            "status": "success" if overview.get("success", False) else "failed",
            "closure_score": data["closure_score"],
            "repair": {"enabled": True},
            "promotion": {"enabled": True},
        }
        data["recovery"] = {"repair_closed_loop": True, "promotion_gate": True}
        overview["data"] = data
        return overview

    def _execution_detail_payload(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_detail(execution_id, limit=limit)

    def lifecycle_contract(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        detail = self._execution_detail_payload(execution_id, limit=limit)
        data = detail.get("data", {}) if isinstance(detail, dict) else {}
        state = data.get("state", {}) if isinstance(data, dict) else {}
        trace = data.get("trace", {}) if isinstance(data, dict) else {}
        trace_payload = trace.get("data", trace) if isinstance(trace, dict) else {}
        lifecycle = trace_payload.get("lifecycle", {}) if isinstance(trace_payload, dict) else {}
        diagnostics = trace_payload.get("diagnostics", {}) if isinstance(trace_payload, dict) else {}
        runtime = self.runtime_lifecycle(str(state.get("execution_id") or execution_id))
        suggestions = self._suggestion_overview_payload()
        governance = asyncio.run(self._governance_orchestration.summary(execution_id=execution_id, limit=limit))
        suggestion_data = suggestions.get("data", {}) if isinstance(suggestions, dict) else {}
        runtime_snapshot = self._runtime_registry.latest().get("data", {}) if hasattr(self._runtime_registry, "latest") else {}
        promotion_overview = {
            "ready": int(suggestion_data.get("promotion_ready", 0) or 0),
            "blocked": int(suggestion_data.get("promotion_blocked", 0) or 0),
            "reasons": dict(suggestion_data.get("promotion_reasons", {}) or {}),
        }
        repair = trace_payload.get("repair", {}) if isinstance(trace_payload, dict) else {}
        health = {
            "is_healthy": bool(lifecycle.get("is_healthy", True)) if isinstance(lifecycle, dict) else True,
            "event_count": diagnostics.get("event_count", 0) if isinstance(diagnostics, dict) else 0,
            "failure_count": diagnostics.get("failure_count", 0) if isinstance(diagnostics, dict) else 0,
            "repair_ready": bool(diagnostics.get("repair_ready", False)) if isinstance(diagnostics, dict) else False,
        }
        stage = str(lifecycle.get("stage") or state.get("metadata", {}).get("stage") or "observing") if isinstance(lifecycle, dict) else "observing"
        status = str(lifecycle.get("status") or state.get("status") or "unknown") if isinstance(lifecycle, dict) else "unknown"
        closure_score = float(health["event_count"] > 0 and 100.0 or 0.0)
        runtime_contract = runtime.get("data", {}) if isinstance(runtime, dict) else {}
        runtime_contract = {**runtime_contract, "verified": bool(runtime_contract.get("verified", False)), "healthy": bool(runtime_contract.get("healthy", False)), "ready": bool(runtime_contract.get("ready", False)), "deploy_ready": bool(runtime_contract.get("deploy_ready", False))}
        governance_contract = governance.get("data", {}) if isinstance(governance, dict) else {}
        suggestion_contract = suggestion_data
        completion_score = 0.0
        completion_score += 20.0 if state else 0.0
        completion_score += 20.0 if health["event_count"] > 0 else 0.0
        completion_score += 20.0 if runtime_contract else 0.0
        completion_score += 15.0 if governance_contract else 0.0
        completion_score += 15.0 if suggestion_contract else 0.0
        completion_score += 10.0 if promotion.get("ready", 0) else 0.0
        completion_score += 10.0 if repair.get("ready", False) else 0.0
        repair = {
            "ready": bool(diagnostics.get("repair_ready", False)) if isinstance(diagnostics, dict) else False,
            "candidate_count": int(diagnostics.get("repair_candidate_count", 0)) if isinstance(diagnostics, dict) else 0,
            "root_causes": list(diagnostics.get("root_cause_tags", []) or []) if isinstance(diagnostics, dict) else [],
        }
        runtime_contract = {**runtime_contract, "healthy": bool(runtime_contract.get("healthy", False)), "verified": bool(runtime_contract.get("verified", False))}
        promotion_eval = self._lifecycle_evolution.evaluate_promotion({
                "execution_id": execution_id,
                "trace": trace_payload,
                "diagnostics": diagnostics,
                "runtime": runtime_contract,
                "governance": governance_contract,
                "suggestion": suggestion_contract,
                "repair": repair,
                "health": health,
                "completion_score": completion_score,
            }, runtime=runtime_contract, governance=governance_contract).get("data", {})
        contract = {
            "execution_id": execution_id,
            "state": state,
            "trace": trace_payload,
            "lifecycle": {**dict(lifecycle) if isinstance(lifecycle, dict) else {}, "stage": stage, "status": status, "closure_score": closure_score},
            "diagnostics": diagnostics,
            "runtime": runtime_contract,
            "governance": governance_contract,
            "suggestion": suggestion_contract,
            "promotion": promotion_eval.get("promotion", {}),
            "promotion_contract": promotion_eval,
            "promotion_overview": promotion_overview,
            "health": {**health, "closure_score": closure_score, "completion_score": completion_score},
            "repair": repair,
            "completion_score": completion_score,
        }
        return {"success": bool(detail.get("success", False)) if isinstance(detail, dict) else False, "data": contract}

    def fitness_view(self) -> Dict[str, Any]:
        payload = self._fitness.evaluate(self._fitness_payload())
        view = self._platform_summary.fitness_view(payload)
        data = view.get("data", {}) if isinstance(view, dict) else {}
        data["closure_score"] = payload.get("lifecycle_health", {}).get("observability_ready", False) and 100.0 or 0.0
        view["data"] = data
        return view

    def deploy_view(self) -> Dict[str, Any]:
        payload = self._runtime_registry.list()
        return self._platform_summary.deploy_view(payload)

    def deploy_lifecycle(self) -> Dict[str, Any]:
        deployment = self.deploy_view()
        runtime = self.runtime_lifecycle()
        success = bool(deployment.get("success", False)) and bool(runtime.get("success", False))
        closure_score = 100.0 if success else 0.0
        return {"success": success, "data": {"deployment": deployment.get("data", {}), "runtime": runtime.get("data", {}), "lifecycle": {"stage": "runtime_linked", "status": "success" if success else "failed", "has_deployment": bool(deployment.get("success", False)), "has_runtime": bool(runtime.get("success", False)), "closure_score": closure_score}, "health": {"closure_score": closure_score, "is_healthy": success}}}

    def runtime_lifecycle(self, runtime_id: str = "") -> Dict[str, Any]:
        latest = self.runtime_latest()
        data = latest.get("data", {}) if isinstance(latest, dict) else {}
        if runtime_id:
            payload = self._runtime_registry.get(runtime_id)
            data = payload if isinstance(payload, dict) else {"runtime_id": runtime_id, "success": bool(payload)}
        has_runtime = bool(data)
        closure_score = 100.0 if has_runtime else 0.0
        lifecycle = {
            "stage": "runtime_linked" if data else "delivering",
            "status": str(data.get("status") or "unknown") if isinstance(data, dict) else "unknown",
            "runtime_id": runtime_id or data.get("runtime_id") or data.get("id") or "",
            "has_runtime": has_runtime,
            "closure_score": closure_score,
        }
        return {"success": True, "data": {"runtime": data, "lifecycle": lifecycle, "health": {"closure_score": closure_score, "is_healthy": has_runtime}}}

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

    def governance_lifecycle(self, execution_id: str = "") -> Dict[str, Any]:
        summary = asyncio.run(self._governance_orchestration.summary(execution_id=execution_id, limit=50))
        pending = asyncio.run(self._governance_orchestration.pending(execution_id=execution_id))
        history = asyncio.run(self._governance_orchestration.history(execution_id=execution_id, limit=50))
        summary_data = summary.get("data", {}) if isinstance(summary, dict) else {}
        pending_data = pending.get("data", []) if isinstance(pending, dict) else []
        history_data = history.get("data", []) if isinstance(history, dict) else []
        closure_score = 100.0 if summary.get("success", False) and not pending_data else 0.0
        return {"success": True, "data": {"summary": summary_data, "pending": pending_data, "history": history_data, "lifecycle": {"stage": "governing", "status": "success" if summary.get("success", False) else "failed", "execution_id": execution_id, "pending_count": len(pending_data), "history_count": len(history_data), "summary_count": int(summary_data.get("history_count", 0) if isinstance(summary_data, dict) else 0), "closure_score": closure_score}, "health": {"closure_score": closure_score, "is_healthy": closure_score > 0}}}

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
        payload = self._platform_summary.console_overview(trace_payload=trace_payload, limit=limit)
        data = payload.get("data", {}) if isinstance(payload, dict) else {}
        lifecycle = data.get("lifecycle", {}) if isinstance(data, dict) else {}
        health = data.get("health", {}) if isinstance(data, dict) else {}
        success_count = sum(1 for item in executions if str(item.get("status") or "").lower() == "success")
        failed_count = sum(1 for item in executions if str(item.get("status") or "").lower() == "failed")
        total_count = len(executions)
        closure_score = round((success_count / total_count) * 100, 2) if total_count else 0.0
        data["closure_score"] = closure_score
        data["closure_summary"] = {
            "success_rate": round((success_count / total_count) * 100, 2) if total_count else 0.0,
            "failure_rate": round((failed_count / total_count) * 100, 2) if total_count else 0.0,
            "total_count": total_count,
        }
        data["lifecycle"] = {**dict(lifecycle), "closure_score": closure_score, "success_count": success_count, "failed_count": failed_count, "total_count": total_count}
        data["health"] = {**dict(health), "closure_score": closure_score}
        payload["data"] = data
        return payload

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
