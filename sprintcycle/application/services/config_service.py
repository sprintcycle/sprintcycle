"""Configuration service for SprintCycle.

Handles runtime configuration loading, saving, and history tracking.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from sprintcycle.domain.ports.config import RuntimeConfigProtocol, get_runtime_config


class ConfigService:
    """Service for managing SprintCycle runtime configuration.

    Handles loading, saving, and tracking history of configuration changes.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).expanduser().resolve()
        self.config_history: List[Dict[str, Any]] = []
        self.runtime_yaml = self.project_path / "sprintcycle.runtime.yaml"

    def _get_runtime_config(self) -> RuntimeConfigProtocol:
        """获取运行时配置（通过端口工厂注入）"""
        return get_runtime_config(str(self.project_path))

    def load_config(self) -> Dict[str, Any]:
        """Load and normalize runtime configuration.

        Returns:
            Dict[str, Any]: Normalized configuration dictionary with lowercase keys.
        """
        try:
            cfg = self._get_runtime_config()
            raw = cfg.to_dict()
            if isinstance(raw, dict) and "PROJECT" in raw and isinstance(raw["PROJECT"], dict):
                flat = {k.lower(): v for k, v in raw["PROJECT"].items()}
                for k, v in raw.items():
                    if k != "PROJECT":
                        flat[k.lower()] = v
                return flat
            if isinstance(raw, dict):
                return {k.lower(): v for k, v in raw.items()}
            return raw
        except Exception:
            return {}

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to runtime.yaml file.

        Args:
            config: Configuration dictionary to save.
        """
        try:
            self.runtime_yaml.parent.mkdir(parents=True, exist_ok=True)
            existing = {}
            if self.runtime_yaml.exists():
                import yaml
                existing = yaml.safe_load(self.runtime_yaml.read_text(encoding="utf-8")) or {}
            existing.update(config)
            import yaml
            self.runtime_yaml.write_text(yaml.dump(existing, default_flow_style=False), encoding="utf-8")
        except Exception:
            pass

    def add_to_history(self, updates: Dict[str, Any], source: str = "api") -> None:
        """Add a configuration change to history.

        Args:
            updates: Dictionary of configuration updates.
            source: Source of the change (e.g., "api", "import").
        """
        self.config_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "updates": updates,
        })

    def get_history(self) -> List[Dict[str, Any]]:
        """Get configuration change history.

        Returns:
            List[Dict[str, Any]]: List of historical configuration changes.
        """
        return list(self.config_history)

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get configuration schema for validation.

        Returns:
            Dict[str, Any]: JSON schema-like structure for configuration.
        """
        return {
            "type": "object",
            "properties": {
                "project_path": {"type": "string"},
                "quality_level": {"type": "string"},
                "parallel_tasks": {"type": "integer"},
                "max_sprints": {"type": "integer"},
            },
        }
