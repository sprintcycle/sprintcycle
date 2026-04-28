"""
Sprint Evolution Integration - Sprint 进化集成层
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import logging

from ..evolution.config import EvolutionEngineConfig
from ..evolution.engine import EvolutionEngine
from ..evolution.types import SprintContext, EvolutionResult

logger = logging.getLogger(__name__)


@dataclass
class EvolutionTrigger:
    name: str
    condition: str
    threshold: Optional[Dict[str, Any]] = None


class SprintEvolutionIntegration:
    """Sprint 进化集成器"""
    
    DEFAULT_TARGETS = ["sprintcycle/config.py", "sprintcycle/server.py", "sprintcycle/evolution/engine.py"]
    
    def __init__(self, config: EvolutionEngineConfig):
        self.config = config
        self.engine = EvolutionEngine(config)
        self.evolution_history: List[EvolutionResult] = []
    
    async def trigger_after_sprint(self, sprint_metrics: Dict[str, Any], targets: Optional[List[str]] = None) -> List[EvolutionResult]:
        sprint_number = sprint_metrics.get("sprint_number", 1)
        logger.info(f"🏃 Sprint {sprint_number} 结束，开始自我进化...")
        
        if not self.engine.should_evolve(sprint_metrics):
            logger.info("📊 指标正常，跳过")
            return []
        
        context = SprintContext(sprint_id=f"sc-{sprint_number}-{datetime.now().strftime('%H%M%S')}", sprint_number=sprint_number, goal=f"Sprint {sprint_number} 优化", current_metrics=sprint_metrics)
        
        if targets is None:
            targets = self.DEFAULT_TARGETS
        
        valid_targets = [t for t in targets if (Path(__file__).parent.parent / t).exists()]
        
        results = []
        for target in valid_targets:
            logger.info(f"  → 进化: {target}")
            result = await self.engine.evolve_code(target=target, context=context, goal=f"优化 {target}")
            results.append(result)
            logger.info(f"    {'✅' if result.success else '⚠️'} {target}")
        
        self.evolution_history.extend(results)
        return results
    
    async def evolve_modules(self, modules: List[str], goal: Optional[str] = None) -> List[EvolutionResult]:
        logger.info(f"👐 手动触发进化: {modules}")
        context = SprintContext(sprint_id=f"manual-{datetime.now().strftime('%H%M%S')}", sprint_number=0, goal=goal or "手动优化")
        return [await self.engine.evolve_code(target=m, context=context, goal=goal) for m in modules]
    
    def get_evolution_status(self) -> Dict[str, Any]:
        return {"engine_summary": self.engine.get_summary(), "history_count": len(self.evolution_history)}
