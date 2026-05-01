"""
RuntimeConfig - 运行时核心配置

统一配置入口，所有小 Config 类通过 from_runtime_config 桥接到此配置。

v0.9.1: 删除 from_measurement_config, from_diagnostic_config, from_memory_config, 
        from_pipeline_config 等桥接方法（对应的 Config 类已删除）
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
import os
import logging

logger = logging.getLogger(__name__)


_DEFAULT_CONFIG = {
    "max_sprints": 10,
    "max_tasks_per_sprint": 5,
    "parallel_tasks": 3,
    "continue_on_error": False,
    "max_variations": 5,
    "evolution_iterations": 3,
    "evolution_enabled": True,
    "state_dir": ".sprintcycle/state",
    "log_level": "INFO",
    "log_dir": "./logs",
    "api_base": None,
    "api_key": None,
    "api_timeout": 60,
    "llm_provider": "deepseek",
    "llm_model": "deepseek-reasoner",
    "llm_temperature": 0.7,
    "llm_max_tokens": 2048,
    "dry_run": False,
    "verbose": False,
    "quiet": False,
}


def _resolve_env_var(value: str) -> str:
    if value and isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        var_name = value[2:-1]
        return os.getenv(var_name, value)
    return value


def _mask_sensitive(value: str) -> str:
    if not value:
        return value
    if len(value) <= 6:
        return "***"
    return "***"


@dataclass
class RuntimeConfig:
    """
    运行时配置
    
    v0.9.1 统一配置：所有小 Config 类已内联到此类，不再需要 from_*_config 桥接方法
    """
    max_sprints: int = 10
    max_tasks_per_sprint: int = 5
    parallel_tasks: int = 3
    continue_on_error: bool = False
    max_variations: int = 5
    evolution_iterations: int = 3
    evolution_enabled: bool = True
    state_dir: str = ".sprintcycle/state"
    log_level: str = "INFO"
    log_dir: str = "./logs"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    api_timeout: int = 60
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-reasoner"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    convergence_threshold: int = 2
    min_improvement: float = 0.01
    quality_gate_enabled: bool = True
    min_correctness: float = 0.5
    min_overall: float = 0.4
    auto_commit: bool = True
    evolution_cache_dir: str = "./evolution_cache"
    test_command: str = "python -m pytest tests/ -v --tb=short"
    coverage_command: str = "python -m pytest --cov --cov-report=json"
    complexity_threshold: int = 10
    diagnostic_timeout: int = 300
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False
    
    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            max_sprints=int(os.getenv("SPRINTCYCLE_MAX_SPRINTS", 10)),
            parallel_tasks=int(os.getenv("SPRINTCYCLE_PARALLEL_TASKS", 3)),
            state_dir=os.getenv("SPRINTCYCLE_STATE_DIR", ".sprintcycle/state"),
            log_level=os.getenv("SPRINTCYCLE_LOG_LEVEL", "INFO"),
            log_dir=os.getenv("SPRINTCYCLE_LOG_DIR", "./logs"),
            api_base=os.getenv("SPRINTCYCLE_API_BASE"),
            api_key=os.getenv("SPRINTCYCLE_API_KEY"),
            evolution_enabled=os.getenv("SPRINTCYCLE_EVOLUTION_ENABLED", "true").lower() == "true",
            dry_run=os.getenv("SPRINTCYCLE_DRY_RUN", "false").lower() == "true",
            llm_provider=os.getenv("SPRINTCYCLE_LLM_PROVIDER", "deepseek"),
            llm_model=os.getenv("SPRINTCYCLE_LLM_MODEL", "deepseek-reasoner"),
            llm_temperature=float(os.getenv("SPRINTCYCLE_LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("SPRINTCYCLE_LLM_MAX_TOKENS", "2048")),
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeConfig":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields and v is not None}
        return cls(**filtered)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_sprints": self.max_sprints,
            "max_tasks_per_sprint": self.max_tasks_per_sprint,
            "parallel_tasks": self.parallel_tasks,
            "continue_on_error": self.continue_on_error,
            "max_variations": self.max_variations,
            "evolution_iterations": self.evolution_iterations,
            "evolution_enabled": self.evolution_enabled,
            "state_dir": self.state_dir,
            "log_level": self.log_level,
            "log_dir": self.log_dir,
            "api_base": self.api_base,
            "api_key": self.api_key,
            "api_timeout": self.api_timeout,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,
            "convergence_threshold": self.convergence_threshold,
            "min_improvement": self.min_improvement,
            "quality_gate_enabled": self.quality_gate_enabled,
            "min_correctness": self.min_correctness,
            "min_overall": self.min_overall,
            "auto_commit": self.auto_commit,
            "evolution_cache_dir": self.evolution_cache_dir,
            "dry_run": self.dry_run,
            "verbose": self.verbose,
            "quiet": self.quiet,
        }
    
    def to_dict_non_default(self) -> Dict[str, Any]:
        result = {}
        for key, value in self.to_dict().items():
            default = _DEFAULT_CONFIG.get(key)
            if value is not None and value != default:
                result[key] = value
            elif key in ('continue_on_error', 'dry_run', 'verbose', 'quiet'):
                if value is False and default is True:
                    result[key] = value
        return result
    
    @classmethod
    def merge(cls, *configs: Union["RuntimeConfig", Dict[str, Any], None]) -> "RuntimeConfig":
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
    
    def update(self, **kwargs) -> "RuntimeConfig":
        return self.merge(self, kwargs)
