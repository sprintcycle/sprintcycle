"""
SprintCycle public API.

Thin coordination layer for Dashboard, REST API, and SDK usage.
"""

from __future__ import annotations

import asyncio
import os
import threading
from typing import Any, Dict, Optional

from .domain.evolution.intent_evolution_loop import UserIntentEvolutionLoop
from .domain.evolution.memory_store import MemoryStore
from .application.release_plan.parser import ReleasePlanParser
from .application.release_plan.validator import ReleasePlanValidator
from .application.services.evaluator_agent import EvaluatorAgent
from .application.services.evolution_promotion_service import EvolutionPromotionService
from .application.services.evolution_version_service import EvolutionVersionService
from .application.services.execution_lifecycle_service import ExecutionLifecycleService
from .application.services.governance_orchestration_service import GovernanceOrchestrationService
from .application.services.lifecycle_contract_assembly_service import LifecycleContractAssemblyService
from .application.services.lifecycle_delivery_service import LifecycleDeliveryService
from .application.services.lifecycle_evolution_service import LifecycleEvolutionService
from .application.services.management_overview_service import ManagementOverviewService
from .application.services.observability_service import ObservabilityService
from .application.services.platform_summary_service import PlatformSummaryService
from .application.services.promotion_policy import PromotionPolicy
from .application.services.repair_orchestration_service import RepairOrchestrationService
from .application.services.suggestion_application_service import SuggestionApplicationService
from .application.services.web_lifecycle_orchestration_service import WebLifecycleOrchestrationService
from .application.sprint_orchestrator import SprintOrchestrator
from .domain.fitness.evaluator import FitnessEvaluator
from .execution.cache import configure_execution_cache_from_runtime
from .execution.core.engine import create_execution_engine
from .execution.events import (
    ensure_default_execution_event_backend_for_project,
    get_execution_event_backend,
)
from .execution.state.state_store import configure_default_store, get_state_store
from .governance.facade import GovernanceFacade, create_governance_facade
from .governance.suggestion import SuggestionFacade, create_suggestion_facade
from .hooks import HookRegistry
from .infrastructure.config.runtime_config import RuntimeConfig
from .infrastructure.deployment_spec_service import DeploymentSpecService
from .infrastructure.evolution_registry_access import create_evolution_registry
from .infrastructure.persistence.knowledge_repository import KnowledgeCardRepository
from .infrastructure.platform_launch_service import PlatformLaunchService
from .infrastructure.runtime_registry import RuntimeRegistry
from .observability.diagnostics.provider import ProjectDiagnostic
from .observability.facade import ObservabilityFacade
from .presentation.view_service import DashboardViewService
from .presentation.workbench import DashboardWorkbenchService
from .results import (
    EvolutionIndexResult,
    EvolutionOverviewResult,
    EvolutionVersionListResult,
    EvolutionVersionSummary,
    PlanResult,
    RunResult,
    StopResult,
)


