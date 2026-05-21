"""RuntimeConfig compatibility layer for SprintCycle.

The project historically expects a ``RuntimeConfig`` object with attribute access
and a few constructor helpers. This module provides that surface on top of the
Dynaconf-backed configuration loader.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from .dynaconf_app import build_dynaconf


def _mask_sensitive(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= 8:
        return "***"
    return f"{text[:3]}***{text[-2:]}"


def _resolve_env_var(value: str) -> str:
    if value.startswith("${") and value.endswith("}"):
        key = value[2:-1]
        import os

        return os.environ.get(key, value)
    return value


class RuntimeConfig:
    """Runtime configuration backed by an attribute-accessible dict."""

    def __init__(self, _data: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        if _data is not None:
            self._data = dict(_data)
        else:
            self._data = {}
        self._data.setdefault("hitl_enabled", False)
        self._data.setdefault("cache_backend", "diskcache")
        self._data.setdefault("cache_default_ttl_hours", 24)
        self._data.setdefault("cache_max_entries", 1000)
        self._data.setdefault("cache_enabled", True)
        self._data.setdefault("max_sprints", 10)
        self._data.setdefault("max_tasks_per_sprint", 5)
        self._data.setdefault("dry_run", False)
        self._data.setdefault("evolution_enabled", True)
        self._data.setdefault("quality_level", "L2")
        self._data.setdefault("storage_backend", "sqlite")
        self._data.setdefault("governance_downgrade_errors_to_warnings", True)
        self._data.setdefault("governance_review_browser_e2e", False)
        self._data.setdefault("governance_review_visual", False)
        self._data.setdefault("governance_cli_emit_events", False)
        self._data.setdefault("governance_history_max_files", 50)
        self._data.setdefault("governance_argv_entry_points", True)
        self._data.setdefault("governance_planning_validate_release_plan", True)
        self._data.setdefault("governance_pluggy_argv", False)
        self._data.update(kwargs)
        # Validate governance_block_on
        valid_block_on_values = {"always", "on_error", "none"}
        raw = self._data.get("governance_block_on")
        if raw is not None and raw not in valid_block_on_values:
            self._data["governance_block_on"] = "none"

    def __getattr__(self, item: str) -> Any:
        if item.startswith("_"):
            raise AttributeError(item)
        return self._data.get(item)

    def __setattr__(self, key: str, value: Any) -> None:
        if key == "_data":
            super().__setattr__(key, value)
        else:
            self._data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def update(self, **kwargs: Any) -> "RuntimeConfig":
        data = self.to_dict()
        data.update(kwargs)
        return RuntimeConfig(data)

    @classmethod
    def merge(cls, *args: Any, **kwargs: Any) -> "RuntimeConfig":
        base: Dict[str, Any] = {}
        for arg in args:
            if isinstance(arg, dict):
                base.update(arg)
            elif isinstance(arg, RuntimeConfig):
                base.update(arg.to_dict())
        base.update(kwargs)
        return RuntimeConfig(base)

    @classmethod
    def from_project(cls, project_path: str) -> "RuntimeConfig":
        settings = build_dynaconf(project_path)
        return cls(_dynaconf_to_dict(settings))

    @classmethod
    def from_dynaconf(cls, project_path: str, extra_files: Optional[Sequence[str]] = None) -> "RuntimeConfig":
        settings = build_dynaconf(project_path, extra_files=extra_files)
        return cls(_dynaconf_to_dict(settings))

    def effective_quality_level(self) -> str:
        from .quality import resolve_effective_quality_level

        profile = str(self._data.get("quality_profile", "default") or "default")
        level = str(self._data.get("quality_level", "L2") or "L2")
        return resolve_effective_quality_level(profile, level)


def _dynaconf_to_dict(settings: Any) -> Dict[str, Any]:
    try:
        data = settings.to_dict()
        return dict(data) if isinstance(data, dict) else {}
    except Exception:
        return {}


__all__ = ["RuntimeConfig", "_mask_sensitive", "_resolve_env_var"]
