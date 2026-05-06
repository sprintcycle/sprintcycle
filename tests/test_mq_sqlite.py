"""SQLiteMQ：SPI 与本地持久化行为。"""

from __future__ import annotations

import pytest

from sprintcycle.mq import MQMessage, SQLiteMQ


def test_sqlite_mq_publish_subscribe_ack(tmp_path):
    db = tmp_path / "mq.db"
    mq = SQLiteMQ(str(db))
    try:
        seen: list[MQMessage] = []

        def h(msg: MQMessage) -> None:
            seen.append(msg)
            mq.ack(msg.id)

        mq.subscribe("exec", h)
        mid = mq.publish("exec", {"n": 1})
        assert len(seen) == 1
        assert seen[0].id == mid
        assert seen[0].topic == "exec"
        assert seen[0].payload == {"n": 1}
        assert mq.pending_count("exec") == 0
    finally:
        mq.close()


def test_sqlite_mq_pending_until_ack(tmp_path):
    db = tmp_path / "mq.db"
    mq = SQLiteMQ(str(db))
    try:
        mid = mq.publish("t", {"x": 2})
        assert mq.pending_count("t") == 1
        mq.ack("nonexistent")
        assert mq.pending_count("t") == 1
        mq.ack(mid)
        assert mq.pending_count("t") == 0
    finally:
        mq.close()


def test_sqlite_mq_unsubscribe(tmp_path):
    db = tmp_path / "mq.db"
    mq = SQLiteMQ(str(db))
    try:
        calls: list[int] = []

        def h(_m):
            calls.append(1)

        mq.subscribe("t", h)
        mq.publish("t", {})
        assert calls == [1]
        mq.unsubscribe("t", h)
        mq.publish("t", {})
        assert calls == [1]
    finally:
        mq.close()


def test_sqlite_mq_subscribe_rejects_non_callable(tmp_path):
    mq = SQLiteMQ(str(tmp_path / "mq.db"))
    try:
        with pytest.raises(TypeError):
            mq.subscribe("t", "not-a-callable")  # type: ignore[arg-type]
    finally:
        mq.close()
