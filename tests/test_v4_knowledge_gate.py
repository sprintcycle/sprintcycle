"""V4.0 知识注入确认门与结果字段。"""

from __future__ import annotations

from pathlib import Path

import pytest

from sprintcycle.api import SprintCycle
from sprintcycle.config import RuntimeConfig
from sprintcycle.persistence.knowledge_repository import KnowledgeCardRepository


@pytest.fixture(autouse=True)
def _reset_store():
    from sprintcycle.execution.state.state_store import reset_default_state_store

    reset_default_state_store()
    yield
    reset_default_state_store()


def test_run_returns_pending_knowledge_confirmation(tmp_path: Path) -> None:
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
    sc = SprintCycle(project_path=str(tmp_path), config=cfg)
    r = sc.run(release_plan_yaml=plan_yaml.strip())
    assert r.pending_knowledge_confirmation is True
    assert r.success is False
    assert r.knowledge_injection_preview.get("sprint_name") == "auth sprint"
    assert r.knowledge_injection_preview.get("cards_used")

    r2 = sc.run(release_plan_yaml=plan_yaml.strip(), confirm_knowledge=True)
    assert r2.pending_knowledge_confirmation is False


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
