"""RuntimeConfig compatibility layer for SprintCycle.

The project historically expects a ``RuntimeConfig`` object with attribute access
and a few constructor helpers. This module provides that surface on top of the
Dynaconf-backed configuration loader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class RuntimeConfig:
    _data: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, item: str) -> Any:
        try:
            return self._data[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

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

    def merge(self, *_args: Any, **kwargs: Any) -> "RuntimeConfig":
        data = self.to_dict()
        data.update(kwargs)
        return RuntimeConfig(data)

    @classmethod
    def from_project(cls, project_path: str) -> "RuntimeConfig":
        settings = build_dynaconf(project_path)
        return cls(_dynaconf_to_dict(settings))

    @classmethod
    def from_dynaconf(cls, project_path: str, extra_files: Optional[Sequence[str]] = None) -> "RuntimeConfig":
        settings = build_dynaconf(project_path, extra_files=extra_files)
        return cls(_dynaconf_to_dict(settings))


def _dynaconf_to_dict(settings: Any) -> Dict[str, Any]:
    try:
        data = settings.to_dict()
        return dict(data) if isinstance(data, dict) else {}
    except Exception:
        return {}


__all__ = ["RuntimeConfig", "_mask_sensitive", "_resolve_env_var"]
