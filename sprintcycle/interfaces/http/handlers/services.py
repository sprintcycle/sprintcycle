"""Service aggregator for HTTP handlers.

Aggregates all application services needed by HTTP handlers.
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
from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
from sprintcycle.infrastructure.adapters.generic.observability.facade import ObservabilityFacade
from sprintcycle.infrastructure.adapters.generic.config.runtime_registry import RuntimeRegistry
from sprintcycle.infrastructure.adapters.core.evolution.evolution_registry_access import create_evolution_registry
from sprintcycle.domain.generic.interfaces.hooks import HookRegistry
from sprintcycle.domain.core.governance.core.facade import GovernanceFacade, create_governance_facade
from sprintcycle.domain.core.governance.suggestion import SuggestionFacade, create_suggestion_facade


class ServiceAggregator:
    """Aggregates all application services for HTTP handlers."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        
        self._config = RuntimeConfig.from_project(project_path)
        self._observability = ObservabilityFacade()
        self._runtime_registry = RuntimeRegistry()
        self._hooks = HookRegistry()
        self._evolution_registry = create_evolution_registry(self._config)

        self._init_state_store()
        
        self._config_service = ConfigService(project_path)
        
        self._governance = create_governance_facade(
            project_path=project_path,
            config=self._config,
        )
        
        self._suggestion = create_suggestion_facade(
            project_path=project_path,
            config=self._config,
            evolution_facade=None,
        )

        from sprintcycle.domain.generic.ports.deploy import create_platform_launch_service
        self._platform_launch = create_platform_launch_service()

        self._dashboard_views = DashboardViewService(project_path=project_path)
        self._dashboard_workbench = DashboardWorkbenchService(view_service=self._dashboard_views)

        self._repair_orchestration = RepairOrchestrationService(
            observability=self._observability,
        )

        self._execution_lifecycle = ExecutionLifecycleService(
            project_path=project_path,
            config=self._config,
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
            project_path=project_path,
            dashboard_views=self._dashboard_views,
            dashboard_workbench=self._dashboard_workbench,
            state_store=self._state_store,
        )

        self._governance_orchestration = GovernanceOrchestrationService(
            project_path=project_path,
            config=self._config,
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

        from sprintcycle.application.services.lifecycle.web_lifecycle_orchestration_service import WebLifecycleOrchestrationService
        self._web_lifecycle = WebLifecycleOrchestrationService(
            project_path=project_path,
            start_execution_run=lambda *args, **kwargs: self._execution_lifecycle.start_execution_run(*args, **kwargs),
            runtime_lifecycle=lambda eid: self._execution_lifecycle.status(eid),
            observability_trace=lambda eid: self._observability_service.trace(eid),
            evaluate_sprint_contract=lambda payload: self._lifecycle_contract.evaluate_sprint_contract(payload),
        )

        self._lifecycle_contract = LifecycleContractAssemblyService(
            project_path=project_path,
            execution_detail=lambda eid, limit: self._execution_lifecycle.execution_detail(eid, limit=limit),
            runtime_lifecycle=lambda eid: self._execution_lifecycle.status(eid),
            suggestion_overview_payload=lambda: self._management_overview.suggestion_overview(),
            governance_orchestration=self._governance_orchestration,
            lifecycle_evolution=self._lifecycle_evolution,
            web_lifecycle=self._web_lifecycle,
            deliver_runtime_governance_promotion=lambda eid, **kwargs: self._lifecycle_delivery.deliver_runtime_governance_promotion(eid, **kwargs),
        )

        self._lifecycle_delivery = LifecycleDeliveryService(
            project_path=project_path,
            runtime_registry=self._runtime_registry,
            governance_orchestration=self._governance_orchestration,
            lifecycle_evolution=self._lifecycle_evolution,
            repair_orchestration=self._repair_orchestration,
            platform_launch=self._platform_launch,
            runtime_latest=lambda: self._execution_lifecycle.runtime_latest(),
            observability_trace=lambda eid: self._observability_service.trace(eid),
            observe_execution=lambda eid: self._execution_lifecycle.execution_detail(eid),
            deploy_view=lambda: self._dashboard_views.deploy_view({}),
            lifecycle_contract=lambda rid: self._lifecycle_contract.assemble(rid),
            evaluate_promotion=lambda eid, **kwargs: self._lifecycle_evolution.promote(eid, **kwargs),
        )

        self._evolution_version = EvolutionVersionService(
            config=self._config,
            registry=self._evolution_registry,
        )

        self._management_overview = ManagementOverviewService(
            suggestion=self._suggestion,
            evolution_dashboard=lambda: self._lifecycle_evolution.overview(),
            evolution_cli=lambda: self._lifecycle_evolution.overview_cli(),
        )

    def _init_state_store(self) -> None:
        from sprintcycle.domain.generic.ports.state_store import get_state_store
        self._state_store = get_state_store()

    @property
    def execution_lifecycle(self) -> ExecutionLifecycleService:
        return self._execution_lifecycle

    @property
    def dashboard_views(self) -> DashboardViewService:
        return self._dashboard_views

    @property
    def dashboard_workbench(self) -> DashboardWorkbenchService:
        return self._dashboard_workbench

    @property
    def platform_summary(self) -> PlatformSummaryService:
        return self._platform_summary

    @property
    def governance_orchestration(self) -> GovernanceOrchestrationService:
        return self._governance_orchestration

    @property
    def lifecycle_contract(self) -> LifecycleContractAssemblyService:
        return self._lifecycle_contract

    @property
    def lifecycle_delivery(self) -> LifecycleDeliveryService:
        return self._lifecycle_delivery

    @property
    def repair_orchestration(self) -> RepairOrchestrationService:
        return self._repair_orchestration

    @property
    def observability_service(self) -> ObservabilityService:
        return self._observability_service

    @property
    def management_overview(self) -> ManagementOverviewService:
        return self._management_overview

    @property
    def suggestion_application(self) -> SuggestionApplicationService:
        return self._suggestion_application

    @property
    def lifecycle_evolution(self) -> LifecycleEvolutionService:
        return self._lifecycle_evolution

    @property
    def evolution_version(self) -> EvolutionVersionService:
        return self._evolution_version

    @property
    def config_service(self) -> ConfigService:
        return self._config_service

    @property
    def suggestion(self) -> SuggestionFacade:
        return self._suggestion

    @property
    def observability(self) -> ObservabilityFacade:
        return self._observability

    @property
    def runtime_registry(self) -> RuntimeRegistry:
        return self._runtime_registry


def create_service_aggregator(project_path: str) -> ServiceAggregator:
    """Factory function to create service aggregator."""
    return ServiceAggregator(project_path)
