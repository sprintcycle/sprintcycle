"""HITL：存储、协调器超时、parse_hitl_gates。"""

from __future__ import annotations

import asyncio

import pytest

from sprintcycle.config.runtime_config import RuntimeConfig
from sprintcycle.execution.events import EventBus, configure_execution_event_backend, get_execution_event_backend
from sprintcycle.hitl.coordinator import HitlCoordinator
from sprintcycle.hitl.store_sqlite import HitlSqliteStore
from sprintcycle.hitl.types import HitlDecision, HitlGate, HitlRequestRecord, parse_hitl_gates


@pytest.fixture
def isolated_event_bus(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    configure_execution_event_backend(EventBus())


def test_parse_hitl_gates() -> None:
    assert "before_sprint" in parse_hitl_gates("before_sprint,after_task")
    assert parse_hitl_gates("") == frozenset()


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
