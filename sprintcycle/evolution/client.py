"""
GEPA Client - Hermes Agent Self-Evolution 客户端封装
"""

import os, json, asyncio, subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .config import EvolutionEngineConfig
from .types import Gene, Variation, SprintContext

logger = logging.getLogger(__name__)


class GEPAClient:
    def __init__(self, config: EvolutionEngineConfig):
        self.config = config
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._hermes_available = self._check_hermes()

    def _check_hermes(self) -> bool:
        try:
            import hermes_agent
            return True
        except ImportError:
            return False

    async def vary(self, code: str, context: SprintContext, goal: str, max_variations: int = 5) -> List[Variation]:
        if self._hermes_available:
            return await self._vary_hermes(code, context, goal, max_variations)
        return self._vary_fallback(code, context, max_variations)

    async def _vary_hermes(self, code: str, context: SprintContext, goal: str, max_variations: int) -> List[Variation]:
        try:
            from hermes_agent.self_evolution import GEPAOptimizer
            optimizer = GEPAOptimizer(llm_provider=self.config.llm_provider, llm_model=self.config.llm_model, api_key=self.config.llm_api_key)
            result = await optimizer.vary(code=code, reflection=f"目标: {goal}", constraints={"dimensions": self.config.pareto_dimensions, "max_variations": max_variations})
            return [Variation(id=rv.get("id", f"var_{i}"), gene_id=rv.get("parent_id", ""), variation_type=rv.get("type", "point"), original_content=code, modified_content=rv.get("content", code), change_summary=rv.get("summary", ""), risk_level=rv.get("risk", "medium"), predicted_fitness=rv.get("fitness", {}), confidence=rv.get("confidence", 0.5)) for i, rv in enumerate(result.get("variations", []))]
        except Exception as e:
            logger.error(f"GEPA vary 失败: {e}")
            return self._vary_fallback(code, context, max_variations)

    def _vary_fallback(self, code: str, context: SprintContext, max_variations: int) -> List[Variation]:
        strategies = [("错误处理", "error_handling", "low"), ("性能优化", "performance", "medium"), ("可读性", "readability", "low")]
        return [Variation(id=f"var_{context.sprint_id}_{i}", gene_id="", variation_type=var_type, original_content=code, modified_content=code, change_summary=f"应用 {name}", risk_level=risk, predicted_fitness={d: 0.5 for d in self.config.pareto_dimensions}, confidence=0.3) for i, (name, var_type, risk) in enumerate(strategies[:max_variations])]

    async def select(self, variations: List[Variation], fitness_scores: List[Dict[str, float]]) -> List[Variation]:
        if self._hermes_available:
            return await self._select_hermes(variations, fitness_scores)
        return self._select_pareto(variations, fitness_scores)

    async def _select_hermes(self, variations: List[Variation], fitness_scores: List[Dict[str, float]]) -> List[Variation]:
        try:
            from hermes_agent.self_evolution import GEPAOptimizer
            optimizer = GEPAOptimizer(llm_provider=self.config.llm_provider, llm_model=self.config.llm_model, api_key=self.config.llm_api_key)
            result = await optimizer.select(variations=[{"id": v.id, "content": v.modified_content, "fitness": fs} for v, fs in zip(variations, fitness_scores)], method=self.config.selection_strategy)
            return [v for v in variations if v.id in result.get("selected_ids", [])]
        except:
            return self._select_pareto(variations, fitness_scores)

    def _select_pareto(self, variations: List[Variation], fitness_scores: List[Dict[str, float]]) -> List[Variation]:
        if not variations:
            return []
        pareto = []
        for i, v in enumerate(variations):
            if not any(self._dominates(fitness_scores[j], fitness_scores[i]) for j in range(len(fitness_scores)) if i != j):
                pareto.append(v)
        return pareto[:max(1, len(pareto) // 2)]

    def _dominates(self, fs1: Dict[str, float], fs2: Dict[str, float]) -> bool:
        better = False
        for dim in self.config.pareto_dimensions:
            v1, v2 = fs1.get(dim, 0), fs2.get(dim, 0)
            if v1 < v2:
                return False
            if v1 > v2:
                better = True
        return better

    async def inherit(self, elite_genes: List[Gene], context: SprintContext) -> List[Gene]:
        if self._hermes_available:
            return await self._inherit_hermes(elite_genes, context)
        return [Gene(id=f"inh_{context.sprint_id}_{g.id}", type=g.type, content=g.content, metadata=g.metadata.copy(), fitness_scores=g.fitness_scores.copy(), parent_ids=[g.id], version=g.version + 1) for g in elite_genes[:2]]

    async def _inherit_hermes(self, elite_genes: List[Gene], context: SprintContext) -> List[Gene]:
        try:
            from hermes_agent.self_evolution import GEPAOptimizer
            optimizer = GEPAOptimizer(llm_provider=self.config.llm_provider, llm_model=self.config.llm_model, api_key=self.config.llm_api_key)
            result = await optimizer.inherit(genes=[g.to_dict() for g in elite_genes], context=f"Sprint {context.sprint_number}")
            return [Gene(id=rg.get("id", f"gene_{i}"), type=elite_genes[0].type, content=rg.get("content", ""), metadata=rg.get("metadata", {}), fitness_scores=rg.get("fitness_scores", {})) for i, rg in enumerate(result.get("genes", []))]
        except:
            return [Gene(id=f"inh_{context.sprint_id}_{g.id}", type=g.type, content=g.content, metadata=g.metadata.copy(), fitness_scores=g.fitness_scores.copy(), parent_ids=[g.id], version=g.version + 1) for g in elite_genes[:2]]

    async def save_checkpoint(self, sprint_id: str, data: Dict[str, Any]) -> None:
        with open(self.cache_dir / f"{sprint_id}.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def load_checkpoint(self, sprint_id: str) -> Optional[Dict[str, Any]]:
        path = self.cache_dir / f"{sprint_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)
