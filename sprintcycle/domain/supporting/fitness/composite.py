"""Composite evaluation helpers for the fitness layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from sprintcycle.domain.supporting.fitness.aggregator import FitnessAggregator


@dataclass
class CompositeFitnessEvaluator:
    aggregator: FitnessAggregator = field(default_factory=FitnessAggregator)

    def evaluate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dimensions = payload.get("dimensions") or []
        if dimensions:
            return self.aggregator.aggregate(dimensions)
        return {"success": True, "data": payload}
