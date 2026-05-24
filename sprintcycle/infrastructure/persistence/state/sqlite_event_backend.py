"""
``ExecutionEventBackend`` 的 SQLite MQ 实现：``emit`` / ``emit_sync`` 持久化后派发订阅者。

迁移到异步 SQLiteMQ（基于 BaseSqliteStore）。
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger

from sprintcycle.domain.core.execution.core.events import Event, EventType
from sprintcycle.infrastructure.mq import MQMessage
from sprintcycle.infrastructure.mq.sqlite_mq import SQLiteMQ


def _event_type_from_topic(topic: str) -> EventType:
    for e in EventType:
        if e.value == topic:
            return e
    raise KeyError(f"unknown event topic: {topic!r}")


def _payload_from_event(event: Event) -> Dict[str, Any]:
    return {
        "data": dict(event.data),
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
    }


def _event_from_mq_message(msg: MQMessage) -> Event:
    et = _event_type_from_topic(msg.topic)
    raw_ts = msg.payload.get("timestamp")
    ts: Optional[datetime] = None
    if isinstance(raw_ts, str) and raw_ts:
        ts = datetime.fromisoformat(raw_ts)
    data = msg.payload.get("data")
    if not isinstance(data, dict):
        data = {}
    return Event(type=et, data=dict(data), timestamp=ts)


class SQLiteMQEventBackend:
    """SQLite 持久化 + 与 ``EventBus`` 对齐的订阅 API。

    依赖异步 SQLiteMQ（基于 BaseSqliteStore）。
    """

    def __init__(self, sqlite_path: str) -> None:
        self._mq = SQLiteMQ(sqlite_path)
        self._handlers: Dict[EventType, List[Callable[..., Any]]] = defaultdict(list)
        self._once_handlers: Dict[EventType, List[Callable[..., Any]]] = defaultdict(list)
        self._bridges: Dict[EventType, Any] = {}
        self._registered_topics: Set[EventType] = set()

    async def close(self) -> None:
        """关闭后端（关闭 MQ 引擎）。"""
        await self._mq.close()

    def _ensure_topic_bridge(self, event_type: EventType) -> None:
        if event_type in self._registered_topics:
            return

        async def bridge(msg: MQMessage) -> None:
            event = _event_from_mq_message(msg)
            await self._invoke_handlers_await(event)
            await self._mq.ack(msg.id)

        topic = event_type.value
        self._mq.subscribe(topic, bridge)  # type: ignore[arg-type]
        self._bridges[event_type] = bridge
        self._registered_topics.add(event_type)

    def _maybe_drop_topic_bridge(self, event_type: EventType) -> None:
        if self._handlers.get(event_type) or self._once_handlers.get(event_type):
            return
        br = self._bridges.pop(event_type, None)
        if br is not None:
            self._mq.unsubscribe(event_type.value, br)  # type: ignore[arg-type]
        self._registered_topics.discard(event_type)

    def on(self, event_type: EventType, handler: Callable[..., Any]) -> "SQLiteMQEventBackend":
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
        self._ensure_topic_bridge(event_type)
        return self

    def once(self, event_type: EventType, handler: Callable[..., Any]) -> "SQLiteMQEventBackend":
        if handler not in self._once_handlers[event_type]:
            self._once_handlers[event_type].append(handler)
        self._ensure_topic_bridge(event_type)
        return self

    def off(self, event_type: EventType, handler: Optional[Callable[..., Any]] = None) -> "SQLiteMQEventBackend":
        if handler is None:
            self._handlers[event_type] = []
            self._once_handlers[event_type] = []
        else:
            while handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
            while handler in self._once_handlers[event_type]:
                self._once_handlers[event_type].remove(handler)
        self._maybe_drop_topic_bridge(event_type)
        return self

    async def _safe_call(self, fn: Callable[..., Any], event: Event) -> None:
        try:
            result = fn(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error("Event handler error for {}: {}", event.type.value, e)

    async def _invoke_handlers_await(self, event: Event) -> None:
        for fn in list(self._handlers.get(event.type, ())):
            await self._safe_call(fn, event)
        once = list(self._once_handlers.get(event.type, ()))
        self._once_handlers[event.type] = []
        for fn in once:
            await self._safe_call(fn, event)

    async def emit(self, event: Event) -> None:
        msg = await self._mq.enqueue(event.type.value, _payload_from_event(event))
        try:
            await self._invoke_handlers_await(event)
        finally:
            await self._mq.ack(msg.id)

    async def emit_sync(self, event: Event) -> None:
        """同步派发（内部使用）。"""
        msg = await self._mq.enqueue(event.type.value, _payload_from_event(event))
        try:
            await self._invoke_handlers_await(event)
        finally:
            await self._mq.ack(msg.id)

    def clear(self) -> None:
        for et in list(self._registered_topics):
            br = self._bridges.pop(et, None)
            if br is not None:
                self._mq.unsubscribe(et.value, br)  # type: ignore[arg-type]
        self._registered_topics.clear()
        self._handlers.clear()
        self._once_handlers.clear()

    def has_listeners(self, event_type: EventType) -> bool:
        return bool(self._handlers.get(event_type) or self._once_handlers.get(event_type))


def execution_events_sqlite_path(project_path: str) -> str:
    """默认执行事件库路径（与状态库同目录约定）。"""
    from pathlib import Path

    root = Path(project_path).expanduser().resolve()
    return str(root / ".sprintcycle" / "data" / "exec_events.sqlite")


async def fetch_execution_events_for_replay(
    sqlite_path: str,
    execution_id: str,
    *,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    只读：从 SQLiteMQ 落库的 ``mq_messages`` 中筛选 execution_id 匹配的事件，
    按时间正序返回（便于时间线回放）。
    """
    import json
    from pathlib import Path

    path = Path(sqlite_path).expanduser().resolve()
    if not path.is_file():
        return []

    eid = (execution_id or "").strip()
    if not eid:
        return []

    lim = max(1, min(int(limit), 2000))

    # 使用 aiosqlite 直接查询（只读诊断函数）
    import aiosqlite

    async with aiosqlite.connect(str(path)) as conn:
        conn.row_factory = aiosqlite.Row
        try:
            cur = await conn.execute(
                """
                SELECT id, topic, payload, created_at FROM mq_messages
                WHERE json_valid(payload)
                  AND json_extract(payload, '$.data.execution_id') = ?
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (eid, lim),
            )
            rows = await cur.fetchall()
            return [_row_to_item(r) for r in rows]
        except aiosqlite.OperationalError:
            pass

        # 降级方案：Python 过滤
        cur = await conn.execute(
            """
            SELECT id, topic, payload, created_at FROM mq_messages
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (lim * 20,),
        )
        out: list[dict[str, Any]] = []
        for r in await cur.fetchall():
            try:
                obj = json.loads(r["payload"])
                if not isinstance(obj, dict):
                    continue
                inner = obj.get("data")
                if not isinstance(inner, dict):
                    continue
                if str(inner.get("execution_id") or "") != eid:
                    continue
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
            out.append(_row_to_item(r))
        out.sort(key=lambda x: (x.get("created_at") or "", x.get("id") or ""))
        return out[-lim:]


def _row_to_item(row: aiosqlite.Row) -> dict[str, Any]:
    """将 aiosqlite.Row 转换为字典。"""
    import json

    topic = str(row["topic"])
    raw = row["payload"]
    data: dict[str, Any] = {}
    ts: Any = None
    try:
        obj = json.loads(raw) if isinstance(raw, str) else {}
        if isinstance(obj, dict):
            inner = obj.get("data")
            if isinstance(inner, dict):
                data = dict(inner)
            ts = obj.get("timestamp")
    except json.JSONDecodeError:
        pass
    return {
        "id": str(row["id"]),
        "event_type": topic,
        "timestamp": ts or str(row["created_at"]),
        "created_at": str(row["created_at"]),
        "data": data,
    }
