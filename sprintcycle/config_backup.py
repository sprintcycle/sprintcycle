"""
SprintCycle 配置模块

支持进化引擎配置和编码引擎配置
"""

from dataclasses import dataclass, field
from typing import Optional
import os
import json
import yaml


@dataclass
class EvolutionLLMConfig:
    """进化引擎 LLM 配置（必填）"""
    provider: str  # deepseek, openai, anthropic
    model: str     # deepseek-reasoner, gpt-4o, etc.
    api_key: str   # 从环境变量读取或直接配置
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048

    def __post_init__(self):
        if self.api_key.startswith("${") and self.api_key.endswith("}"):
            env_var = self.api_key[2:-1]
            self.api_key = os.getenv(env_var, "")
        if self.api_base and self.api_base.startswith("${") and self.api_base.endswith("}"):
            self.api_base = os.getenv(self.api_base[2:-1], "")

    def to_dict(self) -> dict:
        return {
            "provider": self.provider, "model": self.model,
            "api_key": "***" if self.api_key else "",
            "api_base": self.api_base,
            "temperature": self.temperature, "max_tokens": self.max_tokens,
        }


@dataclass
class CodingLLMConfig:
    """编码引擎 LLM 配置（可选，engine=llm时需要）"""
    provider: str
    model: str
    api_key: str
    api_base: Optional[str] = None

    def __post_init__(self):
        if self.api_key.startswith("${") and self.api_key.endswith("}"):
            self.api_key = os.getenv(self.api_key[2:-1], "")


@dataclass
class CodingClaudeConfig:
    """编码引擎 Claude 配置（可选，engine=claude时需要）"""
    model: str = "claude-3-5-sonnet"
    api_key: str = ""

    def __post_init__(self):
        if self.api_key.startswith("${") and self.api_key.endswith("}"):
            self.api_key = os.getenv(self.api_key[2:-1], "")
        elif not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY", "")


@dataclass
class EvolutionConfig:
    """进化引擎配置（必填）"""
    enabled: bool = True
    llm: Optional[EvolutionLLMConfig] = None
    hermes_repo: str = "~/.hermes/hermes-agent"
    cache_dir: str = "./evolution_cache"
    max_iterations: int = 10
    pareto_dimensions: list = field(default_factory=lambda: ["correctness", "performance", "stability", "code_quality"])

    def __post_init__(self):
        if self.llm is None:
            raise ValueError("evolution.llm 是必填配置")
        if not self.llm.api_key:
            raise ValueError("evolution.llm.api_key 未配置")


@dataclass
class CodingConfig:
    """编码引擎配置（可选）"""
    engine: str = "cursor"  # cursor | llm | claude
    llm: Optional[CodingLLMConfig] = None
    claude: Optional[CodingClaudeConfig] = None

    def __post_init__(self):
        if self.engine == "llm" and self.llm is None:
            raise ValueError("coding.engine='llm' 时，必须配置 coding.llm")
        if self.engine == "claude" and self.claude is None:
            raise ValueError("coding.engine='claude' 时，必须配置 coding.claude")


@dataclass
class SprintCycleConfig:
    """SprintCycle 主配置"""
    evolution: EvolutionConfig  # 必填
    coding: CodingConfig = field(default_factory=lambda: CodingConfig())
    project_path: str = "."
    log_dir: str = "./logs"
    chorus_timeout: int = 600
    max_retries: int = 3

    def __post_init__(self):
        if self.evolution is None:
            raise ValueError("evolution 是必填配置")

    @classmethod
    def from_dict(cls, data: dict) -> "SprintCycleConfig":
        evolution_llm = None
        if "evolution" in data and "llm" in data["evolution"]:
            llm_data = data["evolution"]["llm"]
            evolution_llm = EvolutionLLMConfig(
                provider=llm_data.get("provider", "deepseek"),
                model=llm_data.get("model", "deepseek-reasoner"),
                api_key=llm_data.get("api_key", ""),
                api_base=llm_data.get("api_base"),
            )
        
        evolution_config = EvolutionConfig(
            enabled=data.get("evolution", {}).get("enabled", True),
            llm=evolution_llm,
            hermes_repo=data.get("evolution", {}).get("hermes_repo", "~/.hermes/hermes-agent"),
            cache_dir=data.get("evolution", {}).get("cache_dir", "./evolution_cache"),
            max_iterations=data.get("evolution", {}).get("max_iterations", 10),
        )
        
        coding_data = data.get("coding", {})
        coding_llm, coding_claude = None, None
        if "llm" in coding_data:
            coding_llm = CodingLLMConfig(**coding_data["llm"])
        if "claude" in coding_data:
            coding_claude = CodingClaudeConfig(**coding_data["claude"])
        
        return cls(
            evolution=evolution_config,
            coding=CodingConfig(
                engine=coding_data.get("engine", "cursor"),
                llm=coding_llm, claude=coding_claude,
            ),
        )

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SprintCycleConfig":
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


def load_config_from_env() -> SprintCycleConfig:
    """从环境变量加载配置"""
    evolution_llm = EvolutionLLMConfig(
        provider=os.getenv("EVOLUTION_LLM_PROVIDER", "deepseek"),
        model=os.getenv("EVOLUTION_LLM_MODEL", "deepseek-reasoner"),
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )
    
    evolution_config = EvolutionConfig(llm=evolution_llm)
    
    coding_engine = os.getenv("CODING_ENGINE", "cursor")
    coding_llm, coding_claude = None, None
    
    if coding_engine == "llm":
        coding_llm = CodingLLMConfig(
            provider=os.getenv("CODING_LLM_PROVIDER", "deepseek"),
            model=os.getenv("CODING_LLM_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        )
    elif coding_engine == "claude":
        coding_claude = CodingClaudeConfig(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    
    return SprintCycleConfig(
        evolution=evolution_config,
        coding=CodingConfig(engine=coding_engine, llm=coding_llm, claude=coding_claude),
    )


DEFAULT_CONFIG_PATH = "./sprintcycle.yaml"


def load_config(config_path: str = None) -> SprintCycleConfig:
    """加载配置文件"""
    path = config_path or DEFAULT_CONFIG_PATH
    if os.path.exists(path):
        if path.endswith(('.yaml', '.yml')):
            return SprintCycleConfig.from_yaml(path)
        else:
            return SprintCycleConfig.from_dict(json.load(open(path)))
    return load_config_from_env()


def validate_config(config: SprintCycleConfig) -> list:
    """验证配置完整性"""
    errors = []
    if not config.evolution.llm:
        errors.append("evolution.llm 未配置（必填）")
    elif not config.evolution.llm.api_key:
        errors.append("evolution.llm.api_key 未配置（必填）")
    if config.coding.engine == "llm" and not config.coding.llm:
        errors.append("coding.engine='llm' 时，必须配置 coding.llm")
    if config.coding.engine == "claude" and not config.coding.claude:
        errors.append("coding.engine='claude' 时，必须配置 coding.claude")
    return errors