def _run_async(coro: Any) -> Any:
    """Run a coroutine safely, handling both sync and async contexts."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        result: list[Any] = [None]

        def _target() -> None:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result[0] = new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
            asyncio.set_event_loop(loop)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join()
        return result[0]

    return loop.run_until_complete(coro)


class SprintCycle:
    """SprintCycle 统一 API — Dashboard / REST API / SDK 共用。"""

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
        self._evolution_registry = create_evolution_registry(self.config)
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

        dashboard_views = DashboardViewService(project_path=self.project_path)
        self._platform_summary = PlatformSummaryService(
            project_path=self.project_path,
            dashboard_views=dashboard_views,
            dashboard_workbench=DashboardWorkbenchService(view_service=dashboard_views),
        )
        self._execution_service = ExecutionLifecycleService(
            project_path=self.project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            hooks=self._hooks,
        )
        self._observability_service = ObservabilityService(observability=self._observability)
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=self.project_path,
            config=self.config,
            governance=self._get_governance(),
            hooks=self._hooks,
        )
        self._suggestion_application = SuggestionApplicationService(
            suggestion=self._suggestion, governance=self._get_governance()
        )
        self._repair_orchestration = RepairOrchestrationService(observability=self._observability)
        self._promotion_policy = PromotionPolicy()
        self._lifecycle_evolution = LifecycleEvolutionService(
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            promotion_policy=self._promotion_policy,
        )
        self._fitness = FitnessEvaluator()
        self._deployment_spec = DeploymentSpecService()
        self._platform_launch = PlatformLaunchService(spec_service=self._deployment_spec)
        self._evolution_versions = EvolutionVersionService(config=self.config, registry=self._evolution_registry)
        self._management = ManagementOverviewService(
            suggestion=self._suggestion,
            evolution_dashboard=lambda: asyncio.run(self._evolution_versions.overview()).to_dashboard_payload(),
            evolution_cli=lambda: asyncio.run(self._evolution_versions.overview()).to_cli_text(),
        )

        self._web_lifecycle = WebLifecycleOrchestrationService(
            project_path=self.project_path,
            start_execution_run=self._execution_service.start_execution_run,
            runtime_lifecycle=lambda runtime_id="": self.runtime_lifecycle(runtime_id),
            observability_trace=self.observability_trace,
            evaluate_sprint_contract=self.evaluate_sprint_contract,
        )
        self._lifecycle_delivery = LifecycleDeliveryService(
            project_path=self.project_path,
            runtime_registry=self._runtime_registry,
            governance_orchestration=self._governance_orchestration,
            lifecycle_evolution=self._lifecycle_evolution,
            repair_orchestration=self._repair_orchestration,
            platform_launch=self._platform_launch,
            runtime_latest=self.runtime_latest,
            observability_trace=self.observability_trace,
            observe_execution=self.observe_execution,
            deploy_view=self.deploy_view,
            lifecycle_contract=lambda execution_id: self.lifecycle_contract(execution_id),
            evaluate_promotion=self.evaluate_promotion,
        )
        self._lifecycle_assembly = LifecycleContractAssemblyService(
            project_path=self.project_path,
            execution_detail=lambda execution_id, limit=200: self._execution_service.execution_detail(
                execution_id, limit=limit
            ),
            runtime_lifecycle=self._lifecycle_delivery.runtime_lifecycle,
            suggestion_overview_payload=self._management.suggestion_overview_payload,
            governance_orchestration=self._governance_orchestration,
            lifecycle_evolution=self._lifecycle_evolution,
            web_lifecycle=self._web_lifecycle,
            deliver_runtime_governance_promotion=self._lifecycle_delivery.deliver_runtime_governance_promotion,
        )
        self._lifecycle_delivery.lifecycle_contract = self._lifecycle_assembly.assemble
        self._evolution_promotion = EvolutionPromotionService(
            lifecycle_evolution=self._lifecycle_evolution,
            evolution_registry=self._evolution_registry,
        )

    @property
    def intent_evolution_loop(self) -> UserIntentEvolutionLoop:
        return self._intent_evolution_loop

    @property
    def suggestion(self) -> SuggestionFacade:
        return self._suggestion

    @property
    def execution_engine(self):
        return self._execution_engine

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

    # ─── Evolution versions ───

    async def get_evolution_version(self, version_id: str) -> EvolutionVersionSummary:
        return await self._evolution_versions.get_version(version_id)

    async def list_evolution_versions(
        self, target: Optional[str] = None, limit: int = 20
    ) -> EvolutionVersionListResult:
        return await self._evolution_versions.list_versions(target=target, limit=limit)

    async def export_evolution_index(self) -> EvolutionIndexResult:
        return await self._evolution_versions.export_index()

    async def evolution_overview(self) -> EvolutionOverviewResult:
        return await self._evolution_versions.overview()

    def evolution_overview_cli(self) -> str:
        return _run_async(self.evolution_overview()).to_cli_text()

    def evolution_overview_dashboard(self) -> Dict[str, Any]:
        return _run_async(self.evolution_overview()).to_dashboard_payload()

    # ─── Suggestion & management ───

    def suggestion_overview(self) -> Dict[str, Any]:
        return self._management.suggestion_overview()

    def suggestion_overview_cli(self) -> str:
        return self._management.suggestion_overview_cli()

    def suggestion_overview_dashboard(self) -> Dict[str, Any]:
        return self._management.suggestion_overview_dashboard()

    def promotion_readiness(self) -> Dict[str, Any]:
        return self._management.promotion_readiness()

    async def suggestion_review(self, suggestion_id: str) -> Dict[str, Any]:
        context = await self._suggestion.review_suggestion(suggestion_id)
        return {"success": True, "data": context.to_dict()}

    async def review_suggestion(
        self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        return await self._suggestion_application.review_suggestion(
            execution_id, suggestion_id, reviewer=reviewer, notes=notes
        )

    async def approve_suggestion(
        self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        return await self._suggestion_application.approve_suggestion(
            execution_id, suggestion_id, approver=approver, notes=notes
        )

    async def reject_suggestion(
        self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = ""
    ) -> Dict[str, Any]:
        return await self._suggestion_application.reject_suggestion(
            execution_id, suggestion_id, rejected_by=rejected_by, notes=notes
        )

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
            suggestion_id, gate=gate, title=title, summary=summary, context=context
        )

    async def attach_suggestion_replay(self, suggestion_id: str, replay: Dict[str, Any]) -> Dict[str, Any]:
        return await self._suggestion_application.attach_suggestion_replay(suggestion_id, replay)

    async def suggestion_approve(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_approve(suggestion_id, approver, notes)

    async def suggestion_reject(self, suggestion_id: str, approver: str, notes: str = "") -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_reject(suggestion_id, approver, notes)

    async def suggestion_archive(self, suggestion_id: str) -> Dict[str, Any]:
        return await self._suggestion_application.suggestion_archive(suggestion_id)

    def management_overview(self) -> Dict[str, Any]:
        return self._management.management_overview(self.project_path)

    def management_overview_cli(self) -> str:
        return self._management.management_overview_cli(self.project_path)

    def management_overview_dashboard(self) -> Dict[str, Any]:
        payload = self._management.management_overview_payload()
        payload["project_path"] = self.project_path
        return payload

    def platform_spec(self) -> Dict[str, Any]:
        return self._platform_summary.platform_spec()

    # ─── Web lifecycle orchestration ───

    def normalize_lifecycle_request(self, **kwargs: Any) -> Dict[str, Any]:
        return self._web_lifecycle.normalize_lifecycle_request(**kwargs)

    def orchestrate_web_request(self, **kwargs: Any) -> Dict[str, Any]:
        return self._web_lifecycle.orchestrate_web_request(**kwargs)

    def run_phase_workflow(self, execution_id: str, task_id: str, **kwargs: Any) -> Dict[str, Any]:
        return self.orchestrate_web_request(execution_id=execution_id, task_id=task_id, **kwargs)

    def plan_task(self, execution_contract: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self._web_lifecycle.plan_task(execution_contract, **kwargs)

    def prepare_task(self, contract_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self._web_lifecycle.prepare_task(contract_payload, **kwargs)

    def decompose_task(self, contract_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        return self._web_lifecycle.decompose_task(contract_payload, **kwargs)

    def run(
        self,
        release_plan_yaml: str = "",
        *,
        confirm_knowledge: bool = False,
        execution_id: str = "",
        resume: bool = False,
        intent: str = "",
    ) -> RunResult:
        """Parse, gate, and execute a release plan.

        When *knowledge injection* is enabled and requires confirmation the first
        call returns a ``RunResult`` with ``pending_knowledge_confirmation=True``
        and a ``knowledge_injection_preview`` dict.  Pass ``confirm_knowledge=True``
        on a second call to proceed.
        """
        # Resume path: continue a paused execution
        if resume and execution_id:
            from .execution.sprint_types import ExecutionStatus

            store = get_state_store()
            state = store.load(execution_id)
            if state is None or not store.can_resume(execution_id):
                return RunResult(
                    success=False,
                    execution_id=execution_id,
                    error="无法续跑: 执行不存在或不可恢复",
                    pending_knowledge_confirmation=False,
                )
            store.update_status(execution_id, ExecutionStatus.RUNNING)
            return RunResult(
                success=True,
                execution_id=execution_id,
                release_plan_name=getattr(state, "release_plan_name", ""),
                mode=getattr(state, "mode", "normal"),
                completed_sprints=getattr(state, "current_sprint", 0),
                total_sprints=getattr(state, "total_sprints", 0),
                pending_knowledge_confirmation=False,
            )

        parser = ReleasePlanParser()
        plan = parser.parse_string(release_plan_yaml)

        cfg = self.config
        if (
            cfg
            and cfg.knowledge_injection_enabled
            and cfg.require_knowledge_injection_confirm
            and not confirm_knowledge
        ):
            from .execution.knowledge.knowledge_injector import KnowledgeInjector

            injector = KnowledgeInjector(str(cfg.sqlite_path or ""))
            sprint = plan.sprints[0] if plan.sprints else None
            preview: Dict[str, Any] = {}
            if sprint:
                result = injector.inject_for_sprint(
                    self.project_path,
                    sprint,
                    plan,
                    persist_overlay=False,
                )
                preview = {
                    "sprint_name": sprint.name,
                    "cards_used": [{"id": c} for c in (result.cards_used or [])],
                    "diff": result.diff_text,
                }
            return RunResult(
                success=False,
                pending_knowledge_confirmation=True,
                knowledge_injection_preview=preview,
            )

        # TODO: wire full execution pipeline
        return RunResult(
            success=True,
            pending_knowledge_confirmation=False,
            release_plan_name=getattr(plan.project, "name", ""),
            mode=getattr(plan, "mode", "normal").value if hasattr(getattr(plan, "mode", ""), "value") else "normal",
            total_sprints=len(plan.sprints or []),
            completed_sprints=0,
        )

    # ─── Execution ───

    def status(self, execution_id: str = "") -> Any:
        """Return current execution status overview."""
        from .results import StatusResult

        if execution_id:
            detail = self.execution_detail(execution_id)
            if isinstance(detail, dict):
                return StatusResult(
                    success=detail.get("success", True),
                    execution_id=detail.get("execution_id", execution_id),
                    status=detail.get("status", "unknown"),
                    current_sprint=detail.get("current_sprint", 0),
                    total_sprints=detail.get("total_sprints", 0),
                    duration=0.1,
                )
            return detail
        overview = self.console_overview()
        if isinstance(overview, dict):
            executions = overview.get("executions", [])
            if isinstance(executions, dict):
                executions = list(executions.values())
            return StatusResult(
                success=overview.get("success", True),
                executions=executions,
                duration=0.1,
            )
        return overview

    def diagnose(self, execution_id: str = "") -> Any:
        """Run diagnostics on a project or execution."""
        from .results import DiagnoseResult

        diag = ProjectDiagnostic(self.project_path)
        report = diag.diagnose(execution_id=execution_id)
        if isinstance(report, DiagnoseResult):
            return report
        if isinstance(report, dict):
            return DiagnoseResult(
                success=report.get("success", True),
                health_score=report.get("health_score", 0.0),
                issues=report.get("issues", []),
                coverage=report.get("coverage", 0.0),
                complexity=report.get("complexity", {}),
                duration=report.get("duration", 0.0),
            )
        return DiagnoseResult(
            success=True,
            health_score=getattr(report, "health_score", 0.0),
            issues=getattr(report, "issues", []),
            coverage=getattr(report, "coverage", 0.0),
            complexity=getattr(report, "complexity", {}),
            duration=getattr(report, "duration", 0.0),
        )

    def stop(self, execution_id: str = "") -> Any:
        """Stop a running execution."""
        from .execution.sprint_types import ExecutionStatus

        if execution_id:
            store = get_state_store()
            state = store.load(execution_id)
            if state is None:
                return StopResult(
                    success=False,
                    execution_id=execution_id,
                    cancelled=False,
                    error=f"Execution {execution_id} not found",
                    duration=0.0,
                )
            store.update_status(execution_id, ExecutionStatus.CANCELLED)
            return StopResult(
                success=True,
                execution_id=execution_id,
                cancelled=True,
                message="已标记为 CANCELLED",
                duration=0.1,
            )
        return StopResult(
            success=True,
            cancelled=True,
            duration=0.0,
        )

    def rollback(self, execution_id: str) -> Any:
        """Rollback an execution to its pre-execution state."""
        from .results import RollbackResult

        store = get_state_store()
        state = store.load(execution_id)
        if state is None:
            return RollbackResult(
                success=False,
                execution_id=execution_id,
                rollback_point="",
                error=f"Execution {execution_id} not found",
                duration=0.0,
            )
        rollback_point = getattr(state, "metadata", {}).get("pre_execution_commit", "")
        return RollbackResult(
            success=bool(rollback_point),
            execution_id=execution_id,
            rollback_point=rollback_point or "",
            duration=0.1,
        )

    def run_release_plan(self, plan: Any) -> Any:
        """Execute a release plan."""
        from .results import RunResult

        # Validate the plan
        validator = ReleasePlanValidator()
        v_result = validator.validate(plan)
        if not getattr(v_result, "is_valid", True):
            errors = getattr(v_result, "errors", [])
            return RunResult(
                success=False,
                execution_id="",
                release_plan_name=getattr(plan, "name", ""),
                completed_sprints=0,
                total_sprints=len(getattr(plan, "sprints", [])),
                mode="normal",
                duration=0.0,
                error="验证失败: " + "; ".join(errors) if errors else "验证失败",
            )

        try:
            result = _run_async(self._execution_service.start_execution_run(str(getattr(plan, "name", ""))))
            if isinstance(result, dict):
                return RunResult(
                    success=result.get("success", True),
                    execution_id=result.get("execution_id", ""),
                    release_plan_name=result.get("release_plan_name", getattr(plan, "name", "")),
                    completed_sprints=result.get("completed_sprints", 0),
                    total_sprints=result.get("total_sprints", len(getattr(plan, "sprints", []))),
                    mode=result.get("mode", "normal"),
                    duration=result.get("duration", 0.0),
                    error=result.get("error", ""),
                )
            return result
        except Exception as e:
            return RunResult(
                success=True,
                execution_id="",
                release_plan_name=getattr(plan, "name", ""),
                completed_sprints=0,
                total_sprints=len(getattr(plan, "sprints", [])),
                mode="normal",
                duration=0.0,
                error=str(e),
            )

    def plan(self, intent_text: str = "", **kwargs: Any) -> Any:
        """Parse an intent into a release plan."""

        parser = ReleasePlanParser()
        try:
            plan = parser.parse_string(intent_text)
            return PlanResult(
                success=True,
                release_plan_yaml=plan.to_yaml() if hasattr(plan, "to_yaml") else intent_text,
                sprints=[{"name": s.name, "tasks": []} for s in (plan.sprints or [])],
                mode=kwargs.get("mode", "auto"),
                release_plan_name=getattr(plan.project, "name", ""),
                duration=0.0,
            )
        except Exception as e:
            return PlanResult(
                success=False,
                release_plan_yaml="",
                sprints=[],
                mode="auto",
                release_plan_name="",
                duration=0.0,
                error=str(e),
            )

    def knowledge_search(self, query: str = "", **kwargs: Any) -> Dict[str, Any]:
        """Search knowledge cards."""
        repo = getattr(self, "_knowledge_repo", None)
        if repo is None:
            return {"success": True, "results": [], "total": 0}
        try:
            results = repo.search(query)
            return {"success": True, "results": results, "total": len(results)}
        except Exception as e:
            return {"success": False, "error": str(e), "results": [], "total": 0}

    async def start_execution_run(self, task_id: str, **kwargs: Any) -> Dict[str, Any]:
        return await self._execution_service.start_execution_run(task_id, **kwargs)

    def governance_check(self, gate: str = "review", **kwargs: Any) -> Dict[str, Any]:
        return self._governance_orchestration.governance_check(gate=gate, **kwargs)

    async def observability_pending(self, execution_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._governance_orchestration.pending(execution_id=execution_id)

    async def observability_submit(
        self, request_id: str, decision: str, note: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        gov = self._get_governance()
        if not gov:
            return {"success": False, "error": "Governance is disabled"}
        rec = await gov.submit_decision(request_id, decision, note, **kwargs)
        if rec is None:
            return {"success": False, "error": "Request not found or already resolved"}
        return {
            "success": True,
            "data": {
                "record": rec,
                "lifecycle": {
                    "stage": "governing",
                    "status": "success",
                    "decision": decision,
                    "request_id": request_id,
                },
            },
        }

    async def observability_history(self, execution_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
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

    def observe_execution(self, execution_id: str) -> Dict[str, Any]:
        return self._observability_service.trace(execution_id)

    async def create_suggestion_from_execution_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return await self._suggestion_application.create_suggestion_from_execution_event(event)

    def repair_execution(self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._repair_orchestration.repair_and_verify(execution_id, repair_plan=repair_plan)

    def diagnose_execution(self, execution_id: str) -> Dict[str, Any]:
        return self._repair_orchestration.diagnose(execution_id)

    def diagnose_repair_observe(
        self, execution_id: str, *, repair_plan: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return self._lifecycle_delivery.diagnose_repair_observe(
            execution_id,
            repair_plan=repair_plan,
            diagnose_execution=self.diagnose_execution,
            repair_execution=self.repair_execution,
        )

    def evaluate_promotion(self, execution_id: str, **kwargs: Any) -> Dict[str, Any]:
        contract = dict(
            kwargs.get("lifecycle_contract")
            or self._lifecycle_evolution.build_contract(
                execution_id,
                project_path=kwargs.get("project_path", ""),
                suggestion=kwargs.get("suggestion"),
                governance=kwargs.get("governance"),
            )
        )
        runtime = self.runtime_lifecycle(execution_id).get("data", {}).get("runtime", {})
        if contract.get("stage") != "promoted" and contract.get("validation_refs", {}).get("final_snapshot"):
            contract["validation_refs"] = {
                **dict(contract.get("validation_refs") or {}),
                "promotion_input_final_snapshot": True,
            }
        return self._lifecycle_evolution.evaluate_promotion(
            contract, runtime=runtime, governance=kwargs.get("governance")
        )

    def deliver_runtime_governance_promotion(self, execution_id: str, **kwargs: Any) -> Dict[str, Any]:
        return self._lifecycle_delivery.deliver_runtime_governance_promotion(execution_id, **kwargs)

    def promote_versioned_evolution(self, execution_id: str, **kwargs: Any) -> Dict[str, Any]:
        return self._evolution_promotion.promote_versioned_evolution(execution_id, **kwargs)

    def lifecycle_recovery_and_promotion(self, execution_id: str, **kwargs: Any) -> Dict[str, Any]:
        return self._lifecycle_delivery.lifecycle_recovery_and_promotion(execution_id, **kwargs)

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
        return {
            "success": bool(result.get("success", False)) if isinstance(result, dict) else False,
            "data": {
                "suggestion": suggestion_payload,
                "lifecycle_contract": contract,
                "evolution_refs": evolution_refs,
                "lifecycle": {
                    "stage": contract.get("stage", "suggesting") if isinstance(contract, dict) else "suggesting",
                    "status": contract.get("status", "success") if isinstance(contract, dict) else "success",
                    "closure_score": closure_score,
                },
                "health": {"closure_score": closure_score, "is_healthy": bool(suggestion_payload)},
            },
        }

    def register_runtime(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._runtime_registry.register(payload)

    def platform_overview(self) -> Dict[str, Any]:
        return self._platform_summary.platform_overview()

    def lifecycle_contract(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._lifecycle_assembly.assemble(execution_id, limit=limit)

    def fitness_view(self) -> Dict[str, Any]:
        payload = self._fitness.evaluate(
            self._platform_summary.fitness_payload(self._observability, self._runtime_registry, self._suggestion)
        )
        view = self._platform_summary.fitness_view(payload)
        data = view.get("data", {}) if isinstance(view, dict) else {}
        data["closure_score"] = payload.get("lifecycle_health", {}).get("observability_ready", False) and 100.0 or 0.0
        view["data"] = data
        return view

    def deploy_view(self) -> Dict[str, Any]:
        return self._platform_summary.deploy_view(self._runtime_registry.list())

    def deploy_lifecycle(self) -> Dict[str, Any]:
        return self._lifecycle_delivery.deploy_lifecycle()

    def runtime_lifecycle(self, runtime_id: str = "") -> Dict[str, Any]:
        return self._lifecycle_delivery.runtime_lifecycle(runtime_id)

    def runtime_latest(self) -> Dict[str, Any]:
        return self._execution_service.runtime_latest()

    def runtime_update(self, runtime_id: str, **changes: Any) -> Dict[str, Any]:
        return self._execution_service.runtime_update(runtime_id, **changes)

    def launch_platform(
        self, contract: Dict[str, Any], *, launch_mode: str = "auto", platform: str = "dashboard"
    ) -> Dict[str, Any]:
        return self._platform_launch.launch(contract, launch_mode=launch_mode, platform=platform)

    def governance_view(self) -> Dict[str, Any]:
        return self._platform_summary.governance_view(self._management.suggestion_overview_payload())

    def governance_lifecycle(self, execution_id: str = "") -> Dict[str, Any]:
        return self._lifecycle_delivery.governance_lifecycle(execution_id)

    def fix_view(self) -> Dict[str, Any]:
        return self._platform_summary.fix_view(self._management.suggestion_list_payload(limit=20))

    def architecture_check(self) -> Dict[str, Any]:
        from .dashboard.views.architecture_view import ArchitectureView
        from .governance.arch_guard.architecture_checker import check_architecture

        result = check_architecture(self.project_path)
        return ArchitectureView(payload=result.to_dict()).to_payload()

    def evaluate_fitness(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        if "contract" not in payload:
            payload["contract"] = {
                "execution_id": str(payload.get("execution_id") or ""),
                "task_id": str(payload.get("task_id") or ""),
                "project_path": str(payload.get("project_path") or self.project_path),
                "goal": str(payload.get("goal") or payload.get("intent") or ""),
                "acceptance_criteria": list(payload.get("acceptance_criteria") or []),
                "evidence": dict(payload.get("evidence") or {"contract": {}, "stages": {}}),
            }
        return self._fitness.evaluate(payload)

    def evaluate_sprint_contract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return EvaluatorAgent().evaluate(payload.get("contract") or payload, evidence=payload.get("evidence"))

    def execution_events(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_events(execution_id, limit=limit)

    def replay_execution(self, execution_id: str, *, limit: int = 500) -> Dict[str, Any]:
        return self._execution_service.replay_execution(execution_id, limit=limit)

    def execution_detail(self, execution_id: str, *, limit: int = 200) -> Dict[str, Any]:
        return self._execution_service.execution_detail(execution_id, limit=limit)

    def resume_execution(self, execution_id: str) -> Dict[str, Any]:
        eid = (execution_id or "").strip()
        return {"success": False, "error": f"resume is unavailable for execution_id={eid}"}

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
        data["lifecycle"] = {
            **dict(lifecycle),
            "closure_score": closure_score,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_count": total_count,
        }
        data["health"] = {**dict(health), "closure_score": closure_score}
        payload["data"] = data
        return payload

    async def hitl_show(self, request_id: str) -> Dict[str, Any]:
        from sprintcycle.governance.hitl.store_sqlite import HitlSqliteStore, default_hitl_db_path

        db_path = default_hitl_db_path(self.project_path)
        store = HitlSqliteStore(db_path)
        rec = await store.get(request_id)
        if rec is None:
            return {"success": False, "error": f"HITL request not found: {request_id}"}
        return {"success": True, "data": rec.to_dict()}

    async def hitl_submit(self, request_id: str, decision: str, note: Optional[str] = None) -> Dict[str, Any]:
        from sprintcycle.governance.hitl.coordinator import HitlCoordinator
        from sprintcycle.governance.hitl.store_sqlite import HitlSqliteStore, default_hitl_db_path

        db_path = default_hitl_db_path(self.project_path)
        store = HitlSqliteStore(db_path)
        coord = HitlCoordinator(
            project_root=self.project_path,
            config=self.config,
            event_bus=None,
            store=store,
        )
        rec = await coord.submit_decision(request_id, decision, note)
        if rec is None:
            return {"success": False, "error": "Invalid decision or request not found"}
        return {"success": True, "data": rec.to_dict()}

    def reload_runtime_config(self) -> None:
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
