"""Fitness evaluator.

This module belongs to the fitness / evaluation layer. It should only score and
recommend; it must not mutate state, render UI, or execute governance decisions.

使用接口协议，Evaluator Agent 由外层注入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sprintcycle.domain.fitness.aggregator import FitnessAggregator
from sprintcycle.domain.interfaces import EvaluatorAgentProtocol


@dataclass
class FitnessEvaluator:
    """Fitness 评估器"""
    
    aggregator: FitnessAggregator = field(default_factory=FitnessAggregator)
    evaluator_agent: Optional[EvaluatorAgentProtocol] = field(default=None)

    def __post_init__(self) -> None:
        # 保持向后兼容的默认值
        if self.evaluator_agent is None:
            self._agent = self._get_default_agent()
        else:
            self._agent = self.evaluator_agent

    @staticmethod
    def _get_default_agent() -> EvaluatorAgentProtocol:
        """
        获取默认 EvaluatorAgent 实现
        
        注意：此方法仅用于向后兼容，新代码应显式注入。
        为避免域层纯净，默认实现延迟导入在外层提供。
        """
        try:
            from sprintcycle.application.services.evaluator_agent import EvaluatorAgent
            return EvaluatorAgent()
        except ImportError:
            # 为避免循环依赖，提供最小实现
            class MinimalEvaluator:
                def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
                    return {
                        "success": True,
                        "data": {
                            "verdict": "pending",
                            "reason": "No evaluator agent configured",
                        }
                    }
            return MinimalEvaluator()

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dimensions: List[Dict[str, Any]] = list(payload.get("dimensions") or [])
        aggregate: Dict[str, Any]

        if dimensions:
            aggregate = self.aggregator.aggregate(dimensions)
        else:
            events: List[Dict[str, Any]] = list(payload.get("events") or [])
            # 兼容两种调用方式
            if hasattr(self._agent, "evaluate"):
                try:
                    # 尝试旧版：单参数调用
                    aggregate = self._agent.evaluate({"events": events})
                except TypeError:
                    # 新版：双参数调用
                    aggregate = self._agent.evaluate({}, {"events": events})
            else:
                # 兜底
                aggregate = {
                    "success": True,
                    "data": {
                        "verdict": "pending",
                        "reason": "Evaluator agent not available",
                    }
                }
        
        return aggregate


def create_fitness_evaluator(
    evaluator_agent: EvaluatorAgentProtocol | None = None
) -> FitnessEvaluator:
    """
    工厂函数：创建 FitnessEvaluator 实例

    Args:
        evaluator_agent: 可选的评估器代理实例，如不提供将使用默认实现

    Returns:
        配置好的 FitnessEvaluator 实例
    """
    return FitnessEvaluator(evaluator_agent=evaluator_agent)


__all__ = [
    "FitnessEvaluator",
    "create_fitness_evaluator",
    "EvaluatorAgentProtocol",
]
