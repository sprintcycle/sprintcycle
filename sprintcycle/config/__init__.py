"""
Config 模块 - 统一配置管理

v0.9.1 拆分结构：
- runtime_config.py: RuntimeConfig + 工具函数
- llm_config.py: LLMConfig + 兼容别名
- sprintcycle_config.py: SprintCycleConfig, CodingConfig, EvolutionRunConfig
- manager.py: ConfigManager
"""

from .runtime_config import RuntimeConfig
from .llm_config import LLMConfig, CodingLLMConfig, CodingClaudeConfig, EvolutionLLMConfig
from .sprintcycle_config import (
    CodingConfig,
    EvolutionRunConfig,
    SprintCycleConfig,
    load_config_from_env,
    validate_config,
)
from .manager import ConfigManager, get_config_manager, reset_config_manager

__all__ = [
    "RuntimeConfig",
    "ConfigManager",
    "get_config_manager",
    "reset_config_manager",
    "CodingConfig",
    "LLMConfig",
    "CodingLLMConfig",
    "CodingClaudeConfig",
    "EvolutionLLMConfig",
    "EvolutionRunConfig",
    "SprintCycleConfig",
    "load_config_from_env",
    "validate_config",
]
