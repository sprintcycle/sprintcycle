"""
Sprint Evolution Integration - Sprint 进化集成层

v0.9.0: 使用 EvolutionPipeline 替代 GEPAEngine
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging

from ..evolution.pipeline import EvolutionPipeline
from ..evolution.prd_source import DiagnosticPRDSource
from ..evolution.types import EvolutionResult
from ..config.manager import RuntimeConfig

logger = logging.getLogger(__name__)


@dataclass
class EvolutionTrigger:
    name: str
    condition: str
    threshold: Optional[Dict[str, Any]] = None


class SprintEvolutionIntegration:
    """Sprint 进化集成器 — v0.9.0 统一管道版"""
    
    DEFAULT_TARGETS = ["sprintcycle/config/", "sprintcycle/evolution/"]
    
    def __init__(self, config: Optional[RuntimeConfig] = None):
        self.config = config or RuntimeConfig()
        self.evolution_history: List[Dict[str, Any]] = []
    
    def trigger_after_sprint(self, sprint_metrics: Dict[str, Any], targets: Optional[List[str]] = None) -> Dict[str, Any]:
        sprint_number = sprint_metrics.get("sprint_number", 1)
        logger.info(f"Sprint {sprint_number} 结束，启动诊断进化...")
        
        if targets is None:
            targets = self.DEFAULT_TARGETS
        
        valid_targets = [t for t in targets if (Path(".") / t).exists()]
        
        for target in valid_targets:
            logger.info(f"  -> 进化: {target}")
            pipeline = EvolutionPipeline(target, DiagnosticPRDSource(), None)  # TODO: convert RuntimeConfig to PipelineConfig
            result = pipeline.run(max_cycles=1)
            self.evolution_history.append({
                "target": target,
                "success": result.success,
                "sprint_number": sprint_number,
                "timestamp": datetime.now().isoformat(),
            })
            logger.info(f"    {'OK' if result.success else 'WARN'} {target}")
        
        return {"evolved": len(valid_targets), "history_count": len(self.evolution_history)}
    
    def get_evolution_status(self) -> Dict[str, Any]:
        return {"history_count": len(self.evolution_history)}
