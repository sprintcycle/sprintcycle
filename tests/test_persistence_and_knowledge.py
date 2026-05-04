"""SQLite 执行存储、JSON 导入、知识卡片与注入。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sprintcycle.config import RuntimeConfig
from sprintcycle.execution.knowledge_injector import KnowledgeInjector
from sprintcycle.execution.sprint_types import ExecutionStatus
from sprintcycle.execution.state_store import (
    ExecutionState,
    configure_default_store,
    get_state_store,
    reset_default_state_store,
)
from sprintcycle.persistence.import_json_state import import_json_executions_to_sqlite
from sprintcycle.persistence.knowledge_repository import KnowledgeCardRepository


@pytest.fixture(autouse=True)
def _reset_store():
    reset_default_state_store()
    yield
    reset_default_state_store()


def test_sqlite_execution_store_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "db.sqlite"
    cfg = RuntimeConfig(storage_backend="sqlite", sqlite_path=str(db))
    configure_default_store(str(tmp_path), cfg)
    store = get_state_store()
    st = ExecutionState(
        execution_id="e1",
        prd_name="p",
        mode="normal",
        status=ExecutionStatus.RUNNING,
        current_sprint=0,
        total_sprints=2,
        completed_tasks=0,
        total_tasks=3,
        metadata={"pre_execution_commit": "abc"},
    )
    store.save(st)
    loaded = store.load("e1")
    assert loaded is not None
    assert loaded.execution_id == "e1"
    assert loaded.status == ExecutionStatus.RUNNING
    assert loaded.metadata.get("pre_execution_commit") == "abc"
    listed = store.list_executions(limit=10)
    assert len(listed) == 1
    assert store.update_status("e1", ExecutionStatus.COMPLETED)
    assert store.load("e1").status == ExecutionStatus.COMPLETED  # type: ignore[union-attr]


def test_import_json_executions(tmp_path: Path) -> None:
    jdir = tmp_path / "json_state"
    jdir.mkdir()
    st = ExecutionState(
        execution_id="imp-1",
        prd_name="x",
        mode="normal",
        status=ExecutionStatus.PAUSED,
        current_sprint=1,
        total_sprints=2,
        completed_tasks=1,
        total_tasks=2,
    )
    (jdir / "imp-1.json").write_text(json.dumps(st.to_dict(), ensure_ascii=False), encoding="utf-8")
    db = tmp_path / "merged.sqlite"
    n = import_json_executions_to_sqlite(jdir, db)
    assert n == 1
    from sprintcycle.execution.sqlite_state_store import SqliteExecutionStore

    s2 = SqliteExecutionStore(str(db))
    got = s2.load("imp-1")
    assert got is not None
    assert got.status == ExecutionStatus.PAUSED


def test_knowledge_search_and_injection(tmp_path: Path) -> None:
    db = tmp_path / "k.sqlite"
    repo = KnowledgeCardRepository(str(db))
    repo.add(domain="auth", body="Always validate JWT expiry in middleware", tags=["security", "api"])
    found = repo.search(query="JWT", limit=10)
    assert len(found) == 1
    tagged = repo.search(query="", tags=["security"], limit=10)
    assert len(tagged) == 1

    from sprintcycle.prd.models import PRD, PRDProject, PRDSprint, PRDTask, ExecutionMode

    sprint = PRDSprint(name="auth sprint", goals=["harden api"], tasks=[PRDTask(task="t", agent="coder")])
    prd = PRD(project=PRDProject(name="p", path=str(tmp_path)), mode=ExecutionMode.NORMAL, sprints=[sprint])
    inj = KnowledgeInjector(str(db))
    res = inj.inject_for_sprint(str(tmp_path), sprint, prd)
    assert "JWT" in res.yaml_text or "middleware" in res.yaml_text
    overlay = tmp_path / "prd_overlay.yaml"
    assert overlay.is_file()
    assert "experience_notes" in overlay.read_text(encoding="utf-8")
    assert res.diff_text


def test_api_knowledge_search(tmp_path: Path) -> None:
    from sprintcycle.api import SprintCycle

    db = tmp_path / "k2.sqlite"
    cfg = RuntimeConfig(sqlite_path=str(db))
    repo = KnowledgeCardRepository(str(db))
    repo.add(domain="d", body="unique-phrase-xyz")
    sc = SprintCycle(project_path=str(tmp_path), config=cfg)
    out = sc.knowledge_search(query="unique-phrase-xyz")
    assert out["success"] is True
    assert out["count"] == 1
