"""
统一配置管理器

合并来源：
- 配置文件 (config.yaml)
- 环境变量
- CLI 参数
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import os
import copy
import logging
import re

logger = logging.getLogger(__name__)


# 默认配置值
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
    """解析环境变量引用 ${VAR_NAME}"""
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


@dataclass
class RuntimeConfig:
    """
    运行时配置
    
    用于执行时的动态配置，支持从多种来源合并。
    """
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
    
    # GEPA 进化专用配置（原 GEPAConfig 字段，v0.9.0 统一）
    convergence_threshold: int = 2
    min_improvement: float = 0.01
    quality_gate_enabled: bool = True
    min_correctness: float = 0.5
    min_overall: float = 0.4
    auto_commit: bool = True
    evolution_cache_dir: str = "./evolution_cache"

    # 执行选项
    dry_run: bool = False
    verbose: bool = False
    quiet: bool = False
    
    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        """
        从环境变量加载配置
        
        环境变量前缀: SPRINTCYCLE_
        """
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
        """
        从字典加载配置
        
        只加载已定义的字段，忽略未知字段。
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields and v is not None}
        return cls(**filtered)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
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
        """转换为字典，只包含非默认值"""
        result = {}
        for key, value in self.to_dict().items():
            default = _DEFAULT_CONFIG.get(key)
            # 包含 None 值和与默认值不同的值
            if value is not None and value != default:
                result[key] = value
            # 包含显式的 False 值（与默认值 False 相同但需要保留）
            elif key in ('continue_on_error', 'dry_run', 'verbose', 'quiet'):
                if value is False and default is True:
                    result[key] = value
        return result
    
    @classmethod
    def merge(cls, *configs: Union["RuntimeConfig", Dict[str, Any], None]) -> "RuntimeConfig":
        """
        合并多个配置源
        
        后面的配置优先覆盖前面的。
        优先级: CLI参数 > 环境变量 > 配置文件 > 默认值
        
        Args:
            configs: 配置对象列表
            
        Returns:
            合并后的配置
        """
        merged: Dict[str, Any] = {}
        
        for config in configs:
            if config is None:
                continue
            
            if isinstance(config, cls):
                # 只取非默认值的字段
                config_dict = config.to_dict_non_default()
            elif isinstance(config, dict):
                config_dict = config
            else:
                continue
            
            # 合并：后面的值覆盖前面的值
            merged.update(config_dict)
        
        return cls(**merged) if merged else cls()
    
    def update(self, **kwargs) -> "RuntimeConfig":
        """
        更新配置（返回新实例）
        
        Args:
            **kwargs: 要更新的字段
            
        Returns:
            更新后的新配置实例
        """
        new_config = self.merge(self, kwargs)
        return new_config


class ConfigManager:
    """
    统一配置管理器
    
    管理配置的加载、合并和访问。
    支持配置文件、环境变量、CLI 参数等多来源配置。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径（YAML 或 JSON）
        """
        self.config_file = config_file
        self._runtime_config: Optional[RuntimeConfig] = None
        self._file_config: Dict[str, Any] = {}
        
        if config_file and Path(config_file).exists():
            self._load_file_config()
    
    def _load_file_config(self) -> None:
        """从文件加载配置"""
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
            else:
                logger.warning(f"Unknown config file format: {path.suffix}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            self._file_config = {}
    
    def get_runtime(self) -> RuntimeConfig:
        """
        获取运行时配置
        
        按优先级合并：默认值 < 文件配置 < 环境变量
        
        Returns:
            RuntimeConfig 实例
        """
        if self._runtime_config is None:
            # 按优先级合并
            self._runtime_config = RuntimeConfig.merge(
                RuntimeConfig(),  # 默认值
                self._file_config,  # 配置文件
                RuntimeConfig.from_env(),  # 环境变量
            )
        return self._runtime_config
    
    def update_runtime(self, **kwargs) -> RuntimeConfig:
        """
        更新运行时配置
        
        Args:
            **kwargs: 要更新的配置项
            
        Returns:
            更新后的 RuntimeConfig
        """
        runtime = self.get_runtime()
        self._runtime_config = runtime.update(**kwargs)
        return self._runtime_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        支持点号分隔的嵌套访问，如 "evolution.max_variations"
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        runtime = self.get_runtime()
        
        # 先检查 RuntimeConfig 的属性
        if hasattr(runtime, key):
            return getattr(runtime, key)
        
        # 再检查文件配置
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
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        runtime = self.get_runtime()
        if hasattr(runtime, key):
            self._runtime_config = runtime.update(**{key: value})
    
    def save(self, output_path: Optional[str] = None) -> None:
        """
        保存当前配置到文件
        
        Args:
            output_path: 输出路径，默认覆盖原文件
        """
        import yaml
        
        path = output_path or self.config_file
        if not path:
            raise ValueError("No output path specified")
        
        runtime = self.get_runtime()
        config_data = {
            **self._file_config,
            **runtime.to_dict(),
        }
        
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)


# 全局默认配置管理器实例
_default_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[str] = None) -> ConfigManager:
    """获取默认配置管理器"""
    global _default_manager
    if _default_manager is None:
        _default_manager = ConfigManager(config_file)
    return _default_manager


