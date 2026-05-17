from __future__ import annotations

import asyncio

import pytest

from sprintcycle.domain.fitness.multi_dimension import MultiDimensionFitness


class StubAdapter:
    def __init__(self, score: float, details: dict | None = None):
        self.score = score
        self.details = details or {}
        self.calls: list[str] = []

    def run(self, project_root: str):
        self.calls.append(project_root)
        return {"score": self.score, "details": self.details}


class AsyncStubAdapter:
    def __init__(self, score: float):
        self.score = score
        self.calls: list[str] = []

    async def run(self, project_root: str):
        self.calls.append(project_root)
        return {"score": self.score, "details": {"async": True}}


@pytest.mark.asyncio
async def test_multi_dimension_fitness_passes_with_weighted_total() -> None:
    evaluator = MultiDimensionFitness(
        ruff=StubAdapter(90),
        bandit=AsyncStubAdapter(80),
        import_linter=StubAdapter(85),
        typecheck=StubAdapter(75),
        coverage=StubAdapter(88),
        maintainability=StubAdapter(84),
        performance=StubAdapter(82),
    )

    result = await evaluator.evaluate("/tmp/project")

    assert result.passed is True
    assert result.total >= 80
    assert len(result.dimensions) == 7
    assert {d.name for d in result.dimensions} == {
        "quality",
        "security",
        "architecture",
        "types",
        "coverage",
        "maintainability",
        "performance",
    }

    payload = result.to_dict()
    assert payload["passed"] is True
    assert payload["total"] == result.total
    assert len(payload["dimensions"]) == 7


@pytest.mark.asyncio
async def test_multi_dimension_fitness_collects_suggestions_for_low_scores() -> None:
    evaluator = MultiDimensionFitness(
        ruff=StubAdapter(20),
        bandit=AsyncStubAdapter(10),
        import_linter=StubAdapter(30),
        typecheck=StubAdapter(40),
        coverage=StubAdapter(50),
        maintainability=StubAdapter(60),
        performance=StubAdapter(70),
    )

    result = await evaluator.evaluate("/tmp/project")

    assert result.passed is False
    assert result.suggestions
    assert any(item["dimension"] == "quality" for item in result.suggestions)


@pytest.mark.asyncio
async def test_multi_dimension_fitness_uses_default_weights() -> None:
    evaluator = MultiDimensionFitness(
        ruff=StubAdapter(100),
        bandit=AsyncStubAdapter(100),
        import_linter=StubAdapter(100),
        typecheck=StubAdapter(100),
        coverage=StubAdapter(100),
        maintainability=StubAdapter(100),
        performance=StubAdapter(100),
        weights=None,
    )

    result = await evaluator.evaluate("/tmp/project")

    assert result.details["threshold"] == 80
    assert result.passed is True
    assert pytest.approx(result.total, rel=1e-6) == 100.0
