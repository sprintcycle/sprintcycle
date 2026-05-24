"""Multi-dimension fitness orchestration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, Tuple


class DimensionAdapter(Protocol):
    def run(self, project_root: str) -> Any: ...


class AsyncDimensionAdapter(Protocol):
    async def run(self, project_root: str) -> Any: ...


@dataclass(frozen=True)
class DimensionScore:
    name: str
    score: float
    weight: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FitnessResult:
    total: float
    dimensions: List[DimensionScore]
    passed: bool
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "dimensions": [
                {
                    "name": d.name,
                    "score": d.score,
                    "weight": d.weight,
                    "details": dict(d.details),
                }
                for d in self.dimensions
            ],
            "passed": self.passed,
            "suggestions": [dict(item) for item in self.suggestions],
            "details": dict(self.details),
        }


@dataclass
class MultiDimensionFitness:
    ruff: Optional[DimensionAdapter] = None
    bandit: Optional[AsyncDimensionAdapter | DimensionAdapter] = None
    import_linter: Optional[DimensionAdapter] = None
    typecheck: Optional[DimensionAdapter] = None
    coverage: Optional[DimensionAdapter] = None
    maintainability: Optional[DimensionAdapter] = None
    performance: Optional[DimensionAdapter] = None
    weights: Dict[str, float] | None = None
    threshold: float = 80.0
    _default_project_root: Path = field(default_factory=lambda: Path.cwd())

    def __post_init__(self) -> None:
        self.weights = dict(self.weights or self.default_weights())
        self.ruff = self.ruff or self._build_adapter("ruff")
        self.bandit = self.bandit or self._build_adapter("bandit")
        self.import_linter = self.import_linter or self._build_adapter("import_linter")
        self.typecheck = self.typecheck or self._build_adapter("typecheck")
        self.coverage = self.coverage or self._default_coverage_adapter()
        self.maintainability = self.maintainability or self._default_maintainability_adapter()
        self.performance = self.performance or self._default_performance_adapter()
        self._dimension_sources: Dict[str, Optional[Any]] = {
            "quality": self.ruff,
            "security": self.bandit,
            "architecture": self.import_linter,
            "types": self.typecheck,
            "coverage": self.coverage,
            "maintainability": self.maintainability,
            "performance": self.performance,
        }

    @staticmethod
    def default_weights() -> Dict[str, float]:
        return {
            "quality": 0.20,
            "security": 0.15,
            "architecture": 0.20,
            "types": 0.15,
            "coverage": 0.10,
            "maintainability": 0.10,
            "performance": 0.10,
        }

    async def evaluate(self, project_root: str | None = None) -> FitnessResult:
        root = project_root or str(self._default_project_root)
        tasks = [self._evaluate_dimension(name, source, root) for name, source in self._dimension_sources.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        dimension_scores: List[DimensionScore] = []
        suggestions: List[Dict[str, Any]] = []
        for (dimension_name, _), result in zip(self._dimension_sources.items(), results):
            score, details, suggestion = self._normalize_result(dimension_name, result)
            weight = float(self.weights.get(dimension_name, 0.0) if self.weights else 0.0)
            if score >= self.threshold and dimension_name in {
                "quality",
                "security",
                "architecture",
                "types",
                "coverage",
                "maintainability",
                "performance",
            }:
                suggestion = None
            dimension_scores.append(DimensionScore(name=dimension_name, score=score, weight=weight, details=details))
            if suggestion:
                suggestions.append(suggestion)

        total_weight = sum(max(0.0, d.weight) for d in dimension_scores) or 1.0
        total = sum(max(0.0, min(100.0, d.score)) * max(0.0, d.weight) for d in dimension_scores) / total_weight
        passed = total >= self.threshold

        if not suggestions and not passed:
            worst = min(dimension_scores, key=lambda item: item.score, default=None)
            suggestions.append(
                {
                    "kind": "threshold",
                    "dimension": worst.name if worst else "overall",
                    "message": f"weighted total below threshold {self.threshold}",
                    "priority": "high",
                }
            )

        return FitnessResult(
            total=total,
            dimensions=dimension_scores,
            passed=passed,
            suggestions=suggestions,
            details={
                "threshold": self.threshold,
                "weights": dict(self.weights or {}),
            },
        )

    async def _evaluate_dimension(self, name: str, source: Optional[Any], project_root: str) -> Any:
        if source is None:
            return {
                "name": name,
                "score": 0.0,
                "details": {"status": "missing"},
                "suggestion": self._suggestion(name, 0.0),
            }

        runner = getattr(source, "run", None)
        if runner is None:
            return {
                "name": name,
                "score": 0.0,
                "details": {"status": "invalid-adapter"},
                "suggestion": self._suggestion(name, 0.0),
            }

        result = runner(project_root)
        if asyncio.iscoroutine(result):
            result = await result
        return result

    def _normalize_result(self, name: str, result: Any) -> Tuple[float, Dict[str, Any], Optional[Dict[str, Any]]]:
        if isinstance(result, Exception):
            return 0.0, {"error": str(result)}, self._suggestion(name, 0.0, str(result))

        if isinstance(result, Mapping):
            score = self._extract_score(result)
            details = dict(result.get("details") or {})
            if not details:
                details = {
                    k: v for k, v in result.items() if k not in {"score", "details", "suggestion", "suggestions"}
                }
            suggestion = result.get("suggestion") or self._suggestion(name, score)
            if score >= self.threshold:
                suggestion = None
            if score <= 0 and suggestion is None:
                suggestion = self._suggestion(name, score)
            return score, details, suggestion

        if isinstance(result, (int, float)):
            score = float(result)
            return score, {}, None if score >= self.threshold else self._suggestion(name, score)

        return 0.0, {"raw": result}, self._suggestion(name, 0.0)

    def _extract_score(self, payload: Mapping[str, Any]) -> float:
        for key in ("score", "total", "value", "passed_score"):
            if key in payload:
                try:
                    return float(payload[key])
                except (TypeError, ValueError):
                    continue
        if payload.get("passed") is True:
            return 100.0
        return 0.0

    def _suggestion(self, name: str, score: float, error: str | None = None) -> Dict[str, Any]:
        message = error or f"Improve {name} score"
        return {
            "dimension": name,
            "score": score,
            "priority": "high" if score < self.threshold else "low",
            "message": message,
        }

    @staticmethod
    def _build_adapter(name: str) -> DimensionAdapter:
        if name == "ruff":
            return _LazyAdapter("sprintcycle.governance.arch_guard.adapters.ruff_adapter", "RuffAdapter")
        if name == "bandit":
            return _LazyAdapter("sprintcycle.domain.quality_spec.adapters.bandit_adapter", "BanditAdapter")
        if name == "import_linter":
            return _LazyAdapter("sprintcycle.governance.arch_guard.adapters.import_linter", "ImportLinterAdapter")
        if name == "typecheck":
            return _LazyAdapter("sprintcycle.governance.arch_guard.adapters.typecheck_adapter", "TypeCheckAdapter")
        return _NullAdapter(name)

    @staticmethod
    def _default_coverage_adapter() -> DimensionAdapter:
        return _CoverageAdapter()

    @staticmethod
    def _default_maintainability_adapter() -> DimensionAdapter:
        return _MaintainabilityAdapter()

    @staticmethod
    def _default_performance_adapter() -> DimensionAdapter:
        return _PerformanceAdapter()


@dataclass
class _LazyAdapter:
    module_path: str
    class_name: str

    def run(self, project_root: str) -> Any:
        module = __import__(self.module_path, fromlist=[self.class_name])
        adapter_cls = getattr(module, self.class_name)
        adapter = adapter_cls()
        return adapter.run(project_root)


@dataclass
class _NullAdapter:
    name: str

    def run(self, project_root: str) -> Dict[str, Any]:
        return {
            "score": 0.0,
            "details": {"project_root": project_root, "status": f"{self.name}-unavailable"},
            "suggestion": {
                "dimension": self.name,
                "score": 0.0,
                "priority": "low",
                "message": f"{self.name} adapter unavailable",
            },
        }


@dataclass
class _CoverageAdapter:
    def run(self, project_root: str) -> Dict[str, Any]:
        return {
            "score": 0.0,
            "details": {"project_root": project_root, "status": "not-implemented"},
            "suggestion": {
                "dimension": "coverage",
                "score": 0.0,
                "priority": "low",
                "message": "coverage adapter not yet implemented",
            },
        }


@dataclass
class _MaintainabilityAdapter:
    def run(self, project_root: str) -> Dict[str, Any]:
        return {
            "score": 0.0,
            "details": {"project_root": project_root, "status": "not-implemented"},
            "suggestion": {
                "dimension": "maintainability",
                "score": 0.0,
                "priority": "low",
                "message": "maintainability adapter not yet implemented",
            },
        }


@dataclass
class _PerformanceAdapter:
    def run(self, project_root: str) -> Dict[str, Any]:
        return {
            "score": 0.0,
            "details": {"project_root": project_root, "status": "not-implemented"},
            "suggestion": {
                "dimension": "performance",
                "score": 0.0,
                "priority": "low",
                "message": "performance adapter not yet implemented",
            },
        }
