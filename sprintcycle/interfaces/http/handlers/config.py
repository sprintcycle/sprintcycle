"""Config handler - API methods for configuration management operations."""

from __future__ import annotations

from typing import Any, Dict, List

from .services import ServiceAggregator


class ConfigHandler:
    """Handler for configuration-related API methods."""

    def __init__(self, services: ServiceAggregator):
        self._services = services

    def load_config(self) -> Dict[str, Any]:
        return self._services.config_service.load_config()

    def save_config(self, config: Dict[str, Any]) -> None:
        return self._services.config_service.save_config(config)

    def add_config_history(self, updates: Dict[str, Any], source: str = "api") -> None:
        return self._services.config_service.add_to_history(updates, source)

    def get_config_history(self) -> List[Dict[str, Any]]:
        return self._services.config_service.get_history()

    def get_config_schema(self) -> Dict[str, Any]:
        from sprintcycle.application.services.config_service import ConfigService
        return ConfigService.get_schema()
