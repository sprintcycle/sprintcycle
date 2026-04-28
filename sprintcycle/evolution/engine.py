"""
Evolution Engine - SprintCycle 自我进化引擎

🎯 核心使命：让 SprintCycle 进化自身的 Python 代码
进化目标 = SprintCycle 的 .py 文件
"""

import time, asyncio, hashlib
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import logging

from .config import EvolutionEngineConfig
from .client import GEPAClient
from .types import Gene, GeneType, Variation, SprintContext, EvolutionResult, EvolutionStage, EvolutionMetrics

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """
    SprintCycle 自我进化引擎
    读取自身代码 → GEPA 变异 → Pareto 选择 → 应用最优变体 → 自我增强
    """
    
    def __init__(self, config: EvolutionEngineConfig):
        self.config = config
        self.client = GEPAClient(config)
        self.gene_pool: List[Gene] = []
        self.history: List[EvolutionResult] = []
        self.metrics = EvolutionMetrics()

    async def evolve_code(self, target: str, context: Optional[SprintContext] = None, goal: Optional[str] = None, max_variations: int = 5) -> EvolutionResult:
        """🚀 进化 SprintCycle 的 Python 代码文件（核心方法）"""
        start_time = time.time()
        result = EvolutionResult(stage=EvolutionStage.VARIATION, success=True)
        file_path = self._resolve_path(target)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
        except FileNotFoundError:
            return EvolutionResult(stage=EvolutionStage.VARIATION, success=False, error=f"文件不存在: {file_path}")
        except Exception as e:
            return EvolutionResult(stage=EvolutionStage.VARIATION, success=False, error=f"读取失败: {e}")
        
        if context is None:
            context = SprintContext(sprint_id=f"sc-{hashlib.md5(target.encode()).hexdigest()[:8]}", sprint_number=1, goal=goal or "优化代码")
        if not goal:
            goal = f"优化 {file_path.name}"
        
        logger.info(f"🚀 SprintCycle 自我进化: {target}, 目标: {goal}")
        
        try:
            # 变异
            variations = await self.client.vary(code=original_code, context=context, goal=f"[进化] {goal}", max_variations=max_variations)
            result.variations = variations
            self.metrics.variation_count += len(variations)
            
            # 选择
            if variations:
                fitness_scores = [v.predicted_fitness or {d: 0.5 for d in self.config.pareto_dimensions} for v in variations]
                selected = await self.client.select(variations, fitness_scores)
                result.selected_genes = [Gene(id=v.id, type=GeneType.CODE, content=v.modified_content, metadata={"file": str(file_path), "original_hash": hashlib.md5(original_code.encode()).hexdigest()}, fitness_scores=fitness_scores[i], parent_ids=[v.gene_id] if v.gene_id else []) for i, v in enumerate(variations) if v in selected]
                self.metrics.selection_count += len(selected)
            
            # 遗传
            if self.config.inheritance_enabled and self.gene_pool:
                elite = self._get_elite(top_k=2)
                if elite:
                    inherited = await self.client.inherit(elite, context)
                    result.inherited_genes = inherited
                    self.metrics.inheritance_count += len(inherited)
                    self.gene_pool.extend(inherited)
            
            # 应用变更
            if result.success and result.selected_genes:
                best = result.selected_genes[0]
                with open(file_path.with_suffix(file_path.suffix + ".bak"), "w") as f:
                    f.write(original_code)
                with open(file_path, "w") as f:
                    f.write(best.content)
                best.metadata["new_hash"] = hashlib.md5(best.content.encode()).hexdigest()
                logger.info(f"✅ 已更新: {file_path}")
                self.add_gene(best)
            
            self.metrics.generations += 1
        except Exception as e:
            logger.error(f"❌ 进化失败: {e}")
            result.success = False
            result.error = str(e)
        
        result.execution_time = time.time() - start_time
        self.history.append(result)
        return result

    async def evolve_batch(self, targets: List[str], context: Optional[SprintContext] = None, goal: Optional[str] = None) -> List[EvolutionResult]:
        results = []
        for target in targets:
            result = await self.evolve_code(target=target, context=context, goal=goal)
            results.append(result)
            if targets.index(target) < len(targets) - 1:
                await asyncio.sleep(1)
        return results

    def should_evolve(self, metrics: Dict[str, Any]) -> bool:
        return metrics.get("success_rate", 1.0) < 0.7 or metrics.get("error_count", 0) > 10 or metrics.get("avg_duration", 0) > 600

    def add_gene(self, gene: Gene) -> None:
        self.gene_pool.append(gene)

    def _get_elite(self, top_k: int = 2) -> List[Gene]:
        if not self.gene_pool:
            return []
        def avg(g): return sum(g.fitness_scores.values()) / max(1, len(g.fitness_scores))
        return sorted(self.gene_pool, key=avg, reverse=True)[:top_k]

    def _resolve_path(self, target: str) -> Path:
        path = Path(target)
        return path if path.is_absolute() else Path(__file__).parent.parent / target

    def get_summary(self) -> Dict[str, Any]:
        return {"type": "SprintCycle 自我进化", "gene_pool_size": len(self.gene_pool), "generations": self.metrics.generations, "avg_fitness": self.metrics.avg_fitness}

    async def reset(self) -> None:
        self.gene_pool = []
        self.history = []
        self.metrics = EvolutionMetrics()
