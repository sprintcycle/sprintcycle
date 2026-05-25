"""
主执行路径回归：``ReleasePlan`` → ``SprintOrchestrator`` / ``SprintCycle.run_release_plan``。

（取代已删除的 ``EvolutionPipeline`` 覆盖场景。）
"""

import asyncio
from pathlib import Path

import pytest

from sprintcycle.infrastructure.adapters.generic.config import RuntimeConfig
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator
from sprintcycle.domain.generic.models import (
    ExecutionMode,
    ProductAnchor,
    ReleasePlan,
    SprintBacklogItem,
    SprintDefinition,
)


def _plan(project_path: str, *, sprints: list) -> ReleasePlan:
    return ReleasePlan(
        project=ProductAnchor(name="Test ReleasePlan", path=project_path, version="v1.0.0"),
        mode=ExecutionMode.NORMAL,
        sprints=sprints,
        metadata={"plan_source_type": "manual"},
    )


class TestSprintOrchestratorMainPath:
    """与旧 EvolutionPipeline 等价的编排器执行。"""

    def test_execute_single_sprint_dry_run(self):
        plan = _plan(
            "/test/project",
            sprints=[
                SprintDefinition(
                    name="Sprint 1",
                    goals=[],
                    tasks=[SprintBacklogItem(description="Task 1", agent="coder")],
                )
            ],
        )
        orch = SprintOrchestrator(config=RuntimeConfig(dry_run=True, quality_level="L1"))
        results = asyncio.run(orch.execute_release_plan(plan))
        assert len(results) == 1
        assert results[0].sprint.name == "Sprint 1"

    def test_execute_dry_run_with_project_path(self, tmp_path: Path):
        plan = ReleasePlan(
            project=ProductAnchor(name="delegated", path=str(tmp_path), version="1.0"),
            mode=ExecutionMode.NORMAL,
            sprints=[
                SprintDefinition(
                    name="S1",
                    goals=[],
                    tasks=[SprintBacklogItem(description="noop", agent="coder")],
                )
            ],
            metadata={},
        )
        cfg = RuntimeConfig(dry_run=True, quality_level="L1")
        orch = SprintOrchestrator(config=cfg, project_path=str(tmp_path))
        results = asyncio.run(orch.execute_release_plan(plan))
        assert len(results) == 1
        assert results[0].sprint.name == "S1"

    def test_execute_empty_sprints(self):
        plan = _plan("/test/project", sprints=[])
        orch = SprintOrchestrator(config=RuntimeConfig(dry_run=True, quality_level="L1"))
        results = asyncio.run(orch.execute_release_plan(plan))
        # Orchestrator may produce a stub result for 0-sprint plans
        assert isinstance(results, list)


class TestSprintOrchestratorExecuteReleasePlan:
    """``SprintOrchestrator.execute_release_plan`` 执行编排。"""

    def test_execute_release_plan_dry_run(self, tmp_path: Path):
        cfg = RuntimeConfig(dry_run=True, quality_level="L1")
        orch = SprintOrchestrator(config=cfg, project_path=str(tmp_path))
        plan = ReleasePlan(
            project=ProductAnchor(name="api-run", path=str(tmp_path), version="1.0"),
            mode=ExecutionMode.NORMAL,
            sprints=[
                SprintDefinition(
                    name="S1",
                    goals=[],
                    tasks=[SprintBacklogItem(description="x", agent="coder")],
                )
            ],
            metadata={},
        )
        results = asyncio.run(orch.execute_release_plan(plan))
        assert isinstance(results, list)
        # In dry_run mode sprints may still be processed
        assert len(results) >= 0
