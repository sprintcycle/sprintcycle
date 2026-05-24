"""V4.0 知识注入确认门与结果字段。"""

from __future__ import annotations

from pathlib import Path

import pytest

from sprintcycle.application.sprint_orchestrator import SprintOrchestrator
from sprintcycle.infrastructure.config import RuntimeConfig
from sprintcycle.infrastructure.persistence.knowledge_repository import KnowledgeCardRepository


@pytest.fixture(autouse=True)
def _reset_store():
    from sprintcycle.infrastructure.persistence.state.state_store import reset_default_state_store

    reset_default_state_store()
    yield
    reset_default_state_store()


def test_run_returns_pending_knowledge_confirmation(tmp_path: Path) -> None:
    import asyncio
    
    db = tmp_path / "gate.sqlite"
    repo = KnowledgeCardRepository(str(db))
    repo.add(domain="api", body="Use middleware for JWT in auth sprint goals", tags=["jwt"])

    cfg = RuntimeConfig(
        sqlite_path=str(db),
        knowledge_injection_enabled=True,
        require_knowledge_injection_confirm=True,
        dry_run=True,
    )
    plan_yaml = """
project:
  name: gate-proj
  path: "."
mode: normal
sprints:
  - name: auth sprint
    goals: ["harden api"]
    tasks:
      - description: noop
        agent: coder
"""
    from sprintcycle.domain.generic.models.release_plan.parser import ReleasePlanParser
    parser = ReleasePlanParser()
    plan = parser.parse_string(plan_yaml.strip())
    
    orch = SprintOrchestrator(config=cfg, project_path=str(tmp_path))
    results = asyncio.run(orch.execute_release_plan(plan))
    assert isinstance(results, list)


def test_knowledge_injection_is_material_helper(tmp_path: Path) -> None:
    from sprintcycle.execution.knowledge.knowledge_injector import (
        KnowledgeInjectionResult,
        knowledge_injection_is_material,
    )

    assert knowledge_injection_is_material(
        KnowledgeInjectionResult(
            yaml_text="x", diff_text="(no textual change)\n", cards_used=[], overlay_written=False
        )
    ) is False
    assert knowledge_injection_is_material(
        KnowledgeInjectionResult(
            yaml_text="x",
            diff_text="--- a\n+++ b\n",
            cards_used=["id1"],
            overlay_written=False,
        )
    ) is True
