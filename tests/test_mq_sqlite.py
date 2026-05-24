"""SQLiteMQ：SPI 与本地持久化行为。"""

from __future__ import annotations

import pytest

from sprintcycle.infrastructure.mq import MQMessage, SQLiteMQ


@pytest.mark.asyncio
async def test_sqlite_mq_publish_subscribe_ack(tmp_path):
    db = tmp_path / "mq.db"
    mq = SQLiteMQ(str(db))
    try:
        seen: list[MQMessage] = []

        def h(msg: MQMessage) -> None:
            seen.append(msg)
            # ack 是 async，但可以在同步 handler 中直接 await
            import asyncio
            asyncio.get_event_loop().create_task(mq.ack(msg.id))

        await mq.subscribe("exec", h)
        mid = await mq.publish("exec", {"n": 1})
        assert len(seen) == 1
        assert seen[0].id == mid
        assert seen[0].topic == "exec"
        assert seen[0].payload == {"n": 1}
        assert await mq.pending_count("exec") == 0
    finally:
        await mq.close()


@pytest.mark.asyncio
async def test_sqlite_mq_pending_until_ack(tmp_path):
    db = tmp_path / "mq.db"
    mq = SQLiteMQ(str(db))
    try:
        mid = await mq.publish("t", {"x": 2})
        assert await mq.pending_count("t") == 1
        await mq.ack("nonexistent")
        assert await mq.pending_count("t") == 1
        await mq.ack(mid)
        assert await mq.pending_count("t") == 0
    finally:
        await mq.close()


@pytest.mark.asyncio
async def test_sqlite_mq_unsubscribe(tmp_path):
    db = tmp_path / "mq.db"
    mq = SQLiteMQ(str(db))
    try:
        calls: list[int] = []

        def h(_m):
            calls.append(1)

        await mq.subscribe("t", h)
        await mq.publish("t", {})
        assert calls == [1]
        await mq.unsubscribe("t", h)
        await mq.publish("t", {})
        assert calls == [1]
    finally:
        await mq.close()


@pytest.mark.asyncio
async def test_sqlite_mq_subscribe_rejects_non_callable(tmp_path):
    mq = SQLiteMQ(str(tmp_path / "mq.db"))
    try:
        with pytest.raises(TypeError):
            await mq.subscribe("t", "not-a-callable")  # type: ignore[arg-type]
    finally:
        await mq.close()
