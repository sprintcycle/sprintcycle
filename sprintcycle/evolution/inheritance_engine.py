"""
InheritanceEngine - 遗传引擎：成功模式提取与复用

负责从成功的进化周期中提取基因（Gene），并在后续变异中复用这些成功模式。
这是 GEPA 自进化引擎的核心组件之一（Phase 4）。
"""

import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

from sprintcycle.evolution.types import Gene, GeneType, FitnessScore

logger = logging.getLogger(__name__)


# =============================================================================
# Extended Data Models for Inheritance Engine
# =============================================================================


@dataclass
class CodeVariant:
    """代码变体"""
    id: str
    cycle_id: str
    original_code: str
    modified_code: str
    diff_content: str = ""
    fitness_score: FitnessScore = field(default_factory=FitnessScore)
    rank: int = 0
    selected: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cycle_id": self.cycle_id,
            "original_code": self.original_code,
            "modified_code": self.modified_code,
            "diff_content": self.diff_content,
            "fitness_score": self.fitness_score.to_dict(),
            "rank": self.rank,
            "selected": self.selected,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class EvolutionCycle:
    """进化周期 — 代表一次完整的变异→选择→遗传循环"""
    id: str
    sprint_id: str
    goal: str
    best_variant: Optional[CodeVariant] = None
    variants: List[CodeVariant] = field(default_factory=list)
    fitness_scores: List[FitnessScore] = field(default_factory=list)
    success: bool = False
    improvement_rate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sprint_id": self.sprint_id,
            "goal": self.goal,
            "best_variant": self.best_variant.to_dict() if self.best_variant else None,
            "variants": [v.to_dict() for v in self.variants],
            "success": self.success,
            "improvement_rate": self.improvement_rate,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class InheritanceGene:
    """遗传基因（扩展版）— 包含使用统计和上下文标签"""
    id: str
    gene_type: GeneType
    content: str
    description: str = ""
    context_tags: List[str] = field(default_factory=list)
    success_count: int = 0
    fail_count: int = 0
    use_count: int = 0
    avg_fitness: float = 0.5
    parent_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    fitness_score: Optional["FitnessScore"] = None

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def total_uses(self) -> int:
        return self.use_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "gene_type": self.gene_type.value if isinstance(self.gene_type, GeneType) else self.gene_type,
            "content": self.content,
            "description": self.description,
            "context_tags": self.context_tags,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "use_count": self.use_count,
            "avg_fitness": self.avg_fitness,
            "parent_ids": self.parent_ids,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "metadata": self.metadata,
            "success_rate": self.success_rate,
            "fitness_score": self.fitness_score.to_dict() if self.fitness_score else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InheritanceGene":
        gene_type = data.get("gene_type", "code")
        if isinstance(gene_type, str):
            gene_type = GeneType(gene_type)
        return cls(
            id=data["id"],
            gene_type=gene_type,
            content=data["content"],
            description=data.get("description", ""),
            context_tags=data.get("context_tags", []),
            success_count=data.get("success_count", 0),
            fail_count=data.get("fail_count", 0),
            use_count=data.get("use_count", 0),
            avg_fitness=data.get("avg_fitness", 0.5),
            parent_ids=data.get("parent_ids", []),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if isinstance(data.get("created_at"), str)
                else data.get("created_at", datetime.now())
            ),
            last_used_at=(
                datetime.fromisoformat(data["last_used_at"])
                if isinstance(data.get("last_used_at"), str)
                else data.get("last_used_at")
            ),
            metadata=data.get("metadata", {}),
            fitness_score=FitnessScore.from_dict(data["fitness_score"])
                          if data.get("fitness_score") else None,
        )

    def to_gene(self) -> Gene:
        """转换为标准 Gene"""
        return Gene(
            id=self.id,
            type=self.gene_type,
            content=self.content,
            metadata={
                **self.metadata,
                "context_tags": self.context_tags,
                "success_count": self.success_count,
                "fail_count": self.fail_count,
                "avg_fitness": self.avg_fitness,
            },
            parent_ids=self.parent_ids,
        )


# =============================================================================
# Memory Store
# =============================================================================