def reset_config_manager() -> ConfigManager:
    """重置配置管理器"""
    global _default_manager
    _default_manager = ConfigManager()
    return _default_manager


# ============ 编码引擎配置类 ============

@dataclass

# ============ 统一 LLM 配置 ============

@dataclass
class LLMConfig:
    """统一 LLM 配置（替代 CodingLLMConfig/CodingClaudeConfig/EvolutionLLMConfig）"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

    def __post_init__(self):
        # 支持环境变量
        self.api_key = _resolve_env_var(self.api_key) if self.api_key else None
        if not self.api_key:
            self.api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        if self.api_base is None:
            self.api_base = os.getenv("LLM_API_BASE")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider": self.provider,
            "model": self.model,
            "api_base": self.api_base,
            "api_key": _mask_sensitive(self.api_key) if self.api_key else None,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


# 兼容别名（将在 v1.0 移除）
CodingLLMConfig = LLMConfig
CodingClaudeConfig = LLMConfig
EvolutionLLMConfig = LLMConfig


# ============ 编码引擎配置类 ============

@dataclass
class CodingConfig:
    """编码引擎基础配置"""
    engine: str = "cursor"
    llm: Optional[LLMConfig] = None
    claude: Optional[LLMConfig] = None

    def __post_init__(self):
        pass


# ============ 进化配置类 ============

@dataclass
class EvolutionRunConfig:
    """进化运行配置（与 prd/models.py 的 EvolutionConfig 不同）"""
    enabled: bool = True
    max_iterations: int = 10
    max_variations: int = 5
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    selection_pressure: float = 0.5
    pareto_dimensions: List[str] = field(default_factory=lambda: ["correctness", "efficiency", "clarity"])
    llm: Optional[LLMConfig] = None

    def __post_init__(self):
        if self.llm is None:
            raise ValueError("evolution.llm 是必填配置")
        if not self.llm.api_key:
            raise ValueError("evolution.llm.api_key 未配置")


@dataclass
class SprintCycleConfig:
    """SprintCycle 完整配置"""
    max_sprints: int = 10
    max_tasks_per_sprint: int = 5
    parallel_tasks: int = 3
    continue_on_error: bool = False
    evolution_enabled: bool = True
    log_level: str = "INFO"
    evolution: Optional[EvolutionRunConfig] = None
    coding: Optional[CodingConfig] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SprintCycleConfig":
        """从字典加载配置"""
        evolution = None
        coding = None
        
        if "evolution" in data and data["evolution"]:
            evo_data = data["evolution"]
            llm = None
            if "llm" in evo_data and evo_data["llm"]:
                llm = LLMConfig(**evo_data["llm"])
            if llm:
                evolution = EvolutionRunConfig(llm=llm)
        
        if "coding" in data and data["coding"]:
            coding_data = data["coding"]
            llm_cfg = None
            claude_cfg = None
            
            if "llm" in coding_data and coding_data["llm"]:
                llm_cfg = LLMConfig(**coding_data["llm"])
            if "claude" in coding_data and coding_data["claude"]:
                claude_cfg = LLMConfig(**coding_data["claude"])
            
            coding = CodingConfig(
                engine=coding_data.get("engine", "cursor"),
                llm=llm_cfg,
                claude=claude_cfg,
            )
        
        return cls(
            max_sprints=data.get("max_sprints", 10),
            max_tasks_per_sprint=data.get("max_tasks_per_sprint", 5),
            parallel_tasks=data.get("parallel_tasks", 3),
            continue_on_error=data.get("continue_on_error", False),
            evolution_enabled=data.get("evolution_enabled", True),
            log_level=data.get("log_level", "INFO"),
            evolution=evolution,
            coding=coding,
        )


def load_config_from_env() -> SprintCycleConfig:
    """从环境变量加载配置"""
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")
    
    evolution_llm = LLMConfig(
        provider=os.getenv("EVOLUTION_LLM_PROVIDER", "deepseek"),
        model=os.getenv("EVOLUTION_LLM_MODEL", "deepseek-reasoner"),
        api_key=api_key,
    )
    
    evolution = EvolutionRunConfig(llm=evolution_llm)
    
    coding_engine = os.getenv("CODING_ENGINE", "cursor")
    coding = None
    if coding_engine == "llm":
        coding = CodingConfig(
            engine="llm",
            llm=LLMConfig(
                provider="deepseek",
                api_key=api_key,
            )
        )
    elif coding_engine == "claude":
        coding = CodingConfig(
            engine="claude",
            claude=LLMConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
            )
        )
    
    return SprintCycleConfig(
        evolution=evolution,
        coding=coding,
    )


def validate_config(config: SprintCycleConfig) -> List[str]:
    """验证配置是否有效，返回错误列表"""
    errors = []
    
    if config.evolution is None:
        errors.append("evolution.llm 是必填配置")
        return errors
    
    if config.evolution.llm is None:
        errors.append("evolution.llm 是必填配置")
    elif not config.evolution.llm.api_key:
        errors.append("evolution.llm.api_key 未配置")
    
    if config.coding is not None:
        if config.coding.engine == "llm" and config.coding.llm is None:
            errors.append("coding.llm 未配置")
        if config.coding.engine == "claude" and config.coding.claude is None:
            errors.append("coding.claude 未配置")
    
    return errors
