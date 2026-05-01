"""
ConfigManager - 配置文件管理器

负责加载和合并配置文件、环境变量。
配置类已拆分到：
- runtime_config.py: RuntimeConfig
- llm_config.py: LLMConfig
- sprintcycle_config.py: SprintCycleConfig, CodingConfig, EvolutionRunConfig
"""

from typing import Optional, Dict, Any
from pathlib import Path
import logging

from .runtime_config import RuntimeConfig

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._runtime_config: Optional[RuntimeConfig] = None
        self._file_config: Dict[str, Any] = {}
        if config_file and Path(config_file).exists():
            self._load_file_config()
    
    def _load_file_config(self) -> None:
        import yaml
        import json
        if not self.config_file:
            return
        path = Path(self.config_file)
        try:
            if path.suffix in (".yaml", ".yml"):
                with open(path, encoding="utf-8") as f:
                    self._file_config = yaml.safe_load(f) or {}
            elif path.suffix == ".json":
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    self._file_config = data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            self._file_config = {}
    
    def get_runtime(self) -> RuntimeConfig:
        if self._runtime_config is None:
            self._runtime_config = RuntimeConfig.merge(
                RuntimeConfig(),
                self._file_config,
                RuntimeConfig.from_env(),
            )
        return self._runtime_config
    
    def update_runtime(self, **kwargs) -> RuntimeConfig:
        runtime = self.get_runtime()
        self._runtime_config = runtime.update(**kwargs)
        return self._runtime_config
    
    def get(self, key: str, default: Any = None) -> Any:
        runtime = self.get_runtime()
        if hasattr(runtime, key):
            return getattr(runtime, key)
        keys = key.split(".")
        value: Any = self._file_config
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
        config_data = {**self._file_config, **runtime.to_dict()}
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


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


# Re-export for backward compatibility
from .runtime_config import RuntimeConfig, _resolve_env_var, _mask_sensitive  # noqa: F401, E402
from .llm_config import LLMConfig, CodingLLMConfig, CodingClaudeConfig, EvolutionLLMConfig  # noqa: F401, E402
from .sprintcycle_config import (  # noqa: F401, E402
    CodingConfig, EvolutionRunConfig, SprintCycleConfig,
    load_config_from_env, validate_config,
)
