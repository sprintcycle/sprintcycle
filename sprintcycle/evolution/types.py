"""
SprintCycle Evolution Types
进化引擎核心类型定义

v0.9.1: 删除未使用的枚举 GeneType, VariationType, FitnessDimension
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class EvolutionStage(Enum):
    VARIATION = "variation"
    SELECTION = "selection"
    INHERITANCE = "inheritance"


@dataclass
class Gene:
    id: str
    type: str  # v0.9.1: 改为 str 类型，不再使用 GeneType 枚举
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    parent_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "fitness_scores": self.fitness_scores,
            "parent_ids": self.parent_ids,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }


@dataclass
class Variation:
    id: str
    gene_id: str
    variation_type: str  # v0.9.1: 改为 str 类型，不再使用 VariationType 枚举
    original_content: str
    modified_content: str
    change_summary: str
    risk_level: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    predicted_fitness: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return {
            "id": self.id, "gene_id": self.gene_id,
            "variation_type": self.variation_type,
            "original_content": self.original_content,
            "modified_content": self.modified_content,
            "change_summary": self.change_summary,
            "risk_level": self.risk_level,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "predicted_fitness": self.predicted_fitness,
            "confidence": self.confidence,
        }


@dataclass
class SprintContext:
    sprint_id: str
    sprint_number: int
    goal: str
    current_metrics: Dict[str, Any] = field(default_factory=dict)
    gene_pool: List[Gene] = field(default_factory=list)
    execution_traces: List[Dict[str, Any]] = field(default_factory=list)
    reflection: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvolutionResult:
    stage: EvolutionStage
    success: bool
    variations: List[Variation] = field(default_factory=list)
    selected_genes: List[Gene] = field(default_factory=list)
    inherited_genes: List[Gene] = field(default_factory=list)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage.value if isinstance(self.stage, Enum) else self.stage,
            "success": self.success,
            "variations": [v.to_dict() for v in self.variations],
            "selected_genes": [g.to_dict() for g in self.selected_genes],
            "inherited_genes": [g.to_dict() for g in self.inherited_genes],
            "error": self.error,
            "execution_time": self.execution_time,
        }


@dataclass
class EvolutionMetrics:
    total_genes: int = 0
    active_genes: int = 0
    generations: int = 0
    avg_fitness: float = 0.0
    evolution_rate: float = 0.0
    variation_count: int = 0
    selection_count: int = 0
    inheritance_count: int = 0


@dataclass
class FitnessScore:
    """统一适应度评分 - 唯一定义源"""
    correctness: float = 0.5
    performance: float = 0.5
    stability: float = 0.5
    code_quality: float = 0.5
    overall: float = 0.5

    def avg(self) -> float:
        scores = [self.correctness, self.performance, self.stability, self.code_quality]
        return sum(scores) / len(scores)

    def to_dict(self) -> Dict[str, float]:
        return {
            "correctness": self.correctness,
            "performance": self.performance,
            "stability": self.stability,
            "code_quality": self.code_quality,
            "overall": self.overall,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "FitnessScore":
        return cls(
            correctness=data.get("correctness", 0.5),
            performance=data.get("performance", 0.5),
            stability=data.get("stability", 0.5),
            code_quality=data.get("code_quality", 0.5),
            overall=data.get("overall", 0.5),
        )

    def __lt__(self, other: "FitnessScore") -> bool:
        return self.overall < other.overall

    def __gt__(self, other: "FitnessScore") -> bool:
        return self.overall > other.overall

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FitnessScore):
            return NotImplemented
        return self.overall == other.overall

    def __le__(self, other: "FitnessScore") -> bool:
        return self.overall <= other.overall

    def __ge__(self, other: "FitnessScore") -> bool:
        return self.overall >= other.overall
