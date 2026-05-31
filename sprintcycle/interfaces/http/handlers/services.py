"""Service aggregator for HTTP handlers.

ServiceAggregator 只依赖 application 层服务，不直接依赖 domain 层。
"""

from __future__ import annotations

from typing import Any

from sprintcycle.application.composition.di_container import container


class ServiceAggregator:
    """Aggregates all application services for HTTP handlers.

    只依赖 application 层服务，不直接依赖 domain 层。
    """

    def __init__(self, project_path: str):
        self.project_path = project_path
        
        # 确保容器配置正确
        from sprintcycle.application.composition.di_container import create_container
        create_container(project_path=project_path)
        
        self._application_services = container.application_services
        
    @property
    def execution_lifecycle(self):
        return self._application_services.execution_lifecycle_service()

    @property
    def dashboard_views(self):
        return self._application_services.dashboard_view_service()

    @property
    def dashboard_workbench(self):
        return self._application_services.dashboard_workbench_service()

    @property
    def platform_summary(self):
        return self._application_services.platform_summary_service()

    @property
    def governance_orchestration(self):
        return self._application_services.governance_orchestration_service()

    @property
    def lifecycle_root(self):
        return self._application_services.lifecycle_root_service()

    @property
    def web_lifecycle(self):
        return self._application_services.web_lifecycle_service()

    @property
    def runtime_lifecycle(self):
        return self._application_services.runtime_lifecycle_service()

    @property
    def governance_lifecycle(self):
        return self._application_services.governance_lifecycle_service()

    @property
    def promotion_lifecycle(self):
        return self._application_services.promotion_lifecycle_service()

    @property
    def recovery_lifecycle(self):
        return self._application_services.recovery_lifecycle_service()

    @property
    def repair_orchestration(self):
        return self._application_services.repair_orchestration_service()

    @property
    def observability_service(self):
        return self._application_services.observability_service()

    @property
    def management_overview(self):
        return self._application_services.management_overview_service()

    @property
    def suggestion_application(self):
        return self._application_services.suggestion_application_service()

    @property
    def lifecycle_evolution(self):
        return self._application_services.lifecycle_evolution_service()

    @property
    def evolution_version(self):
        return self._application_services.evolution_version_service()

    @property
    def config_service(self):
        return self._application_services.config_service()

    @property
    def suggestion(self):
        return self._application_services.suggestion_facade_service().facade

    @property
    def observability(self):
        return container.observability.observability_facade()

    @property
    def runtime_registry(self):
        return container.runtime_config_container.runtime_registry(
            config=container.runtime_config_container.runtime_config(project_path=self.project_path)
        )


def create_service_aggregator(project_path: str) -> ServiceAggregator:
    """Factory function to create service aggregator."""
    return ServiceAggregator(project_path)
