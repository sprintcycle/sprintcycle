"""
主执行路径回归：``ReleasePlan`` → ``SprintOrchestrator`` / ``SprintCycle.run_release_plan``。

（取代已删除的 ``EvolutionPipeline`` 覆盖场景。）
"""

import asyncio
from pathlib import Path

import pytest

from sprintcycle.api import SprintCycle
from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.application.orchestration.sprint_orchestrator import SprintOrchestrator
from sprintcycle.application.release_plan.models import (
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
        assert len(results) == 0


class TestSprintCycleRunReleasePlan:
    """``SprintCycle.run_release_plan`` 与编排器同栈。"""

    def test_run_release_plan_dry_run(self, tmp_path: Path):
        cfg = RuntimeConfig(dry_run=True, quality_level="L1")
        sc = SprintCycle(project_path=str(tmp_path), config=cfg)
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
        rr = sc.run_release_plan(plan)
        assert rr.success is True
        assert rr.completed_sprints >= 1
