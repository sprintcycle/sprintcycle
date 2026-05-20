"""基于 SQLite 的本地消息队列（stdlib ``sqlite3``，零额外依赖）。"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from .spi import MessageQueue, MQHandler, MQMessage


class SQLiteMQ(MessageQueue):
    """单实例、本地持久化 MQ；适用于开发与小数据量骨架。

    约定（MVP）：

    - ``publish``：先插入 ``pending`` 行，再**同步**调用该 ``topic`` 已注册的处理器。
    - ``ack``：将对应 ``id`` 标为 ``acked``；派发前若处理器抛错，可按需重调用 ``publish``
      或由上层重做（不重试逻辑暂不做）。
    - 多条目 fan-out ACK：同一 ``id`` 只 ack 一次，适合单消费者语义；多条订阅者应自行拆分 topic
      或换用支持 consumer group 的后端。
    """

    def __init__(self, db_path: str):
        self._path = str(Path(db_path).expanduser().resolve())
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._handlers: Dict[str, List[MQHandler]] = defaultdict(list)
        self._ensure_schema()
        try:
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
        except sqlite3.Error as e:
            logger.debug("SQLiteMQ pragma skipped: {}", e)

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS mq_messages (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_mq_messages_topic_status
                ON mq_messages(topic, status);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def subscribe(self, topic: str, handler: MQHandler) -> None:
        if not callable(handler):
            raise TypeError("handler must be callable")
        with self._lock:
            self._handlers[topic].append(handler)  # type: ignore[arg-type]

    def unsubscribe(self, topic: str, handler: MQHandler) -> None:
        with self._lock:
            lst = self._handlers.get(topic)
            if not lst:
                return
            while handler in lst:
                lst.remove(handler)
            if not lst:
                del self._handlers[topic]

    def enqueue(self, topic: str, payload: dict) -> MQMessage:
        """仅写入 ``pending`` 行并返回 ``MQMessage``，不调用订阅者。"""
        mid = uuid.uuid4().hex
        body = json.dumps(dict(payload), ensure_ascii=False)
        payload_normalized: Dict[str, Any] = json.loads(body)
        with self._lock:
            self._conn.execute(
                """INSERT INTO mq_messages (id, topic, payload, status, created_at)
                   VALUES (?, ?, ?, 'pending', datetime('now'))""",
                (mid, topic, body),
            )
            self._conn.commit()
        return MQMessage(id=mid, topic=topic, payload=payload_normalized)

    def _deliver(self, msg: MQMessage) -> None:
        with self._lock:
            handlers_snapshot = list(self._handlers.get(msg.topic, ()))
        for h in handlers_snapshot:
            try:
                result = h(msg)
                if hasattr(result, "__await__"):
                    logger.warning(
                        "SQLiteMQ: async handler for topic {!r} was scheduled but not awaited — "
                        "use a sync wrapper or SQLiteMQEventBackend.emit",
                        msg.topic,
                    )
            except Exception as e:
                logger.exception("SQLiteMQ handler error topic={}: {}", msg.topic, e)

    def publish(self, topic: str, payload: dict) -> str:
        msg = self.enqueue(topic, payload)
        self._deliver(msg)
        return msg.id

    def ack(self, message_id: str) -> None:
        with self._lock:
            cur = self._conn.execute(
                """UPDATE mq_messages SET status='acked' WHERE id=? AND status='pending'""",
                (message_id,),
            )
            self._conn.commit()
            if cur.rowcount == 0:
                logger.debug("SQLiteMQ ack ignored or duplicate: {}", message_id)

    def pending_count(self, topic: str) -> int:
        """诊断用：未 ack 的消息数。"""
        with self._lock:
            row = self._conn.execute(
                """SELECT COUNT(*) FROM mq_messages WHERE topic=? AND status='pending'""",
                (topic,),
            ).fetchone()
            return int(row[0]) if row else 0
