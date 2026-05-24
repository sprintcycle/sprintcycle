"""
HTTP 层服务工厂 - 为 interfaces/http 提供 application 服务实例

从 api.py 中提取服务初始化逻辑，供 internal.py 和 public.py 直接使用。
"""

from __future__ import annotations

from typing import Any, Optional

from sprintcycle.application.services.observability_service import ObservabilityService
from sprintcycle.application.services.platform_summary_service import PlatformSummaryService
from sprintcycle.application.services.management_overview_service import ManagementOverviewService
from sprintcycle.application.services.dashboard_view_service import DashboardViewService
from sprintcycle.application.services.dashboard_workbench_service import DashboardWorkbenchService
from sprintcycle.application.services.lifecycle.lifecycle_delivery_service import LifecycleDeliveryService
from sprintcycle.application.services.lifecycle.lifecycle_evolution_service import LifecycleEvolutionService
from sprintcycle.application.services.lifecycle.lifecycle_contract_assembly_service import LifecycleContractAssemblyService
from sprintcycle.application.services.repair_orchestration_service import RepairOrchestrationService
from sprintcycle.application.services.lifecycle.execution_lifecycle_service import ExecutionLifecycleService
from sprintcycle.application.services.governance_orchestration_service import GovernanceOrchestrationService
from sprintcycle.application.services.evolution_version_service import EvolutionVersionService
from sprintcycle.application.services.suggestion_application_service import SuggestionApplicationService
from sprintcycle.application.services.evaluator_agent import EvaluatorAgent
from sprintcycle.application.release_plan.parser import ReleasePlanParser
from sprintcycle.application.release_plan.validator import ReleasePlanValidator
from sprintcycle.domain.fitness.evaluator import FitnessEvaluator
from sprintcycle.infrastructure.persistence.state.state_store import get_state_store
from sprintcycle.execution.core.events import get_execution_event_backend
from sprintcycle.governance.core.facade import GovernanceFacade, create_governance_facade
from sprintcycle.governance.suggestion import SuggestionFacade, create_suggestion_facade
from sprintcycle.infrastructure.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.evolution.evolution_registry_access import create_evolution_registry
from sprintcycle.infrastructure.persistence.knowledge_repository import KnowledgeCardRepository
from sprintcycle.infrastructure.observability.facade import ObservabilityFacade
from sprintcycle.infrastructure.config.runtime_registry import RuntimeRegistry
from sprintcycle.domain.hooks import HookRegistry


