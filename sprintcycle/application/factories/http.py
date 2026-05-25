"""
HTTP 层服务工厂 - 为 interfaces/http 提供 application 服务实例

从 api.py 中提取服务初始化逻辑，供 internal.py 和 public.py 直接使用。
"""

from __future__ import annotations

from typing import Any, Optional

from sprintcycle.application.services.observability.observability_service import ObservabilityService
from sprintcycle.application.services.dashboard.platform_summary_service import PlatformSummaryService
from sprintcycle.application.services.dashboard.management_overview_service import ManagementOverviewService
from sprintcycle.application.services.dashboard.dashboard_view_service import DashboardViewService
from sprintcycle.application.services.dashboard.dashboard_workbench_service import DashboardWorkbenchService
from sprintcycle.application.services.config_service import ConfigService
from sprintcycle.application.services.lifecycle.lifecycle_delivery_service import LifecycleDeliveryService
from sprintcycle.application.services.lifecycle.lifecycle_evolution_service import LifecycleEvolutionService
from sprintcycle.application.services.lifecycle.lifecycle_contract_assembly_service import LifecycleContractAssemblyService
from sprintcycle.application.services.governance.repair_orchestration_service import RepairOrchestrationService
from sprintcycle.application.services.lifecycle.execution_lifecycle_service import ExecutionLifecycleService
from sprintcycle.application.services.governance.governance_orchestration_service import GovernanceOrchestrationService
from sprintcycle.application.services.evolution.evolution_version_service import EvolutionVersionService
from sprintcycle.application.services.governance.suggestion_application_service import SuggestionApplicationService
from sprintcycle.application.services.execution.evaluator_agent import EvaluatorAgent
from sprintcycle.domain.generic.models.release_plan.parser import ReleasePlanParser
from sprintcycle.domain.generic.models.release_plan.validator import ReleasePlanValidator
from sprintcycle.domain.supporting.fitness.evaluator import FitnessEvaluator
from sprintcycle.infrastructure.adapters.core.execution.state_store.state_store import get_state_store
from sprintcycle.domain.core.execution.core.events import get_execution_event_backend
from sprintcycle.domain.core.governance.core.facade import GovernanceFacade, create_governance_facade
from sprintcycle.domain.core.governance.suggestion import SuggestionFacade, create_suggestion_facade
from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.adapters.core.evolution.evolution_registry_access import create_evolution_registry
from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import KnowledgeCardRepository
from sprintcycle.infrastructure.adapters.generic.observability.facade import ObservabilityFacade
from sprintcycle.infrastructure.adapters.generic.config.runtime_registry import RuntimeRegistry
from sprintcycle.domain.generic.interfaces.hooks import HookRegistry


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

        # 注册 Domain 层依赖的 Infrastructure 工厂函数
        self._register_infrastructure_factories()

    def _register_infrastructure_factories(self) -> None:
        """注册 Domain 层依赖的 Infrastructure 工厂函数（DDD 依赖倒置）"""
        # 注册事件后端工厂
        from sprintcycle.infrastructure.adapters.core.execution.state_store import register_event_backend_factory

        register_event_backend_factory()

        # 注册回滚实现
        from sprintcycle.infrastructure.adapters.core.evolution.rollback_store.rollback_types import (
            GitRollbackMixin,
            RollbackConfig,
            RollbackError,
            VariantBranch,
            _is_git_repo,
            _run_git,
        )
        from sprintcycle.domain.generic.ports.state_store import register_rollback_implementations

        register_rollback_implementations(
            GitRollbackMixin=GitRollbackMixin,
            RollbackConfig=RollbackConfig,
            RollbackError=RollbackError,
            VariantBranch=VariantBranch,
            is_git_repo=_is_git_repo,
            run_git=_run_git,
        )

        # 注册 HITL 存储工厂
        from sprintcycle.infrastructure.adapters.core.governance.hitl_store import HitlSqliteStore
        from sprintcycle.domain.generic.ports.hitl import register_hitl_store_factory

        def create_hitl_store(project_path: str):
            return HitlSqliteStore(project_path)

        register_hitl_store_factory(create_hitl_store)

        # 注册 Suggestion 存储工厂
        from sprintcycle.infrastructure.adapters.core.governance.suggestion_store import SuggestionSqliteStore
        from sprintcycle.domain.generic.ports.suggestion import register_suggestion_store_factory

        def create_suggestion_store(project_path: str):
            return SuggestionSqliteStore(project_path)

        register_suggestion_store_factory(create_suggestion_store)

        # 注册 Observability 门面工厂
        from sprintcycle.domain.generic.ports.observability import register_observability_facade_factory

        def create_observability_facade():
            from sprintcycle.infrastructure.adapters.generic.observability.facade import ObservabilityFacade
            return ObservabilityFacade()

        register_observability_facade_factory(create_observability_facade)

        # 注册 Knowledge 持久化工厂
        from sprintcycle.domain.generic.ports.knowledge import register_knowledge_repository_factory

        def create_knowledge_repository(project_path: str):
            from sprintcycle.infrastructure.adapters.generic.knowledge.knowledge_repository import KnowledgeCardRepository
            return KnowledgeCardRepository(project_path)

        register_knowledge_repository_factory(create_knowledge_repository)

        # 注册 Runtime Registry 工厂
        from sprintcycle.domain.generic.ports.registry import register_runtime_registry_factory

        def create_runtime_registry(config: Any):
            from sprintcycle.infrastructure.adapters.generic.config.runtime_registry import RuntimeRegistry
            return RuntimeRegistry()

        register_runtime_registry_factory(create_runtime_registry)

        # 注册 Evolution 注册表工厂
        from sprintcycle.domain.generic.ports.evolution import (
            register_evolution_registry_factory,
            register_version_manifest_factory,
        )

        register_evolution_registry_factory(create_evolution_registry)

        from sprintcycle.infrastructure.adapters.core.evolution.version_store.interface import get_version_manifest_summary

        register_version_manifest_factory(get_version_manifest_summary)

        # 注册 Integrations 工厂
        from sprintcycle.domain.generic.ports.integrations import (
            register_compile_intent_graph_factory,
            register_compile_sprint_graph_factory,
            register_plan_runtime_factory,
        )
        from sprintcycle.infrastructure.adapters.generic.integrations.langgraph.compiler import (
            compile_intent_graph,
            compile_sprint_graph,
            PlanRuntime,
        )

        register_compile_intent_graph_factory(compile_intent_graph)
        register_compile_sprint_graph_factory(compile_sprint_graph)

        def create_plan_runtime(**kwargs):
            return PlanRuntime(**kwargs)

        register_plan_runtime_factory(create_plan_runtime)

        # 获取状态存储
        from sprintcycle.domain.generic.ports.state_store import get_state_store
        self._state_store = get_state_store()
        
        # 初始化 config service
        self._config_service = ConfigService(self.project_path)
        
        # 初始化 governance facade
        self._governance = create_governance_facade(
            project_path=self.project_path,
            config=self.config,
        )
        
        # 初始化 suggestion facade
        self._suggestion = create_suggestion_facade(
            project_path=self.project_path,
            config=self.config,
            evolution_facade=None,
        )
        
        # 初始化 Platform Launch Service
        from sprintcycle.domain.generic.ports.deploy import create_platform_launch_service
        self._platform_launch = create_platform_launch_service()
        
        # 初始化 Dashboard 服务
        self._dashboard_views = DashboardViewService(project_path=self.project_path)
        self._dashboard_workbench = DashboardWorkbenchService(view_service=self._dashboard_views)
        
        # 初始化 Repair Orchestration（需要先于 LifecycleDelivery）
        self._repair_orchestration = RepairOrchestrationService(
            observability=self._observability,
        )
        
        # 初始化 Lifecycle Contract（需要先于 LifecycleDelivery）
        self._lifecycle_contract = LifecycleContractAssemblyService(
            project_path=self.project_path,
            config=self.config,
        )
        
        # 初始化 application 服务
        self._execution_lifecycle = ExecutionLifecycleService(
            project_path=self.project_path,
            config=self.config,
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            state_store=self._state_store,
            hooks=self._hooks,
        )
        
        self._observability_service = ObservabilityService(
            observability=self._observability,
            state_store=self._state_store,
        )
        
        self._platform_summary = PlatformSummaryService(
            project_path=self.project_path,
            dashboard_views=self._dashboard_views,
            dashboard_workbench=self._dashboard_workbench,
            state_store=self._state_store,
        )
        
        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=self.project_path,
            config=self.config,
            governance=self._governance,
            hooks=self._hooks,
        )
        
        self._suggestion_application = SuggestionApplicationService(
            suggestion=self._suggestion,
            governance=self._governance,
            version_registry=self._evolution_registry,
        )
        
        from sprintcycle.domain.core.governance.promotion_policy import PromotionPolicy
        self._lifecycle_evolution = LifecycleEvolutionService(
            observability=self._observability,
            runtime_registry=self._runtime_registry,
            promotion_policy=PromotionPolicy(),
        )
        
        self._lifecycle_delivery = LifecycleDeliveryService(
            project_path=self.project_path,
            runtime_registry=self._runtime_registry,
            governance_orchestration=self._governance_orchestration,
            lifecycle_evolution=self._lifecycle_evolution,
            repair_orchestration=self._repair_orchestration,
            platform_launch=self._platform_launch,
            runtime_latest=lambda: self._execution_lifecycle.runtime_latest(),
            observability_trace=lambda eid: self._observability_service.trace(eid),
            observe_execution=lambda eid: self._execution_lifecycle.execution_detail(eid),
            deploy_view=lambda: self._dashboard_views.deploy_view({}),
            lifecycle_contract=lambda rid: self._lifecycle_contract.assembly(rid),
            evaluate_promotion=lambda eid, **kwargs: self._lifecycle_evolution.promote(eid, **kwargs),
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
    
    # ===== Configuration Service Methods =====
    
    def load_config(self) -> Dict[str, Any]:
        return self._config_service.load_config()
    
    def save_config(self, config: Dict[str, Any]) -> None:
        return self._config_service.save_config(config)
    
    def add_config_history(self, updates: Dict[str, Any], source: str = "api") -> None:
        return self._config_service.add_to_history(updates, source)
    
    def get_config_history(self) -> List[Dict[str, Any]]:
        return self._config_service.get_history()
    
    def get_config_schema(self) -> Dict[str, Any]:
        return ConfigService.get_schema()

    # ===== Public API 方法 =====

    def diagnose(self, execution_id: str = "") -> Any:
        """运行项目或执行诊断"""
        from sprintcycle.infrastructure.adapters.generic.observability.diagnostics.provider import ProjectDiagnostic
        from sprintcycle.application.dto.results import DiagnoseResult

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
        from sprintcycle.domain.generic.interfaces import ExecutionStatus
        from sprintcycle.infrastructure.adapters.core.execution.state_store.state_store import get_state_store
        from sprintcycle.application.dto.results import StopResult

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
        from sprintcycle.infrastructure.adapters.core.execution.state_store.state_store import get_state_store
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
