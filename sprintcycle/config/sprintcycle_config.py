"""
SprintCycleConfig - 应用级配置
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import os

from .llm_config import LLMConfig


@dataclass
class CodingConfig:
    """编码引擎配置"""
    engine: str = "cursor"
    llm: Optional[LLMConfig] = None
    claude: Optional[LLMConfig] = None


@dataclass
class EvolutionRunConfig:
    """进化运行配置"""
    enabled: bool = True
    max_iterations: int = 10
    max_variations: int = 5
    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    selection_pressure: float = 0.5
    eval_dimensions: List[str] = field(default_factory=lambda: ["correctness", "efficiency", "clarity"])
    llm: Optional[LLMConfig] = None

    def __post_init__(self):
        # v0.9.1: llm 不再强制要求，保持向后兼容
        pass


@dataclass
class SprintCycleConfig:
    """SprintCycle 应用配置"""
    max_sprints: int = 10
    max_tasks_per_sprint: int = 5
    parallel_tasks: int = 3
    continue_on_error: bool = False
    evolution_enabled: bool = True
    log_level: str = "INFO"
    # Evolution fields (inlined from EvolutionRunConfig)
    evolution_max_iterations: int = 10
    evolution_max_variations: int = 5
    evolution_crossover_rate: float = 0.8
    evolution_mutation_rate: float = 0.1
    # Coding fields (inlined from CodingConfig)
    coding_engine: str = "cursor"
    coding_llm: Optional[LLMConfig] = None
    coding_claude: Optional[LLMConfig] = None
    # Backward compat
    evolution: Optional[EvolutionRunConfig] = None
    coding: Optional[CodingConfig] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SprintCycleConfig":
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
        coding = CodingConfig(engine="llm", llm=LLMConfig(provider="deepseek", api_key=api_key))
    elif coding_engine == "claude":
        coding = CodingConfig(engine="claude", claude=LLMConfig(api_key=os.getenv("ANTHROPIC_API_KEY")))
    
    return SprintCycleConfig(evolution=evolution, coding=coding)


def validate_config(config: SprintCycleConfig) -> List[str]:
    """校验配置完整性"""
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
