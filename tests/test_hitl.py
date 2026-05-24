"""HITL：存储、协调器超时、parse_hitl_gates。"""

from __future__ import annotations

import asyncio

import pytest

from sprintcycle.infrastructure.adapters.generic.config.runtime_config import RuntimeConfig
from sprintcycle.execution.core.events import EventBus, configure_execution_event_backend, get_execution_event_backend
from sprintcycle.infrastructure.adapters.core.execution.event_backend.sqlite_event_backend import fetch_execution_events_for_replay
from sprintcycle.governance.hitl.coordinator import HitlCoordinator
from sprintcycle.governance.hitl.decision_normalize import (
    normalize_hitl_decision,
    validate_hitl_decision_for_submit,
)
from sprintcycle.governance.hitl.store import HitlSqliteStore, default_hitl_db_path
from sprintcycle.governance.hitl.types import HitlDecision, HitlGate, HitlRequestRecord, parse_hitl_gates
from sprintcycle.infrastructure.adapters.generic.mq.sqlite_mq import SQLiteMQ


@pytest.fixture
def isolated_event_bus(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configure_execution_event_backend(EventBus())


def test_parse_hitl_gates() -> None:
    assert "before_sprint" in parse_hitl_gates("before_sprint,after_task")
    assert parse_hitl_gates("") == frozenset()


def test_hitl_decision_normalize_and_validate() -> None:
    assert validate_hitl_decision_for_submit("reject") == "abort_execution"
    assert validate_hitl_decision_for_submit("Approve") == "approve"
    assert validate_hitl_decision_for_submit("regen") is None
    assert normalize_hitl_decision("SKIP") == "skip_sprint"


@pytest.mark.asyncio
async def test_fetch_execution_events_for_replay_empty_missing_db(tmp_path) -> None:
    assert await fetch_execution_events_for_replay(str(tmp_path / "missing.sqlite"), "e1") == []


@pytest.mark.asyncio
async def test_fetch_execution_events_for_replay_filters(tmp_path) -> None:
    db = tmp_path / "ev.sqlite"
    mq = SQLiteMQ(str(db))
    try:
        await mq._enqueue(
            "sprint_started",
            {
                "data": {"execution_id": "e-a", "description": "d"},
                "timestamp": "2026-01-01T00:00:00+00:00",
            },
        )
        await mq._enqueue(
            "task_done",
            {"data": {"execution_id": "e-b"}, "timestamp": "2026-01-02T00:00:00+00:00"},
        )
    finally:
        await mq.close()
    rows = await fetch_execution_events_for_replay(str(db), "e-a", limit=50)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "sprint_started"
    assert rows[0]["data"].get("execution_id") == "e-a"


@pytest.mark.asyncio
async def test_hitl_store_roundtrip(tmp_path) -> None:
    db = tmp_path / "h.db"
    store = HitlSqliteStore(str(db))
    rid = "req-1"
    row = HitlRequestRecord(
        request_id=rid,
        execution_id="ex-1",
        gate=HitlGate.BEFORE_SPRINT.value,
        status="open",
        title="t",
        summary="s",
        context={"a": 1},
        created_at="2026-01-01T00:00:00",
        timeout_seconds=60,
    )
    await store.insert_open(row)
    open_rows = await store.list_open()
    assert len(open_rows) == 1
    ok = await store.resolve(rid, HitlDecision.APPROVE.value, "ok", from_timeout=False)
    assert ok is True
    ok2 = await store.resolve(rid, HitlDecision.APPROVE.value, "x", from_timeout=False)
    assert ok2 is False
    cur = await store.get(rid)
    assert cur is not None
    assert cur.status == "resolved"
    assert cur.decision == HitlDecision.APPROVE.value


@pytest.mark.usefixtures("isolated_event_bus")
@pytest.mark.asyncio
async def test_hitl_coordinator_timeout_approve(tmp_path) -> None:
    db = tmp_path / "h.db"
    store = HitlSqliteStore(str(db))
    cfg = RuntimeConfig.merge(
        {"hitl_default_timeout_seconds": 1, "hitl_timeout_behavior": "approve"},
        RuntimeConfig(),
    )
    coord = HitlCoordinator(
        project_root=str(tmp_path),
        config=cfg,
        event_bus=get_execution_event_backend(),
        store=store,
    )
    d = await asyncio.wait_for(
        coord.wait_for_decision(
            execution_id="ex-9",
            gate=HitlGate.BEFORE_SPRINT,
            title="x",
            summary="y",
            context={},
        ),
        timeout=5.0,
    )
    assert d == HitlDecision.APPROVE


@pytest.mark.usefixtures("isolated_event_bus")
@pytest.mark.asyncio
async def test_hitl_submit_unblocks_waiter(tmp_path) -> None:
    db = tmp_path / "h.db"
    store = HitlSqliteStore(str(db))
    cfg = RuntimeConfig.merge({"hitl_default_timeout_seconds": 30}, RuntimeConfig())
    coord = HitlCoordinator(
        project_root=str(tmp_path),
        config=cfg,
        event_bus=get_execution_event_backend(),
        store=store,
    )

    async def waiter() -> HitlDecision:
        return await coord.wait_for_decision(
            execution_id="ex-w",
            gate=HitlGate.BEFORE_SPRINT,
            title="w",
            summary="s",
            context={},
        )

    t = asyncio.create_task(waiter())
    await asyncio.sleep(0.35)
    pending = await store.list_open("ex-w")
    assert len(pending) == 1
    rid = pending[0].request_id
    sub = await coord.submit_decision(rid, HitlDecision.SKIP_SPRINT.value, "skip now")
    assert sub is not None
    out = await asyncio.wait_for(t, timeout=5.0)
    assert out == HitlDecision.SKIP_SPRINT


@pytest.mark.asyncio
async def test_hitl_show_reads_db_without_hitl_enabled(tmp_path, monkeypatch) -> None:
    from sprintcycle.application.http_factories import HTTPServices

    monkeypatch.chdir(tmp_path)
    db = default_hitl_db_path(str(tmp_path.resolve()))
    store = HitlSqliteStore(db)
    rid = "req-show-1"
    await store.insert_open(
        HitlRequestRecord(
            request_id=rid,
            execution_id="ex-1",
            gate=HitlGate.BEFORE_SPRINT.value,
            status="open",
            title="t",
            summary="s",
            context={},
            created_at="2026-01-01T00:00:00",
            timeout_seconds=60,
        )
    )
    services = HTTPServices(project_path=str(tmp_path.resolve()))
    assert services.config.hitl_enabled is False
    out = await services.hitl_show(rid)
    assert out["success"] is True
    assert isinstance(out.get("data"), dict)
    assert out["data"]["request_id"] == rid


@pytest.mark.asyncio
async def test_hitl_submit_rejects_invalid_decision(tmp_path, monkeypatch) -> None:
    from sprintcycle.application.http_factories import HTTPServices

    monkeypatch.chdir(tmp_path)
    cfg = RuntimeConfig.merge({"hitl_enabled": True}, RuntimeConfig())
    services = HTTPServices(project_path=str(tmp_path.resolve()))
    services.config = cfg
    out = await services.hitl_submit("no-such-id", "regen", None)
    assert out["success"] is False
    assert "Invalid" in (out.get("error") or "")
