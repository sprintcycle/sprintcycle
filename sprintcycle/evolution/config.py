"""
SprintCycle Evolution Configuration

v0.9.0: EvolutionEngineConfig 已废弃，统一使用 RuntimeConfig。
本模块保留仅为向后兼容，所有逻辑委托给 config.manager.RuntimeConfig。
"""

import os
import warnings
from dataclasses import dataclass, field
from typing import Optional, List

from sprintcycle.config.manager import RuntimeConfig


@dataclass
class EvolutionEngineConfig:
    """进化引擎配置 — DEPRECATED: use RuntimeConfig instead
    
    v0.9.0: 此类仅为向后兼容保留，所有字段从 RuntimeConfig 读取。
    """
    llm_provider: str = "deepseek"
    llm_model: str = "deepseek-chat"
    llm_api_key: str = ""
    llm_api_base: Optional[str] = None
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    hermes_repo: str = "~/.hermes/hermes-agent"
    cache_dir: str = "./evolution_cache"
    max_iterations: int = 10
    max_variations_per_gen: int = 5
    pareto_dimensions: List[str] = field(default_factory=lambda: ["correctness", "performance", "stability", "code_quality"])
    reflection_enabled: bool = True
    selection_strategy: str = "pareto_frontier"
    inheritance_enabled: bool = True
    elite_ratio: float = 0.1

    def __post_init__(self):
        warnings.warn(
            "EvolutionEngineConfig is deprecated, use RuntimeConfig instead",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self.llm_api_key:
            self.llm_api_key = os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
        self.hermes_repo = os.path.expanduser(self.hermes_repo)
        self.cache_dir = os.path.expanduser(self.cache_dir)

    @classmethod
    def from_runtime_config(cls, config: RuntimeConfig) -> "EvolutionEngineConfig":
        """从 RuntimeConfig 创建（推荐方式）"""
        return cls(
            llm_provider=config.llm_provider,
            llm_model=config.llm_model,
            llm_api_key=config.api_key or "",
            llm_api_base=config.api_base,
            llm_temperature=config.llm_temperature,
            llm_max_tokens=config.llm_max_tokens,
            cache_dir=config.evolution_cache_dir,
            max_iterations=config.evolution_iterations,
            max_variations_per_gen=config.max_variations,
        )

    def to_runtime_config(self) -> RuntimeConfig:
        """转换为 RuntimeConfig"""
        return RuntimeConfig(
            llm_provider=self.llm_provider,
            llm_model=self.llm_model,
            api_key=self.llm_api_key or None,
            api_base=self.llm_api_base,
            llm_temperature=self.llm_temperature,
            llm_max_tokens=self.llm_max_tokens,
            evolution_cache_dir=self.cache_dir,
            evolution_iterations=self.max_iterations,
            max_variations=self.max_variations_per_gen,
        )
