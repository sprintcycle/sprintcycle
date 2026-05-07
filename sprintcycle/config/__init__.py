"""
Config 模块 - 统一配置管理

推荐导入::

    from sprintcycle.config import RuntimeConfig

架构：

- ``dynaconf_app.build_dynaconf``：多源合并、``SPRINTCYCLE_*``、dotenv
- ``runtime_config.RuntimeConfig``：Pydantic 校验与默认值；``flatten_sprintcycle_toml`` 映射 TOML 表
- ``manager.ConfigManager``：可选附加配置文件 + 项目根
- ``llm_config.py`` / ``sprintcycle_config.py``：其余结构化配置
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
from .runtime_config import DashboardPortDefaults, RuntimeConfig, flatten_sprintcycle_toml
from .sprintcycle_config import (
    CodingConfig,
    EvolutionRunConfig,
    SprintCycleConfig,
    load_config_from_env,
    validate_config,
)

__all__ = [
    "DashboardPortDefaults",
    "RuntimeConfig",
    "flatten_sprintcycle_toml",
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
