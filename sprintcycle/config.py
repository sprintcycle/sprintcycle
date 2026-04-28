"""
SprintCycle 配置模块
支持进化引擎配置和编码引擎配置
"""

from dataclasses import dataclass, field
from typing import Optional
import os
import yaml


@dataclass
class EvolutionLLMConfig:
    """进化引擎 LLM 配置（必填）"""
    provider: str
    model: str
    api_key: str
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048

    def __post_init__(self):
        if self.api_key.startswith("${") and self.api_key.endswith("}"):
            self.api_key = os.getenv(self.api_key[2:-1], "")


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


@dataclass
class SprintCycleConfig:
    """SprintCycle 主配置"""
    evolution: EvolutionConfig
    coding: CodingConfig = field(default_factory=lambda: CodingConfig())


def load_config_from_env() -> SprintCycleConfig:
    """从环境变量加载配置"""
    evolution_llm = EvolutionLLMConfig(
        provider=os.getenv("EVOLUTION_LLM_PROVIDER", "deepseek"),
        model=os.getenv("EVOLUTION_LLM_MODEL", "deepseek-reasoner"),
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
    )
    return SprintCycleConfig(
        evolution=EvolutionConfig(llm=evolution_llm),
        coding=CodingConfig(engine=os.getenv("CODING_ENGINE", "cursor")),
    )


def validate_config(config: SprintCycleConfig) -> list:
    """验证配置"""
    errors = []
    if not config.evolution.llm:
        errors.append("evolution.llm 未配置")
    if not config.evolution.llm.api_key:
        errors.append("evolution.llm.api_key 未配置")
    return errors
