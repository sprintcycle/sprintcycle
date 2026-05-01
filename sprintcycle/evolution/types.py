"""
SprintCycle Evolution Types

v0.9.2: 删除空壳进化算法类型 (Gene, Variation, FitnessScore, EvolutionStage, EvolutionResult, EvolutionMetrics)
这些类型没有实际的变异/选择算法支撑，是误导性的空壳。
保留 SprintContext（被 dispatcher.py 和 execution/__init__.py 使用）。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class SprintContext:
    """Sprint 执行上下文"""
    sprint_id: str
    sprint_number: int
    goal: str
    current_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_traces: List[Dict[str, Any]] = field(default_factory=list)
    reflection: str = ""
    constraints: Dict[str, Any] = field(default_factory=dict)


__all__ = ["SprintContext"]
