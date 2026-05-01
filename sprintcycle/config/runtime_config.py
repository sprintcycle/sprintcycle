"""
RuntimeConfig - 运行时核心配置

v0.9.2: 使用 pydantic-settings BaseSettings 自动从环境变量加载
"""

import os
import logging
from typing import Optional, Dict, Any, Union

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

logger = logging.getLogger(__name__)


# ============================================================
# Default config values
# ============================================================

_DEFAULT_CONFIG: Dict[str, Any] = {
    "max_sprints": 10, "max_tasks_per_sprint": 5, "parallel_tasks": 3,
    "continue_on_error": False, "max_variations": 5, "evolution_iterations": 3,
    "evolution_enabled": True, "state_dir": ".sprintcycle/state",
    "log_level": "INFO", "log_dir": "./logs", "api_base": None, "api_key": None,
    "api_timeout": 60, "llm_provider": "deepseek", "llm_model": "deepseek-reasoner",
    "llm_temperature": 0.7, "llm_max_tokens": 2048, "convergence_threshold": 2,
    "min_improvement": 0.01, "quality_gate_enabled": True, "min_correctness": 0.5,
    "min_overall": 0.4, "auto_commit": True, "evolution_cache_dir": "./evolution_cache",
    "test_command": "python -m pytest tests/ -v --tb=short",
    "coverage_command": "python -m pytest --cov --cov-report=json",
    "complexity_threshold": 10, "diagnostic_timeout": 300,
    "dry_run": False, "verbose": False, "quiet": False,
}


def _resolve_env_var(value: str) -> str:
    """解析 ${VAR_NAME} 形式的环境变量引用"""
    if value and isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.getenv(var_name, value)
    return value


def _mask_sensitive(value: str) -> str:
    """遮蔽敏感信息"""
    if not value:
        return value
    if len(value) <= 6:
        return "***"
    return "***"


def _get_api_key_from_env() -> Optional[str]:
    """从环境变量获取 API key（向后兼容）"""
    return os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")


def _get_api_base_from_env() -> Optional[str]:
    """从环境变量获取 API base（向后兼容）"""
    return os.getenv("LLM_API_BASE") or os.getenv("SPRINTCYCLE_API_BASE")


# ============================================================
# RuntimeConfig - pydantic-settings BaseSettings
# ============================================================

class RuntimeConfig(BaseSettings):
    """
    运行时核心配置

    v0.9.2: 使用 pydantic-settings BaseSettings 自动从环境变量加载
    所有配置通过环境变量 SPRINTCYCLE_* 前缀覆盖
    """
    model_config = SettingsConfigDict(
        env_prefix="SPRINTCYCLE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 执行配置
    max_sprints: int = 10
    max_tasks_per_sprint: int = 5
    parallel_tasks: int = 3
    continue_on_error: bool = False
    # 进化配置
    max_variations: int = 5
    evolution_iterations: int = 3
    evolution_enabled: bool = True
    # 存储配置
    state_dir: str = ".sprintcycle/state"
    log_level: str = "INFO"
    log_dir: str = "./logs"
    # API 配置
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    api_timeout: int = 60
    # LLM 配置
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-reasoner"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    # 质量门配置
    convergence_threshold: int = 2
    min_improvement: float = 0.01
    quality_gate_enabled: bool = True
    min_correctness: float = 0.5
    min_overall: float = 0.4
    # 工具配置
    auto_commit: bool = True
    evolution_cache_dir: str = "./evolution_cache"
    test_command: str = "python -m pytest tests/ -v --tb=short"
    coverage_command: str = "python -m pytest --cov --cov-report=json"
    complexity_threshold: int = 10
    diagnostic_timeout: int = 300
    # 执行选项
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False

    @model_validator(mode="before")
    @classmethod
    def _resolve_compat(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """处理向后兼容的环境变量和 ${VAR} 形式的环境变量引用"""
        if not isinstance(values, dict):
            return values
        
        # 兼容旧版环境变量名
        if not values.get("api_key"):
            values["api_key"] = _get_api_key_from_env()
        if not values.get("api_base"):
            values["api_base"] = _get_api_base_from_env()
        
        # 解析 ${VAR} 形式的环境变量引用
        if values.get("api_key") and isinstance(values["api_key"], str):
            values["api_key"] = _resolve_env_var(values["api_key"])
        
        # 兼容 LLM_PROVIDER 和 LLM_MODEL
        env_provider = os.getenv("LLM_PROVIDER")
        if env_provider:
            values["llm_provider"] = env_provider
        env_model = os.getenv("LLM_MODEL")
        if env_model:
            values["llm_model"] = env_model
        
        return values

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()

    def to_dict_non_default(self) -> Dict[str, Any]:
        """转换为字典，只包含非默认值的字段"""
        result: Dict[str, Any] = {}
        for key, value in self.to_dict().items():
            default = _DEFAULT_CONFIG.get(key)
            if value is not None and value != default:
                result[key] = value
            elif key in ('continue_on_error', 'dry_run', 'verbose', 'quiet'):
                if value is False and default is True:
                    result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        """从字典加载配置"""
        filtered = {k: v for k, v in data.items() if v is not None}
        return cls(**filtered)

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        """从环境变量加载配置（pydantic-settings 自动处理）"""
        return cls()

    @classmethod
    def merge(cls, *configs: Union["RuntimeConfig", Dict[str, Any], None]) -> "RuntimeConfig":
        """合并多个配置源"""
        merged: Dict[str, Any] = {}
        for config in configs:
            if config is None:
                continue
            if isinstance(config, cls):
                config_dict = config.to_dict_non_default()
            elif isinstance(config, dict):
                config_dict = config
            else:
                continue
            merged.update(config_dict)
        return cls(**merged) if merged else cls()

    def update(self, **kwargs: Any) -> "RuntimeConfig":
        """更新配置（返回新实例）"""
        return self.merge(self, kwargs)
