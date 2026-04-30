"""
VariationEngine - 变异引擎
"""

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from sprintcycle.evolution.types import Gene, GeneType, Variation, VariationType

logger = logging.getLogger(__name__)


class VariationStrategy(Enum):
    RANDOM = "random"
    TARGETED = "targeted"
    GENE_BASED = "gene_based"
    REFACTORING = "refactoring"
    OPTIMIZATION = "optimization"


@dataclass
class VariationConfig:
    max_variations_per_cycle: int = 5
    mutation_rate: float = 0.1
    use_gene_pool: bool = True
    risk_threshold: str = "medium"
    strategy_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "random": 0.15,
            "targeted": 0.25,
            "gene_based": 0.25,
            "refactoring": 0.1,
            "optimization": 0.1,
            "llm": 0.15,
        }
    )


@dataclass
class GeneratedVariant:
    id: str
    gene_id: str
    variation_type: VariationType
    original_code: str
    modified_code: str
    change_summary: str
    strategy: VariationStrategy
    risk_level: str = "medium"
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def to_variation(self) -> Variation:
        return Variation(
            id=self.id,
            gene_id=self.gene_id,
            variation_type=self.variation_type,
            original_content=self.original_code,
            modified_content=self.modified_code,
            change_summary=self.change_summary,
            risk_level=self.risk_level,
            metadata={
                "strategy": self.strategy.value,
                "confidence": self.confidence,
                **self.metadata,
            },
            predicted_fitness={},
            confidence=self.confidence,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gene_id": self.gene_id,
            "variation_type": self.variation_type.value if isinstance(self.variation_type, VariationType) else self.variation_type,
            "original_code": self.original_code,
            "modified_code": self.modified_code,
            "change_summary": self.change_summary,
            "strategy": self.strategy.value,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class VariationEngine:
    def __init__(
        self,
        config: Optional[VariationConfig] = None,
        memory_store: Optional[Any] = None,
        llm_call_fn: Optional[Callable[[str], str]] = None,
    ):
        self.config = config or VariationConfig()
        self._memory = memory_store
        self._llm_call_fn = llm_call_fn
        self._gene_pool: List[Gene] = []
        self._load_genes_from_memory()
    
    def _load_genes_from_memory(self) -> None:
        if not self._memory:
            return
        
        try:
            successful_patterns = self._memory.get_successful_patterns(
                memory_type="gene",
                min_score=0.7,
                limit=50,
            )
            
            for pattern in successful_patterns:
                content = pattern.content.get("content", "")
                if content:
                    gene = Gene(
                        id=pattern.id,
                        type=GeneType.CODE,
                        content=content,
                        metadata={"source": "memory", "score": pattern.score},
                    )
                    self._gene_pool.append(gene)
            
            logger.info(f"Loaded {len(self._gene_pool)} genes from memory")
        except Exception as e:
            logger.warning(f"Failed to load genes from memory: {e}")
    
    def generate_variants(
        self,
        baseline: Any,
        goal: Optional[str] = None,
        max_count: Optional[int] = None,
    ) -> List[GeneratedVariant]:
        max_count = max_count or self.config.max_variations_per_cycle
        
        original_code = self._extract_code(baseline)
        if not original_code:
            logger.warning("No code to vary")
            return []
        
        variants: List[Any] = []
        
        for strategy_name, weight in self.config.strategy_weights.items():
            if len(variants) >= max_count:
                break
            
            count = max(1, int(max_count * weight))
            
            if strategy_name == "random":
                variants.extend(self._generate_random_variants(original_code, count))
            elif strategy_name == "targeted":
                variants.extend(self._generate_targeted_variants(original_code, goal, count))
            elif strategy_name == "gene_based":
                variants.extend(self._generate_gene_based_variants(original_code, count))
            elif strategy_name == "refactoring":
                variants.extend(self._generate_refactoring_variants(original_code, count))
            elif strategy_name == "optimization":
                variants.extend(self._generate_optimization_variants(original_code, count))
            elif strategy_name == "llm":
                variants.extend(self._generate_llm_variants(original_code, goal, count))
        
        variants = self._deduplicate_variants(variants)
        return variants[:max_count]
    
    def _extract_code(self, baseline: Any) -> str:
        if isinstance(baseline, str):
            return baseline
        elif hasattr(baseline, "code"):
            return baseline.code
        elif hasattr(baseline, "original_code"):
            return baseline.original_code
        elif isinstance(baseline, dict):
            return baseline.get("code", baseline.get("original_code", ""))
        return ""
    
    def _generate_random_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        strategies = [
            ("添加日志", self._add_logging),
            ("添加类型注解", self._add_type_hints),
            ("简化条件", self._simplify_condition),
            ("提取常量", self._extract_constant),
        ]
        
        variants: List[Any] = []
        for i in range(min(count, len(strategies))):
            name, func = strategies[i]
            try:
                modified = func(code)
                if modified and modified != code:
                    variants.append(GeneratedVariant(
                        id=str(uuid.uuid4()),
                        gene_id="",
                        variation_type=VariationType.POINT,
                        original_code=code,
                        modified_code=modified,
                        change_summary=name,
                        strategy=VariationStrategy.RANDOM,
                        risk_level="low",
                        confidence=0.4,
                    ))
            except Exception as e:
                logger.debug(f"Random variation failed: {e}")
        
        return variants
    
    def _generate_targeted_variants(
        self, code: str, goal: Optional[str], count: int
    ) -> List[GeneratedVariant]:
        if not goal:
            return []
        
        variants: List[Any] = []
        
        if "性能" in goal or "performance" in goal.lower():
            variants.extend(self._generate_performance_variants(code, count // 2 + 1))
        
        if "可读性" in goal or "readability" in goal.lower():
            variants.extend(self._generate_readability_variants(code, count // 2 + 1))
        
        if "错误处理" in goal or "error" in goal.lower():
            variants.extend(self._generate_error_handling_variants(code, count // 2 + 1))
        
        for v in variants:
            v.strategy = VariationStrategy.TARGETED
            v.confidence = 0.6
        
        return variants[:count]
    
    def _generate_gene_based_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        if not self._gene_pool:
            return []
        
        variants: List[Any] = []
        for gene in self._gene_pool[:count]:
            try:
                modified = self._apply_gene(code, gene)
                if modified and modified != code:
                    variants.append(GeneratedVariant(
                        id=str(uuid.uuid4()),
                        gene_id=gene.id,
                        variation_type=VariationType.BLOCK,
                        original_code=code,
                        modified_code=modified,
                        change_summary=f"应用基因模式: {gene.id}",
                        strategy=VariationStrategy.GENE_BASED,
                        risk_level="medium",
                        confidence=0.5 + gene.metadata.get("score", 0.5) * 0.3,
                    ))
            except Exception as e:
                logger.debug(f"Gene-based variation failed: {e}")
        
        return variants
    
    def _generate_refactoring_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        """基于规则的代码重构变体"""
        import re
        variants: List[Any] = []
        
        # 策略1: 简化条件表达式 (if x == True -> if x)
        def simplify_conditions(code: str) -> str:
            code = re.sub(r'if\s+(\w+)\s*==\s*True:', r'if :', code)
            code = re.sub(r'if\s+(\w+)\s*!=\s*False:', r'if :', code)
            code = re.sub(r'if\s+(\w+)\s*==\s*False:', r'if not :', code)
            code = re.sub(r'if\s+(\w+)\s*!=\s*True:', r'if not :', code)
            return code
        
        simplified = simplify_conditions(code)
        if simplified != code:
            variants.append(GeneratedVariant(
                id=str(uuid.uuid4()), gene_id="",
                variation_type=VariationType.POINT,
                original_code=code, modified_code=simplified,
                change_summary="简化布尔条件表达式",
                strategy=VariationStrategy.REFACTORING,
                risk_level="low", confidence=0.7,
            ))
        
        # 策略2: 简化return语句（消除多余临时变量）
        def simplify_returns(code: str) -> str:
            import re as _re
            pattern = r'(\w+)\s*=\s*([^\n]+)\n\s+return\s+\1'
            match = _re.search(pattern, code)
            if match and len(match.group(2)) < 80:
                return code[:match.start()] + f'return {match.group(2)}' + code[match.end():]
            return code
        
        extracted = simplify_returns(code)
        if extracted != code:
            variants.append(GeneratedVariant(
                id=str(uuid.uuid4()), gene_id="",
                variation_type=VariationType.BLOCK,
                original_code=code, modified_code=extracted,
                change_summary="提取魔法数字为常量",
                strategy=VariationStrategy.REFACTORING,
                risk_level="medium", confidence=0.5,
            ))
        
        return variants[:count]
    
    def _generate_optimization_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        """基于规则的代码优化变体"""
        import re
        variants: List[Any] = []
        
        # 策略1: for循环转列表推导
        def loop_to_comprehension(code: str) -> str:
            pattern = r'(\w+)\s*=\s*\[\]\s*\n(\s+)for\s+(\w+)\s+in\s+([^:]+):\s*\n\s+\1\.append\(([^)]+)\)'
            match = re.search(pattern, code)
            if match:
                var, indent, item, iterable, expr = match.groups()
                comprehension = f"{var} = [{expr} for {item} in {iterable}]"
                return code[:match.start()] + comprehension + code[match.end():]
            return code
        
        optimized = loop_to_comprehension(code)
        if optimized != code:
            variants.append(GeneratedVariant(
                id=str(uuid.uuid4()), gene_id="",
                variation_type=VariationType.BLOCK,
                original_code=code, modified_code=optimized,
                change_summary="for循环转列表推导",
                strategy=VariationStrategy.OPTIMIZATION,
                risk_level="medium", confidence=0.6,
            ))
        
        # 策略2: 添加lru_cache装饰器
        def add_caching(code: str) -> str:
            func_pattern = r'(def\s+(\w+)\([^)]*\)[^:]*:)'
            match = re.search(func_pattern, code)
            if match and 'lru_cache' not in code and 'cache' not in code:
                func_name = match.group(2)
                if func_name not in ('__init__', '__str__', '__repr__'):
                    return code[:match.start()] + '@functools.lru_cache(maxsize=None)\n' + code[match.start():]
            return code
        
        cached = add_caching(code)
        if cached != code:
            variants.append(GeneratedVariant(
                id=str(uuid.uuid4()), gene_id="",
                variation_type=VariationType.POINT,
                original_code=code, modified_code=cached,
                change_summary="添加lru_cache缓存",
                strategy=VariationStrategy.OPTIMIZATION,
                risk_level="low", confidence=0.5,
            ))
        
        return variants[:count]
    
    def _generate_performance_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        return self._generate_optimization_variants(code, count)
    
    def _generate_readability_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        return [
            GeneratedVariant(
                id=str(uuid.uuid4()),
                gene_id="",
                variation_type=VariationType.POINT,
                original_code=code,
                modified_code=self._add_docstring(code),
                change_summary="添加文档字符串",
                strategy=VariationStrategy.TARGETED,
                risk_level="low",
                confidence=0.6,
            )
        ][:count]
    
    def _generate_error_handling_variants(
        self, code: str, count: int
    ) -> List[GeneratedVariant]:
        return [
            GeneratedVariant(
                id=str(uuid.uuid4()),
                gene_id="",
                variation_type=VariationType.BLOCK,
                original_code=code,
                modified_code=self._add_try_except(code),
                change_summary="添加 try-except 错误处理",
                strategy=VariationStrategy.TARGETED,
                risk_level="low",
                confidence=0.7,
            )
        ][:count]
    
    def _add_logging(self, code: str) -> str:
        import re
        pattern = r'(def \w+\([^)]*\):)'
        replacement = r'\1\n    import logging\n    logger = logging.getLogger(__name__)\n    logger.info("Function called")'
        return re.sub(pattern, replacement, code, count=1)
    
    def _add_type_hints(self, code: str) -> str:
        import re
        pattern = r'def (\w+)\(([^)]*)\):'
        def add_types(match):
            func_name = match.group(1)
            params = match.group(2)
            if params.strip():
                typed_params = re.sub(r'(\w+)', r'\1: Any', params)
            else:
                typed_params = params
            return f'def {func_name}({typed_params}) -> Any:'
        return re.sub(pattern, add_types, code, count=1)
    
    def _simplify_condition(self, code: str) -> str:
        import re
        code = re.sub(r'==\s*True', '', code)
        code = re.sub(r'!=\s*False', '', code)
        return code
    
    def _extract_constant(self, code: str) -> str:
        return code
    
    def _apply_gene(self, code: str, gene: Gene) -> str:
        gene_content = gene.content
        if len(gene_content) < len(code) and len(gene_content) > 10:
            return code + "\n\n# Gene applied\n" + gene_content
        return code
    
    def _add_docstring(self, code: str) -> str:
        import re
        pattern = r'(def \w+\([^)]*\):)'
        replacement = r'\1\n    """TODO: Add docstring"""\n'
        return re.sub(pattern, replacement, code, count=1)
    
    def _add_try_except(self, code: str) -> str:
        import re
        pattern = r'(def \w+\([^)]*\):[^\n]*\n)(    [^\n]+\n)'
        replacement = r'\1    try:\n\2    except Exception as e:\n        logger.exception(e)\n'
        return re.sub(pattern, replacement, code, count=1)
    
    def _generate_llm_variants(
        self, code: str, goal: Optional[str], count: int
    ) -> List[GeneratedVariant]:
        """LLM驱动的代码变异 — 调用DeepSeek API生成改进代码"""
        if not self._llm_call_fn:
            # No LLM available, skip silently
            return []
        
        variants: List[Any] = []
        prompt = f"""Improve the following Python code. Goal: {goal or 'improve code quality'}

Original code:
```python
{code}
```

Provide ONLY the improved Python code, no explanations. Make meaningful improvements like:
- Better error handling
- More pythonic patterns
- Improved readability
- Type annotations
- Performance improvements
"""
        for i in range(count):
            try:
                result = self._llm_call_fn(prompt)
                if result and result.strip():
                    # Extract code from markdown blocks if present
                    import re
                    code_match = re.search(r'```python\n(.*?)```', result, re.DOTALL)
                    modified = code_match.group(1).strip() if code_match else result.strip()
                    
                    if modified and modified != code:
                        variants.append(GeneratedVariant(
                            id=str(uuid.uuid4()), gene_id="",
                            variation_type=VariationType.SEMANTIC,
                            original_code=code, modified_code=modified,
                            change_summary=f"LLM优化 (目标: {goal or '通用'})",
                            strategy=VariationStrategy.RANDOM,  # reuse existing enum
                            risk_level="high", confidence=0.6,
                            metadata={"llm_generated": True},
                        ))
            except Exception as e:
                logger.debug(f"LLM variation {i+1} failed: {e}")
        
        return variants[:count]

    def _deduplicate_variants(
        self, variants: List[GeneratedVariant]
    ) -> List[GeneratedVariant]:
        seen_hashes = set()
        unique = []
        
        for v in variants:
            code_hash = hashlib.md5(v.modified_code.encode()).hexdigest()
            if code_hash not in seen_hashes:
                seen_hashes.add(code_hash)
                unique.append(v)
        
        return unique
    
    def get_gene_pool(self) -> List[Gene]:
        return self._gene_pool.copy()
    
    def add_to_gene_pool(self, gene: Gene) -> None:
        if gene not in self._gene_pool:
            self._gene_pool.append(gene)
