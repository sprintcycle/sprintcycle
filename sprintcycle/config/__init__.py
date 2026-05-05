"""
Config 模块 - 统一配置管理

推荐导入（对外稳定入口）::

    from sprintcycle.config import RuntimeConfig

v0.9.2 架构：
- runtime_config.py: RuntimeConfig（pydantic-settings 或 dataclass）
- llm_config.py: LLMConfig（pydantic 或 dataclass）
- sprintcycle_config.py: SprintCycleConfig, CodingConfig, EvolutionRunConfig（dataclass）
- manager.py: ConfigManager

迁移到 pydantic:
- pydantic-settings: RuntimeConfig 自动从环境变量加载
- pydantic: LLMConfig 提供类型安全
"""

from .llm_config import CodingClaudeConfig, CodingLLMConfig, EvolutionLLMConfig, LLMConfig
from .manager import ConfigManager, get_config_manager, reset_config_manager
from .quality import (
    QUALITY_LEVELS,
    QUALITY_PROFILES,
    QualityProfile,
    normalize_quality_level,
    normalize_quality_profile,
    resolve_effective_quality_level,
    runs_architecture_guard,
    runs_coverage_gate,
    runs_pytest,
    runs_static_gate,
)
from .runtime_config import RuntimeConfig
from .sprintcycle_config import (
    CodingConfig,
    EvolutionRunConfig,
    SprintCycleConfig,
    load_config_from_env,
    validate_config,
)
from .toml_loader import flatten_sprintcycle_toml, load_sprintcycle_toml

__all__ = [
    "RuntimeConfig",
    "QUALITY_LEVELS",
    "QUALITY_PROFILES",
    "QualityProfile",
    "normalize_quality_level",
    "normalize_quality_profile",
    "resolve_effective_quality_level",
    "runs_architecture_guard",
    "runs_coverage_gate",
    "runs_pytest",
    "runs_static_gate",
    "flatten_sprintcycle_toml",
    "load_sprintcycle_toml",
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
