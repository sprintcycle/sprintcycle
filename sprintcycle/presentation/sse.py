"""Dashboard SSE helpers."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from loguru import logger

from sprintcycle.execution.events import Event


@dataclass
class SSEClient:
    """SSE client with its outbound queue."""

    client_id: str
    queue: asyncio.Queue[str]

    async def send(self, event: Event) -> None:
        await self.queue.put(event.to_sse_message())

    async def send_raw(self, message: str) -> None:
        await self.queue.put(message)


class SSEClientManager:
    """Manage SSE clients for a single dashboard process."""

    def __init__(self) -> None:
        self._clients: Dict[str, SSEClient] = {}
        self._lock = asyncio.Lock()

    async def create_client(self) -> SSEClient:
        client_id = str(uuid.uuid4())
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        client = SSEClient(client_id, queue)
        async with self._lock:
            self._clients[client_id] = client
        logger.info("SSE client connected: {}", client_id)
        return client

    async def remove_client(self, client_id: str) -> None:
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info("SSE client disconnected: {}", client_id)

    async def broadcast(self, event: Event) -> None:
        async with self._lock:
            clients = list(self._clients.values())

        if not clients:
            return

        message = event.to_sse_message()
        disconnected: list[str] = []
        for client in clients:
            try:
                client.queue.put_nowait(message)
            except asyncio.QueueFull:
                logger.warning("SSE client queue full: {}", client.client_id)
                disconnected.append(client.client_id)

        for client_id in disconnected:
            await self.remove_client(client_id)

    def get_client_count(self) -> int:
        return len(self._clients)


class SSEEventHandler:
    def __init__(self, client_manager: SSEClientManager):
        self._client_manager = client_manager
        self._is_running = False

    async def handle_event(self, event: Event) -> None:
        if self._is_running:
            await self._client_manager.broadcast(event)

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False


_client_manager: Optional[SSEClientManager] = None


def get_client_manager() -> SSEClientManager:
    global _client_manager
    if _client_manager is None:
        _client_manager = SSEClientManager()
    return _client_manager
