"""
Config 模块 - 统一配置管理

提供配置加载、合并和访问功能。
"""

from .manager import (
    RuntimeConfig,
    ConfigManager,
    get_config_manager,
    reset_config_manager,
)

__all__ = [
    "RuntimeConfig",
    "ConfigManager",
    "get_config_manager",
    "reset_config_manager",
]
