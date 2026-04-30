"""
SprintCycle Evolution Configuration

Centralized configuration for GEPA evolution engine.
EvolutionEngineConfig is DEPRECATED, use GEPAConfig instead.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EvolutionEngineConfig:
    """进化引擎配置 — DEPRECATED: use GEPAConfig instead"""
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
        import warnings
        warnings.warn(
            "EvolutionEngineConfig is deprecated, use GEPAConfig instead",
            DeprecationWarning, stacklevel=2,
        )
        if not self.llm_api_key:
            self.llm_api_key = os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
        self.hermes_repo = os.path.expanduser(self.hermes_repo)
        self.cache_dir = os.path.expanduser(self.cache_dir)

    @classmethod
    def from_sprintcycle_config(cls, config) -> "EvolutionEngineConfig":
        return cls(
            llm_provider=config.evolution.llm.provider,
            llm_model=config.evolution.llm.model,
            llm_api_key=config.evolution.llm.api_key,
            llm_api_base=config.evolution.llm.api_base,
            hermes_repo=config.evolution.hermes_repo,
            cache_dir=config.evolution.cache_dir,
            max_iterations=config.evolution.max_iterations,
            pareto_dimensions=config.evolution.pareto_dimensions,
        )

    def to_gepa_config(self, repo_path: str = ".") -> "GEPAConfig":
        """Convert to GEPAConfig"""
        from sprintcycle.evolution.gepa_engine import GEPAConfig
        return GEPAConfig(
            repo_path=repo_path,
            evolution_cache_dir=self.cache_dir,
            max_cycles=self.max_iterations,
            max_variations_per_cycle=self.max_variations_per_gen,
        )