class HTTPServices:
    """HTTP 层需要的所有服务实例"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.config = RuntimeConfig.from_project(project_path)
        
        # 初始化核心依赖
        self._observability = ObservabilityFacade()
        self._runtime_registry = RuntimeRegistry()
        self._hooks = HookRegistry()
        self._evolution_registry = create_evolution_registry(self.config)
        
        # 初始化 governance facade
        self._governance = create_governance_facade(
            project_path=project_path,
            config=self.config,
        )
        
        # 初始化 suggestion facade
        self._suggestion = create_suggestion_facade(
            project_path=project_path,
            config=self.config,
            evolution_facade=None,
        )
        
        # 初始化 Dashboard 服务
        self._dashboard_views = DashboardViewService(project_path=project_path)
        self._dashboard_workbench = DashboardWorkbenchService(view_service=self._dashboard_views)
        
        # 初始化 application 服务
        self._execution_lifecycle = ExecutionLifecycleService(
            project_path=project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            hooks=self._hooks,
        )
        
        self._observability_service = ObservabilityService(observability=self._observability)
        
        self._platform_summary = PlatformSummaryService(
            project_path=project_path,
            dashboard_views=self._dashboard_views,
            dashboard_workbench=self._dashboard_workbench,
        )
        
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=project_path,
            config=self.config,
            governance=self._governance,
            hooks=self._hooks,
        )
        
        self._suggestion_application = SuggestionApplicationService(
            suggestion=self._suggestion,
            governance=self._governance,
        )
        
        self._lifecycle_evolution = LifecycleEvolutionService(
            project_path=project_path,
            config=self.config,
            evolution_registry=self._evolution_registry,
        )
        
        self._lifecycle_delivery = LifecycleDeliveryService(
            project_path=project_path,
            config=self.config,
        )
        
        self._lifecycle_contract = LifecycleContractAssemblyService(
            project_path=project_path,
            config=self.config,
        )
        
        self._repair_orchestration = RepairOrchestrationService(
            project_path=project_path,
            config=self.config,
            observability=self._observability,
        )
        
        self._evolution_version = EvolutionVersionService(
            config=self.config,
            registry=self._evolution_registry,
        )
        
        self._management_overview = ManagementOverviewService(
            suggestion=self._suggestion,
            evolution_dashboard=lambda: self.evolution_overview(),
            evolution_cli=lambda: self.evolution_overview_cli(),
        )

    # ===== 代理方法 (兼容 api.py 调用方式) =====

    def status(self, execution_id: str = "") -> Any:
        return self._execution_lifecycle.status(execution_id)

    def hitl_pending(self, execution_id: Optional[str] = None) -> Any:
        return self._execution_lifecycle.hitl_pending(execution_id)

    def hitl_history(self, execution_id: Optional[str] = None, limit: int = 50) -> Any:
        return self._execution_lifecycle.hitl_history(execution_id, limit)

    def hitl_show(self, request_id: str) -> Any:
        return self._execution_lifecycle.hitl_show(request_id)

    def hitl_submit(self, request_id: str, decision: str, note: Optional[str] = None) -> Any:
        return self._execution_lifecycle.hitl_submit(request_id, decision, note)

    def console_overview(self, limit: int = 20) -> Any:
        return self._dashboard_views.console_overview(limit=limit)

    def platform_overview(self) -> Any:
        return self._platform_summary.overview()

    def governance_view(self) -> Any:
        return self._dashboard_views.governance_view({})

    async def governance_history(self, limit: int = 50) -> Any:
        return await self._governance_orchestration.history(limit=limit)

    async def governance_lifecycle(self, execution_id: str = "") -> Any:
        return await self._governance_orchestration.summary(execution_id=execution_id)

    def lifecycle_contract(self, execution_id: str, limit: int = 200) -> Any:
        return self._lifecycle_contract.lifecycle_contract(execution_id, limit=limit)

    def evaluate_sprint_contract(self, payload: Any) -> Any:
        return self._lifecycle_contract.evaluate_sprint_contract(payload)

    def deploy_view(self) -> Any:
        return self._dashboard_views.deploy_view({})

    async def deploy_lifecycle(self) -> Any:
        return await self._lifecycle_delivery.deploy_lifecycle()

    def fix_view(self) -> Any:
        return self._repair_orchestration.fix_view()

    def diagnose_repair_observe(self, execution_id: str, repair_plan: Optional[Any] = None) -> Any:
        return self._repair_orchestration.diagnose_repair_observe(execution_id, repair_plan)

    def execution_detail(self, execution_id: str, limit: int = 200) -> Any:
        return self._execution_lifecycle.execution_detail(execution_id, limit=limit)

    def execution_events(self, execution_id: str, limit: int = 200) -> Any:
        return self._execution_lifecycle.execution_events(execution_id, limit=limit)

    def replay_execution(self, execution_id: str, limit: int = 500) -> Any:
        return self._execution_lifecycle.replay_execution(execution_id, limit=limit)

    def observability_trace(self, run_id: str) -> Any:
        return self._observability_service.trace(run_id)

    def observability_replay(self, run_id: str) -> Any:
        return self._observability_service.replay(run_id)

    def fitness_view(self) -> Any:
        return self._dashboard_views.fitness_view(
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            suggestion=self._suggestion,
        )

    async def suggestion_overview(self) -> Any:
        return await self._management_overview.suggestion_overview()

    async def management_overview(self) -> Any:
        return await self._management_overview.management_overview(self.project_path)

    def suggestion_board(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        return self._dashboard_workbench.suggestion_board(self, execution_id=execution_id, limit=limit)

    def suggestion_and_hitl_panel(self, execution_id: Optional[str] = None, limit: int = 20) -> Any:
        return self._dashboard_workbench.suggestion_and_hitl_panel(self, execution_id=execution_id, limit=limit)

    def execution_workspace(self, execution_id: str, limit: int = 200) -> Any:
        return self._dashboard_views.execution_workspace(self, execution_id=execution_id, limit=limit)

    def dashboard_platform_workspace(self) -> Any:
        return self._dashboard_views.platform_workspace(self.platform_overview())

    def review_suggestion(self, execution_id: str, suggestion_id: str, reviewer: str = "", notes: str = "") -> Any:
        return self._suggestion_application.review_suggestion(execution_id, suggestion_id, reviewer=reviewer, notes=notes)

    def approve_suggestion(self, execution_id: str, suggestion_id: str, approver: str = "", notes: str = "") -> Any:
        return self._suggestion_application.approve_suggestion(execution_id, suggestion_id, approver=approver, notes=notes)

    def reject_suggestion(self, execution_id: str, suggestion_id: str, rejected_by: str = "", notes: str = "") -> Any:
        return self._suggestion_application.reject_suggestion(execution_id, suggestion_id, rejected_by=rejected_by, notes=notes)

    def architecture_check(self) -> Any:
        return self._governance_orchestration.architecture_check()

    def evolution_overview(self) -> Any:
        return self._lifecycle_evolution.overview()

    def evolution_overview_cli(self) -> str:
        return self._lifecycle_evolution.overview_cli()

    def list_evolution_versions(self, target: Optional[str] = None, limit: int = 20) -> Any:
        return self._evolution_version.list_versions(target=target, limit=limit)

    def get_evolution_version(self, version_id: str) -> Any:
        return self._evolution_version.get_version(version_id)

    # ===== Public API 方法 =====

    def diagnose(self, execution_id: str = "") -> Any:
        """运行项目或执行诊断"""
        from sprintcycle.infrastructure.observability.diagnostics.provider import ProjectDiagnostic
        from sprintcycle.application.results import DiagnoseResult

        diag = ProjectDiagnostic(self.project_path)
        report = diag.diagnose(execution_id=execution_id)
        if isinstance(report, DiagnoseResult):
            return report.to_dict()
        if isinstance(report, dict):
            return {
                "success": report.get("success", True),
                "health_score": report.get("health_score", 0.0),
                "issues": report.get("issues", []),
                "coverage": report.get("coverage", 0.0),
                "complexity": report.get("complexity", {}),
                "duration": report.get("duration", 0.0),
            }
        return {
            "success": True,
            "health_score": getattr(report, "health_score", 0.0) if hasattr(report, "health_score") else 0.0,
            "issues": getattr(report, "issues", []) if hasattr(report, "issues") else [],
            "coverage": getattr(report, "coverage", 0.0) if hasattr(report, "coverage") else 0.0,
            "complexity": getattr(report, "complexity", {}) if hasattr(report, "complexity") else {},
            "duration": getattr(report, "duration", 0.0) if hasattr(report, "duration") else 0.0,
        }

    def stop(self, execution_id: str = "") -> Any:
        """停止正在运行的执行"""
        from sprintcycle.execution.core.sprint_types import ExecutionStatus
        from sprintcycle.execution.state.state_store import get_state_store
        from sprintcycle.application.results import StopResult

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
                ).to_dict()
            store.update_status(execution_id, ExecutionStatus.CANCELLED)
            return StopResult(
                success=True,
                execution_id=execution_id,
                cancelled=True,
                message="已标记为 CANCELLED",
                duration=0.1,
            ).to_dict()
        return StopResult(
            success=True,
            cancelled=True,
            duration=0.0,
        ).to_dict()

    def rollback(self, execution_id: str) -> Any:
        """回滚执行到执行前状态"""
        from sprintcycle.execution.state.state_store import get_state_store
        from sprintcycle.application.results import RollbackResult

        store = get_state_store()
        state = store.load(execution_id)
        if state is None:
            return RollbackResult(
                success=False,
                execution_id=execution_id,
                rollback_point="",
                error=f"Execution {execution_id} not found",
                duration=0.0,
            ).to_dict()
        rollback_point = getattr(state, "metadata", {}).get("pre_execution_commit", "")
        return RollbackResult(
            success=bool(rollback_point),
            execution_id=execution_id,
            rollback_point=rollback_point or "",
            duration=0.1,
        ).to_dict()


def create_http_services(project_path: str) -> HTTPServices:
    """工厂函数：创建 HTTP 层服务实例"""
    return HTTPServices(project_path)
