"""HITL 存储抽象。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from ..types import HitlRequestRecord


class HitlStore(Protocol):
    async def insert_open(self, row: HitlRequestRecord) -> None: ...

    async def resolve(self, request_id: str, decision: str, note: Optional[str], from_timeout: bool = False) -> bool: ...

    async def get(self, request_id: str) -> Optional[HitlRequestRecord]: ...

    async def list_open(self, execution_id: Optional[str] = None) -> List[HitlRequestRecord]: ...

    async def list_history(self, execution_id: Optional[str] = None, limit: int = 50) -> List[HitlRequestRecord]: ...

    async def append_event(self, request_id: str, event: Dict[str, Any]) -> None: ...
