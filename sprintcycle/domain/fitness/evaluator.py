"""Fitness evaluator.

This module belongs to the fitness / evaluation layer. It should only score and
recommend; it must not mutate state, render UI, or execute governance decisions.

使用接口协议，Evaluator Agent 由外层注入。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sprintcycle.domain.fitness.aggregator import FitnessAggregator


class EvaluatorAgentProtocol(ABC):
    """评估器代理接口"""
    
    @abstractmethod
    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """执行评估"""
        ...


@dataclass
class FitnessEvaluator:
    """Fitness 评估器"""
    
    aggregator: FitnessAggregator = field(default_factory=FitnessAggregator)
    evaluator_agent: Optional[EvaluatorAgentProtocol] = field(default=None)

    def __post_init__(self) -> None:
        if self.evaluator_agent is None:
            # 使用默认实现（从 application 层导入）
            from sprintcycle.application.services.evaluator_agent import EvaluatorAgent
            self._agent = EvaluatorAgent()
        else:
            self._agent = self.evaluator_agent

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dimensions: List[Dict[str, Any]] = list(payload.get("dimensions") or [])
        aggregate: Dict[str, Any]

        if dimensions:
            aggregate = self.aggregator.aggregate(dimensions)
        else:
            events: List[Dict[str, Any]] = list(payload.get("events") or [])
            aggregate = self._agent.evaluate({"events": events})
        
        return aggregate


__all__ = [
    "FitnessEvaluator",
    "EvaluatorAgentProtocol",
]
