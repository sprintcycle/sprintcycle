"""
Config 模块 - 统一配置管理

提供配置加载、合并和访问功能。
"""

from .manager import (
    RuntimeConfig,
    ConfigManager,
    get_config_manager,
    reset_config_manager,
    CodingConfig,
    LLMConfig,
    CodingLLMConfig,  # compat alias
    CodingClaudeConfig,  # compat alias
    EvolutionLLMConfig,  # compat alias
    EvolutionRunConfig,
    SprintCycleConfig,
    load_config_from_env,
    validate_config,
)

# EvolutionConfig in manager.py is now EvolutionRunConfig
# EvolutionConfig in prd/models.py is the PRD evolution config (different class)

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