class GeneMemoryStore:
    """基因记忆存储"""

    def __init__(self, storage_path: str = "./evolution_cache/genes"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._genes: Dict[str, InheritanceGene] = {}
        self._load_all()

    def _gene_file(self, gene_id: str) -> Path:
        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", gene_id)
        return self.storage_path / f"{safe_id}.json"

    def _load_all(self) -> None:
        try:
            for f in self.storage_path.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    gene = InheritanceGene.from_dict(data)
                    self._genes[gene.id] = gene
                except Exception as e:
                    logger.warning(f"Failed to load gene file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load genes from disk: {e}")

    def store_gene(self, gene: InheritanceGene) -> None:
        self._genes[gene.id] = gene
        try:
            with open(self._gene_file(gene.id), "w", encoding="utf-8") as f:
                json.dump(gene.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist gene {gene.id}: {e}")

    def get_gene(self, gene_id: str) -> Optional[InheritanceGene]:
        return self._genes.get(gene_id)

    def get_all_genes(self) -> List[InheritanceGene]:
        return list(self._genes.values())

    def search_genes(self, context_tags: List[str], limit: int = 10) -> List[InheritanceGene]:
        results = []
        for gene in self._genes.values():
            if any(tag in gene.context_tags for tag in context_tags):
                results.append(gene)
        return sorted(results, key=lambda g: g.success_rate, reverse=True)[:limit]

    def update_gene_stats(self, gene_id: str, success: bool, fitness: Optional[float] = None) -> None:
        gene = self._genes.get(gene_id)
        if not gene:
            return
        if success:
            gene.success_count += 1
        else:
            gene.fail_count += 1
        gene.use_count += 1
        gene.last_used_at = datetime.now()
        if fitness is not None:
            old_count = gene.use_count
            new_count = old_count + 1
            gene.avg_fitness = (gene.avg_fitness * old_count + fitness) / new_count
        self.store_gene(gene)

    def delete_gene(self, gene_id: str) -> bool:
        if gene_id in self._genes:
            del self._genes[gene_id]
            try:
                self._gene_file(gene_id).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Failed to delete gene file: {e}")
            return True
        return False


# =============================================================================
# LLM Caller
# =============================================================================

def _call_deepseek_llm(
    prompt: str,
    api_key: Optional[str] = None,
    model: str = "deepseek-chat",
    api_base: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    max_retries: int = 3,
) -> str:
    """调用 DeepSeek LLM API (with retry)"""
    key = api_key or os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", ""))
    base = (api_base or os.getenv("DEEPSEEK_API_BASE")) or "https://api.deepseek.com"
    url = f"{base.rstrip('/')}/chat/completions"

    for attempt in range(max_retries):
        try:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"LLM call attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                import time as _time
                _time.sleep(2 ** attempt)
            else:
                logger.error(f"LLM call failed after {max_retries} attempts")
                return ""
    return ""




# =============================================================================
# Exception
# =============================================================================

class InheritanceError(Exception):
    """遗传引擎异常"""
    pass


# =============================================================================
# Main Engine
# =============================================================================

class InheritanceEngine:
    """
    遗传引擎 — 成功模式提取与复用

    核心职责：
    1. extract_genes() — 从成功的进化周期中提取基因
    2. select_genes_for_variation() — 根据改进目标选择相关基因
    3. record_gene_result() — 记录基因使用结果
    4. prune_genes() — 淘汰低效基因
    """

    GENE_EXTRACT_PROMPT = """分析以下代码变更，提取可复用的改进模式。

请从变更中识别出：
1. 具体的代码模式（如：如何添加错误处理、如何优化性能）
2. 适用的上下文场景（如：错误处理、性能优化、可读性改进）
3. 该模式的核心内容

请按以下 JSON 格式输出（只输出 JSON，不要其他内容）：
{
  "description": "用一句话描述这个改进模式",
  "context_tags": ["错误处理", "性能优化"],
  "content": "具体的代码内容或模式描述"
}
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-reasoner",
        api_base: Optional[str] = None,
        temperature: float = 0.3,
        storage_path: str = "./evolution_cache/genes",
        llm_call_fn: Optional[Callable[..., str]] = None,
    ):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model
        self.api_base = api_base
        self.temperature = temperature
        self.memory = GeneMemoryStore(storage_path=storage_path)
        self._llm_call_fn = llm_call_fn

    def _call_llm(self, prompt: str) -> str:
        if self._llm_call_fn is not None:
            return self._llm_call_fn(prompt)
        return _call_deepseek_llm(
            prompt=prompt,
            api_key=self.api_key,
            model=self.model,
            api_base=self.api_base,
            temperature=self.temperature,
        )

    def extract_genes(self, cycle: EvolutionCycle) -> List[InheritanceGene]:
        """从成功的进化周期中提取基因"""
        if not cycle.success or not cycle.best_variant:
            return []

        variant = cycle.best_variant
        diff_content = variant.diff_content or self._compute_diff(
            variant.original_code, variant.modified_code
        )
        prompt = (
            f"{self.GENE_EXTRACT_PROMPT}\n\n"
            f"=== 原始代码 ===\n{variant.original_code}\n\n"
            f"=== 变更后代码 ===\n{variant.modified_code}\n\n"
            f"=== Diff ===\n{diff_content}"
        )

        try:
            result = self._call_llm(prompt)
            gene = self._parse_gene(result, cycle.id)
            if gene:
                if gene.fitness_score is None:
                    gene.fitness_score = variant.fitness_score
                self.memory.store_gene(gene)
                logger.info(f"Extracted gene {gene.id} from cycle {cycle.id}")
                return [gene]
        except Exception as e:
            logger.error(f"Gene extraction failed for cycle {cycle.id}: {e}")
        return []

    def _compute_diff(self, original: str, modified: str) -> str:
        import difflib
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile="original",
            tofile="modified",
            lineterm="",
        )
        return "".join(list(diff)[:100])

    def _parse_gene(self, llm_output: str, cycle_id: str) -> Optional[InheritanceGene]:
        if not llm_output or not llm_output.strip():
            # Return minimal fallback gene for empty input
            return InheritanceGene(
                id=f"gene_{uuid.uuid4().hex[:12]}",
                gene_type=GeneType.CODE,
                content="",
                metadata={"source_cycle_id": cycle_id, "raw_llm_output": ""},
            )

        # Parse JSON using direct extraction (avoiding regex group issues)
        json_data = self._extract_json(llm_output)
        if json_data:
            return InheritanceGene(
                id=f"gene_{uuid.uuid4().hex[:12]}",
                gene_type=GeneType.CODE,
                description=json_data.get("description", ""),
                context_tags=json_data.get("context_tags", []),
                content=json_data.get("content", llm_output),
                metadata={
                    "source_cycle_id": cycle_id,
                    "raw_llm_output": llm_output[:500],
                },
            )

        # Fallback: text extraction
        return InheritanceGene(
            id=f"gene_{uuid.uuid4().hex[:12]}",
            gene_type=GeneType.CODE,
            description=self._extract_description(llm_output),
            context_tags=self._extract_tags(llm_output),
            content=self._extract_content(llm_output) or llm_output[:500],
            metadata={"source_cycle_id": cycle_id, "raw_llm_output": llm_output[:500]},
        )

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON 对象（处理嵌套和 markdown 代码块）"""
        if not text.strip():
            return None
        # Remove markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text.strip())
        # Find first {
        start = cleaned.find("{")
        if start == -1:
            return None
        # Try to parse as JSON from start
        for end in range(len(cleaned) - 1, start, -1):
            candidate = cleaned[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
        return None

    def _extract_description(self, text: str) -> str:
        lines = text.split("\n")
        for line in lines[:5]:
            line = line.strip().strip("#*-. ")
            if line and len(line) > 10 and len(line) < 200:
                return line
        return text[:200].strip()

    def _extract_content(self, text: str) -> str:
        code_blocks = re.findall(r"```(?:\w+)?\s*(.*?)```", text, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        lines = [l.strip() for l in text.split("\n")
                 if l.startswith(("    ", "\t", "def ", "class ", "if ", "for "))]
        return "\n".join(lines[:20])

    def _extract_tags(self, text: str) -> List[str]:
        known_tags = [
            "错误处理", "性能优化", "可读性", "稳定性", "安全性",
            "error_handling", "performance", "readability", "stability", "security",
            "性能", "优化", "简化", "增强", "修复",
        ]
        found = []
        lower_text = text.lower()
        for tag in known_tags:
            if tag.lower() in lower_text:
                found.append(tag)
        return list(set(found))[:5]

    def select_genes_for_variation(self, targets: List[str]) -> List[InheritanceGene]:
        """根据改进目标选择相关基因"""
        if not targets:
            all_genes = self.memory.get_all_genes()
            return sorted(all_genes, key=lambda g: g.success_rate, reverse=True)

        selected = self.memory.search_genes(targets, limit=20)

        if len(selected) < 5:
            all_genes = self.memory.get_all_genes()
            existing_ids = {g.id for g in selected}
            remaining = [g for g in all_genes if g.id not in existing_ids]
            remaining_sorted = sorted(remaining, key=lambda g: g.success_rate, reverse=True)
            selected = selected + remaining_sorted[:5]

        for gene in selected:
            gene.use_count += 1
            self.memory.store_gene(gene)

        logger.info(f"Selected {len(selected)} genes for targets: {targets}")
        return selected

    def record_gene_result(self, gene_id: str, success: bool, fitness: Optional[float] = None) -> None:
        """记录基因使用结果，更新成功/失败计数"""
        gene = self.memory.get_gene(gene_id)
        if gene:
            self.memory.update_gene_stats(gene_id, success, fitness)
            status = "SUCCESS" if success else "FAIL"
            logger.debug(f"Gene {gene_id} result: {status}, rate: {gene.success_rate:.2f}")
        else:
            logger.warning(f"Gene {gene_id} not found when recording result")

    def prune_genes(
        self,
        min_success_rate: float = 0.3,
        min_uses: int = 3,
    ) -> int:
        """淘汰低效基因"""
        all_genes = self.memory.get_all_genes()
        pruned = 0
        for gene in all_genes:
            if gene.total_uses >= min_uses and gene.success_rate < min_success_rate:
                self.memory.delete_gene(gene.id)
                logger.info(f"Pruned gene {gene.id}: rate={gene.success_rate:.2f}, uses={gene.total_uses}")
                pruned += 1
        return pruned

    def get_gene_pool(self) -> List[InheritanceGene]:
        return self.memory.get_all_genes()

    def get_gene(self, gene_id: str) -> Optional[InheritanceGene]:
        return self.memory.get_gene(gene_id)

    def get_stats(self) -> Dict[str, Any]:
        genes = self.memory.get_all_genes()
        if not genes:
            return {
                "total_genes": 0,
                "avg_success_rate": 0.0,
                "total_uses": 0,
                "high_performers": 0,
            }
        return {
            "total_genes": len(genes),
            "avg_success_rate": sum(g.success_rate for g in genes) / len(genes),
            "total_uses": sum(g.total_uses for g in genes),
            "high_performers": sum(1 for g in genes if g.success_rate >= 0.7),
        }
