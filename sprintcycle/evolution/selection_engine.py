"""
SelectionEngine - 选择引擎
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from sprintcycle.evolution.types import Variation, FitnessScore

logger = logging.getLogger(__name__)



@dataclass
class SelectionConfig:
    selection_strategy: str = "pareto"
    elite_ratio: float = 0.1
    tournament_size: int = 3
    pareto_weight_correctness: float = 0.3
    pareto_weight_performance: float = 0.2
    pareto_weight_stability: float = 0.2
    pareto_weight_quality: float = 0.3
    min_fitness_threshold: float = 0.3


@dataclass
class EvaluatedVariant:
    variant: Any
    fitness: FitnessScore
    dominated: bool = False
    pareto_rank: int = 0
    crowd_distance: float = 0.0
    
    @property
    def id(self) -> str:
        if hasattr(self.variant, "id"):
            return self.variant.id
        return str(id(self.variant))


class SelectionEngine:
    def __init__(
        self,
        config: Optional[SelectionConfig] = None,
        measurement_provider: Optional[Any] = None,
        fitness_fn: Optional[Callable[[Any], FitnessScore]] = None,
    ):
        self.config = config or SelectionConfig()
        self._measurement = measurement_provider
        self._fitness_fn = fitness_fn
        self._evaluation_history: List[EvaluatedVariant] = []
    
    def evaluate_variants(
        self,
        variants: List[Any],
        baseline: Optional[Any] = None,
    ) -> List[EvaluatedVariant]:
        if not variants:
            return []
        
        evaluated = []
        
        for variant in variants:
            try:
                fitness = self._evaluate_single(variant, baseline)
                ev = EvaluatedVariant(variant=variant, fitness=fitness)
                evaluated.append(ev)
            except Exception as e:
                logger.warning(f"Failed to evaluate variant {getattr(variant, 'id', 'unknown')}: {e}")
                ev = EvaluatedVariant(
                    variant=variant,
                    fitness=FitnessScore(correctness=0.0, overall=0.0),
                )
                ev.dominated = True
                evaluated.append(ev)
        
        self._compute_pareto_frontier(evaluated)
        self._compute_crowding_distance(evaluated)
        self._evaluation_history.extend(evaluated)
        
        evaluated.sort(
            key=lambda e: (e.pareto_rank, -e.crowd_distance),
            reverse=False,
        )
        
        logger.info(f"Evaluated {len(evaluated)} variants")
        return evaluated
    
    def _evaluate_single(
        self, variant: Any, baseline: Optional[Any] = None
    ) -> FitnessScore:
        if self._fitness_fn:
            return self._fitness_fn(variant)
        
        if self._measurement:
            try:
                code = self._get_variant_code(variant)
                predicted = getattr(variant, "predicted_fitness", None)
                if predicted:
                    return FitnessScore.from_dict(predicted)
                
                risk_level = getattr(variant, "risk_level", "medium")
                confidence = getattr(variant, "confidence", 0.5)
                risk_score = {"low": 1.0, "medium": 0.7, "high": 0.4}.get(risk_level, 0.5)
                
                fitness = FitnessScore(
                    correctness=confidence,
                    performance=risk_score,
                    stability=risk_score,
                    code_quality=confidence * 0.8 + 0.1,
                )
                fitness.overall = (
                    fitness.correctness * self.config.pareto_weight_correctness +
                    fitness.performance * self.config.pareto_weight_performance +
                    fitness.stability * self.config.pareto_weight_stability +
                    fitness.code_quality * self.config.pareto_weight_quality
                )
                return fitness
            except Exception as e:
                logger.warning(f"Measurement failed: {e}")
        
        return FitnessScore()
    
    def _get_variant_code(self, variant: Any) -> str:
        if hasattr(variant, "modified_code"):
            return variant.modified_code
        elif hasattr(variant, "modified_content"):
            return variant.modified_content
        elif isinstance(variant, dict):
            return variant.get("modified_code", variant.get("modified_content", ""))
        return ""
    
    def _compute_pareto_frontier(self, variants: List[EvaluatedVariant]) -> None:
        if not variants:
            return
        
        max_values = {
            "correctness": max(v.fitness.correctness for v in variants) or 1.0,
            "performance": max(v.fitness.performance for v in variants) or 1.0,
            "stability": max(v.fitness.stability for v in variants) or 1.0,
            "code_quality": max(v.fitness.code_quality for v in variants) or 1.0,
        }
        
        for v in variants:
            norm = FitnessScore(
                correctness=v.fitness.correctness / max_values["correctness"],
                performance=v.fitness.performance / max_values["performance"],
                stability=v.fitness.stability / max_values["stability"],
                code_quality=v.fitness.code_quality / max_values["code_quality"],
            )
            v.fitness = norm
        
        n = len(variants)
        domination_count = [0] * n
        dominated_set = [[] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    if self._dominates(variants[i], variants[j]):
                        dominated_set[i].append(j)
                    elif self._dominates(variants[j], variants[i]):
                        domination_count[i] += 1
        
        ranks = [0] * n
        current_rank = 0
        while True:
            front = [i for i in range(n) if domination_count[i] == 0]
            if not front:
                break
            
            for i in front:
                ranks[i] = current_rank
                domination_count[i] = -1  # mark as processed
                for j in dominated_set[i]:
                    domination_count[j] -= 1
        
        for i, v in enumerate(variants):
            v.pareto_rank = ranks[i]
            v.dominated = ranks[i] > 0
    
    def _dominates(self, a: EvaluatedVariant, b: EvaluatedVariant) -> bool:
        f_a = a.fitness
        f_b = b.fitness
        
        better = (
            f_a.correctness >= f_b.correctness and
            f_a.performance >= f_b.performance and
            f_a.stability >= f_b.stability and
            f_a.code_quality >= f_b.code_quality
        )
        
        strictly_better = (
            f_a.correctness > f_b.correctness or
            f_a.performance > f_b.performance or
            f_a.stability > f_b.stability or
            f_a.code_quality > f_b.code_quality
        )
        
        return better and strictly_better
    
    def _compute_crowding_distance(self, variants: List[EvaluatedVariant]) -> None:
        if len(variants) <= 2:
            for v in variants:
                v.crow_distance = float("inf")
            return
        
        dimensions = ["correctness", "performance", "stability", "code_quality"]
        
        for dim in dimensions:
            sorted_variants = sorted(variants, key=lambda v: getattr(v.fitness, dim))
            
            sorted_variants[0].crow_distance = float("inf")
            sorted_variants[-1].crow_distance = float("inf")
            
            dim_range = (
                getattr(sorted_variants[-1].fitness, dim) -
                getattr(sorted_variants[0].fitness, dim)
            )
            
            if dim_range > 0:
                for i in range(1, len(sorted_variants) - 1):
                    sorted_variants[i].crow_distance += (
                        getattr(sorted_variants[i + 1].fitness, dim) -
                        getattr(sorted_variants[i - 1].fitness, dim)
                    ) / dim_range
    
    def select_best(
        self,
        evaluated: List[EvaluatedVariant],
        baseline: Optional[EvaluatedVariant] = None,
    ) -> Optional[EvaluatedVariant]:
        if not evaluated:
            return None
        
        valid = [
            v for v in evaluated
            if v.fitness.overall >= self.config.min_fitness_threshold and not v.dominated
        ]
        
        if not valid:
            valid = sorted(evaluated, key=lambda v: v.fitness.overall, reverse=True)
            if valid:
                valid = [valid[0]]
        
        if not valid:
            return None
        
        if self.config.selection_strategy == "pareto":
            best = min(valid, key=lambda v: v.pareto_rank)
        elif self.config.selection_strategy == "tournament":
            best = self._tournament_select(valid)
        elif self.config.selection_strategy == "roulette":
            best = self._roulette_select(valid)
        else:
            best = max(valid, key=lambda v: v.fitness.overall)
        
        logger.info(
            f"Selected best variant: {best.id}, "
            f"fitness={best.fitness.overall:.3f}, "
            f"pareto_rank={best.pareto_rank}"
        )
        
        return best
    
    def _tournament_select(self, variants: List[EvaluatedVariant]) -> EvaluatedVariant:
        import random
        tournament_size = min(self.config.tournament_size, len(variants))
        tournament = random.sample(variants, tournament_size)
        return max(tournament, key=lambda v: (v.pareto_rank, -v.crowd_distance))
    
    def _roulette_select(self, variants: List[EvaluatedVariant]) -> EvaluatedVariant:
        import random
        total_fitness = sum(v.fitness.overall for v in variants)
        if total_fitness <= 0:
            return random.choice(variants)
        
        pick = random.random() * total_fitness
        cumulative = 0
        
        for v in variants:
            cumulative += v.fitness.overall
            if cumulative >= pick:
                return v
        
        return variants[-1]
    
    def select_elites(
        self, evaluated: List[EvaluatedVariant], count: int
    ) -> List[EvaluatedVariant]:
        if count <= 0:
            return []
        
        sorted_variants = sorted(
            evaluated,
            key=lambda v: (v.fitness.overall, v.crowd_distance),
            reverse=True,
        )
        
        elites = []
        seen_ids = set()
        
        for v in sorted_variants:
            vid = v.id
            if vid not in seen_ids:
                elites.append(v)
                seen_ids.add(vid)
                if len(elites) >= count:
                    break
        
        return elites
    
    def get_evaluation_history(self) -> List[EvaluatedVariant]:
        return self._evaluation_history.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_evaluated": len(self._evaluation_history),
            "strategy": self.config.selection_strategy,
            "min_threshold": self.config.min_fitness_threshold,
        }
