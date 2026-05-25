"""Lifecycle handler - API methods for lifecycle operations."""

from __future__ import annotations

from typing import Any

from .services import ServiceAggregator


class LifecycleHandler:
    """Handler for lifecycle contract-related API methods."""

    def __init__(self, services: ServiceAggregator):
        self._services = services

    def lifecycle_contract(self, execution_id: str, limit: int = 200) -> Any:
        return self._services.lifecycle_contract.lifecycle_contract(execution_id, limit=limit)

    def evaluate_sprint_contract(self, payload: Any) -> Any:
        return self._services.lifecycle_contract.evaluate_sprint_contract(payload)

    async def deploy_lifecycle(self) -> Any:
        return await self._services.lifecycle_delivery.deploy_lifecycle()

    def evolution_overview(self) -> Any:
        return self._services.lifecycle_evolution.overview()

    def evolution_overview_cli(self) -> str:
        return self._services.lifecycle_evolution.overview_cli()

    def list_evolution_versions(self, target: str = None, limit: int = 20) -> Any:
        return self._services.evolution_version.list_versions(target=target, limit=limit)

    def get_evolution_version(self, version_id: str) -> Any:
        return self._services.evolution_version.get_version(version_id)
