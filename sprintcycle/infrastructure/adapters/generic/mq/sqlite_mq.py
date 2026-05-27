"""基于 SQLite 的本地消息队列（异步 SQLAlchemy + aiosqlite）。

实现 ``MessageQueue`` SPI，支持 publish/subscribe/ack 语义。
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from typing import Dict, List

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from sprintcycle.infrastructure.adapters.generic.mq.spi import MQHandler, MQMessage, MessageQueue
from sprintcycle.infrastructure.shared.persistence.base import BaseSqliteStore


class SQLiteMQ(BaseSqliteStore, MessageQueue):
    """异步 SQLite MQ。

    约定（MVP）：
    - ``publish``：先插入 ``pending`` 行，再**同步**调用该 ``topic`` 已注册的处理器。
    - ``ack``：将对应 ``id`` 标为 ``acked``。
    - 多条目 fan-out ACK：同一 ``id`` 只 ack 一次。
    """

    def __init__(self, db_path: str) -> None:
        super().__init__(db_path)
        # 内存中的处理器注册表（跨连接共享）
        self._handlers: Dict[str, List[MQHandler]] = defaultdict(list)
        self._handlers_lock = asyncio.Lock()

    # ─────────────────────────────────────────────────────────────────
    # BaseSqliteStore 模板方法实现
    # ─────────────────────────────────────────────────────────────────

    def _define_schema(self, conn: AsyncConnection) -> None:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS mq_messages (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS idx_mq_messages_topic_status
                ON mq_messages(topic, status)
                """
            )
        )

    # ─────────────────────────────────────────────────────────────────
    # MessageQueue SPI 实现
    # ─────────────────────────────────────────────────────────────────

    async def subscribe(self, topic: str, handler: MQHandler) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable")
        async with self._handlers_lock:
            if handler not in self._handlers[topic]:
                self._handlers[topic].append(handler)

    async def unsubscribe(self, topic: str, handler: MQHandler) -> None:
        async with self._handlers_lock:
            lst = self._handlers.get(topic)
            if not lst:
                return
            while handler in lst:
                lst.remove(handler)
            if not lst:
                del self._handlers[topic]

    async def publish(self, topic: str, payload: dict) -> str:
        """发布消息并立即同步派发给订阅者。"""
        msg = await self._enqueue(topic, payload)
        await self._deliver(msg)
        return msg.id

    async def ack(self, message_id: str) -> None:
        await self.execute_modify(
            """UPDATE mq_messages SET status='acked' WHERE id=? AND status='pending'""",
            (message_id,),
        )

    async def pending_count(self, topic: str) -> int:
        """诊断用：未 ack 的消息数。"""
        row = await self.execute_one(
            """SELECT COUNT(*) FROM mq_messages WHERE topic=? AND status='pending'""",
            (topic,),
        )
        return int(row[0]) if row else 0

    # ─────────────────────────────────────────────────────────────────
    # 内部方法
    # ─────────────────────────────────────────────────────────────────

    async def _enqueue(self, topic: str, payload: dict) -> MQMessage:
        """仅写入 pending 行并返回 MQMessage。"""
        mid = uuid.uuid4().hex
        body = self.json_dumps(payload)
        await self.execute_modify(
            """INSERT INTO mq_messages (id, topic, payload, status, created_at)
               VALUES (?, ?, ?, 'pending', datetime('now'))""",
            (mid, topic, body),
        )
        return MQMessage(id=mid, topic=topic, payload=payload)

    async def _deliver(self, msg: MQMessage) -> None:
        """同步调用当前 topic 的所有处理器。"""
        async with self._handlers_lock:
            handlers_snapshot = list(self._handlers.get(msg.topic, ()))
        for h in handlers_snapshot:
            try:
                result = h(msg)
                if asyncio.iscoroutine(result):
                    logger.warning(
                        "SQLiteMQ: coroutine handler for topic {!r} was not awaited — "
                        "use SQLiteMQEventBackend.emit for async handlers",
                        msg.topic,
                    )
                    await result
            except Exception as e:
                logger.exception("SQLiteMQ handler error topic={}: {}", msg.topic, e)
