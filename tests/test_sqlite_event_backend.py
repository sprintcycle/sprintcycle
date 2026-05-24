"""SQLiteMQEventBackend：emit 持久化、异步 await、与 EventType 对齐的订阅。"""

from __future__ import annotations

import pytest

from sprintcycle.execution.core.events import Event, EventType
from sprintcycle.infrastructure.persistence.state.sqlite_event_backend import SQLiteMQEventBackend, execution_events_sqlite_path


@pytest.mark.asyncio
async def test_emit_awaits_async_handler(tmp_path):
    db = tmp_path / "ev.db"
    be = SQLiteMQEventBackend(str(db))
    try:
        log: list[str] = []

        async def h(ev: Event) -> None:
            log.append("a")

        be.on(EventType.TASK_START, h)
        await be.emit(Event(type=EventType.TASK_START, data={"k": 1}))
        assert log == ["a"]
    finally:
        await be.close()


def test_execution_events_sqlite_path_under_project(tmp_path):
    p = tmp_path / "proj"
    p.mkdir()
    out = execution_events_sqlite_path(str(p))
    assert str(p.resolve()) in out
    assert out.endswith("exec_events.sqlite")


@pytest.mark.asyncio
async def test_emit_sync_invokes_sync_handler(tmp_path):
    be = SQLiteMQEventBackend(str(tmp_path / "e2.db"))
    try:
        seen: list[Event] = []

        def h(ev: Event) -> None:
            seen.append(ev)

        be.on(EventType.SPRINT_START, h)
        await be.emit_sync(Event(type=EventType.SPRINT_START, data={"n": 2}))
        assert len(seen) == 1
        assert seen[0].data["n"] == 2
    finally:
        await be.close()


@pytest.mark.asyncio
async def test_mq_publish_triggers_bridge_sync_handler(tmp_path):
    """经 SQLiteMQ.publish 投递时走 bridge（同步 handler）。"""
    be = SQLiteMQEventBackend(str(tmp_path / "e3.db"))
    try:
        seen: list[str] = []

        def h(ev: Event) -> None:
            seen.append("x")

        be.on(EventType.EXECUTION_START, h)
        await be._mq.publish(EventType.EXECUTION_START.value, {"data": {}, "timestamp": None})
        assert seen == ["x"]
    finally:
        await be.close()
