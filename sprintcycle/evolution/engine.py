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

    @classmethod
    def from_prd(cls, prd, config: Optional[EvolutionEngineConfig] = None) -> "EvolutionEngine":
        """
        从 PRD 创建进化引擎实例
        
        Args:
            prd: PRD 对象
            config: 进化引擎配置（可选）
            
        Returns:
            配置好的 EvolutionEngine 实例
        """
        engine = cls(config or EvolutionEngineConfig())
        
        # 如果 PRD 指定了基因池恢复
        if hasattr(prd, 'metadata') and 'checkpoint_sprint_id' in prd.metadata:
            # 异步加载检查点
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(engine.load_checkpoint(prd.metadata['checkpoint_sprint_id']))
        
        return engine

    def extract_evolution_targets(self, prd) -> List[Dict[str, Any]]:
        """
        从 PRD 提取进化目标
        
        Args:
            prd: PRD 对象
            
        Returns:
            进化目标列表
        """
        targets = []
        
        if prd.is_evolution_mode and prd.evolution:
            # 自进化模式：从 evolution 配置提取
            for target_file in prd.evolution.targets:
                targets.append({
                    "target": target_file,
                    "goals": prd.evolution.goals,
                    "constraints": prd.evolution.constraints,
                    "mode": "evolution",
                })
        
        # 从 Sprint 任务中提取 evolver 任务
        for sprint in prd.sprints:
            for task in sprint.tasks:
                if task.agent == "evolver" and task.target:
                    targets.append({
                        "target": task.target,
                        "goals": [task.task] + task.constraints,
                        "constraints": task.constraints,
                        "mode": "task_evolution",
                        "sprint": sprint.name,
                    })
        
        return targets

    async def evolve_from_prd(self, prd, iterations: int = 1) -> List[EvolutionResult]:
        """
        根据 PRD 执行进化
        
        Args:
            prd: PRD 对象
            iterations: 迭代次数
            
        Returns:
            进化结果列表
        """
        targets = self.extract_evolution_targets(prd)
        
        if not targets:
            logger.warning("⚠️  PRD 中未找到进化目标")
            return []
        
        logger.info(f"🎯 从 PRD 提取 {len(targets)} 个进化目标")
        
        results = []
        for i, target_info in enumerate(targets):
            logger.info(f"\n[{i+1}/{len(targets)}] 进化目标: {target_info['target']}")
            
            # 构建目标路径
            target_path = str(Path(prd.project.path) / target_info['target'])
            
            # 创建上下文
            goal_text = "; ".join(target_info['goals']) if target_info['goals'] else "优化代码"
            context = SprintContext(
                sprint_id=f"prd-evo-{int(time.time())}-{i}",
                sprint_number=i + 1,
                goal=goal_text,
                constraints={
                    "dimensions": self.config.pareto_dimensions,
                    "prd_constraints": target_info.get('constraints', []),
                }
            )
            
            # 执行多次迭代
            for iteration in range(iterations):
                logger.info(f"   迭代 {iteration + 1}/{iterations}")
                result = await self.evolve_code(
                    target=target_path,
                    context=context,
                    goal=goal_text,
                    max_variations=prd.evolution.max_variations if prd.evolution else 5,
                )
                results.append(result)
                
                if not result.success:
                    logger.warning(f"   ⚠️  进化失败: {result.error}")
                    break
                
                # 短暂暂停
                if iteration < iterations - 1:
                    await asyncio.sleep(1)
        
        return results
    
    async def evolve_sprint(self, sprint, max_generations: int = 3) -> EvolutionResult:
        """
        对一个 Sprint 进行进化优化
        
        这是方案 A 的核心方法：将 Evolution 作为 Sprint 的增强能力。
        通过内部调用 GEPA 进化流程，优化 Sprint 中的目标代码。
        
        Args:
            sprint: PRDSprint 对象
            max_generations: 最大进化代数
            
        Returns:
            EvolutionResult: 进化后的执行结果
        """
        logger.info(f"🚀 开始 Evolution 增强 Sprint: {sprint.name}")
        
        start_time = time.time()
        result = EvolutionResult(stage=EvolutionStage.VARIATION, success=True)
        
        # 1. 从 Sprint 中提取目标文件
        targets = self._extract_targets_from_sprint(sprint)
        
        if not targets:
            logger.warning(f"⚠️ Sprint {sprint.name} 没有可进化的目标文件")
            result.success = False
            result.error = "没有可进化的目标文件"
            return result
        
        logger.info(f"📋 提取到 {len(targets)} 个进化目标: {targets}")
        
        # 2. 对每个目标进行 GEPA 进化
        all_variations = []
        all_selected_genes = []
        
        for generation in range(max_generations):
            logger.info(f"📍 Generation {generation + 1}/{max_generations}")
            generation_variations = []
            generation_genes = []
            
            for target in targets:
                try:
                    # 创建上下文
                    context = SprintContext(
                        sprint_id=f"sprint-evo-{hashlib.md5(sprint.name.encode()).hexdigest()[:8]}",
                        sprint_number=generation + 1,
                        goal=f"Sprint {sprint.name} 进化优化",
                    )
                    
                    # 调用原有的 evolve_code 方法
                    evo_result = await self.evolve_code(
                        target=target,
                        context=context,
                        goal=f"Sprint {sprint.name} 目标优化",
                    )
                    
                    generation_variations.extend(evo_result.variations)
                    generation_genes.extend(evo_result.selected_genes)
                    
                    logger.info(f"  ✅ {target} 进化完成")
                except Exception as e:
                    logger.warning(f"  ⚠️ {target} 进化失败: {e}")
            
            all_variations.extend(generation_variations)
            all_selected_genes.extend(generation_genes)
            
            # 休息一下，避免 API 限制
            if generation < max_generations - 1:
                await asyncio.sleep(1)
        
        # 3. 构建最终结果
        result.variations = all_variations
        result.selected_genes = all_selected_genes
        result.success = len(all_selected_genes) > 0
        result.execution_time = time.time() - start_time
        
        if result.success:
            logger.info(f"✅ Sprint {sprint.name} Evolution 完成: {len(all_selected_genes)} 个基因被选中")
        else:
            logger.warning(f"⚠️ Sprint {sprint.name} Evolution 未产生有效结果")
        
        return result
    
    def _extract_targets_from_sprint(self, sprint) -> List[str]:
        """
        从 Sprint 中提取需要进化的目标文件
        
        Args:
            sprint: PRDSprint 对象
            
        Returns:
            List[str]: 目标文件路径列表
        """
        targets = []
        
        # 从任务中提取 target
        if hasattr(sprint, 'tasks'):
            for task in sprint.tasks:
                if hasattr(task, 'target') and task.target:
                    # 跳过非代码文件
                    if not task.target.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs')):
                        continue
                    targets.append(task.target)
        
        # 去重
        return list(set(targets))
