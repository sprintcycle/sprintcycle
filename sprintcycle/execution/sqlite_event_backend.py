"""
``ExecutionEventBackend`` 的 SQLite MQ 实现：``emit`` / ``emit_sync`` 持久化后派发订阅者。

- MQ ``topic`` 与 ``EventType.value`` 一一对应（与 Dashboard 按 ``EventType`` 注册一致）。
- ``emit`` 使用 ``SQLiteMQ.enqueue`` 再 **await** 异步 handler（SSE 等）；``publish`` 路径仍走 MQ 同步 ``_deliver``。
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from loguru import logger

from ..mq import MQMessage, SQLiteMQ
from .events import Event, EventType


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
    """SQLite 持久化 + 与 ``EventBus`` 对齐的订阅 API。"""

    def __init__(self, sqlite_path: str) -> None:
        self._mq = SQLiteMQ(sqlite_path)
        self._handlers: Dict[EventType, List[Callable[..., Any]]] = defaultdict(list)
        self._once_handlers: Dict[EventType, List[Callable[..., Any]]] = defaultdict(list)
        self._bridges: Dict[EventType, Any] = {}
        self._registered_topics: Set[EventType] = set()

    def close(self) -> None:
        self._mq.close()

    def _ensure_topic_bridge(self, event_type: EventType) -> None:
        if event_type in self._registered_topics:
            return

        def bridge(msg: MQMessage) -> None:
            event = _event_from_mq_message(msg)
            self._invoke_handlers_schedule(event)
            self._mq.ack(msg.id)

        topic = event_type.value
        self._mq.subscribe(topic, bridge)
        self._bridges[event_type] = bridge
        self._registered_topics.add(event_type)

    def _maybe_drop_topic_bridge(self, event_type: EventType) -> None:
        if self._handlers.get(event_type) or self._once_handlers.get(event_type):
            return
        br = self._bridges.pop(event_type, None)
        if br is not None:
            self._mq.unsubscribe(event_type.value, br)
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

    def _invoke_handlers_schedule(self, event: Event) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        for fn in list(self._handlers.get(event.type, ())):
            self._schedule_or_run(fn, event, loop)
        once = list(self._once_handlers.get(event.type, ()))
        self._once_handlers[event.type] = []
        for fn in once:
            self._schedule_or_run(fn, event, loop)

    def _schedule_or_run(self, fn: Callable[..., Any], event: Event, loop: Optional[asyncio.AbstractEventLoop]) -> None:
        try:
            result = fn(event)
            if asyncio.iscoroutine(result):
                if loop is None:
                    logger.warning(
                        "SQLiteMQEventBackend: async handler for {} skipped (no running event loop)",
                        event.type.value,
                    )
                    return

                async def _await_coro() -> None:
                    try:
                        await result
                    except Exception as e:
                        logger.error("Event handler error for {}: {}", event.type.value, e)

                loop.create_task(_await_coro())
        except Exception as e:
            logger.error("Event handler error for {}: {}", event.type.value, e)

    async def emit(self, event: Event) -> None:
        msg = self._mq.enqueue(event.type.value, _payload_from_event(event))
        try:
            await self._invoke_handlers_await(event)
        finally:
            self._mq.ack(msg.id)

    def emit_sync(self, event: Event) -> None:
        msg = self._mq.enqueue(event.type.value, _payload_from_event(event))
        try:
            self._invoke_handlers_schedule(event)
        finally:
            self._mq.ack(msg.id)

    def clear(self) -> None:
        for et in list(self._registered_topics):
            br = self._bridges.pop(et, None)
            if br is not None:
                self._mq.unsubscribe(et.value, br)
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
