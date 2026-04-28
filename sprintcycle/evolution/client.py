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
        except Exception as e:
            logger.error(f"GEPA select 失败: {e}")
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
        except Exception as e:
            logger.error(f"GEPA inherit 失败: {e}")
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

    async def reflect(
        self,
        failed_variations: List[Variation],
        execution_results: List[Dict[str, Any]],
        context: SprintContext,
    ) -> Dict[str, Any]:
        """
        GEPA 第四阶段: Reflect - 从失败中学习

        分析失败的变体，理解失败原因，提取可学习的经验教训，
        并生成改进建议以指导下一轮进化。

        Args:
            failed_variations: 失败的变体列表
            execution_results: 执行结果列表（包含成功/失败状态、错误信息等）
            context: Sprint 上下文

        Returns:
            反思结果，包含:
                - lessons_learned: 从失败中学到的教训
                - improvement_suggestions: 改进建议
                - root_causes: 根本原因分析
                - confidence_adjustments: 置信度调整
        """
        if self._hermes_available:
            return await self._reflect_with_hermes(failed_variations, execution_results, context)
        return self._reflect_fallback(failed_variations, execution_results, context)

    async def _reflect_with_hermes(
        self,
        failed_variations: List[Variation],
        execution_results: List[Dict[str, Any]],
        context: SprintContext,
    ) -> Dict[str, Any]:
        """使用 Hermes 库进行反思"""
        try:
            from hermes_agent.self_evolution import GEPAOptimizer

            optimizer = GEPAOptimizer(
                llm_provider=self.config.llm_provider,
                llm_model=self.config.llm_model,
                api_key=self.config.llm_api_key,
                api_base=self.config.llm_api_base,
            )

            variation_data = [
                {
                    "id": v.id,
                    "content": v.modified_content,
                    "result": execution_results[i] if i < len(execution_results) else {},
                }
                for i, v in enumerate(failed_variations)
            ]

            result = await optimizer.reflect(
                failed_variations=variation_data,
                context=f"Sprint {context.sprint_number}: {context.goal}",
            )

            return {
                "lessons_learned": result.get("lessons", []),
                "improvement_suggestions": result.get("suggestions", []),
                "root_causes": result.get("root_causes", []),
                "confidence_adjustments": result.get("confidence_factors", {}),
            }
        except Exception as e:
            logger.error(f"GEPA reflect 失败: {e}")
            return self._reflect_fallback(failed_variations, execution_results, context)

    def _reflect_fallback(
        self,
        failed_variations: List[Variation],
        execution_results: List[Dict[str, Any]],
        context: SprintContext,
    ) -> Dict[str, Any]:
        """内置简化反思逻辑"""
        lessons_learned: List[str] = []
        root_causes: List[str] = []
        improvement_suggestions: List[str] = []
        confidence_adjustments: Dict[str, float] = {}

        # 分析失败模式
        error_types: Dict[str, int] = {}
        for i, result in enumerate(execution_results):
            if not result.get("success", True):
                error_type = result.get("error_type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1

                if error_type == "syntax_error":
                    lessons_learned.append("语法错误: 变异引入的代码不符合 Python 语法")
                    root_causes.append(f"Variation {failed_variations[i].id}: 语法验证不足")
                    improvement_suggestions.append("在变异生成后添加语法检查步骤")
                    confidence_adjustments[failed_variations[i].id] = 0.2

                elif error_type == "runtime_error":
                    lessons_learned.append("运行时错误: 变异代码执行时出错")
                    root_causes.append(f"Variation {failed_variations[i].id}: 运行时行为未充分验证")
                    improvement_suggestions.append("增加单元测试覆盖，在沙箱环境中验证运行时行为")
                    confidence_adjustments[failed_variations[i].id] = 0.3

                elif error_type == "performance_degradation":
                    lessons_learned.append("性能下降: 变异导致执行效率降低")
                    root_causes.append(f"Variation {failed_variations[i].id}: 性能影响未预估")
                    improvement_suggestions.append("增加性能基准测试，评估变异前后的性能差异")
                    confidence_adjustments[failed_variations[i].id] = 0.25

                elif error_type == "logic_error":
                    lessons_learned.append("逻辑错误: 变异改变了原有正确的业务逻辑")
                    root_causes.append(f"Variation {failed_variations[i].id}: 语义保持性不足")
                    improvement_suggestions.append("增加语义相似度检查，确保业务逻辑不被破坏")
                    confidence_adjustments[failed_variations[i].id] = 0.15

                else:
                    lessons_learned.append(f"未知错误类型: {error_type}")
                    root_causes.append(f"Variation {failed_variations[i].id}: 原因不明")
                    improvement_suggestions.append("需要进一步调查失败原因")
                    confidence_adjustments[failed_variations[i].id] = 0.4

        # 统计反思
        total_failures = sum(error_types.values())
        if total_failures > 0:
            most_common = max(error_types.items(), key=lambda x: x[1])
            lessons_learned.append(
                f"共 {total_failures} 次失败，最常见错误类型: {most_common[0]} ({most_common[1]}次)"
            )

        # 生成通用改进建议
        if len(failed_variations) > 3:
            improvement_suggestions.append("失败率较高，考虑回滚到稳定版本，重新制定进化策略")

        # 保存反思结果到缓存
        self._save_reflection_cache(context.sprint_id, {
            "lessons_learned": lessons_learned,
            "root_causes": root_causes,
            "improvement_suggestions": improvement_suggestions,
            "confidence_adjustments": confidence_adjustments,
            "failed_count": len(failed_variations),
            "total_failures": total_failures,
        })

        return {
            "lessons_learned": lessons_learned,
            "improvement_suggestions": improvement_suggestions,
            "root_causes": root_causes,
            "confidence_adjustments": confidence_adjustments,
        }

    def _save_reflection_cache(self, sprint_id: str, reflection_data: Dict[str, Any]) -> None:
        """保存反思结果到缓存"""
        cache_file = self.cache_dir / f"{sprint_id}_reflection.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(reflection_data, f, ensure_ascii=False, indent=2)
            logger.info(f"反思结果已保存: {cache_file}")
        except Exception as e:
            logger.error(f"保存反思结果失败: {e}")

    async def load_reflection(self, sprint_id: str) -> Optional[Dict[str, Any]]:
        """加载历史反思结果"""
        cache_file = self.cache_dir / f"{sprint_id}_reflection.json"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载反思结果失败: {e}")
            return None
