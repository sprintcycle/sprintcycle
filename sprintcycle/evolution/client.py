"""GEPA Client - DEPRECATED: use GEPAEngine instead"""

import warnings
warnings.warn("GEPAClient is deprecated, use sprintcycle.evolution.GEPAEngine instead", DeprecationWarning, stacklevel=2)

"""
GEPA Client - Hermes Agent Self-Evolution (GEPA) 客户端封装
提供重试机制和智能 fallback 策略
"""
import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import time
from enum import Enum
from dataclasses import dataclass

from .config import EvolutionEngineConfig
from .types import Gene, Variation, SprintContext

logger = logging.getLogger(__name__)


class GEPACallStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    FALLBACK = "fallback"
    PARTIAL = "partial"


@dataclass
class GEPACallResult:
    status: GEPACallStatus
    data: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    retry_count: int = 0
    used_fallback: bool = False
    
    @property
    def is_success(self) -> bool:
        return self.status in (GEPACallStatus.SUCCESS, GEPACallStatus.FALLBACK)


class GEPAClient:
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 30.0
    
    def __init__(self, config: EvolutionEngineConfig, max_retries: int = DEFAULT_MAX_RETRIES, retry_delay: float = DEFAULT_RETRY_DELAY, timeout: float = DEFAULT_TIMEOUT):
        self.config = config
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self._hermes_available = self._check_hermes_availability()
        self._call_stats = {"total": 0, "success": 0, "fallback": 0, "failed": 0}
        
        if not self._hermes_available:
            logger.warning("Hermes 库不可用，将使用内置 fallback 逻辑")
        else:
            logger.info("Hermes 库可用，GEPA 客户端已初始化")

    def _check_hermes_availability(self) -> bool:
        try:
            import hermes_agent
            return True
        except ImportError:
            try:
                result = subprocess.run(["python", "-c", "from hermes_agent.self_evolution import GEPAOptimizer; print('OK')"], capture_output=True, timeout=10)
                return result.returncode == 0
            except Exception:
                return False

    async def _call_with_retry(self, method: str, *args, fallback_func: Optional[callable] = None, fallback_args: tuple = (), fallback_kwargs: dict = None, **kwargs) -> GEPACallResult:
        start_time = time.time()
        retry_count = 0
        fallback_kwargs = fallback_kwargs or {}
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                if self._hermes_available:
                    result = await self._call_hermes_method(method, *args, **kwargs)
                    self._call_stats["total"] += 1
                    self._call_stats["success"] += 1
                    return GEPACallResult(status=GEPACallStatus.SUCCESS, data=result, duration=time.time() - start_time, retry_count=retry_count)
                else:
                    raise ImportError("Hermes 不可用")
            except Exception as e:
                last_error = str(e)
                if retry_count < self.max_retries:
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay * retry_count)
                    continue
                break
        
        if fallback_func:
            try:
                self._call_stats["total"] += 1
                self._call_stats["fallback"] += 1
                if asyncio.iscoroutinefunction(fallback_func):
                    result = await fallback_func(*fallback_args, **fallback_kwargs)
                else:
                    result = fallback_func(*fallback_args, **fallback_kwargs)
                return GEPACallResult(status=GEPACallStatus.FALLBACK, data=result, error=last_error, duration=time.time() - start_time, retry_count=retry_count, used_fallback=True)
            except Exception as fallback_error:
                self._call_stats["failed"] += 1
                return GEPACallResult(status=GEPACallStatus.FAILED, error=f"Fallback 也失败: {fallback_error}", duration=time.time() - start_time, retry_count=retry_count)
        else:
            self._call_stats["failed"] += 1
            return GEPACallResult(status=GEPACallStatus.FAILED, error=last_error, duration=time.time() - start_time, retry_count=retry_count)

    async def _call_hermes_method(self, method: str, *args, **kwargs) -> Any:
        from hermes_agent.self_evolution import GEPAOptimizer
        optimizer = GEPAOptimizer(llm_provider=self.config.llm_provider, llm_model=self.config.llm_model, api_key=self.config.llm_api_key, api_base=self.config.llm_api_base)
        async def call():
            return await getattr(optimizer, method)(*args, **kwargs)
        return await asyncio.wait_for(call(), timeout=self.timeout)

    async def vary(self, code: str, context: SprintContext, goal: str, max_variations: int = 5) -> List[Variation]:
        result = await self._call_with_retry(
            method="vary",
            fallback_func=self._vary_fallback,
            fallback_args=(code, context, goal, max_variations),
            code=code, context=context, goal=goal, max_variations=max_variations,
        )
        if result.is_success:
            return result.data if result.data else []
        return self._get_emergency_variations(code, context, goal)

    def _vary_fallback(self, code: str, context: SprintContext, goal: str, max_variations: int) -> List[Variation]:
        strategies = [
            ("添加错误处理", "error_handling", "low"),
            ("优化性能", "performance", "medium"),
            ("改进可读性", "readability", "low"),
            ("增强稳定性", "stability", "medium"),
            ("简化逻辑", "simplification", "low"),
        ]
        variations = []
        for i, (name, var_type, risk) in enumerate(strategies[:max_variations]):
            variation = Variation(
                id=f"var_{context.sprint_id}_{i}", gene_id="", variation_type=var_type,
                original_content=code, modified_content=self._apply_strategy(code, var_type),
                change_summary=f"应用 {name} 策略", risk_level=risk,
                metadata={"strategy": name, "goal": goal, "fallback": True},
                predicted_fitness={d: 0.5 for d in self.config.pareto_dimensions}, confidence=0.3,
            )
            variations.append(variation)
        return variations

    def _apply_strategy(self, code: str, strategy: str) -> str:
        if strategy == "error_handling":
            if "try:" not in code:
                return f"try:\n    {code}\nexcept Exception as e:\n    print(f'Error: {{e}}')\n    raise"
        return code

    def _get_emergency_variations(self, code: str, context: SprintContext, goal: str) -> List[Variation]:
        return [
            Variation(
                id=f"emergency_{context.sprint_id}_0", gene_id="", variation_type="unchanged",
                original_content=code, modified_content=code, change_summary="紧急模式",
                risk_level="low", metadata={"emergency": True, "goal": goal},
                predicted_fitness={d: 0.5 for d in self.config.pareto_dimensions}, confidence=0.1,
            ),
        ]

    async def select(self, variations: List[Variation], fitness_scores: List[Dict[str, float]]) -> List[Variation]:
        if not variations:
            return []
        result = await self._call_with_retry(
            method="select",
            fallback_func=self._select_pareto_frontier,
            fallback_args=(variations, fitness_scores),
            variations=variations, fitness_scores=fitness_scores,
        )
        if result.is_success and result.data:
            return result.data
        return self._select_pareto_frontier(variations, fitness_scores)

    def _select_pareto_frontier(self, variations: List[Variation], fitness_scores: List[Dict[str, float]]) -> List[Variation]:
        if not variations or not fitness_scores:
            return []
        pareto_front = []
        for i, variation in enumerate(variations):
            is_dominated = False
            for j, other_fs in enumerate(fitness_scores):
                if i != j and self._dominates(other_fs, fitness_scores[i]):
                    is_dominated = True
                    break
            if not is_dominated:
                pareto_front.append(variation)
        return pareto_front[:max(1, len(pareto_front) // 2)]

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
        if not elite_genes:
            return []
        result = await self._call_with_retry(
            method="inherit",
            fallback_func=self._inherit_fallback,
            fallback_args=(elite_genes, context),
            elite_genes=elite_genes, context=context,
        )
        if result.is_success and result.data:
            return result.data
        return self._inherit_fallback(elite_genes, context)

    def _inherit_fallback(self, elite_genes: List[Gene], context: SprintContext) -> List[Gene]:
        inherited = []
        for gene in elite_genes[:2]:
            inherited_gene = Gene(
                id=f"inh_{context.sprint_id}_{gene.id}", type=gene.type, content=gene.content,
                metadata=gene.metadata.copy(), fitness_scores=gene.fitness_scores.copy(),
                parent_ids=[gene.id], version=gene.version + 1,
            )
            inherited.append(inherited_gene)
        return inherited

    async def save_checkpoint(self, sprint_id: str, data: Dict[str, Any]) -> bool:
        try:
            path = self.cache_dir / f"{sprint_id}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    async def load_checkpoint(self, sprint_id: str) -> Optional[Dict[str, Any]]:
        try:
            path = self.cache_dir / f"{sprint_id}.json"
            if not path.exists():
                return None
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def get_stats(self) -> Dict[str, Any]:
        total = self._call_stats["total"]
        return {
            **self._call_stats,
            "success_rate": self._call_stats["success"] / total if total > 0 else 0,
            "fallback_rate": self._call_stats["fallback"] / total if total > 0 else 0,
            "hermes_available": self._hermes_available,
        }
