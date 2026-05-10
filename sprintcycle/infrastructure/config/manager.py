"""
统一配置管理器：Dynaconf 多源合并 + ``RuntimeConfig`` 校验。

可选 YAML/JSON 文件通过 ``extra_files`` 在 ``sprintcycle.toml`` 之后加载；``SPRINTCYCLE_*`` 覆盖文件。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .llm_config import LLMConfig
from .runtime_config import RuntimeConfig


class ConfigManager:
    """管理 ``RuntimeConfig`` 的加载与内存更新。"""

    def __init__(self, config_file: Optional[str] = None, project_path: str = "."):
        self.config_file = config_file
        self._project_path = project_path
        self._runtime_config: Optional[RuntimeConfig] = None

    def _extra_files(self) -> Optional[tuple[str, ...]]:
        if self.config_file and Path(self.config_file).exists():
            return (self.config_file,)
        return None

    def get_runtime(self) -> RuntimeConfig:
        if self._runtime_config is None:
            self._runtime_config = RuntimeConfig.from_dynaconf(
                self._project_path,
                extra_files=self._extra_files(),
            )
        return self._runtime_config

    def update_runtime(self, **kwargs: Any) -> RuntimeConfig:
        runtime = self.get_runtime()
        self._runtime_config = runtime.update(**kwargs)
        return self._runtime_config

    def get(self, key: str, default: Any = None) -> Any:
        runtime = self.get_runtime()
        if hasattr(runtime, key):
            return getattr(runtime, key)
        keys = key.split(".")
        value: Any = runtime.to_dict()
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        runtime = self.get_runtime()
        if hasattr(runtime, key):
            self._runtime_config = runtime.update(**{key: value})

    def save(self, output_path: Optional[str] = None) -> None:
        import yaml

        path = output_path or self.config_file
        if not path:
            raise ValueError("No output path specified")
        runtime = self.get_runtime()
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(runtime.to_dict(), f, default_flow_style=False, allow_unicode=True)


_default_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager(config_file)
    return _default_manager


def reset_config_manager() -> ConfigManager:
    global _default_manager
    _default_manager = ConfigManager()
    return _default_manager


__all__ = [
    "ConfigManager",
    "LLMConfig",
    "RuntimeConfig",
    "get_config_manager",
    "reset_config_manager",
]
