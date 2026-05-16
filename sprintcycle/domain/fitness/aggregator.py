"""Unified fitness aggregation primitives.

This module normalizes multi-dimensional fitness inputs and produces a single
explainable aggregate result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

from sprintcycle.domain.fitness.thresholds import DEFAULT_FITNESS_THRESHOLDS


@dataclass(frozen=True)
class FitnessMetadata:
    """Layered metadata for a fitness dimension.

    `core` contains standardized fields. `extra` preserves arbitrary upstream
    information without forcing normalization at the aggregator boundary.
    """

    core: Mapping[str, Any] = field(default_factory=dict)
    extra: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: Any) -> "FitnessMetadata":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            return cls()

        core = dict(value.get("core") or {}) if isinstance(value.get("core"), Mapping) else {}
        extra = dict(value.get("extra") or {}) if isinstance(value.get("extra"), Mapping) else {}

        reserved = {"core", "extra"}
        for key, raw in value.items():
            if key not in reserved:
                extra[key] = raw

        return cls(core=core, extra=extra)


@dataclass(frozen=True)
class FitnessDimensionResult:
    """A normalized result for one fitness dimension."""

    name: str
    score: float
    weight: float = 1.0
    reason: str = ""
    metadata: FitnessMetadata = field(default_factory=FitnessMetadata)

    @classmethod
    def from_value(cls, value: Any) -> "FitnessDimensionResult":
        if isinstance(value, cls):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("fitness dimension result must be a mapping")

        metadata = FitnessMetadata.from_value(value.get("metadata") or {})
        return cls(
            name=str(value.get("name") or value.get("dimension") or "unknown"),
            score=float(value.get("score") or 0),
            weight=float(value.get("weight") or 1.0),
            reason=str(value.get("reason") or ""),
            metadata=metadata,
        )


@dataclass(frozen=True)
class FitnessAggregateResult:
    total_score: float
    dimensions: List[FitnessDimensionResult]
    weighted_contributions: List[Dict[str, Any]]
    summary: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class FitnessAggregator:
    thresholds: Mapping[str, int] = field(default_factory=lambda: DEFAULT_FITNESS_THRESHOLDS)

    def aggregate(self, dimensions: Iterable[Any]) -> Dict[str, Any]:
        normalized = [FitnessDimensionResult.from_value(d) for d in dimensions]
        if not normalized:
            result = FitnessAggregateResult(
                total_score=0.0,
                dimensions=[],
                weighted_contributions=[],
                summary={"status": "empty", "thresholds": dict(self.thresholds)},
                metadata={"core": {}, "extra": {}},
            )
            return {"success": True, "data": self._serialize(result)}

        total_weight = sum(max(d.weight, 0.0) for d in normalized) or 1.0
        weighted_contributions: List[Dict[str, Any]] = []
        total_score = 0.0

        for dimension in normalized:
            weight = max(dimension.weight, 0.0)
            contribution = (dimension.score * weight) / total_weight
            total_score += contribution
            weighted_contributions.append(
                {
                    "name": dimension.name,
                    "score": dimension.score,
                    "weight": dimension.weight,
                    "contribution": contribution,
                    "reason": dimension.reason,
                    "metadata": {
                        "core": dict(dimension.metadata.core),
                        "extra": dict(dimension.metadata.extra),
                    },
                }
            )

        total_score = max(0.0, min(100.0, total_score))
        summary = self._build_summary(total_score, normalized)
        result = FitnessAggregateResult(
            total_score=total_score,
            dimensions=normalized,
            weighted_contributions=weighted_contributions,
            summary=summary,
            metadata={"core": {"dimension_count": len(normalized)}, "extra": {}},
        )
        return {"success": True, "data": self._serialize(result)}

    def _build_summary(self, total_score: float, dimensions: List[FitnessDimensionResult]) -> Dict[str, Any]:
        if total_score >= self.thresholds.get("healthy", 80):
            status = "healthy"
        elif total_score >= self.thresholds.get("watch", 60):
            status = "watch"
        elif total_score >= self.thresholds.get("degraded", 40):
            status = "degraded"
        else:
            status = "critical"

        return {
            "status": status,
            "dimension_count": len(dimensions),
            "reasons": [d.reason for d in dimensions if d.reason],
        }

    def _serialize(self, result: FitnessAggregateResult) -> Dict[str, Any]:
        return {
            "total_score": result.total_score,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.score,
                    "weight": d.weight,
                    "reason": d.reason,
                    "metadata": {
                        "core": dict(d.metadata.core),
                        "extra": dict(d.metadata.extra),
                    },
                }
                for d in result.dimensions
            ],
            "weighted_contributions": result.weighted_contributions,
            "summary": result.summary,
            "metadata": result.metadata,
        }
