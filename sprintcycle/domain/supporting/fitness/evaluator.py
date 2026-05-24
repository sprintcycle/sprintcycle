"""Fitness evaluator.

This module belongs to the fitness / evaluation layer. It should only score and
recommend; it must not mutate state, render UI, or execute governance decisions.

使用接口协议，Evaluator Agent 由外层注入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sprintcycle.domain.supporting.fitness.aggregator import FitnessAggregator
from sprintcycle.domain.generic.interfaces import EvaluatorAgentProtocol


@dataclass
class FitnessEvaluator:
    """Fitness 评估器"""
    
    evaluator_agent: EvaluatorAgentProtocol
    aggregator: FitnessAggregator = field(default_factory=FitnessAggregator)

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dimensions: List[Dict[str, Any]] = list(payload.get("dimensions") or [])

        if dimensions:
            return self.aggregator.aggregate(dimensions)
        else:
            events: List[Dict[str, Any]] = list(payload.get("events") or [])
            return self.evaluator_agent.evaluate({"events": events})


__all__ = [
    "FitnessEvaluator",
    "EvaluatorAgentProtocol",
]
